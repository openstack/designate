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
import time

from oslo_config import cfg
import oslo_messaging as messaging
from oslo_log import log as logging
from oslo_concurrency import lockutils

from designate import backend
from designate import coordination
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
CONF = cfg.CONF

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


class Service(service.RPCService, coordination.CoordinationMixin,
              service.Service):
    """
    Service side of the Pool Manager RPC API.

    API version history:

        1.0 - Initial version
    """
    RPC_API_VERSION = '2.0'

    target = messaging.Target(version=RPC_API_VERSION)

    def __init__(self, threads=None):
        super(Service, self).__init__(threads=threads)

        # Build the Pool (and related) Object from Config
        self.pool = objects.Pool.from_config(
            CONF, CONF['service:pool_manager'].pool_id)

        # Get a pool manager cache connection.
        self.cache = cache.get_pool_manager_cache(
            CONF['service:pool_manager'].cache_driver)

        # Store some settings for quick access later
        self.threshold = CONF['service:pool_manager'].threshold_percentage
        self.timeout = CONF['service:pool_manager'].poll_timeout
        self.retry_interval = CONF['service:pool_manager'].poll_retry_interval
        self.max_retries = CONF['service:pool_manager'].poll_max_retries
        self.delay = CONF['service:pool_manager'].poll_delay

        # Create the necessary Backend instances for each target
        self._setup_target_backends()

    def _setup_target_backends(self):
        self.target_backends = {}

        for target in self.pool.targets:
            # Fetch an instance of the Backend class, passing in the options
            # and masters
            self.target_backends[target.id] = backend.get_backend(
                    target.type, target)

        LOG.info(_LI('%d targets setup'), len(self.pool.targets))

        if not self.target_backends:
            raise exceptions.NoPoolTargetsConfigured()

    @property
    def service_name(self):
        return 'pool_manager'

    @property
    def _rpc_topic(self):
        # Modify the default topic so it's pool manager instance specific.
        topic = super(Service, self)._rpc_topic

        topic = '%s.%s' % (topic, CONF['service:pool_manager'].pool_id)
        LOG.info(_LI('Using topic %(topic)s for this pool manager instance.'),
                 {'topic': topic})

        return topic

    def start(self):
        for target in self.pool.targets:
            self.target_backends[target.id].start()

        super(Service, self).start()

        # Setup a Leader Election, use for ensuring certain tasks are executed
        # on exactly one pool-manager instance at a time]
        self._pool_election = coordination.LeaderElection(
            self._coordinator, '%s:%s' % (self.service_name, self.pool.id))
        self._pool_election.start()

        if CONF['service:pool_manager'].enable_recovery_timer:
            LOG.info(_LI('Starting periodic recovery timer'))
            self.tg.add_timer(
                CONF['service:pool_manager'].periodic_recovery_interval,
                self.periodic_recovery,
                CONF['service:pool_manager'].periodic_recovery_interval)

        if CONF['service:pool_manager'].enable_sync_timer:
            LOG.info(_LI('Starting periodic synchronization timer'))
            self.tg.add_timer(
                CONF['service:pool_manager'].periodic_sync_interval,
                self.periodic_sync,
                CONF['service:pool_manager'].periodic_sync_interval)

    def stop(self):
        self._pool_election.stop()

        super(Service, self).stop()

        for target in self.pool.targets:
            self.target_backends[target.id].stop()

    @property
    def central_api(self):
        return central_api.CentralAPI.get_instance()

    @property
    def mdns_api(self):
        return mdns_api.MdnsAPI.get_instance()

    # Periodioc Tasks
    def periodic_recovery(self):
        """
        :return: None
        """
        # NOTE(kiall): Only run this periodic task on the pool leader
        if self._pool_election.is_leader:
            context = DesignateContext.get_admin_context(all_tenants=True)

            LOG.debug("Starting Periodic Recovery")

            try:
                # Handle Deletion Failures
                zones = self._get_failed_zones(context, DELETE_ACTION)

                for zone in zones:
                    self.delete_zone(context, zone)

                # Handle Creation Failures
                zones = self._get_failed_zones(context, CREATE_ACTION)

                for zone in zones:
                    self.create_zone(context, zone)

                # Handle Update Failures
                zones = self._get_failed_zones(context, UPDATE_ACTION)

                for zone in zones:
                    self.update_zone(context, zone)

            except Exception:
                LOG.exception(_LE('An unhandled exception in periodic '
                                  'recovery occurred'))

    def periodic_sync(self):
        """
        :return: None
        """
        # NOTE(kiall): Only run this periodic task on the pool leader
        if self._pool_election.is_leader:
            context = DesignateContext.get_admin_context(all_tenants=True)

            LOG.debug("Starting Periodic Synchronization")

            criterion = {
                'pool_id': CONF['service:pool_manager'].pool_id,
                'status': '!%s' % ERROR_STATUS
            }

            periodic_sync_seconds = \
                CONF['service:pool_manager'].periodic_sync_seconds

            if periodic_sync_seconds is not None:
                # Generate the current serial, will provide a UTC Unix TS.
                current = utils.increment_serial()
                criterion['serial'] = ">%s" % (current - periodic_sync_seconds)

            zones = self.central_api.find_zones(context, criterion)

            try:
                for zone in zones:
                    # TODO(kiall): If the zone was created within the last
                    #              periodic_sync_seconds, attempt to recreate
                    #              to fill in targets which may have failed.
                    self.update_zone(context, zone)

            except Exception:
                LOG.exception(_LE('An unhandled exception in periodic '
                                  'synchronization occurred.'))

    # Standard Create/Update/Delete Methods

    def create_zone(self, context, zone):
        """
        :param context: Security context information.
        :param zone: Zone to be created
        :return: None
        """
        LOG.info(_LI("Creating new zone %s"), zone.name)

        results = []

        # Create the zone on each of the Pool Targets
        for target in self.pool.targets:
            results.append(
                self._create_zone_on_target(context, target, zone)
            )

        if self._exceed_or_meet_threshold(results.count(True)):
            LOG.debug('Consensus reached for creating zone %(zone)s '
                      'on pool targets' % {'zone': zone.name})

        else:

            LOG.warn(_LW('Consensus not reached for creating zone %(zone)s'
                         ' on pool targets') % {'zone': zone.name})

            self.central_api.update_status(
                    context, zone.id, ERROR_STATUS, zone.serial)

            return

        # Send a NOTIFY to each also-notifies
        for also_notify in self.pool.also_notifies:
            self._update_zone_on_also_notify(context, also_notify, zone)

        # Send a NOTIFY to each nameserver
        for nameserver in self.pool.nameservers:
            create_status = self._build_status_object(
                nameserver, zone, CREATE_ACTION)
            self.cache.store(context, create_status)

            self.mdns_api.poll_for_serial_number(
                context, zone, nameserver, self.timeout,
                self.retry_interval, self.max_retries, self.delay)

    def _create_zone_on_target(self, context, target, zone):
        """
        :param context: Security context information.
        :param target: Target to create Zone on
        :param zone: Zone to be created
        :return: True/False
        """
        LOG.debug("Creating zone %s on target %s", zone.name, target.id)

        backend = self.target_backends[target.id]
        retries = 0

        while retries < self.max_retries:
            try:
                backend.create_zone(context, zone)

                return True
            except Exception:
                retries += 1
                LOG.exception(_LE("Failed to create zone %(zone)s on "
                             "target %(target)s on attempt %(attempt)d"),
                        {
                           'zone': zone.name,
                           'target': target.id,
                           'attempt': retries
                        })
                time.sleep(self.retry_interval)

        return False

    def update_zone(self, context, zone):
        """
        :param context: Security context information.
        :param zone: Zone to be updated
        :return: None
        """
        LOG.info(_LI("Updating zone %s"), zone.name)

        results = []

        # Update the zone on each of the Pool Targets
        for target in self.pool.targets:
            results.append(
                self._update_zone_on_target(context, target, zone))

        if self._exceed_or_meet_threshold(results.count(True)):
            LOG.debug('Consensus reached for updating zone %(zone)s '
                      'on pool targets' % {'zone': zone.name})

        else:
            LOG.warn(_LW('Consensus not reached for updating zone %(zone)s'
                         ' on pool targets') % {'zone': zone.name})

            self.central_api.update_status(
                    context, zone.id, ERROR_STATUS, zone.serial)

            return

        # Send a NOTIFY to each also-notifies
        for also_notify in self.pool.also_notifies:
            self._update_zone_on_also_notify(context, also_notify, zone)

        # Ensure the change has propogated to each nameserver
        for nameserver in self.pool.nameservers:
            # See if there is already another update in progress
            try:
                update_status = self.cache.retrieve(
                    context, nameserver.id, zone.id, UPDATE_ACTION)
            except exceptions.PoolManagerStatusNotFound:
                update_status = self._build_status_object(
                    nameserver, zone, UPDATE_ACTION)
                self.cache.store(context, update_status)

            self.mdns_api.poll_for_serial_number(
                context, zone, nameserver, self.timeout,
                self.retry_interval, self.max_retries, self.delay)

    def _update_zone_on_target(self, context, target, zone):
        """
        :param context: Security context information.
        :param target: Target to update Zone on
        :param zone: Zone to be updated
        :return: True/False
        """
        LOG.debug("Updating zone %s on target %s", zone.name, target.id)

        backend = self.target_backends[target.id]

        try:
            backend.update_zone(context, zone)

            return True
        except Exception:
            LOG.exception(_LE("Failed to update zone %(zone)s on target "
                              "%(target)s"),
                          {'zone': zone.name, 'target': target.id})
            return False

    def _update_zone_on_also_notify(self, context, also_notify, zone):
        LOG.info(_LI('Updating zone %(zone)s on also_notify %(server)s.'),
                 {'zone': zone.name,
                  'server': self._get_destination(also_notify)})

        self.mdns_api.notify_zone_changed(
            context, zone, also_notify.host, also_notify.port, self.timeout,
            self.retry_interval, self.max_retries, 0)

    def delete_zone(self, context, zone):
        """
        :param context: Security context information.
        :param zone: Zone to be deleted
        :return: None
        """
        LOG.info(_LI("Deleting zone %s"), zone.name)

        results = []

        # Delete the zone on each of the Pool Targets
        for target in self.pool.targets:
            results.append(
                self._delete_zone_on_target(context, target, zone))

        # TODO(kiall): We should monitor that the Zone is actually deleted
        #              correctly on each of the nameservers, rather than
        #              assuming a successful delete-on-target is OK as we have
        #              in the past.
        if self._exceed_or_meet_threshold(
                results.count(True), MAXIMUM_THRESHOLD):
            LOG.debug('Consensus reached for deleting zone %(zone)s '
                      'on pool targets' % {'zone': zone.name})

            self.central_api.update_status(
                    context, zone.id, SUCCESS_STATUS, zone.serial)

        else:
            LOG.warn(_LW('Consensus not reached for deleting zone %(zone)s'
                         ' on pool targets') % {'zone': zone.name})

            self.central_api.update_status(
                    context, zone.id, ERROR_STATUS, zone.serial)

    def _delete_zone_on_target(self, context, target, zone):
        """
        :param context: Security context information.
        :param target: Target to delete Zone from
        :param zone: Zone to be deleted
        :return: True/False
        """
        LOG.debug("Deleting zone %s on target %s", zone.name, target.id)

        backend = self.target_backends[target.id]
        retries = 0

        while retries < self.max_retries:
            try:
                backend.delete_zone(context, zone)

                return True
            except Exception:
                retries += 1
                LOG.exception(_LE("Failed to delete zone %(zone)s on "
                             "target %(target)s on attempt %(attempt)d"),
                        {
                           'zone': zone.name,
                           'target': target.id,
                           'attempt': retries
                        })
                time.sleep(self.retry_interval)

        return False

    def update_status(self, context, zone, nameserver, status,
                      actual_serial):
        """
        update_status is called by mdns for creates and updates.
        deletes are handled by the backend entirely and status is determined
        at the time of delete itself.
        :param context: Security context information.
        :param zone: The designate zone object.
        :param nameserver: The nameserver for which a status update is being
                           sent.
        :param status: The status, 'SUCCESS' or 'ERROR'.
        :param actual_serial: The actual serial number received from the name
                              server for the zone.
        :return: None
        """
        LOG.debug("Calling update_status for %s : %s : %s : %s" %
                  (zone.name, zone.action, status, actual_serial))
        action = UPDATE_ACTION if zone.action == 'NONE' else zone.action

        with lockutils.lock('update-status-%s' % zone.id):
            try:
                current_status = self.cache.retrieve(
                    context, nameserver.id, zone.id, action)
            except exceptions.PoolManagerStatusNotFound:
                current_status = self._build_status_object(
                    nameserver, zone, action)
                self.cache.store(context, current_status)
            cache_serial = current_status.serial_number

            LOG.debug('For zone %s : %s on nameserver %s the cache serial '
                      'is %s and the actual serial is %s.' %
                      (zone.name, action,
                       self._get_destination(nameserver),
                       cache_serial, actual_serial))
            if actual_serial and cache_serial <= actual_serial:
                current_status.status = status
                current_status.serial_number = actual_serial
                self.cache.store(context, current_status)

            consensus_serial = self._get_consensus_serial(context, zone)

            # If there is a valid consensus serial we can still send a success
            # for that serial.
            # If there is a higher error serial we can also send an error for
            # the error serial.
            if consensus_serial != 0 and cache_serial <= consensus_serial \
                    and zone.status != 'ACTIVE':
                LOG.info(_LI('For zone %(zone)s '
                             'the consensus serial is %(consensus_serial)s.'),
                         {'zone': zone.name,
                          'consensus_serial': consensus_serial})
                self.central_api.update_status(
                    context, zone.id, SUCCESS_STATUS, consensus_serial)

            if status == ERROR_STATUS:
                error_serial = self._get_error_serial(
                    context, zone, consensus_serial)
                if error_serial > consensus_serial or error_serial == 0:
                    LOG.warn(_LW('For zone %(zone)s '
                                 'the error serial is %(error_serial)s.') %
                             {'zone': zone.name,
                              'error_serial': error_serial})
                    self.central_api.update_status(
                        context, zone.id, ERROR_STATUS, error_serial)

            if status == NO_DOMAIN_STATUS and action != DELETE_ACTION:
                LOG.warn(_LW('Zone %(zone)s is not present in some '
                             'targets') % {'zone': zone.name})
                self.central_api.update_status(
                    context, zone.id, NO_DOMAIN_STATUS, 0)

            if consensus_serial == zone.serial and self._is_consensus(
                    context, zone, action, SUCCESS_STATUS,
                    MAXIMUM_THRESHOLD):
                self._clear_cache(context, zone, action)

    # Utility Methods
    def _get_failed_zones(self, context, action):
        criterion = {
            'pool_id': CONF['service:pool_manager'].pool_id,
            'action': action,
            'status': 'ERROR'
        }
        return self.central_api.find_zones(context, criterion)

    @staticmethod
    def _get_destination(nameserver):
        return '%s:%s' % (nameserver.host, nameserver.port)

    @staticmethod
    def _percentage(count, total_count):
        return (Decimal(count) / Decimal(total_count)) * Decimal(100)

    def _exceed_or_meet_threshold(self, count, threshold=None):
        threshold = threshold or self.threshold

        return self._percentage(
            count, len(self.pool.targets)) >= Decimal(threshold)

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

    def _is_consensus(self, context, zone, action, status, threshold=None):
        status_count = 0
        pool_manager_statuses = self._retrieve_statuses(
            context, zone, action)
        for pool_manager_status in pool_manager_statuses:
            if pool_manager_status.status == status:
                status_count += 1
        if threshold is None:
            threshold = self.threshold
        return self._exceed_or_meet_threshold(status_count, threshold)

    def _get_consensus_serial(self, context, zone):
        consensus_serial = 0
        action = UPDATE_ACTION if zone.action == 'NONE' else zone.action

        pm_statuses = self._retrieve_statuses(context, zone, action)
        for serial in self._get_serials_descending(pm_statuses):
            serial_count = 0
            for pm_status in pm_statuses:
                if pm_status.serial_number >= serial:
                    serial_count += 1
            if self._exceed_or_meet_threshold(serial_count, self.threshold):
                consensus_serial = serial
                break
        return consensus_serial

    def _get_error_serial(self, context, zone, consensus_serial):
        error_serial = 0
        action = UPDATE_ACTION if zone.action == 'NONE' else zone.action

        if self._is_consensus(context, zone, action, ERROR_STATUS):
            pm_statuses = self._retrieve_statuses(context, zone, action)
            for serial in self._get_serials_ascending(pm_statuses):
                if serial > consensus_serial:
                    error_serial = serial
                    break
        return error_serial

    # When we hear back from the nameserver, the serial_number is set to the
    # value the nameserver
    @staticmethod
    def _build_status_object(nameserver, zone, action):
        values = {
            'nameserver_id': nameserver.id,
            'zone_id': zone.id,
            'status': None,
            'serial_number': 0,
            'action': action
        }
        return objects.PoolManagerStatus(**values)

    # Methods for manipulating the cache.
    def _clear_cache(self, context, zone, action=None):
        LOG.debug('Clearing cache for zone %s with action %s.' %
                  (zone.name, action))

        pool_manager_statuses = []
        if action:
            actions = [action]
        else:
            actions = [CREATE_ACTION, UPDATE_ACTION, DELETE_ACTION]

        for nameserver in self.pool.nameservers:
            for action in actions:
                pool_manager_status = self._build_status_object(
                    nameserver, zone, action)
                pool_manager_statuses.append(pool_manager_status)

        for pool_manager_status in pool_manager_statuses:
            # Ignore any not found errors while clearing the cache
            try:
                self.cache.clear(context, pool_manager_status)
            except exceptions.PoolManagerStatusNotFound:
                pass

    def _retrieve_from_mdns(self, context, nameserver, zone, action):
        try:
            (status, actual_serial, retries) = \
                self.mdns_api.get_serial_number(
                    context, zone, nameserver.host, nameserver.port,
                    self.timeout, self.retry_interval, self.max_retries,
                    self.delay)
        except messaging.MessagingException as msg_ex:
            LOG.debug('Could not retrieve status and serial for zone %s on '
                      'nameserver %s with action %s (%s: %s)' %
                      (zone.name, self._get_destination(nameserver), action,
                       type(msg_ex), str(msg_ex)))
            return None

        pool_manager_status = self._build_status_object(
            nameserver, zone, action)

        if status == NO_DOMAIN_STATUS:
            if action == CREATE_ACTION:
                pool_manager_status.status = 'ERROR'
            elif action == DELETE_ACTION:
                pool_manager_status.status = 'SUCCESS'
            elif action == UPDATE_ACTION:
                pool_manager_status.action = 'CREATE'
                pool_manager_status.status = 'ERROR'
        else:
            pool_manager_status.status = status
        pool_manager_status.serial_number = actual_serial \
            if actual_serial is not None else 0
        LOG.debug('Retrieved status %s and serial %s for zone %s '
                  'on nameserver %s with action %s from mdns.' %
                  (pool_manager_status.status,
                   pool_manager_status.serial_number,
                   zone.name, self._get_destination(nameserver), action))
        self.cache.store(context, pool_manager_status)

        return pool_manager_status

    def _retrieve_statuses(self, context, zone, action):
        pool_manager_statuses = []
        for nameserver in self.pool.nameservers:
            try:
                pool_manager_status = self.cache.retrieve(
                    context, nameserver.id, zone.id, action)
                LOG.debug('Cache hit! Retrieved status %s and serial %s '
                          'for zone %s on nameserver %s with action %s from '
                          'the cache.' %
                          (pool_manager_status.status,
                           pool_manager_status.serial_number,
                           zone.name,
                           self._get_destination(nameserver), action))
            except exceptions.PoolManagerStatusNotFound:
                LOG.debug('Cache miss! Did not retrieve status and serial '
                          'for zone %s on nameserver %s with action %s from '
                          'the cache. Getting it from the server.' %
                          (zone.name,
                           self._get_destination(nameserver),
                           action))
                pool_manager_status = self._retrieve_from_mdns(
                    context, nameserver, zone, action)

            if pool_manager_status is not None:
                pool_manager_statuses.append(pool_manager_status)

        return pool_manager_statuses
