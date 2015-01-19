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
from decimal import Decimal

from oslo.config import cfg
from oslo import messaging

from designate import backend
from designate import exceptions
from designate import objects
from designate.central import rpcapi as central_api
from designate.mdns import rpcapi as mdns_api
from designate import service
from designate.context import DesignateContext
from designate.i18n import _LE
from designate.i18n import _LI
from designate.i18n import _LW
from designate.openstack.common import log as logging
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
                    LOG.info(_LI('Domain %(domain)s is managed by this '
                                 'pool.  Executing.') %
                             {'domain': domain.name})
                    return f(self, context, domain, *args, **kwargs)
                else:
                    LOG.info(_LI('Domain %(domain)s is not managed by this '
                                 'pool.   Skipping.') %
                             {'domain': domain.name})
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

        self.threshold = cfg.CONF['service:pool_manager'].threshold_percentage
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

        if not self.server_backends:
            raise exceptions.NoPoolServersConfigured()

        self.enable_recovery_timer = \
            cfg.CONF['service:pool_manager'].enable_recovery_timer
        self.enable_sync_timer = \
            cfg.CONF['service:pool_manager'].enable_sync_timer

    def start(self):
        for server_backend in self.server_backends:
            backend_instance = server_backend['backend_instance']
            backend_instance.start()

        super(Service, self).start()

        if self.enable_recovery_timer:
            LOG.info(_LI('Starting periodic recovery timer.'))
            self.tg.add_timer(
                cfg.CONF['service:pool_manager'].periodic_recovery_interval,
                self.periodic_recovery)

        if self.enable_sync_timer:
            LOG.info(_LI('Starting periodic sync timer.'))
            self.tg.add_timer(
                cfg.CONF['service:pool_manager'].periodic_sync_interval,
                self.periodic_sync)

    def stop(self):
        super(Service, self).stop()

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
        LOG.debug("Calling create_domain for %s" % domain.name)

        for server_backend in self.server_backends:
            server = server_backend['server']
            create_status = self._create_create_status(server, domain)
            self._create_domain_on_server(
                context, create_status, domain, server_backend)

    @execute_on_pool(cfg.CONF['service:pool_manager'].pool_id)
    def delete_domain(self, context, domain):
        """
        :param context: Security context information.
        :param domain: The designate domain object.
        :return: None
        """
        LOG.debug("Calling delete_domain for %s" % domain.name)

        for server_backend in self.server_backends:
            server = server_backend['server']
            delete_status = self._create_delete_status(server, domain)
            self._delete_domain_on_server(
                context, delete_status, domain, server_backend)

        if not self._is_delete_consensus(context, domain):
            status = ERROR_STATUS
            LOG.warn(_LW('Consensus not reached '
                         'for deleting domain %(domain)s') %
                     {'domain': domain.name})
            self.central_api.update_status(
                context, domain.id, status, domain.serial)

    @execute_on_pool(cfg.CONF['service:pool_manager'].pool_id)
    def update_domain(self, context, domain):
        """
        :param context: Security context information.
        :param domain: The designate domain object.
        :return: None
        """
        LOG.debug("Calling update_domain for %s" % domain.name)

        for server_backend in self.server_backends:
            self._update_domain_on_server(context, domain, server_backend)

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
        LOG.debug("Calling update_status for %s" % domain.name)

        server = self._get_server(destination)
        update_status = self._retrieve_from_cache(
            context, server, domain, UPDATE_ACTION)
        cache_serial = update_status.serial_number

        LOG.debug('For domain %s on server %s the cache serial is %s '
                  'and the actual serial is %s.' %
                  (domain.name, self._get_destination(server),
                   cache_serial, actual_serial))
        if actual_serial and cache_serial < actual_serial:
            update_status.status = status
            update_status.serial_number = actual_serial
            self._store_in_cache(context, update_status)

        consensus_serial = self._get_consensus_serial(context, domain)
        LOG.info(_LI('For domain %(domain)s '
                     'the consensus serial is %(consensus_serial)s.') %
                 {'domain': domain.name,
                  'consensus_serial': consensus_serial})
        if cache_serial < consensus_serial:
            self.central_api.update_status(
                context, domain.id, SUCCESS_STATUS, consensus_serial)

        if status == ERROR_STATUS:
            error_serial = self._get_error_serial(
                context, domain, consensus_serial)
            LOG.warn(_LW('For domain %(domain)s '
                         'the error serial is %(error_serial)s.') %
                     {'domain': domain.name,
                      'error_serial': error_serial})
            if error_serial > consensus_serial or error_serial == 0:
                self.central_api.update_status(
                    context, domain.id, ERROR_STATUS, error_serial)

    def periodic_recovery(self):
        """
        :return:
        """
        LOG.debug("Calling periodic_recovery.")

        context = DesignateContext.get_admin_context(all_tenants=True)

        try:
            self._periodic_create_domains_that_failed(context)
            self._periodic_delete_domains_that_failed(context)
            self._periodic_update_domains_that_failed(context)
        except Exception:
            LOG.error(_LE('An unhandled exception in periodic recovery '
                          'occurred.  This should never happen!'))

    def periodic_sync(self):
        """
        :return: None
        """
        LOG.debug("Calling periodic_sync.")

        context = DesignateContext.get_admin_context(all_tenants=True)

        criterion = {
            'pool_id': cfg.CONF['service:pool_manager'].pool_id
        }
        domains = self.central_api.find_domains(context, criterion)

        try:
            for domain in domains:
                for server_backend in self.server_backends:
                    self._update_domain_on_server(
                        context, domain, server_backend)

        except Exception:
            LOG.error(_LE('An unhandled exception in periodic sync '
                          'occurred.  This should never happen!'))

    def _create_domain_on_server(self, context, create_status, domain,
                                 server_backend):

        server = server_backend['server']
        backend_instance = server_backend['backend_instance']

        try:
            with wrap_backend_call():
                backend_instance.create_domain(context, domain)
            create_status.status = SUCCESS_STATUS
            self._store_in_cache(context, create_status)
            LOG.info(_LI('Created domain %(domain)s '
                         'on server %(server)s.') %
                     {'domain': domain.name,
                      'server': self._get_destination(server)})

            update_status = self._create_update_status(server, domain)
            update_status.serial_number = 0
            # Setting the update status to ERROR ensures the periodic
            # recovery is run if there is a problem.
            update_status.status = ERROR_STATUS
            self._store_in_cache(context, update_status)

            # PowerDNS needs to explicitly send a NOTIFY for the AXFR to
            # happen whereas BIND9 does an AXFR implicitly after the domain
            # is created.  Sending a NOTIFY for all cases.
            self._notify_zone_changed(context, domain, server)
            self._poll_for_serial_number(context, domain, server)
        except exceptions.Backend:
            create_status.status = ERROR_STATUS
            self._store_in_cache(context, create_status)
            LOG.warn(_LW('Failed to create domain %(domain)s '
                         'on server %(server)s.') %
                     {'domain': domain.name,
                      'server': self._get_destination(server)})

    def _periodic_create_domains_that_failed(self, context):

        create_statuses = self._find_pool_manager_statuses(
            context, CREATE_ACTION, status=ERROR_STATUS)

        for create_status in create_statuses:
            domain = self.central_api.get_domain(
                context, create_status.domain_id)
            server_backend = self._get_server_backend(create_status.server_id)
            self._create_domain_on_server(
                context, create_status, domain, server_backend)

    def _delete_domain_on_server(self, context, delete_status, domain,
                                 server_backend):

        server = server_backend['server']
        backend_instance = server_backend['backend_instance']
        consensus_existed = self._is_delete_consensus(context, domain)

        try:
            with wrap_backend_call():
                backend_instance.delete_domain(context, domain)
            delete_status.status = SUCCESS_STATUS
            self._store_in_cache(context, delete_status)
            LOG.info(_LI('Deleted domain %(domain)s '
                         'from server %(server)s.') %
                     {'domain': domain.name,
                      'server': self._get_destination(server)})
            if not consensus_existed \
                    and self._is_delete_consensus(context, domain):
                LOG.info(_LI('Consensus reached '
                             'for deleting domain %(domain)s') %
                         {'domain': domain.name})
                self.central_api.update_status(
                    context, domain.id, SUCCESS_STATUS, domain.serial)
        except exceptions.Backend:
            delete_status.status = ERROR_STATUS
            self._store_in_cache(context, delete_status)
            LOG.warn(_LW('Failed to delete domain %(domain)s '
                         'from server %(server)s.') %
                     {'domain': domain.name,
                      'server': self._get_destination(server)})

    def _periodic_delete_domains_that_failed(self, context):

        delete_statuses = self._find_pool_manager_statuses(
            context, DELETE_ACTION, status=ERROR_STATUS)

        # Used to retrieve a domain from Central that may have already been
        # "deleted".
        context.show_deleted = True

        for delete_status in delete_statuses:
            domain = self.central_api.get_domain(
                context, delete_status.domain_id)
            server_backend = self._get_server_backend(delete_status.server_id)
            self._delete_domain_on_server(
                context, delete_status, domain, server_backend)

    def _update_domain_on_server(self, context, domain, server_backend):

        server = server_backend['server']

        try:
            update_status = self._retrieve_from_cache(
                context, server, domain, UPDATE_ACTION)
            if update_status.status == ERROR_STATUS \
                    or update_status.serial_number < domain.serial:
                self._notify_zone_changed(context, domain, server)
                self._poll_for_serial_number(context, domain, server)
                LOG.info(_LI('Updating domain %(domain)s '
                         'on server %(server)s.') %
                         {'domain': domain.name,
                          'server': self._get_destination(server)})
            else:
                # TODO(Ron): Do not log this warning on a periodic_sync.
                LOG.warn(_LW('No need to update domain %(domain)s '
                         'on server %(server)s.') %
                         {'domain': domain.name,
                          'server': self._get_destination(server)})
        except exceptions.PoolManagerStatusNotFound:
            pass

    def _periodic_update_domains_that_failed(self, context):

        update_statuses = self._find_pool_manager_statuses(
            context, UPDATE_ACTION, status=ERROR_STATUS)

        for update_status in update_statuses:
            domain = self.central_api.get_domain(
                context, update_status.domain_id)
            server_backend = self._get_server_backend(update_status.server_id)
            self._update_domain_on_server(context, domain, server_backend)

    def _notify_zone_changed(self, context, domain, server):
        self.mdns_api.notify_zone_changed(
            context, domain, self._get_destination(server),
            self.timeout, self.retry_interval, self.max_retries, 0)

    def _poll_for_serial_number(self, context, domain, server):
        self.mdns_api.poll_for_serial_number(
            context, domain, self._get_destination(server), self.timeout,
            self.retry_interval, self.max_retries, self.delay)

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
        return (Decimal(count) / Decimal(total_count)) * Decimal(100)

    def _exceed_or_meet_threshold(self, count):
        return self._percentage(
            count, len(self.server_backends)) >= Decimal(self.threshold)

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
        success_count = 0
        pool_manager_statuses = self._find_pool_manager_statuses(
            context, action, domain=domain)
        for pool_manager_status in pool_manager_statuses:
            if pool_manager_status.status == SUCCESS_STATUS:
                success_count += 1
        return self._exceed_or_meet_threshold(success_count)

    def _is_delete_consensus(self, context, domain):
        return self._is_success_consensus(context, domain, DELETE_ACTION)

    def _get_consensus_serial(self, context, domain):
        consensus_serial = 0
        update_statuses = self._find_pool_manager_statuses(
            context, UPDATE_ACTION, domain=domain)
        for serial in self._get_serials_descending(update_statuses):
            serial_count = 0
            for update_status in update_statuses:
                if update_status.serial_number >= serial:
                    serial_count += 1
            if self._exceed_or_meet_threshold(serial_count):
                consensus_serial = serial
                break
        return consensus_serial

    def _get_error_serial(self, context, domain, consensus_serial):
        error_serial = 0
        if not self._is_success_consensus(context, domain, UPDATE_ACTION):
            update_statuses = self._find_pool_manager_statuses(
                context, UPDATE_ACTION, domain=domain)
            for serial in self._get_serials_ascending(update_statuses):
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
