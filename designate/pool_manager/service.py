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
from oslo_log import log as logging
from oslo_concurrency import lockutils

from designate import backend
from designate import exceptions
from designate import objects
from designate import utils
from designate.central import rpcapi as central_api
from designate.mdns import rpcapi as mdns_api
from designate import service
from designate.context import DesignateContext
from designate.i18n import _LE
from designate.i18n import _LI
from designate.i18n import _LW
from designate.pool_manager import cache


LOG = logging.getLogger(__name__)

SUCCESS_STATUS = 'SUCCESS'
ERROR_STATUS = 'ERROR'
NO_DOMAIN_STATUS = 'NO_DOMAIN'
CREATE_ACTION = 'CREATE'
DELETE_ACTION = 'DELETE'
UPDATE_ACTION = 'UPDATE'
MAXIMUM_THRESHOLD = 100


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


class Service(service.RPCService, service.Service):
    """
    Service side of the Pool Manager RPC API.

    API version history:

        1.0 - Initial version
    """
    RPC_API_VERSION = '1.0'

    target = messaging.Target(version=RPC_API_VERSION)

    def __init__(self, threads=None):
        super(Service, self).__init__(threads=threads)

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

    @property
    def service_name(self):
        return 'pool_manager'

    @property
    def _rpc_topic(self):
        # Modify the default topic so it's pool manager instance specific.
        topic = super(Service, self)._rpc_topic

        topic = '%s.%s' % (topic, cfg.CONF['service:pool_manager'].pool_id)
        LOG.info(_LI('Using topic %(topic)s for this pool manager instance.')
                 % {'topic': topic})

        return topic

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

    def create_domain(self, context, domain):
        """
        :param context: Security context information.
        :param domain: The designate domain object.
        :return: None
        """
        LOG.debug("Calling create_domain for %s" % domain.name)

        for server_backend in self.server_backends:
            server = server_backend['server']
            create_status = self._build_status_object(
                server, domain, CREATE_ACTION)
            self._create_domain_on_server(
                context, create_status, domain, server_backend)

        # ERROR status is updated right away, but success is updated when we
        # hear back from mdns
        if self._is_consensus(context, domain, CREATE_ACTION, ERROR_STATUS):
            LOG.warn(_LW('Consensus not reached '
                         'for creating domain %(domain)s') %
                     {'domain': domain.name})
            self.central_api.update_status(
                context, domain.id, ERROR_STATUS, domain.serial)

    def delete_domain(self, context, domain):
        """
        :param context: Security context information.
        :param domain: The designate domain object.
        :return: None
        """
        LOG.debug("Calling delete_domain for %s" % domain.name)

        for server_backend in self.server_backends:
            server = server_backend['server']
            delete_status = self._build_status_object(
                server, domain, DELETE_ACTION)
            self._delete_domain_on_server(
                context, delete_status, domain, server_backend)

        self._check_delete_status(context, domain)

    def update_domain(self, context, domain):
        """
        :param context: Security context information.
        :param domain: The designate domain object.
        :return: None
        """
        LOG.debug("Calling update_domain for %s" % domain.name)

        for server_backend in self.server_backends:
            server = server_backend['server']
            # See if there is already another update in progress
            try:
                update_status = self.cache.retrieve(
                    context, server.id, domain.id, UPDATE_ACTION)
            except exceptions.PoolManagerStatusNotFound:
                update_status = self._build_status_object(
                    server, domain, UPDATE_ACTION)
                self.cache.store(context, update_status)

            self._update_domain_on_server(context, domain, server_backend)

    def update_status(self, context, domain, server, status, actual_serial):
        """
        update_status is called by mdns for creates and updates.
        deletes are handled by the backend entirely and status is determined
        at the time of delete itself.
        :param context: Security context information.
        :param domain: The designate domain object.
        :param server: The server for which a status update is being sent.
        :param status: The status, 'SUCCESS' or 'ERROR'.
        :param actual_serial: The actual serial number received from the name
                              server for the domain.
        :return: None
        """
        LOG.debug("Calling update_status for %s : %s : %s : %s" %
                  (domain.name, domain.action, status, actual_serial))
        action = UPDATE_ACTION if domain.action == 'NONE' else domain.action

        with lockutils.lock('update-status-%s' % domain.id):
            try:
                current_status = self.cache.retrieve(
                    context, server.id, domain.id, action)
            except exceptions.PoolManagerStatusNotFound:
                current_status = self._build_status_object(
                    server, domain, action)
                self.cache.store(context, current_status)
            cache_serial = current_status.serial_number

            LOG.debug('For domain %s : %s on server %s the cache serial is %s '
                      'and the actual serial is %s.' %
                      (domain.name, action,
                       self._get_destination(server),
                       cache_serial, actual_serial))
            if actual_serial and cache_serial <= actual_serial:
                current_status.status = status
                current_status.serial_number = actual_serial
                self.cache.store(context, current_status)

            consensus_serial = self._get_consensus_serial(context, domain)

            # If there is a valid consensus serial we can still send a success
            # for that serial.
            # If there is a higher error serial we can also send an error for
            # the error serial.
            if consensus_serial != 0 and cache_serial <= consensus_serial \
                    and domain.status != 'ACTIVE':
                LOG.info(_LI('For domain %(domain)s '
                             'the consensus serial is %(consensus_serial)s.') %
                         {'domain': domain.name,
                          'consensus_serial': consensus_serial})
                self.central_api.update_status(
                    context, domain.id, SUCCESS_STATUS, consensus_serial)

            if status == ERROR_STATUS:
                error_serial = self._get_error_serial(
                    context, domain, consensus_serial)
                if error_serial > consensus_serial or error_serial == 0:
                    LOG.warn(_LW('For domain %(domain)s '
                                 'the error serial is %(error_serial)s.') %
                             {'domain': domain.name,
                              'error_serial': error_serial})
                    self.central_api.update_status(
                        context, domain.id, ERROR_STATUS, error_serial)

            if consensus_serial == domain.serial and self._is_consensus(
                    context, domain, action, SUCCESS_STATUS,
                    MAXIMUM_THRESHOLD):
                self._clear_cache(context, domain, action)

    def periodic_recovery(self):
        """
        :return:
        """
        LOG.debug("Calling periodic_recovery.")

        context = DesignateContext.get_admin_context(all_tenants=True)

        try:
            self._periodic_delete_domains_that_failed(context)
            self._periodic_create_domains_that_failed(context)
            self._periodic_update_domains_that_failed(context)
        except Exception:
            LOG.exception(_LE('An unhandled exception in periodic recovery '
                              'occurred.  This should never happen!'))

    def periodic_sync(self):
        """
        :return: None
        """
        LOG.debug("Calling periodic_sync.")

        context = DesignateContext.get_admin_context(all_tenants=True)

        criterion = {
            'pool_id': cfg.CONF['service:pool_manager'].pool_id,
            'status': '%s%s' % ('!', ERROR_STATUS)
        }

        periodic_sync_seconds = \
            cfg.CONF['service:pool_manager'].periodic_sync_seconds

        if periodic_sync_seconds is not None:
            # Generate the current serial, will provide a UTC Unix TS.
            current = utils.increment_serial()
            criterion['serial'] = ">%s" % (current - periodic_sync_seconds)

        domains = self.central_api.find_domains(context, criterion)

        try:
            for domain in domains:
                self.update_domain(context, domain)
        except Exception:
            LOG.exception(_LE('An unhandled exception in periodic sync '
                              'occurred.  This should never happen!'))

    def _create_domain_on_server(self, context, create_status, domain,
                                 server_backend):

        server = server_backend['server']
        backend_instance = server_backend['backend_instance']

        try:
            with wrap_backend_call():
                backend_instance.create_domain(context, domain)
            # The status will be updated when we hear back the serial number
            # from minidns
            self.cache.store(context, create_status)
            LOG.info(_LI('Created domain %(domain)s on server %(server)s.') %
                     {'domain': domain.name,
                      'server': self._get_destination(server)})

            # PowerDNS needs to explicitly send a NOTIFY for the AXFR to
            # happen whereas BIND9 does an AXFR implicitly after the domain
            # is created.  Sending a NOTIFY for all cases.
            self._update_domain_on_server(context, domain, server_backend)
        except exceptions.Backend:
            create_status.status = ERROR_STATUS
            self.cache.store(context, create_status)
            LOG.warn(_LW('Failed to create domain %(domain)s '
                         'on server %(server)s.') %
                     {'domain': domain.name,
                      'server': self._get_destination(server)})

    def _periodic_create_domains_that_failed(self, context):

        domains = self._get_failed_domains(context, CREATE_ACTION)

        for domain in domains:
            create_statuses = self._retrieve_statuses(
                context, domain, CREATE_ACTION)
            for create_status in create_statuses:
                server_backend = self._get_server_backend(
                    create_status.server_id)
                self._create_domain_on_server(
                    context, create_status, domain, server_backend)

    def _delete_domain_on_server(self, context, delete_status, domain,
                                 server_backend):

        server = server_backend['server']
        backend_instance = server_backend['backend_instance']

        try:
            with wrap_backend_call():
                backend_instance.delete_domain(context, domain)
            delete_status.status = SUCCESS_STATUS
            delete_status.serial_number = domain.serial
            self.cache.store(context, delete_status)
            LOG.info(_LI('Deleted domain %(domain)s from server %(server)s.') %
                     {'domain': domain.name,
                      'server': self._get_destination(server)})

        except exceptions.Backend:
            delete_status.status = ERROR_STATUS
            self.cache.store(context, delete_status)
            LOG.warn(_LW('Failed to delete domain %(domain)s '
                         'from server %(server)s.') %
                     {'domain': domain.name,
                      'server': self._get_destination(server)})

    def _check_delete_status(self, context, domain):
        if self._is_consensus(context, domain, DELETE_ACTION, SUCCESS_STATUS):
            LOG.info(_LI('Consensus reached for deleting domain %(domain)s') %
                     {'domain': domain.name})
            self.central_api.update_status(
                context, domain.id, SUCCESS_STATUS, domain.serial)
        else:
            LOG.warn(_LW('Consensus not reached for deleting domain '
                         '%(domain)s') % {'domain': domain.name})
            self.central_api.update_status(
                context, domain.id, ERROR_STATUS, domain.serial)

        if self._is_consensus(context, domain, DELETE_ACTION, SUCCESS_STATUS,
                              MAXIMUM_THRESHOLD):
            # Clear all the entries from cache
            self._clear_cache(context, domain)

    def _periodic_delete_domains_that_failed(self, context):

        domains = self._get_failed_domains(context, DELETE_ACTION)

        for domain in domains:
            delete_statuses = self._retrieve_statuses(
                context, domain, DELETE_ACTION)
            for delete_status in delete_statuses:
                server_backend = self._get_server_backend(
                    delete_status.server_id)
                self._delete_domain_on_server(
                    context, delete_status, domain, server_backend)

            self._check_delete_status(context, domain)

    def _update_domain_on_server(self, context, domain, server_backend):

        server = server_backend['server']

        self.mdns_api.notify_zone_changed(
            context, domain, server, self.timeout, self.retry_interval,
            self.max_retries, 0)
        self.mdns_api.poll_for_serial_number(
            context, domain, server, self.timeout, self.retry_interval,
            self.max_retries, self.delay)
        LOG.info(_LI('Updating domain %(domain)s on server %(server)s.') %
                 {'domain': domain.name,
                  'server': self._get_destination(server)})

    def _periodic_update_domains_that_failed(self, context):

        domains = self._get_failed_domains(context, UPDATE_ACTION)

        for domain in domains:
            update_statuses = self._retrieve_statuses(
                context, domain, UPDATE_ACTION)
            for update_status in update_statuses:
                server_backend = self._get_server_backend(
                    update_status.server_id)
                self._update_domain_on_server(context, domain, server_backend)

    def _get_failed_domains(self, context, action):
        criterion = {
            'pool_id': cfg.CONF['service:pool_manager'].pool_id,
            'action': action,
            'status': 'ERROR'
        }
        return self.central_api.find_domains(context, criterion)

    def _get_server_backend(self, server_id):
        for server_backend in self.server_backends:
            server = server_backend['server']
            if server.id == server_id:
                return server_backend

    @staticmethod
    def _get_destination(server):
        return '%s:%s' % (server.host, server.port)

    @staticmethod
    def _percentage(count, total_count):
        return (Decimal(count) / Decimal(total_count)) * Decimal(100)

    def _exceed_or_meet_threshold(self, count, threshold):
        return self._percentage(
            count, len(self.server_backends)) >= Decimal(threshold)

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

    def _is_consensus(self, context, domain, action, status, threshold=None):
        status_count = 0
        pool_manager_statuses = self._retrieve_statuses(
            context, domain, action)
        for pool_manager_status in pool_manager_statuses:
            if pool_manager_status.status == status:
                status_count += 1
        if threshold is None:
            threshold = self.threshold
        return self._exceed_or_meet_threshold(status_count, threshold)

    def _get_consensus_serial(self, context, domain):
        consensus_serial = 0
        action = UPDATE_ACTION if domain.action == 'NONE' else domain.action

        pm_statuses = self._retrieve_statuses(context, domain, action)
        for serial in self._get_serials_descending(pm_statuses):
            serial_count = 0
            for pm_status in pm_statuses:
                if pm_status.serial_number >= serial:
                    serial_count += 1
            if self._exceed_or_meet_threshold(serial_count, self.threshold):
                consensus_serial = serial
                break
        return consensus_serial

    def _get_error_serial(self, context, domain, consensus_serial):
        error_serial = 0
        action = UPDATE_ACTION if domain.action == 'NONE' else domain.action

        if self._is_consensus(context, domain, action, ERROR_STATUS):
            pm_statuses = self._retrieve_statuses(context, domain, action)
            for serial in self._get_serials_ascending(pm_statuses):
                if serial > consensus_serial:
                    error_serial = serial
                    break
        return error_serial

    # When we hear back from the server, the serial_number is set to the value
    # the server
    @staticmethod
    def _build_status_object(server, domain, action):
        values = {
            'server_id': server.id,
            'domain_id': domain.id,
            'status': None,
            'serial_number': 0,
            'action': action
        }
        return objects.PoolManagerStatus(**values)

    # Methods for manipulating the cache.
    def _clear_cache(self, context, domain, action=None):
        pool_manager_statuses = []
        if action:
            actions = [action]
        else:
            actions = [CREATE_ACTION, UPDATE_ACTION, DELETE_ACTION]

        for server_backend in self.server_backends:
            server = server_backend['server']
            for action in actions:
                pool_manager_status = self._build_status_object(
                    server, domain, action)
                pool_manager_statuses.append(pool_manager_status)

        for pool_manager_status in pool_manager_statuses:
            # Ignore any not found errors while clearing the cache
            try:
                self.cache.clear(context, pool_manager_status)
            except exceptions.PoolManagerStatusNotFound:
                pass
        LOG.debug('Cleared cache for domain %s with action %s.' %
                  (domain.name, action))

    def _retrieve_from_mdns(self, context, server, domain, action):
        try:
            (status, actual_serial, retries) = \
                self.mdns_api.get_serial_number(
                    context, domain, server, self.timeout, self.retry_interval,
                    self.max_retries, self.delay)
        except messaging.MessagingException as msg_ex:
            LOG.debug('Could not retrieve status and serial for domain %s on '
                      'server %s with action %s from the server. %s:%s' %
                      (domain.name, self._get_destination(server), action,
                       type(msg_ex), str(msg_ex)))
            return None

        pool_manager_status = self._build_status_object(server, domain, action)
        if status == NO_DOMAIN_STATUS:
            if action == CREATE_ACTION:
                pool_manager_status.status = 'ERROR'
            elif action == DELETE_ACTION:
                pool_manager_status.status = 'SUCCESS'
            # TODO(Ron): Handle this case properly.
            elif action == UPDATE_ACTION:
                pool_manager_status.status = 'ERROR'
        else:
            pool_manager_status.status = status
        pool_manager_status.serial_number = actual_serial \
            if actual_serial is not None else 0
        LOG.debug('Retrieved status %s and serial %s for domain %s '
                  'on server %s with action %s from mdns.' %
                  (pool_manager_status.status,
                   pool_manager_status.serial_number,
                   domain.name, self._get_destination(server), action))
        self.cache.store(context, pool_manager_status)

        return pool_manager_status

    def _retrieve_statuses(self, context, domain, action):
        pool_manager_statuses = []
        for server_backend in self.server_backends:
            server = server_backend['server']
            try:
                pool_manager_status = self.cache.retrieve(
                    context, server.id, domain.id, action)
                LOG.debug('Cache hit!  Retrieved status %s and serial %s '
                          'for domain %s on server %s with action %s from '
                          'the cache.' %
                          (pool_manager_status.status,
                           pool_manager_status.serial_number,
                           domain.name, self._get_destination(server), action))
            except exceptions.PoolManagerStatusNotFound:
                LOG.debug('Cache miss!  Did not retrieve status and serial '
                          'for domain %s on server %s with action %s from '
                          'the cache. Getting it from the server.' %
                          (domain.name, self._get_destination(server), action))
                pool_manager_status = self._retrieve_from_mdns(
                    context, server, domain, action)

            if pool_manager_status is not None:
                pool_manager_statuses.append(pool_manager_status)

        return pool_manager_statuses
