# Copyright 2014 eBay Inc.
#
# Author: Ron Rickard <rrickard@ebaysf.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from contextlib import contextmanager

from oslo.config import cfg
from oslo import messaging

from designate import backend
from designate import exceptions
from designate import objects
from designate.central import rpcapi as central_api
from designate.mdns import rpcapi as mdns_api
from designate import service
from designate.context import DesignateContext
from designate.openstack.common import log as logging
from designate.openstack.common import threadgroup
from designate.pool_manager import cache


LOG = logging.getLogger(__name__)

SUCCESS_STATUS = 'SUCCESS'
ERROR_STATUS = 'ERROR'
CREATE_ACTION = 'CREATE'
DELETE_ACTION = 'DELETE'
UPDATE_ACTION = 'UPDATE'


@contextmanager
def wrap_backend_call():
    """
    Wraps backend calls, ensuring any exception raised is a Backend exception.
    """
    try:
        yield
    except exceptions.Backend:
        raise
    except Exception as e:
        raise exceptions.Backend('Unknown backend failure: %r' % e)


def execute_on_pool(pool_id):
        def wrap(f):
            def wrapped_f(self, context, domain, *args, **kwargs):
                if domain.pool_id == pool_id:
                    LOG.debug('Domain %s is managed by pool ID %s.'
                              '  Executing.' % (domain.name, pool_id))
                    return f(self, context, domain, *args, **kwargs)
                else:
                    LOG.debug('Domain %s is not managed by pool ID %s.'
                              '  Skipping.' % (domain.name, pool_id))
            return wrapped_f
        return wrap


class Service(service.RPCService):
    """
    Service side of the Pool Manager RPC API.

    API version history:

        1.0 - Initial version
    """
    RPC_API_VERSION = '1.0'

    target = messaging.Target(version=RPC_API_VERSION)

    def __init__(self, *args, **kwargs):
        super(Service, self).__init__(*args, **kwargs)

        # Get a pool manager cache connection.
        cache_driver = cfg.CONF['service:pool_manager'].cache_driver
        self.cache = cache.get_pool_manager_cache(cache_driver)

        self.timeout = cfg.CONF['service:pool_manager'].poll_timeout
        self.retry_interval = \
            cfg.CONF['service:pool_manager'].poll_retry_interval
        self.max_retries = cfg.CONF['service:pool_manager'].poll_max_retries
        self.delay = cfg.CONF['service:pool_manager'].poll_delay

        self.server_backends = []

        sections = []
        for backend_name in cfg.CONF['service:pool_manager'].backends:
            server_ids = cfg.CONF['backend:%s' % backend_name].server_ids

            for server_id in server_ids:
                sections.append({"backend": backend_name,
                                 "server_id": server_id})

        for section in sections:
            backend_driver = section['backend']
            server_id = section['server_id']
            server = backend.get_server_object(backend_driver, server_id)

            backend_instance = backend.get_backend(
                backend_driver, server.backend_options)
            server_backend = {
                'server': server,
                'backend_instance': backend_instance
            }
            self.server_backends.append(server_backend)

        self.thread_group = threadgroup.ThreadGroup()
        self.admin_context = DesignateContext.get_admin_context(
            all_tenants=True)

    def start(self):
        for server_backend in self.server_backends:
            backend_instance = server_backend['backend_instance']
            backend_instance.start()

        self.thread_group.add_timer(
            cfg.CONF['service:pool_manager'].periodic_sync_interval,
            self.periodic_sync)

        super(Service, self).start()

    def stop(self):
        super(Service, self).stop()

        self.thread_group.stop(True)

        for server_backend in self.server_backends:
            backend_instance = server_backend['backend_instance']
            backend_instance.stop()

    @property
    def central_api(self):
        return central_api.CentralAPI.get_instance()

    @property
    def mdns_api(self):
        return mdns_api.MdnsAPI.get_instance()

    @execute_on_pool(cfg.CONF['service:pool_manager'].pool_id)
    def create_domain(self, context, domain):
        """
        :param context: Security context information.
        :param domain: The designate domain object.
        :return: None
        """
        LOG.debug("Calling create_domain.")

        for server_backend in self.server_backends:
            server = server_backend['server']
            backend_instance = server_backend['backend_instance']
            create_status = self._create_create_status(server, domain)
            try:
                with wrap_backend_call():
                    backend_instance.create_domain(context, domain)
                create_status.status = SUCCESS_STATUS
            except exceptions.Backend:
                create_status.status = ERROR_STATUS
            finally:
                self._store_in_cache(context, create_status)
                update_status = self._create_update_status(server, domain)
                update_status.serial_number = 0
                self._store_in_cache(context, update_status)

        status = ERROR_STATUS
        if self._is_create_consensus(context, domain):
            status = SUCCESS_STATUS
        self.central_api.update_status(
            context, domain.id, status, domain.serial)

        for server_backend in self.server_backends:
            server = server_backend['server']
            # PowerDNS needs a notify for the AXFR to happen reliably.
            self.mdns_api.notify_zone_changed(
                context, domain, self._get_destination(server), self.timeout,
                self.retry_interval, self.max_retries, 0)

        for server_backend in self.server_backends:
            server = server_backend['server']
            self.mdns_api.poll_for_serial_number(
                context, domain, self._get_destination(server), self.timeout,
                self.retry_interval, self.max_retries, self.delay)

    @execute_on_pool(cfg.CONF['service:pool_manager'].pool_id)
    def delete_domain(self, context, domain):
        """
        :param context: Security context information.
        :param domain: The designate domain object.
        :return: None
        """
        LOG.debug("Calling delete_domain.")

        for server_backend in self.server_backends:
            server = server_backend['server']
            backend_instance = server_backend['backend_instance']
            delete_status = self._create_delete_status(server, domain)
            try:
                with wrap_backend_call():
                    backend_instance.delete_domain(context, domain)
                delete_status.status = SUCCESS_STATUS
            except exceptions.Backend:
                delete_status.status = ERROR_STATUS
            finally:
                self._store_in_cache(context, delete_status)

        status = ERROR_STATUS
        if self._is_delete_consensus(context, domain):
            status = SUCCESS_STATUS
        self.central_api.update_status(
            context, domain.id, status, domain.serial)

    @execute_on_pool(cfg.CONF['service:pool_manager'].pool_id)
    def update_domain(self, context, domain):
        """
        :param context: Security context information.
        :param domain: The designate domain object.
        :return: None
        """
        LOG.debug("Calling update_domain.")

        LOG.debug('Serial %s for domain %s' % (domain.serial, domain.id))
        for server_backend in self.server_backends:
            server = server_backend['server']
            self.mdns_api.notify_zone_changed(
                context, domain, self._get_destination(server), self.timeout,
                self.retry_interval, self.max_retries, 0)

        for server_backend in self.server_backends:
            server = server_backend['server']
            self.mdns_api.poll_for_serial_number(
                context, domain, self._get_destination(server), self.timeout,
                self.retry_interval, self.max_retries, self.delay)

    def update_status(self, context, domain, destination,
                      status, actual_serial):
        """
        :param context: Security context information.
        :param domain: The designate domain object.
        :param destination: The server in the format "ip:port".
        :param status: The status, 'SUCCESS' or 'ERROR'.
        :param actual_serial: The actual serial number received from the name
                              server for the domain.
        :return: None
        """
        LOG.debug("Calling update_status.")

        server = self._get_server(destination)
        update_status = self._retrieve_from_cache(
            context, server, domain, UPDATE_ACTION)
        existing_serial = update_status.serial_number

        LOG.debug('Domain %s, server %s: existing serial %s, actual serial %s'
                  % (domain.id, server.id, existing_serial, actual_serial))
        if actual_serial and existing_serial < actual_serial:
            update_status.status = status
            update_status.serial_number = actual_serial
            self._store_in_cache(context, update_status)

        consensus_serial = self._get_consensus_serial(context, domain)
        LOG.debug('Consensus serial %s for domain %s'
                  % (consensus_serial, domain.id))
        if existing_serial < consensus_serial:
            self.central_api.update_status(
                context, domain.id, SUCCESS_STATUS, consensus_serial)

        if status == ERROR_STATUS:
            error_serial = self._get_error_serial(
                context, domain, consensus_serial)
            LOG.debug('Error serial %s for domain %s'
                      % (error_serial, domain.id))
            if error_serial > consensus_serial:
                self.central_api.update_status(
                    context, domain.id, ERROR_STATUS, error_serial)

    def periodic_sync(self):
        """
        :return: None
        """
        LOG.debug("Calling periodic_sync.")

        context = self.admin_context

        self._periodic_create_domains_that_failed(context)
        self._periodic_delete_domains_that_failed(context)

        criterion = {
            'pool_id': cfg.CONF['service:pool_manager'].pool_id
        }
        domains = self.central_api.find_domains(context, criterion)

        self._periodic_notify_zone_changed(context, domains)
        self._periodic_poll_for_serial_number(context, domains)

    def _periodic_create_domains_that_failed(self, context):

        create_statuses = self._find_pool_manager_statuses(
            context, CREATE_ACTION, status=ERROR_STATUS)

        for create_status in create_statuses:
            domain = self.central_api.get_domain(
                context, create_status.domain_id)
            consensus_existed = self._is_create_consensus(context, domain)

            backend_instance = self._get_server_backend(
                create_status.server_id)['backend_instance']
            try:
                with wrap_backend_call():
                    backend_instance.create_domain(context, domain)
                create_status.status = SUCCESS_STATUS
                self._store_in_cache(context, create_status)

                if not consensus_existed \
                        and self._is_create_consensus(context, domain):
                    self.central_api.update_status(
                        context, domain.id, SUCCESS_STATUS, domain.serial)
            except exceptions.Backend:
                pass

    def _periodic_delete_domains_that_failed(self, context):

        delete_statuses = self._find_pool_manager_statuses(
            context, DELETE_ACTION, status=ERROR_STATUS)

        for delete_status in delete_statuses:
            domain = self.central_api.get_domain(
                context, delete_status.domain_id)
            consensus_existed = self._is_delete_consensus(context, domain)

            backend_instance = self._get_server_backend(
                delete_status.server_id)['backend_instance']
            try:
                with wrap_backend_call():
                    backend_instance.delete_domain(context, domain)
                delete_status.status = SUCCESS_STATUS
                self._store_in_cache(context, delete_status)

                if not consensus_existed \
                        and self._is_delete_consensus(context, domain):
                    self.central_api.update_status(
                        context, domain.id, SUCCESS_STATUS, domain.serial)
            except exceptions.Backend:
                pass

    def _periodic_notify_zone_changed(self, context, domains):

        for domain in domains:
            for server_backend in self.server_backends:
                server = server_backend['server']
                pool_manager_status = self._retrieve_from_cache(
                    context, server, domain, UPDATE_ACTION)
                if pool_manager_status.serial_number < domain.serial:
                    self.mdns_api.notify_zone_changed(
                        context, domain, self._get_destination(server),
                        self.timeout, self.retry_interval, self.max_retries,
                        0)

    def _periodic_poll_for_serial_number(self, context, domains):

        for domain in domains:
            for server_backend in self.server_backends:
                server = server_backend['server']
                self.mdns_api.poll_for_serial_number(
                    context, domain, self._get_destination(server),
                    self.timeout, self.retry_interval, self.max_retries,
                    self.delay)

    def _get_server_backend(self, server_id):
        for server_backend in self.server_backends:
            server = server_backend['server']
            if server.id == server_id:
                return server_backend

    @staticmethod
    def _get_destination(server):
        return '%s:%s' % (server.host, server.port)

    def _get_server(self, destination):
        parts = destination.split(':')
        for server_backend in self.server_backends:
            server = server_backend['server']
            if server.host == parts[0] and server.port == int(parts[1]):
                return server

    @staticmethod
    def _percentage(count, total_count):
        return (float(count) / float(total_count)) * 100.0

    def _exceed_or_meet_threshold(self, count, total_count):
        return self._percentage(count, total_count) >= \
            cfg.CONF['service:pool_manager'].threshold_percentage

    def _find_pool_manager_statuses(self, context, action,
                                    domain=None, status=None):
        criterion = {
            'action': action
        }
        if domain:
            criterion['domain_id'] = domain.id
        if status:
            criterion['status'] = status

        return self.cache.find_pool_manager_statuses(
            context, criterion=criterion)

    @staticmethod
    def _get_sorted_serials(pool_manager_statuses, descending=False):
        serials = []
        for pool_manager_status in pool_manager_statuses:
            serials.append(pool_manager_status.serial_number)
        serials.sort(reverse=descending)
        return serials

    def _get_serials_ascending(self, pool_manager_statuses):
        return self._get_sorted_serials(pool_manager_statuses)

    def _get_serials_descending(self, pool_manager_statuses):
        return self._get_sorted_serials(pool_manager_statuses, descending=True)

    def _is_success_consensus(self, context, domain, action):
        pool_manager_statuses = self._find_pool_manager_statuses(
            context, action, domain=domain)
        total_count = len(pool_manager_statuses)
        success_count = 0
        for pool_manager_status in pool_manager_statuses:
            if pool_manager_status.status == SUCCESS_STATUS:
                success_count += 1
        return self._exceed_or_meet_threshold(success_count, total_count)

    def _is_create_consensus(self, context, domain):
        return self._is_success_consensus(context, domain, CREATE_ACTION)

    def _is_delete_consensus(self, context, domain):
        return self._is_success_consensus(context, domain, DELETE_ACTION)

    def _get_consensus_serial(self, context, domain):
        consensus_serial = 0
        pool_manager_statuses = self._find_pool_manager_statuses(
            context, UPDATE_ACTION, domain=domain)
        total_count = len(pool_manager_statuses)
        for serial in self._get_serials_descending(pool_manager_statuses):
            serial_count = 0
            for pool_manager_status in pool_manager_statuses:
                if pool_manager_status.serial_number >= serial:
                    serial_count += 1
            if self._exceed_or_meet_threshold(serial_count, total_count):
                consensus_serial = serial
                break
        return consensus_serial

    def _get_error_serial(self, context, domain, consensus_serial):
        error_serial = 0
        if not self._is_success_consensus(context, domain, UPDATE_ACTION):
            pool_manager_statuses = self._find_pool_manager_statuses(
                context, UPDATE_ACTION, domain=domain)
            for serial in self._get_serials_ascending(pool_manager_statuses):
                if serial > consensus_serial:
                    error_serial = serial
                    break
        return error_serial

    @staticmethod
    def _create_pool_manager_status(server, domain, action):
        values = {
            'server_id': server.id,
            'domain_id': domain.id,
            'status': None,
            'serial_number': domain.serial,
            'action': action
        }
        return objects.PoolManagerStatus(**values)

    def _create_create_status(self, server, domain):
        return self._create_pool_manager_status(server, domain, CREATE_ACTION)

    def _create_delete_status(self, server, domain):
        return self._create_pool_manager_status(server, domain, DELETE_ACTION)

    def _create_update_status(self, server, domain):
        return self._create_pool_manager_status(server, domain, UPDATE_ACTION)

    def _retrieve_from_cache(self, context, server, domain, action):
        criterion = {
            'server_id': server.id,
            'domain_id': domain.id,
            'action': action
        }
        return self.cache.find_pool_manager_status(
            context, criterion=criterion)

    def _store_in_cache(self, context, pool_manager_status):
        if pool_manager_status.id:
            self.cache.update_pool_manager_status(context, pool_manager_status)
        else:
            self.cache.create_pool_manager_status(context, pool_manager_status)
