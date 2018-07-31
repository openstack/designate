# Copyright 2012 Managed I.T.
# Copyright 2013 - 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
import re
import collections
import copy
import functools
import threading
import itertools
import string
import signal
import random
import time

import six
from eventlet import tpool
from dns import zone as dnszone
from dns import exception as dnsexception
from oslo_config import cfg
import oslo_messaging as messaging
from oslo_log import log as logging
from oslo_concurrency import lockutils

from designate.i18n import _LI
from designate.i18n import _LC
from designate.i18n import _LE
from designate.i18n import _LW
from designate import context as dcontext
from designate import exceptions
from designate import dnsutils
from designate import network_api
from designate import notifications
from designate import objects
from designate import policy
from designate import quota
from designate import service
from designate import scheduler
from designate import utils
from designate import storage
from designate.mdns import rpcapi as mdns_rpcapi
from designate.pool_manager import rpcapi as pool_manager_rpcapi
from designate.storage import transaction
from designate.worker import rpcapi as worker_rpcapi


LOG = logging.getLogger(__name__)
ZONE_LOCKS = threading.local()
NOTIFICATION_BUFFER = threading.local()


def synchronized_zone(zone_arg=1, new_zone=False):
    """Ensures only a single operation is in progress for each zone

    A Decorator which ensures only a single operation can be happening
    on a single zone at once, within the current designate-central instance
    """
    def outer(f):
        @functools.wraps(f)
        def sync_wrapper(self, *args, **kwargs):
            if not hasattr(ZONE_LOCKS, 'held'):
                # Create the held set if necessary
                ZONE_LOCKS.held = set()

            zone_id = None

            if 'zone_id' in kwargs:
                zone_id = kwargs['zone_id']

            elif 'zone' in kwargs:
                zone_id = kwargs['zone'].id

            elif 'recordset' in kwargs:
                zone_id = kwargs['recordset'].zone_id

            elif 'record' in kwargs:
                zone_id = kwargs['record'].zone_id

            # The various objects won't always have an ID set, we should
            # attempt to locate an Object containing the ID.
            if zone_id is None:
                for arg in itertools.chain(kwargs.values(), args):
                    if isinstance(arg, objects.Zone):
                        zone_id = arg.id
                        if zone_id is not None:
                            break

                    elif (isinstance(arg, objects.RecordSet) or
                          isinstance(arg, objects.Record) or
                          isinstance(arg, objects.ZoneTransferRequest) or
                          isinstance(arg, objects.ZoneTransferAccept)):

                        zone_id = arg.zone_id
                        if zone_id is not None:
                            break

            # If we still don't have an ID, find the Nth argument as
            # defined by the zone_arg decorator option.
            if zone_id is None and len(args) > zone_arg:
                zone_id = args[zone_arg]

                if isinstance(zone_id, objects.Zone):
                    # If the value is a Zone object, extract it's ID.
                    zone_id = zone_id.id

            if not new_zone and zone_id is None:
                raise Exception('Failed to determine zone id for '
                                'synchronized operation')

            if zone_id in ZONE_LOCKS.held:
                # Call the wrapped function
                return f(self, *args, **kwargs)
            else:
                with lockutils.lock('zone-%s' % zone_id):
                    ZONE_LOCKS.held.add(zone_id)

                    # Call the wrapped function
                    result = f(self, *args, **kwargs)

                    ZONE_LOCKS.held.remove(zone_id)
                    return result

        sync_wrapper.__wrapped_function = f
        sync_wrapper.__wrapper_name = 'synchronized_zone'
        return sync_wrapper

    return outer


def notification(notification_type):
    def outer(f):
        @functools.wraps(f)
        def notification_wrapper(self, *args, **kwargs):
            if not hasattr(NOTIFICATION_BUFFER, 'queue'):
                # Create the notifications queue if necessary
                NOTIFICATION_BUFFER.stack = 0
                NOTIFICATION_BUFFER.queue = collections.deque()

            NOTIFICATION_BUFFER.stack += 1

            try:
                # Find the context argument
                context = dcontext.DesignateContext.\
                    get_context_from_function_and_args(f, args, kwargs)

                # Call the wrapped function
                result = f(self, *args, **kwargs)

                # Feed the args/result to a notification plugin
                # to determine what is emitted
                payloads = notifications.get_plugin().emit(
                    notification_type, context, result, args, kwargs)

                # Enqueue the notification
                for payload in payloads:
                    LOG.debug('Queueing notification for %(type)s ',
                              {'type': notification_type})
                    NOTIFICATION_BUFFER.queue.appendleft(
                        (context, notification_type, payload,))

                return result

            finally:
                NOTIFICATION_BUFFER.stack -= 1

                if NOTIFICATION_BUFFER.stack == 0:
                    LOG.debug('Emitting %(count)d notifications',
                              {'count': len(NOTIFICATION_BUFFER.queue)})
                    # Send the queued notifications, in order.
                    for value in NOTIFICATION_BUFFER.queue:
                        LOG.debug('Emitting %(type)s notification',
                                  {'type': value[1]})
                        self.notifier.info(value[0], value[1], value[2])

                    # Reset the queue
                    NOTIFICATION_BUFFER.queue.clear()

        return notification_wrapper
    return outer


class Service(service.RPCService, service.Service):
    RPC_API_VERSION = '6.2'

    target = messaging.Target(version=RPC_API_VERSION)

    def __init__(self, threads=None):
        super(Service, self).__init__(threads=threads)

        self.network_api = network_api.get_network_api(cfg.CONF.network_api)

        # update_service_status needs is called by the emitter so we pass
        # ourselves as the rpc_api.
        self.heartbeat_emitter.rpc_api = self

    @property
    def scheduler(self):
        if not hasattr(self, '_scheduler'):
            # Get a scheduler instance
            self._scheduler = scheduler.get_scheduler(storage=self.storage)
        return self._scheduler

    @property
    def quota(self):
        if not hasattr(self, '_quota'):
            # Get a quota manager instance
            self._quota = quota.get_quota()
        return self._quota

    @property
    def storage(self):
        if not hasattr(self, '_storage'):
            # Get a storage connection
            storage_driver = cfg.CONF['service:central'].storage_driver
            self._storage = storage.get_storage(storage_driver)
        return self._storage

    @property
    def service_name(self):
        return cfg.CONF['service:central'].central_topic

    def start(self):

        if (cfg.CONF['service:central'].managed_resource_tenant_id ==
                "00000000-0000-0000-0000-000000000000"):
            msg = _LW("Managed Resource Tenant ID is not properly configured")
            LOG.warning(msg)

        super(Service, self).start()

    def stop(self):
        super(Service, self).stop()

    @property
    def mdns_api(self):
        return mdns_rpcapi.MdnsAPI.get_instance()

    @property
    def pool_manager_api(self):
        return pool_manager_rpcapi.PoolManagerAPI.get_instance()

    @property
    def worker_api(self):
        return worker_rpcapi.WorkerAPI.get_instance()

    @property
    def zone_api(self):
        # TODO(timsim): Remove this when pool_manager_api is gone
        if cfg.CONF['service:worker'].enabled:
                return self.worker_api
        return self.pool_manager_api

    def _is_valid_zone_name(self, context, zone_name):
        # Validate zone name length
        if len(zone_name) > cfg.CONF['service:central'].max_zone_name_len:
            raise exceptions.InvalidZoneName('Name too long')

        # Break the zone name up into its component labels
        zone_labels = zone_name.strip('.').split('.')

        # We need more than 1 label.
        if len(zone_labels) <= 1:
            raise exceptions.InvalidZoneName('More than one label is '
                                             'required')

        # Check the TLD for validity if there are entries in the database
        if self.storage.find_tlds({}):
            LOG.info(_LI("Checking for TLDs"))
            try:
                self.storage.find_tld(context, {'name': zone_labels[-1]})
            except exceptions.TldNotFound:
                raise exceptions.InvalidZoneName('Invalid TLD')

            # Now check that the zone name is not the same as a TLD
            try:
                stripped_zone_name = zone_name.rstrip('.').lower()
                self.storage.find_tld(
                    context,
                    {'name': stripped_zone_name})
            except exceptions.TldNotFound:
                pass
            else:
                raise exceptions.InvalidZoneName(
                    'Zone name cannot be the same as a TLD')

        # Check zone name blacklist
        if self._is_blacklisted_zone_name(context, zone_name):
            # Some users are allowed bypass the blacklist.. Is this one?
            if not policy.check('use_blacklisted_zone', context,
                                do_raise=False):
                raise exceptions.InvalidZoneName('Blacklisted zone name')

        return True

    def _is_valid_recordset_name(self, context, zone, recordset_name):
        if not recordset_name.endswith('.'):
            raise ValueError('Please supply a FQDN')

        # Validate record name length
        max_len = cfg.CONF['service:central'].max_recordset_name_len
        if len(recordset_name) > max_len:
            raise exceptions.InvalidRecordSetName('Name too long')

        # RecordSets must be contained in the parent zone
        if (recordset_name != zone['name']
                and not recordset_name.endswith("." + zone['name'])):
            raise exceptions.InvalidRecordSetLocation(
                'RecordSet is not contained within it\'s parent zone')

    def _is_valid_recordset_placement(self, context, zone, recordset_name,
                                      recordset_type, recordset_id=None):
        # CNAME's must not be created at the zone apex.
        if recordset_type == 'CNAME' and recordset_name == zone.name:
            raise exceptions.InvalidRecordSetLocation(
                'CNAME recordsets may not be created at the zone apex')

        # CNAME's must not share a name with other recordsets
        criterion = {
            'zone_id': zone.id,
            'name': recordset_name,
        }

        if recordset_type != 'CNAME':
            criterion['type'] = 'CNAME'

        recordsets = self.storage.find_recordsets(context, criterion)

        if ((len(recordsets) == 1 and recordsets[0].id != recordset_id)
                or len(recordsets) > 1):
            raise exceptions.InvalidRecordSetLocation(
                'CNAME recordsets may not share a name with any other records')

        return True

    def _is_valid_recordset_placement_subzone(self, context, zone,
                                              recordset_name,
                                              criterion=None):
        """
        Check that the placement of the requested rrset belongs to any of the
        zones subzones..
        """
        LOG.debug("Checking if %s belongs in any of %s subzones" %
                  (recordset_name, zone.name))

        criterion = criterion or {}

        context = context.elevated(all_tenants=True)

        if zone.name == recordset_name:
            return

        child_zones = self.storage.find_zones(
            context, {"parent_zone_id": zone.id})
        for child_zone in child_zones:
            try:
                self._is_valid_recordset_name(
                    context, child_zone, recordset_name)
            except Exception:
                continue
            else:
                msg = 'RecordSet belongs in a child zone: %s' % \
                    child_zone['name']
                raise exceptions.InvalidRecordSetLocation(msg)

    def _is_valid_recordset_records(self, recordset):
        """
        Check to make sure that the records in the recordset
        follow the rules, and won't blow up on the nameserver.
        """
        try:
            recordset.records
        except (AttributeError, exceptions.RelationNotLoaded):
            pass
        else:
            if len(recordset.records) > 1 and recordset.type == 'CNAME':
                raise exceptions.BadRequest(
                    'CNAME recordsets may not have more than 1 record'
                )

    def _is_blacklisted_zone_name(self, context, zone_name):
        """
        Ensures the provided zone_name is not blacklisted.
        """
        blacklists = self.storage.find_blacklists(context)

        class Timeout(Exception):
            pass

        def _handle_timeout(signum, frame):
            raise Timeout()

        signal.signal(signal.SIGALRM, _handle_timeout)

        try:
            for blacklist in blacklists:
                signal.setitimer(signal.ITIMER_REAL, 0.02)

                try:
                    if bool(re.search(blacklist.pattern, zone_name)):
                        return True
                finally:
                    signal.setitimer(signal.ITIMER_REAL, 0)

        except Timeout:
            LOG.critical(_LC(
                'Blacklist regex (%(pattern)s) took too long to evaluate '
                'against zone name (%(zone_name)s') %
                         {
                             'pattern': blacklist.pattern,
                             'zone_name': zone_name
                         }
                        )

            return True

        return False

    def _is_subzone(self, context, zone_name, pool_id):
        """
        Ensures the provided zone_name is the subzone
        of an existing zone (checks across all tenants)
        """
        context = context.elevated(all_tenants=True)

        # Break the name up into it's component labels
        labels = zone_name.split(".")

        criterion = {"pool_id": pool_id}

        i = 1

        # Starting with label #2, search for matching zone's in the database
        while (i < len(labels)):
            name = '.'.join(labels[i:])
            criterion["name"] = name
            try:
                zone = self.storage.find_zone(context, criterion)
            except exceptions.ZoneNotFound:
                i += 1
            else:
                return zone

        return False

    def _is_superzone(self, context, zone_name, pool_id):
        """
        Ensures the provided zone_name is the parent zone
        of an existing subzone (checks across all tenants)
        """
        context = context.elevated(all_tenants=True)

        # Create wildcard term to catch all subzones
        search_term = "%%.%(name)s" % {"name": zone_name}

        criterion = {'name': search_term, "pool_id": pool_id}
        subzones = self.storage.find_zones(context, criterion)

        return subzones

    def _is_valid_ttl(self, context, ttl):
        if ttl is None:
            return
        min_ttl = cfg.CONF['service:central'].min_ttl
        if min_ttl is not None and ttl < int(min_ttl):
            try:
                policy.check('use_low_ttl', context)
            except exceptions.Forbidden:
                raise exceptions.InvalidTTL('TTL is below the minimum: %s'
                                            % min_ttl)

    def _increment_zone_serial(self, context, zone, set_delayed_notify=False):
        """Update the zone serial and the SOA record
        Optionally set delayed_notify to have PM issue delayed notify
        """

        # Increment the serial number
        zone.serial = utils.increment_serial(zone.serial)
        if set_delayed_notify:
            zone.delayed_notify = True

        zone = self.storage.update_zone(context, zone)

        # Update SOA record
        self._update_soa(context, zone)

        return zone

    # SOA Recordset Methods
    def _build_soa_record(self, zone, ns_records):
        return "%s %s. %d %d %d %d %d" % (ns_records[0]['hostname'],
                                          zone['email'].replace("@", "."),
                                          zone['serial'],
                                          zone['refresh'],
                                          zone['retry'],
                                          zone['expire'],
                                          zone['minimum'])

    def _create_soa(self, context, zone):
        pool_ns_records = self._get_pool_ns_records(context, zone.pool_id)

        soa_values = [self._build_soa_record(zone, pool_ns_records)]
        recordlist = objects.RecordList(objects=[
            objects.Record(data=r, managed=True) for r in soa_values])
        values = {
            'name': zone['name'],
            'type': "SOA",
            'records': recordlist
        }
        soa, zone = self._create_recordset_in_storage(
            context, zone, objects.RecordSet(**values),
            increment_serial=False)
        return soa

    def _update_soa(self, context, zone):
        # NOTE: We should not be updating SOA records when a zone is SECONDARY.
        if zone.type != 'PRIMARY':
            return

        # Get the pool for it's list of ns_records
        pool_ns_records = self._get_pool_ns_records(context, zone.pool_id)

        soa = self.find_recordset(context,
                                  criterion={'zone_id': zone['id'],
                                             'type': "SOA"})

        soa.records[0].data = self._build_soa_record(zone, pool_ns_records)

        self._update_recordset_in_storage(context, zone, soa,
                                          increment_serial=False)

    # NS Recordset Methods
    def _create_ns(self, context, zone, ns_records):
        # NOTE: We should not be creating NS records when a zone is SECONDARY.
        if zone.type != 'PRIMARY':
            return

        # Create an NS record for each server
        recordlist = objects.RecordList(objects=[
            objects.Record(data=r, managed=True) for r in ns_records])
        values = {
            'name': zone['name'],
            'type': "NS",
            'records': recordlist
        }
        ns, zone = self._create_recordset_in_storage(
            context, zone, objects.RecordSet(**values),
            increment_serial=False)

        return ns

    def _add_ns(self, context, zone, ns_record):
        # Get NS recordset
        # If the zone doesn't have an NS recordset yet, create one
        recordsets = self.find_recordsets(
            context, criterion={'zone_id': zone['id'], 'type': "NS"}
        )

        managed = []
        for rs in recordsets:
            if rs.managed:
                managed.append(rs)

        if len(managed) == 0:
            self._create_ns(context, zone, [ns_record])
            return
        elif len(managed) != 1:
            raise exceptions.RecordSetNotFound("No valid recordset found")

        ns_recordset = managed[0]

        # Add new record to recordset based on the new nameserver
        ns_recordset.records.append(
            objects.Record(data=ns_record, managed=True))

        self._update_recordset_in_storage(context, zone, ns_recordset,
                                          set_delayed_notify=True)

    def _delete_ns(self, context, zone, ns_record):
        ns_recordset = self.find_recordset(
            context, criterion={'zone_id': zone['id'], 'type': "NS"})

        for record in copy.deepcopy(ns_recordset.records):
            if record.data == ns_record:
                ns_recordset.records.remove(record)

        self._update_recordset_in_storage(context, zone, ns_recordset,
                                          set_delayed_notify=True)

    # Quota Enforcement Methods
    def _enforce_zone_quota(self, context, tenant_id):
        criterion = {'tenant_id': tenant_id}
        count = self.storage.count_zones(context, criterion)

        self.quota.limit_check(context, tenant_id, zones=count)

    def _enforce_recordset_quota(self, context, zone):
        # Ensure the recordsets per zone quota is OK
        criterion = {'zone_id': zone.id}
        count = self.storage.count_recordsets(context, criterion)

        self.quota.limit_check(
            context, zone.tenant_id, zone_recordsets=count)

    def _enforce_record_quota(self, context, zone, recordset):
        # Quotas don't apply to managed records.
        if recordset.managed:
            return

        # Ensure the records per zone quota is OK
        zone_criterion = {
            'zone_id': zone.id,
            'managed': False,  # only include non-managed records
        }

        zone_records = self.storage.count_records(context, zone_criterion)

        recordset_criterion = {
            'recordset_id': recordset.id,
            'managed': False,  # only include non-managed records
        }
        recordset_records = self.storage.count_records(
            context, recordset_criterion)

        # We need to check the current number of zones + the
        # changes that add, so lets get +/- from our recordset
        # records based on the action
        adjusted_zone_records = (
            zone_records - recordset_records + len(recordset.records))

        self.quota.limit_check(context, zone.tenant_id,
                               zone_records=adjusted_zone_records)

        # Ensure the records per recordset quota is OK
        self.quota.limit_check(context, zone.tenant_id,
                               recordset_records=recordset_records)

    # Misc Methods
    def get_absolute_limits(self, context):
        # NOTE(Kiall): Currently, we only have quota based limits..
        return self.quota.get_quotas(context, context.tenant)

    # Quota Methods
    def get_quotas(self, context, tenant_id):
        target = {'tenant_id': tenant_id}
        policy.check('get_quotas', context, target)

        if tenant_id != context.tenant and not context.all_tenants:
            raise exceptions.Forbidden()

        return self.quota.get_quotas(context, tenant_id)

    def get_quota(self, context, tenant_id, resource):
        target = {'tenant_id': tenant_id, 'resource': resource}
        policy.check('get_quota', context, target)

        return self.quota.get_quota(context, tenant_id, resource)

    @transaction
    def set_quota(self, context, tenant_id, resource, hard_limit):
        target = {
            'tenant_id': tenant_id,
            'resource': resource,
            'hard_limit': hard_limit,
        }

        policy.check('set_quota', context, target)
        if tenant_id != context.tenant and not context.all_tenants:
            raise exceptions.Forbidden()

        return self.quota.set_quota(context, tenant_id, resource, hard_limit)

    @transaction
    def reset_quotas(self, context, tenant_id):
        target = {'tenant_id': tenant_id}
        policy.check('reset_quotas', context, target)

        self.quota.reset_quotas(context, tenant_id)

    # TLD Methods
    @notification('dns.tld.create')
    @transaction
    def create_tld(self, context, tld):
        policy.check('create_tld', context)

        # The TLD is only created on central's storage and not on the backend.
        created_tld = self.storage.create_tld(context, tld)

        return created_tld

    def find_tlds(self, context, criterion=None, marker=None, limit=None,
                  sort_key=None, sort_dir=None):
        policy.check('find_tlds', context)

        return self.storage.find_tlds(context, criterion, marker, limit,
                                      sort_key, sort_dir)

    def get_tld(self, context, tld_id):
        policy.check('get_tld', context, {'tld_id': tld_id})

        return self.storage.get_tld(context, tld_id)

    @notification('dns.tld.update')
    @transaction
    def update_tld(self, context, tld):
        target = {
            'tld_id': tld.obj_get_original_value('id'),
        }
        policy.check('update_tld', context, target)

        tld = self.storage.update_tld(context, tld)

        return tld

    @notification('dns.tld.delete')
    @transaction
    def delete_tld(self, context, tld_id):
        policy.check('delete_tld', context, {'tld_id': tld_id})

        tld = self.storage.delete_tld(context, tld_id)

        return tld

    # TSIG Key Methods
    @notification('dns.tsigkey.create')
    @transaction
    def create_tsigkey(self, context, tsigkey):
        policy.check('create_tsigkey', context)

        created_tsigkey = self.storage.create_tsigkey(context, tsigkey)

        # TODO(Ron): this method needs to do more than update storage.

        return created_tsigkey

    def find_tsigkeys(self, context, criterion=None, marker=None, limit=None,
                      sort_key=None, sort_dir=None):
        policy.check('find_tsigkeys', context)

        return self.storage.find_tsigkeys(context, criterion, marker,
                                          limit, sort_key, sort_dir)

    def get_tsigkey(self, context, tsigkey_id):
        policy.check('get_tsigkey', context, {'tsigkey_id': tsigkey_id})

        return self.storage.get_tsigkey(context, tsigkey_id)

    @notification('dns.tsigkey.update')
    @transaction
    def update_tsigkey(self, context, tsigkey):
        target = {
            'tsigkey_id': tsigkey.obj_get_original_value('id'),
        }
        policy.check('update_tsigkey', context, target)

        tsigkey = self.storage.update_tsigkey(context, tsigkey)

        # TODO(Ron): this method needs to do more than update storage.

        return tsigkey

    @notification('dns.tsigkey.delete')
    @transaction
    def delete_tsigkey(self, context, tsigkey_id):
        policy.check('delete_tsigkey', context, {'tsigkey_id': tsigkey_id})

        tsigkey = self.storage.delete_tsigkey(context, tsigkey_id)

        # TODO(Ron): this method needs to do more than update storage.

        return tsigkey

    # Tenant Methods
    def find_tenants(self, context):
        policy.check('find_tenants', context)
        return self.storage.find_tenants(context)

    def get_tenant(self, context, tenant_id):
        target = {
            'tenant_id': tenant_id
        }

        policy.check('get_tenant', context, target)

        return self.storage.get_tenant(context, tenant_id)

    def count_tenants(self, context):
        policy.check('count_tenants', context)
        return self.storage.count_tenants(context)

    # Zone Methods

    def _generate_soa_refresh_interval(self):
        """Generate a random refresh interval to stagger AXFRs across multiple
        zones and resolvers
        maximum val: default_soa_refresh_min
        minimum val: default_soa_refresh_max
        """
        assert cfg.CONF.default_soa_refresh_min is not None
        assert cfg.CONF.default_soa_refresh_max is not None
        dispersion = (cfg.CONF.default_soa_refresh_max -
                      cfg.CONF.default_soa_refresh_min) * random.random()
        refresh_time = cfg.CONF.default_soa_refresh_min + dispersion
        return int(refresh_time)

    def _get_pool_ns_records(self, context, pool_id):
        """Get pool ns_records using an elevated context and all_tenants = True

        :param pool_id: Pool ID
        :returns: ns_records
        """
        elevated_context = context.elevated(all_tenants=True)
        pool = self.storage.get_pool(elevated_context, pool_id)
        return pool.ns_records

    @notification('dns.domain.create')
    @notification('dns.zone.create')
    @synchronized_zone(new_zone=True)
    def create_zone(self, context, zone):
        """Create zone: perform checks and then call _create_zone()
        """

        # Default to creating in the current users tenant
        zone.tenant_id = zone.tenant_id or context.tenant

        target = {
            'tenant_id': zone.tenant_id,
            'zone_name': zone.name
        }

        policy.check('create_zone', context, target)

        # Ensure the tenant has enough quota to continue
        self._enforce_zone_quota(context, zone.tenant_id)

        # Ensure the zone name is valid
        self._is_valid_zone_name(context, zone.name)

        # Ensure TTL is above the minimum
        self._is_valid_ttl(context, zone.ttl)

        # Get a pool id
        zone.pool_id = self.scheduler.schedule_zone(context, zone)

        # Handle sub-zones appropriately
        parent_zone = self._is_subzone(
            context, zone.name, zone.pool_id)
        if parent_zone:
            if parent_zone.tenant_id == zone.tenant_id:
                # Record the Parent Zone ID
                zone.parent_zone_id = parent_zone.id
            else:
                raise exceptions.IllegalChildZone('Unable to create'
                                                  'subzone in another '
                                                  'tenants zone')

        # Handle super-zones appropriately
        subzones = self._is_superzone(context, zone.name, zone.pool_id)
        msg = 'Unable to create zone because another tenant owns a ' \
            'subzone of the zone'
        if subzones:
            LOG.debug("Zone '{0}' is a superzone.".format(zone.name))
            for subzone in subzones:
                if subzone.tenant_id != zone.tenant_id:
                    raise exceptions.IllegalParentZone(msg)

        # If this succeeds, subzone parent IDs will be updated
        # after zone is created

        # NOTE(kiall): Fetch the servers before creating the zone, this way
        #              we can prevent zone creation if no servers are
        #              configured.

        pool_ns_records = self._get_pool_ns_records(context, zone.pool_id)
        if len(pool_ns_records) == 0:
            LOG.critical(_LC('No nameservers configured. '
                             'Please create at least one nameserver'))
            raise exceptions.NoServersConfigured()

        # End of pre-flight checks, create zone
        return self._create_zone(context, zone, subzones)

    def _create_zone(self, context, zone, subzones):
        """Create zone straight away
        """

        if zone.type == 'SECONDARY' and zone.serial is None:
            zone.serial = 1

        # randomize the zone refresh time
        zone.refresh = self._generate_soa_refresh_interval()

        zone = self._create_zone_in_storage(context, zone)

        self.zone_api.create_zone(context, zone)

        if zone.type == 'SECONDARY':
            self.mdns_api.perform_zone_xfr(context, zone)

        # If zone is a superzone, update subzones
        # with new parent IDs
        for subzone in subzones:
            LOG.debug("Updating subzone '{0}' parent ID "
                      "using superzone ID '{1}'"
                      .format(subzone.name, zone.id))
            subzone.parent_zone_id = zone.id
            self.update_zone(context, subzone)

        return zone

    @transaction
    def _create_zone_in_storage(self, context, zone):

        zone.action = 'CREATE'
        zone.status = 'PENDING'

        zone = self.storage.create_zone(context, zone)
        pool_ns_records = self.get_zone_ns_records(context, zone['id'])

        # Create the SOA and NS recordsets for the new zone.  The SOA
        # record will always be the first 'created_at' record for a zone.
        self._create_soa(context, zone)
        self._create_ns(context, zone, [n.hostname for n in pool_ns_records])

        if zone.obj_attr_is_set('recordsets'):
            for rrset in zone.recordsets:
                # This allows eventlet to yield, as this looping operation
                # can be very long-lived.
                time.sleep(0)
                self._create_recordset_in_storage(
                    context, zone, rrset, increment_serial=False)

        return zone

    def get_zone(self, context, zone_id):
        """Get a zone, even if flagged for deletion
        """
        zone = self.storage.get_zone(context, zone_id)

        target = {
            'zone_id': zone_id,
            'zone_name': zone.name,
            'tenant_id': zone.tenant_id
        }
        policy.check('get_zone', context, target)

        return zone

    def get_zone_ns_records(self, context, zone_id=None, criterion=None):

        if zone_id is None:
            policy.check('get_zone_ns_records', context)
            pool_id = cfg.CONF['service:central'].default_pool_id
        else:
            zone = self.storage.get_zone(context, zone_id)
            target = {
                'zone_id': zone_id,
                'zone_name': zone.name,
                'tenant_id': zone.tenant_id
            }
            pool_id = zone.pool_id

            policy.check('get_zone_ns_records', context, target)

        # Need elevated context to get the pool
        elevated_context = context.elevated(all_tenants=True)

        # Get the pool for it's list of ns_records
        pool = self.storage.get_pool(elevated_context, pool_id)

        return pool.ns_records

    def find_zones(self, context, criterion=None, marker=None, limit=None,
                   sort_key=None, sort_dir=None):
        """List existing zones including the ones flagged for deletion.
        """
        target = {'tenant_id': context.tenant}
        policy.check('find_zones', context, target)

        return self.storage.find_zones(context, criterion, marker, limit,
                                       sort_key, sort_dir)

    def find_zone(self, context, criterion=None):
        target = {'tenant_id': context.tenant}
        policy.check('find_zone', context, target)

        return self.storage.find_zone(context, criterion)

    @notification('dns.domain.update')
    @notification('dns.zone.update')
    @synchronized_zone()
    def update_zone(self, context, zone, increment_serial=True):
        """Update zone. Perform checks and then call _update_zone()

        :returns: updated zone
        """
        target = {
            'zone_id': zone.obj_get_original_value('id'),
            'zone_name': zone.obj_get_original_value('name'),
            'tenant_id': zone.obj_get_original_value('tenant_id'),
        }

        policy.check('update_zone', context, target)

        changes = zone.obj_get_changes()

        # Ensure immutable fields are not changed
        if 'tenant_id' in changes:
            # TODO(kiall): Moving between tenants should be allowed, but the
            #              current code will not take into account that
            #              RecordSets and Records must also be moved.
            raise exceptions.BadRequest('Moving a zone between tenants is '
                                        'not allowed')

        if 'name' in changes:
            raise exceptions.BadRequest('Renaming a zone is not allowed')

        # Ensure TTL is above the minimum
        ttl = changes.get('ttl')
        self._is_valid_ttl(context, ttl)

        return self._update_zone(context, zone, increment_serial, changes)

    def _update_zone(self, context, zone, increment_serial, changes):
        """Update zone
        """
        zone = self._update_zone_in_storage(
            context, zone, increment_serial=increment_serial)

        # Fire off a XFR
        if 'masters' in changes:
            self.mdns_api.perform_zone_xfr(context, zone)

        self.zone_api.update_zone(context, zone)

        return zone

    @transaction
    def _update_zone_in_storage(self, context, zone,
            increment_serial=True, set_delayed_notify=False):

        zone.action = 'UPDATE'
        zone.status = 'PENDING'

        if increment_serial:
            # _increment_zone_serial increments and updates the zone
            zone = self._increment_zone_serial(
                context, zone, set_delayed_notify=set_delayed_notify)
        else:
            zone = self.storage.update_zone(context, zone)

        return zone

    @notification('dns.domain.delete')
    @notification('dns.zone.delete')
    @synchronized_zone()
    def delete_zone(self, context, zone_id):
        """Delete or abandon a zone
        On abandon, delete the zone from the DB immediately.
        Otherwise, set action to DELETE and status to PENDING and poke
        Pool Manager's "delete_zone" to update the resolvers. PM will then
        poke back to set action to NONE and status to DELETED
        """
        zone = self.storage.get_zone(context, zone_id)

        target = {
            'zone_id': zone_id,
            'zone_name': zone.name,
            'tenant_id': zone.tenant_id
        }

        if hasattr(context, 'abandon') and context.abandon:
            policy.check('abandon_zone', context, target)
        else:
            policy.check('delete_zone', context, target)

        # Prevent deletion of a zone which has child zones
        criterion = {'parent_zone_id': zone_id}

        if self.storage.count_zones(context, criterion) > 0:
            raise exceptions.ZoneHasSubZone('Please delete any subzones '
                                            'before deleting this zone')

        if hasattr(context, 'abandon') and context.abandon:
            LOG.info(_LI("Abandoning zone '%(zone)s'"), {'zone': zone.name})
            zone = self.storage.delete_zone(context, zone.id)
        else:
            zone = self._delete_zone_in_storage(context, zone)
            self.zone_api.delete_zone(context, zone)

        return zone

    @transaction
    def _delete_zone_in_storage(self, context, zone):
        """Set zone action to DELETE and status to PENDING
        to have the zone soft-deleted later on
        """

        zone.action = 'DELETE'
        zone.status = 'PENDING'

        zone = self.storage.update_zone(context, zone)

        return zone

    def purge_zones(self, context, criterion, limit=None):
        """Purge deleted zones.
        :returns: number of purged zones
        """

        policy.check('purge_zones', context, criterion)

        LOG.debug("Performing purge with limit of %r and criterion of %r"
                  % (limit, criterion))

        return self.storage.purge_zones(context, criterion, limit)

    def xfr_zone(self, context, zone_id):
        zone = self.storage.get_zone(context, zone_id)

        target = {
            'zone_id': zone_id,
            'zone_name': zone.name,
            'tenant_id': zone.tenant_id
        }

        policy.check('xfr_zone', context, target)

        if zone.type != 'SECONDARY':
            msg = "Can't XFR a non Secondary zone."
            raise exceptions.BadRequest(msg)

        # Ensure the format of the servers are correct, then poll the
        # serial
        srv = random.choice(zone.masters)
        status, serial, retries = self.mdns_api.get_serial_number(
            context, zone, srv.host, srv.port, 3, 1, 3, 0)

        # Perform XFR if serial's are not equal
        if serial > zone.serial:
            msg = _LI(
                "Serial %(srv_serial)d is not equal to zone's %(serial)d,"
                " performing AXFR")
            LOG.info(
                msg, {"srv_serial": serial, "serial": zone.serial})
            self.mdns_api.perform_zone_xfr(context, zone)

    def count_zones(self, context, criterion=None):
        if criterion is None:
            criterion = {}

        target = {
            'tenant_id': criterion.get('tenant_id', None)
        }

        policy.check('count_zones', context, target)

        return self.storage.count_zones(context, criterion)

    # Report combining all the count reports based on criterion
    def count_report(self, context, criterion=None):
        reports = []

        if criterion is None:
            # Get all the reports
            reports.append({'zones': self.count_zones(context),
                            'records': self.count_records(context),
                            'tenants': self.count_tenants(context)})

        elif criterion == 'zones':
            reports.append({'zones': self.count_zones(context)})

        elif criterion == 'zones_delayed_notify':
            num_zones = self.count_zones(context, criterion=dict(
                delayed_notify=True))
            reports.append({'zones_delayed_notify': num_zones})

        elif criterion == 'records':
            reports.append({'records': self.count_records(context)})

        elif criterion == 'tenants':
            reports.append({'tenants': self.count_tenants(context)})

        else:
            raise exceptions.ReportNotFound()

        return reports

    @notification('dns.zone.touch')
    @synchronized_zone()
    def touch_zone(self, context, zone_id):
        zone = self.storage.get_zone(context, zone_id)

        target = {
            'zone_id': zone_id,
            'zone_name': zone.name,
            'tenant_id': zone.tenant_id
        }

        policy.check('touch_zone', context, target)

        self._touch_zone_in_storage(context, zone)

        self.zone_api.update_zone(context, zone)

        return zone

    @transaction
    def _touch_zone_in_storage(self, context, zone):

        zone = self._increment_zone_serial(context, zone)

        return zone

    # RecordSet Methods
    @notification('dns.recordset.create')
    @synchronized_zone()
    def create_recordset(self, context, zone_id, recordset,
                         increment_serial=True):
        zone = self.storage.get_zone(context, zone_id)

        # Don't allow updates to zones that are being deleted
        if zone.action == 'DELETE':
            raise exceptions.BadRequest('Can not update a deleting zone')

        target = {
            'zone_id': zone_id,
            'zone_name': zone.name,
            'zone_type': zone.type,
            'recordset_name': recordset.name,
            'tenant_id': zone.tenant_id,
        }

        policy.check('create_recordset', context, target)

        recordset, zone = self._create_recordset_in_storage(
            context, zone, recordset, increment_serial=increment_serial)

        self.zone_api.update_zone(context, zone)

        recordset.zone_name = zone.name
        recordset.obj_reset_changes(['zone_name'])

        return recordset

    def _validate_recordset(self, context, zone, recordset):

        # See if we're validating an existing or new recordset
        recordset_id = None
        if hasattr(recordset, 'id'):
            recordset_id = recordset.id

        # Ensure TTL is above the minimum
        if not recordset_id:
            ttl = getattr(recordset, 'ttl', None)
        else:
            changes = recordset.obj_get_changes()
            ttl = changes.get('ttl', None)

        self._is_valid_ttl(context, ttl)

        # Ensure the recordset name and placement is valid
        self._is_valid_recordset_name(context, zone, recordset.name)

        self._is_valid_recordset_placement(
            context, zone, recordset.name, recordset.type, recordset_id)

        self._is_valid_recordset_placement_subzone(
            context, zone, recordset.name)

        # Validate the records
        self._is_valid_recordset_records(recordset)

    @transaction
    def _create_recordset_in_storage(self, context, zone, recordset,
                                     increment_serial=True):

        # Ensure the tenant has enough quota to continue
        self._enforce_recordset_quota(context, zone)

        self._validate_recordset(context, zone, recordset)

        if recordset.obj_attr_is_set('records') and len(recordset.records) > 0:

            # Ensure the tenant has enough zone record quotas to
            # create new records
            self._enforce_record_quota(context, zone, recordset)

            if increment_serial:
                # update the zone's status and increment the serial
                zone = self._update_zone_in_storage(
                    context, zone, increment_serial)

            for record in recordset.records:
                record.action = 'CREATE'
                record.status = 'PENDING'
                record.serial = zone.serial

        recordset = self.storage.create_recordset(context, zone.id,
                                                  recordset)

        # Return the zone too in case it was updated
        return (recordset, zone)

    def get_recordset(self, context, zone_id, recordset_id):
        recordset = self.storage.get_recordset(context, recordset_id)

        if zone_id:
            zone = self.storage.get_zone(context, zone_id)
            # Ensure the zone_id matches the record's zone_id
            if zone.id != recordset.zone_id:
                raise exceptions.RecordSetNotFound()
        else:
            zone = self.storage.get_zone(context, recordset.zone_id)

        target = {
            'zone_id': zone.id,
            'zone_name': zone.name,
            'recordset_id': recordset.id,
            'tenant_id': zone.tenant_id,
        }

        policy.check('get_recordset', context, target)

        recordset.zone_name = zone.name
        recordset.obj_reset_changes(['zone_name'])
        recordset = recordset

        return recordset

    def find_recordsets(self, context, criterion=None, marker=None, limit=None,
                        sort_key=None, sort_dir=None, force_index=False):
        target = {'tenant_id': context.tenant}
        policy.check('find_recordsets', context, target)

        recordsets = self.storage.find_recordsets(context, criterion, marker,
                                                  limit, sort_key, sort_dir,
                                                  force_index)

        return recordsets

    def find_recordset(self, context, criterion=None):
        target = {'tenant_id': context.tenant}
        policy.check('find_recordset', context, target)

        recordset = self.storage.find_recordset(context, criterion)

        return recordset

    def export_zone(self, context, zone_id):
        zone = self.get_zone(context, zone_id)

        criterion = {'zone_id': zone_id}
        recordsets = self.storage.find_recordsets_export(context, criterion)

        return utils.render_template('export-zone.jinja2',
                                     zone=zone,
                                     recordsets=recordsets)

    @notification('dns.recordset.update')
    @synchronized_zone()
    def update_recordset(self, context, recordset, increment_serial=True):
        zone_id = recordset.obj_get_original_value('zone_id')
        zone = self.storage.get_zone(context, zone_id)

        changes = recordset.obj_get_changes()

        # Ensure immutable fields are not changed
        if 'tenant_id' in changes:
            raise exceptions.BadRequest('Moving a recordset between tenants '
                                        'is not allowed')

        if 'zone_id' in changes or 'zone_name' in changes:
            raise exceptions.BadRequest('Moving a recordset between zones '
                                        'is not allowed')

        if 'type' in changes:
            raise exceptions.BadRequest('Changing a recordsets type is not '
                                        'allowed')

        # Don't allow updates to zones that are being deleted
        if zone.action == 'DELETE':
            raise exceptions.BadRequest('Can not update a deleting zone')

        target = {
            'zone_id': recordset.obj_get_original_value('zone_id'),
            'zone_type': zone.type,
            'recordset_id': recordset.obj_get_original_value('id'),
            'zone_name': zone.name,
            'tenant_id': zone.tenant_id
        }

        policy.check('update_recordset', context, target)

        if recordset.managed and not context.edit_managed_records:
            raise exceptions.BadRequest('Managed records may not be updated')

        recordset, zone = self._update_recordset_in_storage(
            context, zone, recordset, increment_serial=increment_serial)

        self.zone_api.update_zone(context, zone)

        return recordset

    @transaction
    def _update_recordset_in_storage(self, context, zone, recordset,
            increment_serial=True, set_delayed_notify=False):

        self._validate_recordset(context, zone, recordset)

        if increment_serial:
            # update the zone's status and increment the serial
            zone = self._update_zone_in_storage(
                context, zone, increment_serial,
                set_delayed_notify=set_delayed_notify)

        if recordset.records:
            for record in recordset.records:
                if record.action != 'DELETE':
                    record.action = 'UPDATE'
                    record.status = 'PENDING'
                    record.serial = zone.serial

            # Ensure the tenant has enough zone record quotas to
            # create new records
            self._enforce_record_quota(context, zone, recordset)

        # Update the recordset
        recordset = self.storage.update_recordset(context, recordset)

        return (recordset, zone)

    @notification('dns.recordset.delete')
    @synchronized_zone()
    def delete_recordset(self, context, zone_id, recordset_id,
                         increment_serial=True):
        zone = self.storage.get_zone(context, zone_id)
        recordset = self.storage.get_recordset(context, recordset_id)

        # Ensure the zone_id matches the recordset's zone_id
        if zone.id != recordset.zone_id:
            raise exceptions.RecordSetNotFound()

        # Don't allow updates to zones that are being deleted
        if zone.action == 'DELETE':
            raise exceptions.BadRequest('Can not update a deleting zone')

        target = {
            'zone_id': zone_id,
            'zone_name': zone.name,
            'zone_type': zone.type,
            'recordset_id': recordset.id,
            'tenant_id': zone.tenant_id
        }

        policy.check('delete_recordset', context, target)

        if recordset.managed and not context.edit_managed_records:
            raise exceptions.BadRequest('Managed records may not be deleted')

        recordset, zone = self._delete_recordset_in_storage(
            context, zone, recordset, increment_serial=increment_serial)

        self.zone_api.update_zone(context, zone)

        recordset.zone_name = zone.name
        recordset.obj_reset_changes(['zone_name'])

        return recordset

    @transaction
    def _delete_recordset_in_storage(self, context, zone, recordset,
                                     increment_serial=True):

        if increment_serial:
            # update the zone's status and increment the serial
            zone = self._update_zone_in_storage(
                context, zone, increment_serial)

        if recordset.records:
            for record in recordset.records:
                record.action = 'DELETE'
                record.status = 'PENDING'
                record.serial = zone.serial

        # Update the recordset's action/status and then delete it
        self.storage.update_recordset(context, recordset)
        recordset = self.storage.delete_recordset(context, recordset.id)

        return (recordset, zone)

    def count_recordsets(self, context, criterion=None):
        if criterion is None:
            criterion = {}

        target = {
            'tenant_id': criterion.get('tenant_id', None)
        }

        policy.check('count_recordsets', context, target)

        return self.storage.count_recordsets(context, criterion)

    # Record Methods
    @notification('dns.record.create')
    @synchronized_zone()
    def create_record(self, context, zone_id, recordset_id, record,
                      increment_serial=True):
        zone = self.storage.get_zone(context, zone_id)

        # Don't allow updates to zones that are being deleted
        if zone.action == 'DELETE':
            raise exceptions.BadRequest('Can not update a deleting zone')

        recordset = self.storage.get_recordset(context, recordset_id)

        target = {
            'zone_id': zone_id,
            'zone_name': zone.name,
            'zone_type': zone.type,
            'recordset_id': recordset_id,
            'recordset_name': recordset.name,
            'tenant_id': zone.tenant_id
        }

        policy.check('create_record', context, target)

        record, zone = self._create_record_in_storage(
            context, zone, recordset, record,
            increment_serial=increment_serial)

        self.zone_api.update_zone(context, zone)

        return record

    @transaction
    def _create_record_in_storage(self, context, zone, recordset, record,
                                  increment_serial=True):

        # Ensure the tenant has enough quota to continue
        self._enforce_record_quota(context, zone, recordset)

        if increment_serial:
            # update the zone's status and increment the serial
            zone = self._update_zone_in_storage(
                context, zone, increment_serial)

        record.action = 'CREATE'
        record.status = 'PENDING'
        record.serial = zone.serial

        record = self.storage.create_record(context, zone.id, recordset.id,
                                            record)

        return (record, zone)

    def get_record(self, context, zone_id, recordset_id, record_id):
        zone = self.storage.get_zone(context, zone_id)
        recordset = self.storage.get_recordset(context, recordset_id)
        record = self.storage.get_record(context, record_id)

        # Ensure the zone_id matches the record's zone_id
        if zone.id != record.zone_id:
            raise exceptions.RecordNotFound()

        # Ensure the recordset_id matches the record's recordset_id
        if recordset.id != record.recordset_id:
            raise exceptions.RecordNotFound()

        target = {
            'zone_id': zone_id,
            'zone_name': zone.name,
            'recordset_id': recordset_id,
            'recordset_name': recordset.name,
            'record_id': record.id,
            'tenant_id': zone.tenant_id
        }

        policy.check('get_record', context, target)

        return record

    def find_records(self, context, criterion=None, marker=None, limit=None,
                     sort_key=None, sort_dir=None):
        target = {'tenant_id': context.tenant}
        policy.check('find_records', context, target)

        return self.storage.find_records(context, criterion, marker, limit,
                                         sort_key, sort_dir)

    def find_record(self, context, criterion=None):
        target = {'tenant_id': context.tenant}
        policy.check('find_record', context, target)

        return self.storage.find_record(context, criterion)

    @notification('dns.record.update')
    @synchronized_zone()
    def update_record(self, context, record, increment_serial=True):
        zone_id = record.obj_get_original_value('zone_id')
        zone = self.storage.get_zone(context, zone_id)

        # Don't allow updates to zones that are being deleted
        if zone.action == 'DELETE':
            raise exceptions.BadRequest('Can not update a deleting zone')

        recordset_id = record.obj_get_original_value('recordset_id')
        recordset = self.storage.get_recordset(context, recordset_id)

        changes = record.obj_get_changes()

        # Ensure immutable fields are not changed
        if 'tenant_id' in changes:
            raise exceptions.BadRequest('Moving a recordset between tenants '
                                        'is not allowed')

        if 'zone_id' in changes:
            raise exceptions.BadRequest('Moving a recordset between zones '
                                        'is not allowed')

        if 'recordset_id' in changes:
            raise exceptions.BadRequest('Moving a recordset between '
                                        'recordsets is not allowed')

        target = {
            'zone_id': record.obj_get_original_value('zone_id'),
            'zone_name': zone.name,
            'zone_type': zone.type,
            'recordset_id': record.obj_get_original_value('recordset_id'),
            'recordset_name': recordset.name,
            'record_id': record.obj_get_original_value('id'),
            'tenant_id': zone.tenant_id
        }

        policy.check('update_record', context, target)

        if recordset.managed and not context.edit_managed_records:
            raise exceptions.BadRequest('Managed records may not be updated')

        record, zone = self._update_record_in_storage(
            context, zone, record, increment_serial=increment_serial)

        self.zone_api.update_zone(context, zone)

        return record

    @transaction
    def _update_record_in_storage(self, context, zone, record,
                                  increment_serial=True):

        if increment_serial:
            # update the zone's status and increment the serial
            zone = self._update_zone_in_storage(
                context, zone, increment_serial)

        record.action = 'UPDATE'
        record.status = 'PENDING'
        record.serial = zone.serial

        # Update the record
        record = self.storage.update_record(context, record)

        return (record, zone)

    @notification('dns.record.delete')
    @synchronized_zone()
    def delete_record(self, context, zone_id, recordset_id, record_id,
                      increment_serial=True):
        zone = self.storage.get_zone(context, zone_id)

        # Don't allow updates to zones that are being deleted
        if zone.action == 'DELETE':
            raise exceptions.BadRequest('Can not update a deleting zone')

        recordset = self.storage.get_recordset(context, recordset_id)
        record = self.storage.get_record(context, record_id)

        # Ensure the zone_id matches the record's zone_id
        if zone.id != record.zone_id:
            raise exceptions.RecordNotFound()

        # Ensure the recordset_id matches the record's recordset_id
        if recordset.id != record.recordset_id:
            raise exceptions.RecordNotFound()

        target = {
            'zone_id': zone_id,
            'zone_name': zone.name,
            'zone_type': zone.type,
            'recordset_id': recordset_id,
            'recordset_name': recordset.name,
            'record_id': record.id,
            'tenant_id': zone.tenant_id
        }

        policy.check('delete_record', context, target)

        if recordset.managed and not context.edit_managed_records:
            raise exceptions.BadRequest('Managed records may not be deleted')

        record, zone = self._delete_record_in_storage(
            context, zone, record, increment_serial=increment_serial)

        self.zone_api.update_zone(context, zone)

        return record

    @transaction
    def _delete_record_in_storage(self, context, zone, record,
                                  increment_serial=True):

        if increment_serial:
            # update the zone's status and increment the serial
            zone = self._update_zone_in_storage(
                context, zone, increment_serial)

        record.action = 'DELETE'
        record.status = 'PENDING'
        record.serial = zone.serial

        record = self.storage.update_record(context, record)

        return (record, zone)

    def count_records(self, context, criterion=None):
        if criterion is None:
            criterion = {}

        target = {
            'tenant_id': criterion.get('tenant_id', None)
        }

        policy.check('count_records', context, target)
        return self.storage.count_records(context, criterion)

    # Diagnostics Methods
    def _sync_zone(self, context, zone):
        return self.pool_manager_api.update_zone(context, zone)

    @transaction
    def sync_zones(self, context):
        policy.check('diagnostics_sync_zones', context)

        zones = self.storage.find_zones(context)

        results = {}
        for zone in zones:
            results[zone.id] = self._sync_zone(context, zone)

        return results

    @transaction
    def sync_zone(self, context, zone_id):
        zone = self.storage.get_zone(context, zone_id)

        target = {
            'zone_id': zone_id,
            'zone_name': zone.name,
            'tenant_id': zone.tenant_id
        }

        policy.check('diagnostics_sync_zone', context, target)

        return self._sync_zone(context, zone)

    @transaction
    def sync_record(self, context, zone_id, recordset_id, record_id):
        zone = self.storage.get_zone(context, zone_id)
        recordset = self.storage.get_recordset(context, recordset_id)

        target = {
            'zone_id': zone_id,
            'zone_name': zone.name,
            'recordset_id': recordset_id,
            'recordset_name': recordset.name,
            'record_id': record_id,
            'tenant_id': zone.tenant_id
        }

        policy.check('diagnostics_sync_record', context, target)

        self.zone_api.update_zone(context, zone)

    def ping(self, context):
        policy.check('diagnostics_ping', context)

        # TODO(Ron): Handle this method properly.
        try:
            backend_status = {'status': None}
        except Exception as e:
            backend_status = {'status': False, 'message': str(e)}

        try:
            storage_status = self.storage.ping(context)
        except Exception as e:
            storage_status = {'status': False, 'message': str(e)}

        if backend_status and storage_status:
            status = True
        else:
            status = False

        return {
            'host': cfg.CONF.host,
            'status': status,
            'backend': backend_status,
            'storage': storage_status
        }

    def _determine_floatingips(self, context, fips, records=None,
                               tenant_id=None):
        """
        Given the context or tenant, records and fips it returns the valid
        floatingips either with a associated record or not. Deletes invalid
        records also.

        Returns a list of tuples with FloatingIPs and it's Record.
        """
        tenant_id = tenant_id or context.tenant

        elevated_context = context.elevated(all_tenants=True,
                                            edit_managed_records=True)
        criterion = {
            'managed': True,
            'managed_resource_type': 'ptr:floatingip',
        }

        records = self.find_records(elevated_context, criterion)
        records = dict([(r['managed_extra'], r) for r in records])

        invalid = []
        data = {}
        # First populate the list of FIPS
        for fip_key, fip_values in fips.items():
            # Check if the FIP has a record
            record = records.get(fip_values['address'])

            # NOTE: Now check if it's owned by the tenant that actually has the
            # FIP in the external service and if not invalidate it (delete it)
            # thus not returning it with in the tuple with the FIP, but None..

            if record:
                record_tenant = record['managed_tenant_id']

                if record_tenant != tenant_id:
                    msg = "Invalid FloatingIP %s belongs to %s but record " \
                          "owner %s"
                    LOG.debug(msg, fip_key, tenant_id, record_tenant)

                    invalid.append(record)
                    record = None
            data[fip_key] = (fip_values, record)

        return data, invalid

    def _invalidate_floatingips(self, context, records):
        """
        Utility method to delete a list of records.
        """
        elevated_context = context.elevated(all_tenants=True,
                                            edit_managed_records=True)
        if len(records) > 0:
            for r in records:
                msg = 'Deleting record %s for FIP %s'
                LOG.debug(msg, r['id'], r['managed_resource_id'])
                self.delete_record(elevated_context, r['zone_id'],
                                   r['recordset_id'], r['id'])

    def _format_floatingips(self, context, data, recordsets=None):
        """
        Given a list of FloatingIP and Record tuples we look through creating
        a new dict of FloatingIPs
        """
        elevated_context = context.elevated(all_tenants=True)

        fips = objects.FloatingIPList()
        for key, value in data.items():
            fip, record = value

            fip_ptr = objects.FloatingIP().from_dict({
                'address': fip['address'],
                'id': fip['id'],
                'region': fip['region'],
                'ptrdname': None,
                'ttl': None,
                'description': None,
                'action': None,
                'status': 'ACTIVE'
            })

            # TTL population requires a present record in order to find the
            # RS or Zone
            if record:
                fip_ptr['action'] = record.action
                fip_ptr['status'] = record.status

                # We can have a recordset dict passed in
                if (recordsets is not None and
                        record['recordset_id'] in recordsets):
                    recordset = recordsets[record['recordset_id']]
                else:
                    recordset = self.storage.get_recordset(
                        elevated_context, record['recordset_id'])

                if recordset['ttl'] is not None:
                    fip_ptr['ttl'] = recordset['ttl']
                else:
                    zone = self.get_zone(
                        elevated_context, record['zone_id'])
                    fip_ptr['ttl'] = zone['ttl']

                fip_ptr['ptrdname'] = record['data']
                fip_ptr['description'] = record['description']
            else:
                LOG.debug("No record information found for %s" %
                          value[0]['id'])

            # Store the "fip_record" with the region and it's id as key
            fips.append(fip_ptr)
        return fips

    def _list_floatingips(self, context, region=None):
        data = self.network_api.list_floatingips(context, region=region)
        return self._list_to_dict(data, keys=['region', 'id'])

    def _list_to_dict(self, data, keys=['id']):
        new = {}
        for i in data:
            key = tuple([i[key] for key in keys])
            new[key] = i
        return new

    def _get_floatingip(self, context, region, floatingip_id, fips):
        if (region, floatingip_id) not in fips:
            msg = 'FloatingIP %s in %s is not associated for tenant "%s"' % \
                (floatingip_id, region, context.tenant)
            raise exceptions.NotFound(msg)
        return fips[region, floatingip_id]

    # PTR ops
    def list_floatingips(self, context):
        """
        List Floating IPs PTR

        A) We have service_catalog in the context and do a lookup using the
               token pr Neutron in the SC
        B) We lookup FIPs using the configured values for this deployment.
        """
        elevated_context = context.elevated(all_tenants=True,
                                            edit_managed_records=True)

        tenant_fips = self._list_floatingips(context)

        valid, invalid = self._determine_floatingips(
            elevated_context, tenant_fips)

        self._invalidate_floatingips(context, invalid)

        return self._format_floatingips(context, valid)

    def get_floatingip(self, context, region, floatingip_id):
        """
        Get Floating IP PTR
        """
        elevated_context = context.elevated(all_tenants=True)

        tenant_fips = self._list_floatingips(context, region=region)

        fip = self._get_floatingip(context, region, floatingip_id, tenant_fips)

        result = self._list_to_dict([fip], keys=['region', 'id'])

        valid, invalid = self._determine_floatingips(
            elevated_context, result)

        self._invalidate_floatingips(context, invalid)

        return self._format_floatingips(context, valid)[0]

    def _set_floatingip_reverse(self, context, region, floatingip_id, values):
        """
        Set the FloatingIP's PTR record based on values.
        """

        elevated_context = context.elevated(all_tenants=True,
                                            edit_managed_records=True)

        tenant_fips = self._list_floatingips(context, region=region)

        fip = self._get_floatingip(context, region, floatingip_id, tenant_fips)

        zone_name = self.network_api.address_zone(fip['address'])

        # NOTE: Find existing zone or create it..
        try:
            zone = self.storage.find_zone(
                elevated_context, {'name': zone_name})
        except exceptions.ZoneNotFound:
            msg = _LI(
                'Creating zone for %(fip_id)s:%(region)s - '
                '%(fip_addr)s zone %(zonename)s'), \
                {'fip_id': floatingip_id, 'region': region,
                'fip_addr': fip['address'], 'zonename': zone_name}
            LOG.info(msg)

            email = cfg.CONF['service:central'].managed_resource_email
            tenant_id = cfg.CONF['service:central'].managed_resource_tenant_id

            zone_values = {
                'type': 'PRIMARY',
                'name': zone_name,
                'email': email,
                'tenant_id': tenant_id
            }

            zone = self.create_zone(
                elevated_context, objects.Zone(**zone_values))

        record_name = self.network_api.address_name(fip['address'])

        recordset_values = {
            'name': record_name,
            'type': 'PTR',
            'ttl': values.get('ttl', None)
        }

        try:
            recordset = self.find_recordset(
                elevated_context, {'name': record_name, 'type': 'PTR'})

            # Update the recordset values
            recordset.name = recordset_values['name']
            recordset.type = recordset_values['type']
            recordset.ttl = recordset_values['ttl']
            recordset.zone_id = zone['id']
            recordset = self.update_recordset(
                elevated_context,
                recordset=recordset)

            # Delete the current records for the recordset
            LOG.debug("Removing old Record")
            for record in recordset.records:
                self.delete_record(
                    elevated_context,
                    zone_id=recordset['zone_id'],
                    recordset_id=recordset['id'],
                    record_id=record['id'])

        except exceptions.RecordSetNotFound:
            recordset = self.create_recordset(
                elevated_context,
                zone_id=zone['id'],
                recordset=objects.RecordSet(**recordset_values))

        record_values = {
            'data': values['ptrdname'],
            'description': values['description'],
            'managed': True,
            'managed_extra': fip['address'],
            'managed_resource_id': floatingip_id,
            'managed_resource_region': region,
            'managed_resource_type': 'ptr:floatingip',
            'managed_tenant_id': context.tenant
        }

        record = self.create_record(
            elevated_context,
            zone_id=zone['id'],
            recordset_id=recordset['id'],
            record=objects.Record(**record_values))

        return self._format_floatingips(
            context, {(region, floatingip_id): (fip, record)},
            {recordset['id']: recordset})[0]

    def _unset_floatingip_reverse(self, context, region, floatingip_id):
        """
        Unset the FloatingIP PTR record based on the

        Service's FloatingIP ID > managed_resource_id
        Tenant ID > managed_tenant_id

        We find the record based on the criteria and delete it or raise.
        """
        elevated_context = context.elevated(all_tenants=True,
                                            edit_managed_records=True)
        criterion = {
            'managed_resource_id': floatingip_id,
            'managed_tenant_id': context.tenant
        }

        try:
            record = self.storage.find_record(
                elevated_context, criterion=criterion)
        except exceptions.RecordNotFound:
            msg = 'No such FloatingIP %s:%s' % (region, floatingip_id)
            raise exceptions.NotFound(msg)

        self.delete_record(
            elevated_context,
            zone_id=record['zone_id'],
            recordset_id=record['recordset_id'],
            record_id=record['id'])

    @transaction
    def update_floatingip(self, context, region, floatingip_id, values):
        """
        We strictly see if values['ptrdname'] is str or None and set / unset
        the requested FloatingIP's PTR record based on that.
        """
        if 'ptrdname' in values.obj_what_changed() and\
                values['ptrdname'] is None:
            self._unset_floatingip_reverse(context, region, floatingip_id)
        elif isinstance(values['ptrdname'], six.string_types):
            return self._set_floatingip_reverse(
                context, region, floatingip_id, values)

    # Blacklisted zones
    @notification('dns.blacklist.create')
    @transaction
    def create_blacklist(self, context, blacklist):
        policy.check('create_blacklist', context)

        created_blacklist = self.storage.create_blacklist(context, blacklist)

        return created_blacklist

    def get_blacklist(self, context, blacklist_id):
        policy.check('get_blacklist', context)

        blacklist = self.storage.get_blacklist(context, blacklist_id)

        return blacklist

    def find_blacklists(self, context, criterion=None, marker=None,
                        limit=None, sort_key=None, sort_dir=None):
        policy.check('find_blacklists', context)

        blacklists = self.storage.find_blacklists(context, criterion,
                                                  marker, limit,
                                                  sort_key, sort_dir)

        return blacklists

    def find_blacklist(self, context, criterion):
        policy.check('find_blacklist', context)

        blacklist = self.storage.find_blacklist(context, criterion)

        return blacklist

    @notification('dns.blacklist.update')
    @transaction
    def update_blacklist(self, context, blacklist):
        target = {
            'blacklist_id': blacklist.id,
        }
        policy.check('update_blacklist', context, target)

        blacklist = self.storage.update_blacklist(context, blacklist)

        return blacklist

    @notification('dns.blacklist.delete')
    @transaction
    def delete_blacklist(self, context, blacklist_id):
        policy.check('delete_blacklist', context)

        blacklist = self.storage.delete_blacklist(context, blacklist_id)

        return blacklist

    # Server Pools
    @notification('dns.pool.create')
    @transaction
    def create_pool(self, context, pool):
        # Verify that there is a tenant_id
        if pool.tenant_id is None:
            pool.tenant_id = context.tenant

        policy.check('create_pool', context)

        created_pool = self.storage.create_pool(context, pool)

        return created_pool

    def find_pools(self, context, criterion=None, marker=None, limit=None,
                   sort_key=None, sort_dir=None):

        policy.check('find_pools', context)

        return self.storage.find_pools(context, criterion, marker, limit,
                                       sort_key, sort_dir)

    def find_pool(self, context, criterion=None):

        policy.check('find_pool', context)

        return self.storage.find_pool(context, criterion)

    def get_pool(self, context, pool_id):

        policy.check('get_pool', context)

        return self.storage.get_pool(context, pool_id)

    @notification('dns.pool.update')
    @transaction
    def update_pool(self, context, pool):

        policy.check('update_pool', context)

        # If there is a nameserver, then additional steps need to be done
        # Since these are treated as mutable objects, we're only going to
        # be comparing the nameserver.value which is the FQDN
        if pool.obj_attr_is_set('ns_records'):
            elevated_context = context.elevated(all_tenants=True)

            # TODO(kiall): ListObjects should be able to give you their
            #              original set of values.
            original_pool_ns_records = self._get_pool_ns_records(context,
                                                                 pool.id)
            # Find the current NS hostnames
            existing_ns = set([n.hostname for n in original_pool_ns_records])

            # Find the desired NS hostnames
            request_ns = set([n.hostname for n in pool.ns_records])

            # Get the NS's to be created and deleted, ignoring the ones that
            # are in both sets, as those haven't changed.
            # TODO(kiall): Factor in priority
            create_ns = request_ns.difference(existing_ns)
            delete_ns = existing_ns.difference(request_ns)

        updated_pool = self.storage.update_pool(context, pool)

        # After the update, handle new ns_records
        for ns in create_ns:
            # Create new NS recordsets for every zone
            zones = self.find_zones(
                context=elevated_context,
                criterion={'pool_id': pool.id, 'action': '!DELETE'})
            for z in zones:
                self._add_ns(elevated_context, z, ns)

        # Then handle the ns_records to delete
        for ns in delete_ns:
            # Cannot delete the last nameserver, so verify that first.
            if len(pool.ns_records) == 0:
                raise exceptions.LastServerDeleteNotAllowed(
                    "Not allowed to delete last of servers"
                )

            # Delete the NS record for every zone
            zones = self.find_zones(
                context=elevated_context,
                criterion={'pool_id': pool.id})
            for z in zones:
                self._delete_ns(elevated_context, z, ns)

        return updated_pool

    @notification('dns.pool.delete')
    @transaction
    def delete_pool(self, context, pool_id):

        policy.check('delete_pool', context)

        # Make sure that there are no existing zones in the pool
        elevated_context = context.elevated(all_tenants=True)
        zones = self.find_zones(
            context=elevated_context,
            criterion={'pool_id': pool_id, 'action': '!DELETE'})

        # If there are existing zones, do not delete the pool
        LOG.debug("Zones is None? %r " % zones)
        if len(zones) == 0:
            pool = self.storage.delete_pool(context, pool_id)
        else:
            raise exceptions.InvalidOperation('pool must not contain zones')

        return pool

    # Pool Manager Integration
    @notification('dns.domain.update')
    @notification('dns.zone.update')
    @transaction
    @synchronized_zone()
    def update_status(self, context, zone_id, status, serial):
        """
        :param context: Security context information.
        :param zone_id: The ID of the designate zone.
        :param status: The status, 'SUCCESS' or 'ERROR'.
        :param serial: The consensus serial number for the zone.
        :return: updated zone
        """
        # TODO(kiall): If the status is SUCCESS and the zone is already ACTIVE,
        #              we likely don't need to do anything.
        self._update_record_status(context, zone_id, status, serial)
        zone = self._update_zone_status(context, zone_id, status, serial)
        return zone

    def _update_zone_status(self, context, zone_id, status, serial):
        """Update zone status in storage

        :return: updated zone
        """
        zone = self.storage.get_zone(context, zone_id)

        zone, deleted = self._update_zone_or_record_status(
            zone, status, serial)

        if zone.status != 'DELETED':
            LOG.debug('Setting zone %s, serial %s: action %s, status %s'
                      % (zone.id, zone.serial, zone.action, zone.status))
            self.storage.update_zone(context, zone)

        if deleted:
            LOG.debug('update_status: deleting %s' % zone.name)
            self.storage.delete_zone(context, zone.id)

        return zone

    def _update_record_status(self, context, zone_id, status, serial):
        """Update status on every record in a zone based on `serial`
        :returns: updated records
        """
        criterion = {
            'zone_id': zone_id
        }

        if status == 'SUCCESS':
            criterion.update({
                'status': ['PENDING', 'ERROR'],
                'serial': '<=%d' % serial,
            })

        elif status == 'ERROR' and serial == 0:
            criterion.update({
                'status': 'PENDING',
            })

        elif status == 'ERROR':
            criterion.update({
                'status': 'PENDING',
                'serial': '<=%d' % serial,
            })

        records = self.storage.find_records(context, criterion=criterion)

        for record in records:
            record, deleted = self._update_zone_or_record_status(
                record, status, serial)

            if record.obj_what_changed():
                LOG.debug('Setting record %s, serial %s: action %s, status %s'
                          % (record.id, record.serial,
                             record.action, record.status))
                self.storage.update_record(context, record)

            # TODO(Ron): Including this to retain the current logic.
            # We should NOT be deleting records.  The record status should
            # be used to indicate the record has been deleted.
            if deleted:
                LOG.debug('Deleting record %s, serial %s: action %s, status %s'
                          % (record.id, record.serial,
                             record.action, record.status))

                self.storage.delete_record(context, record.id)

                recordset = self.storage.get_recordset(
                    context, record.recordset_id)
                if len(recordset.records) == 0:
                    self.storage.delete_recordset(context, recordset.id)

        return records

    @staticmethod
    def _update_zone_or_record_status(zone_or_record, status, serial):
        deleted = False
        if status == 'SUCCESS':
            if zone_or_record.action in ['CREATE', 'UPDATE'] \
                    and zone_or_record.status in ['PENDING', 'ERROR'] \
                    and serial >= zone_or_record.serial:
                zone_or_record.action = 'NONE'
                zone_or_record.status = 'ACTIVE'
            elif zone_or_record.action == 'DELETE' \
                    and zone_or_record.status in ['PENDING', 'ERROR'] \
                    and serial >= zone_or_record.serial:
                zone_or_record.action = 'NONE'
                zone_or_record.status = 'DELETED'
                deleted = True

        elif status == 'ERROR':
            if zone_or_record.status == 'PENDING' \
                    and (serial >= zone_or_record.serial or serial == 0):
                zone_or_record.status = 'ERROR'

        elif status == 'NO_ZONE':
            if zone_or_record.action in ['CREATE', 'UPDATE']:
                zone_or_record.action = 'CREATE'
                zone_or_record.status = 'ERROR'
            elif zone_or_record.action == 'DELETE':
                zone_or_record.action = 'NONE'
                zone_or_record.status = 'DELETED'
                deleted = True

        return zone_or_record, deleted

    # Zone Transfers
    def _transfer_key_generator(self, size=8):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(size))

    @notification('dns.zone_transfer_request.create')
    @transaction
    def create_zone_transfer_request(self, context, zone_transfer_request):

        # get zone
        zone = self.get_zone(context, zone_transfer_request.zone_id)

        # Don't allow transfers for zones that are being deleted
        if zone.action == 'DELETE':
            raise exceptions.BadRequest('Can not transfer a deleting zone')

        target = {
            'tenant_id': zone.tenant_id,
        }
        policy.check('create_zone_transfer_request', context, target)

        zone_transfer_request.key = self._transfer_key_generator()

        if zone_transfer_request.tenant_id is None:
            zone_transfer_request.tenant_id = context.tenant

        created_zone_transfer_request = \
            self.storage.create_zone_transfer_request(
                context, zone_transfer_request)

        return created_zone_transfer_request

    def get_zone_transfer_request(self, context, zone_transfer_request_id):

        elevated_context = context.elevated(all_tenants=True)

        # Get zone transfer request
        zone_transfer_request = self.storage.get_zone_transfer_request(
            elevated_context, zone_transfer_request_id)

        LOG.info(_LI('Target Tenant ID found - using scoped policy'))
        target = {
            'target_tenant_id': zone_transfer_request.target_tenant_id,
            'tenant_id': zone_transfer_request.tenant_id,
        }
        policy.check('get_zone_transfer_request', context, target)

        return zone_transfer_request

    def find_zone_transfer_requests(self, context, criterion=None, marker=None,
                                    limit=None, sort_key=None, sort_dir=None):

        policy.check('find_zone_transfer_requests', context)

        requests = self.storage.find_zone_transfer_requests(
            context, criterion,
            marker, limit,
            sort_key, sort_dir)

        return requests

    def find_zone_transfer_request(self, context, criterion):
        target = {
            'tenant_id': context.tenant,
        }
        policy.check('find_zone_transfer_request', context, target)
        return self.storage.find_zone_transfer_requests(context, criterion)

    @notification('dns.zone_transfer_request.update')
    @transaction
    def update_zone_transfer_request(self, context, zone_transfer_request):

        if 'zone_id' in zone_transfer_request.obj_what_changed():
            raise exceptions.InvalidOperation('Zone cannot be changed')

        target = {
            'tenant_id': zone_transfer_request.tenant_id,
        }
        policy.check('update_zone_transfer_request', context, target)
        request = self.storage.update_zone_transfer_request(
            context, zone_transfer_request)

        return request

    @notification('dns.zone_transfer_request.delete')
    @transaction
    def delete_zone_transfer_request(self, context, zone_transfer_request_id):
        # Get zone transfer request
        zone_transfer_request = self.storage.get_zone_transfer_request(
            context, zone_transfer_request_id)
        target = {
            'tenant_id': zone_transfer_request.tenant_id,
        }
        policy.check('delete_zone_transfer_request', context, target)
        return self.storage.delete_zone_transfer_request(
            context,
            zone_transfer_request_id)

    @notification('dns.zone_transfer_accept.create')
    @transaction
    def create_zone_transfer_accept(self, context, zone_transfer_accept):
        elevated_context = context.elevated(all_tenants=True)
        zone_transfer_request = self.get_zone_transfer_request(
            context, zone_transfer_accept.zone_transfer_request_id)

        zone_transfer_accept.zone_id = zone_transfer_request.zone_id

        if zone_transfer_request.status != 'ACTIVE':
            if zone_transfer_request.status == 'COMPLETE':
                raise exceptions.InvaildZoneTransfer(
                    'Zone Transfer Request has been used')
            raise exceptions.InvaildZoneTransfer(
                'Zone Transfer Request Invalid')

        if zone_transfer_request.key != zone_transfer_accept.key:
            raise exceptions.IncorrectZoneTransferKey(
                'Key does not match stored key for request')

        target = {
            'target_tenant_id': zone_transfer_request.target_tenant_id
        }
        policy.check('create_zone_transfer_accept', context, target)

        if zone_transfer_accept.tenant_id is None:
            zone_transfer_accept.tenant_id = context.tenant

        created_zone_transfer_accept = \
            self.storage.create_zone_transfer_accept(
                context, zone_transfer_accept)

        try:
            zone = self.storage.get_zone(
                elevated_context,
                zone_transfer_request.zone_id)

            # Don't allow transfers for zones that are being deleted
            if zone.action == 'DELETE':
                raise exceptions.BadRequest('Can not transfer a deleting zone')

            zone.tenant_id = zone_transfer_accept.tenant_id
            self.storage.update_zone(elevated_context, zone)

        except Exception:
            created_zone_transfer_accept.status = 'ERROR'
            self.storage.update_zone_transfer_accept(
                context, created_zone_transfer_accept)
            raise
        else:
            created_zone_transfer_accept.status = 'COMPLETE'
            zone_transfer_request.status = 'COMPLETE'
            self.storage.update_zone_transfer_accept(
                context, created_zone_transfer_accept)
            self.storage.update_zone_transfer_request(
                elevated_context, zone_transfer_request)

        return created_zone_transfer_accept

    def get_zone_transfer_accept(self, context, zone_transfer_accept_id):
        # Get zone transfer accept

        zone_transfer_accept = self.storage.get_zone_transfer_accept(
            context, zone_transfer_accept_id)

        target = {
            'tenant_id': zone_transfer_accept.tenant_id
        }
        policy.check('get_zone_transfer_accept', context, target)

        return zone_transfer_accept

    def find_zone_transfer_accepts(self, context, criterion=None, marker=None,
                                   limit=None, sort_key=None, sort_dir=None):
        policy.check('find_zone_transfer_accepts', context)
        return self.storage.find_zone_transfer_accepts(context, criterion,
                                                       marker, limit,
                                                       sort_key, sort_dir)

    def find_zone_transfer_accept(self, context, criterion):
        policy.check('find_zone_transfer_accept', context)
        return self.storage.find_zone_transfer_accept(context, criterion)

    @notification('dns.zone_transfer_accept.update')
    @transaction
    def update_zone_transfer_accept(self, context, zone_transfer_accept):
        target = {
            'tenant_id': zone_transfer_accept.tenant_id
        }
        policy.check('update_zone_transfer_accept', context, target)
        accept = self.storage.update_zone_transfer_accept(
            context, zone_transfer_accept)

        return accept

    @notification('dns.zone_transfer_accept.delete')
    @transaction
    def delete_zone_transfer_accept(self, context, zone_transfer_accept_id):
        # Get zone transfer accept
        zt_accept = self.storage.get_zone_transfer_accept(
            context, zone_transfer_accept_id)

        target = {
            'tenant_id': zt_accept.tenant_id
        }
        policy.check('delete_zone_transfer_accept', context, target)
        return self.storage.delete_zone_transfer_accept(
            context,
            zone_transfer_accept_id)

    # Zone Import Methods
    @notification('dns.zone_import.create')
    def create_zone_import(self, context, request_body):
        target = {'tenant_id': context.tenant}
        policy.check('create_zone_import', context, target)

        values = {
            'status': 'PENDING',
            'message': None,
            'zone_id': None,
            'tenant_id': context.tenant,
            'task_type': 'IMPORT'
        }
        zone_import = objects.ZoneImport(**values)

        created_zone_import = self.storage.create_zone_import(context,
                                                            zone_import)

        self.tg.add_thread(self._import_zone, context, created_zone_import,
                    request_body)

        return created_zone_import

    def _import_zone(self, context, zone_import, request_body):

        def _import(self, context, zone_import, request_body):
            # Dnspython needs a str instead of a unicode object
            if six.PY2:
                request_body = str(request_body)
            zone = None
            try:
                dnspython_zone = dnszone.from_text(
                    request_body,
                    # Don't relativize, or we end up with '@' record names.
                    relativize=False,
                    # Don't check origin, we allow missing NS records
                    # (missing SOA records are taken care of in _create_zone).
                    check_origin=False)
                zone = dnsutils.from_dnspython_zone(dnspython_zone)
                zone.type = 'PRIMARY'

                for rrset in list(zone.recordsets):
                    if rrset.type in ('NS', 'SOA'):
                        zone.recordsets.remove(rrset)

            except dnszone.UnknownOrigin:
                zone_import.message = ('The $ORIGIN statement is required and'
                                      ' must be the first statement in the'
                                      ' zonefile.')
                zone_import.status = 'ERROR'
            except dnsexception.SyntaxError:
                zone_import.message = 'Malformed zonefile.'
                zone_import.status = 'ERROR'
            except exceptions.BadRequest:
                zone_import.message = 'An SOA record is required.'
                zone_import.status = 'ERROR'
            except Exception as e:
                msg = _LE('An undefined error occurred during zone import')
                LOG.exception(msg)
                msg = 'An undefined error occurred. %s'\
                      % six.text_type(e)[:130]
                zone_import.message = msg
                zone_import.status = 'ERROR'

            return zone, zone_import

        # Execute the import in a real Python thread
        zone, zone_import = tpool.execute(_import, self, context,
            zone_import, request_body)

        # If the zone import was valid, create the zone
        if zone_import.status != 'ERROR':
            try:
                zone = self.create_zone(context, zone)
                zone_import.status = 'COMPLETE'
                zone_import.zone_id = zone.id
                zone_import.message = '%(name)s imported' % {'name':
                                                             zone.name}
            except exceptions.DuplicateZone:
                zone_import.status = 'ERROR'
                zone_import.message = 'Duplicate zone.'
            except exceptions.InvalidTTL as e:
                zone_import.status = 'ERROR'
                zone_import.message = six.text_type(e)
            except Exception as e:
                msg = _LE('An undefined error occurred during zone '
                          'import creation')
                LOG.exception(msg)
                msg = 'An undefined error occurred. %s'\
                      % six.text_type(e)[:130]
                zone_import.message = msg
                zone_import.status = 'ERROR'

        self.update_zone_import(context, zone_import)

    def find_zone_imports(self, context, criterion=None, marker=None,
                  limit=None, sort_key=None, sort_dir=None):
        target = {'tenant_id': context.tenant}
        policy.check('find_zone_imports', context, target)

        criterion = {
            'task_type': 'IMPORT'
        }
        return self.storage.find_zone_imports(context, criterion, marker,
                                      limit, sort_key, sort_dir)

    def get_zone_import(self, context, zone_import_id):
        target = {'tenant_id': context.tenant}
        policy.check('get_zone_import', context, target)
        return self.storage.get_zone_import(context, zone_import_id)

    @notification('dns.zone_import.update')
    def update_zone_import(self, context, zone_import):
        target = {
            'tenant_id': zone_import.tenant_id,
        }
        policy.check('update_zone_import', context, target)

        return self.storage.update_zone_import(context, zone_import)

    @notification('dns.zone_import.delete')
    @transaction
    def delete_zone_import(self, context, zone_import_id):
        target = {
            'zone_import_id': zone_import_id,
            'tenant_id': context.tenant
        }
        policy.check('delete_zone_import', context, target)

        zone_import = self.storage.delete_zone_import(context, zone_import_id)

        return zone_import

    # Zone Export Methods
    @notification('dns.zone_export.create')
    def create_zone_export(self, context, zone_id):
        # Try getting the zone to ensure it exists
        zone = self.storage.get_zone(context, zone_id)

        target = {'tenant_id': context.tenant}
        policy.check('create_zone_export', context, target)

        values = {
            'status': 'PENDING',
            'message': None,
            'zone_id': zone_id,
            'tenant_id': context.tenant,
            'task_type': 'EXPORT'
        }
        zone_export = objects.ZoneExport(**values)

        created_zone_export = self.storage.create_zone_export(context,
                                                              zone_export)
        if not cfg.CONF['service:worker'].enabled:
            # So that we can maintain asynch behavior during the time that this
            # lives in central, we'll return the 'PENDING' object, and then the
            # 'COMPLETE'/'ERROR' status will be available on the first poll.
            export = copy.deepcopy(created_zone_export)

            synchronous = cfg.CONF['service:zone_manager'].export_synchronous
            criterion = {'zone_id': zone_id}
            count = self.storage.count_recordsets(context, criterion)

            if synchronous:
                try:
                    self.quota.limit_check(
                            context, context.tenant, api_export_size=count)
                except exceptions.OverQuota:
                    LOG.debug('Zone Export too large to perform synchronously')
                    export.status = 'ERROR'
                    export.message = 'Zone is too large to export'
                    return export

                export.location = \
                    "designate://v2/zones/tasks/exports/%(eid)s/export" % \
                    {'eid': export.id}

                export.status = 'COMPLETE'
            else:
                LOG.debug('No method found to export zone')
                export.status = 'ERROR'
                export.message = 'No suitable method for export'

            self.update_zone_export(context, export)
        else:
            export = copy.deepcopy(created_zone_export)
            self.worker_api.start_zone_export(context, zone, export)

        return created_zone_export

    def find_zone_exports(self, context, criterion=None, marker=None,
                  limit=None, sort_key=None, sort_dir=None):
        target = {'tenant_id': context.tenant}
        policy.check('find_zone_exports', context, target)

        criterion = {
            'task_type': 'EXPORT'
        }
        return self.storage.find_zone_exports(context, criterion, marker,
                                      limit, sort_key, sort_dir)

    def get_zone_export(self, context, zone_export_id):
        target = {'tenant_id': context.tenant}
        policy.check('get_zone_export', context, target)

        return self.storage.get_zone_export(context, zone_export_id)

    @notification('dns.zone_export.update')
    def update_zone_export(self, context, zone_export):
        target = {
            'tenant_id': zone_export.tenant_id,
        }
        policy.check('update_zone_export', context, target)

        return self.storage.update_zone_export(context, zone_export)

    @notification('dns.zone_export.delete')
    @transaction
    def delete_zone_export(self, context, zone_export_id):
        target = {
            'zone_export_id': zone_export_id,
            'tenant_id': context.tenant
        }
        policy.check('delete_zone_export', context, target)

        zone_export = self.storage.delete_zone_export(context, zone_export_id)

        return zone_export

    def find_service_statuses(self, context, criterion=None, marker=None,
                              limit=None, sort_key=None, sort_dir=None):
        """List service statuses.
        """
        policy.check('find_service_statuses', context)

        return self.storage.find_service_statuses(
            context, criterion, marker, limit, sort_key, sort_dir)

    def find_service_status(self, context, criterion=None):
        policy.check('find_service_status', context)

        return self.storage.find_service_status(context, criterion)

    def update_service_status(self, context, service_status):
        policy.check('update_service_status', context)

        criterion = {
            "service_name": service_status.service_name,
            "hostname": service_status.hostname
        }

        if service_status.obj_attr_is_set('id'):
            criterion["id"] = service_status.id

        try:
            db_status = self.storage.find_service_status(
                context, criterion)
            db_status.update(dict(service_status))

            return self.storage.update_service_status(context, db_status)
        except exceptions.ServiceStatusNotFound:
            return self.storage.create_service_status(
                context, service_status)
