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
import copy
import random
from random import SystemRandom
import re
import signal
import string
import time

from dns import exception as dnsexception
from dns import zone as dnszone
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_utils import timeutils

from designate.common import constants
from designate.common.decorators import lock
from designate.common.decorators import notification
from designate.common.decorators import rpc
import designate.conf
from designate import coordination
from designate import dnsutils
from designate import exceptions
from designate import network_api
from designate import objects
from designate import policy
from designate import quota
from designate import scheduler
from designate import service
from designate import storage
from designate.storage import transaction
from designate.storage import transaction_shallow_copy
from designate import utils
from designate.worker import rpcapi as worker_rpcapi


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class Service(service.RPCService):
    RPC_API_VERSION = '6.10'

    target = messaging.Target(version=RPC_API_VERSION)

    def __init__(self):
        self.zone_lock_local = lock.ZoneLockLocal()
        self.notification_thread_local = notification.NotificationThreadLocal()

        self._scheduler = None
        self._storage = None
        self._quota = None

        super().__init__(
            self.service_name, CONF['service:central'].topic,
            threads=CONF['service:central'].threads,
        )
        self.coordination = coordination.Coordination(
            self.service_name, self.tg, grouping_enabled=False
        )
        self.network_api = network_api.get_network_api(CONF.network_api)

    @property
    def scheduler(self):
        if not self._scheduler:
            # Get a scheduler instance
            self._scheduler = scheduler.get_scheduler(storage=self.storage)
        return self._scheduler

    @property
    def quota(self):
        if not self._quota:
            # Get a quota manager instance
            self._quota = quota.get_quota()
        return self._quota

    @property
    def storage(self):
        if not self._storage:
            self._storage = storage.get_storage()
        return self._storage

    @property
    def service_name(self):
        return 'central'

    def start(self):
        if (CONF['service:central'].managed_resource_tenant_id ==
                "00000000-0000-0000-0000-000000000000"):
            LOG.warning("Managed Resource Tenant ID is not properly "
                        "configured")

        super().start()
        self.coordination.start()

    def stop(self, graceful=True):
        self.coordination.stop()
        super().stop(graceful)

    @property
    def worker_api(self):
        return worker_rpcapi.WorkerAPI.get_instance()

    def _is_valid_zone_name(self, context, zone_name):
        # Validate zone name length
        if zone_name is None:
            raise exceptions.InvalidObject

        if len(zone_name) > CONF['service:central'].max_zone_name_len:
            raise exceptions.InvalidZoneName('Name too long')

        # Break the zone name up into its component labels
        zone_labels = zone_name.strip('.').split('.')

        # We need more than 1 label.
        if len(zone_labels) <= 1:
            raise exceptions.InvalidZoneName('More than one label is '
                                             'required')

        tlds = self.storage.find_tlds(context)
        if tlds:
            LOG.debug("Checking if %s has a valid TLD", zone_name)
            allowed = False
            for i in range(-len(zone_labels), 0):
                last_i_labels = zone_labels[i:]
                LOG.debug("Checking %s against the TLD list", last_i_labels)
                if ".".join(last_i_labels) in tlds:
                    allowed = True
                    break
            if not allowed:
                raise exceptions.InvalidZoneName('Invalid TLD')

            # Now check that the zone name is not the same as a TLD
            try:
                stripped_zone_name = zone_name.rstrip('.').lower()
                self.storage.find_tld(
                    context,
                    {'name': stripped_zone_name})
            except exceptions.TldNotFound:
                LOG.debug("%s has a valid TLD", zone_name)
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
        if recordset_name is None:
            raise exceptions.InvalidObject

        if not recordset_name.endswith('.'):
            raise ValueError('Please supply a FQDN')

        # Validate record name length
        max_len = CONF['service:central'].max_recordset_name_len
        if len(recordset_name) > max_len:
            raise exceptions.InvalidRecordSetName('Name too long')

        # RecordSets must be contained in the parent zone
        if (recordset_name != zone['name'] and
                not recordset_name.endswith("." + zone['name'])):
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

        if ((len(recordsets) == 1 and recordsets[0].id != recordset_id) or
                len(recordsets) > 1):
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
        LOG.debug("Checking if %s belongs in any of %s subzones",
                  recordset_name, zone.name)

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
                msg = (
                    'RecordSet belongs in a child zone: {}'
                    .format(child_zone['name'])
                )
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
            LOG.critical(
                'Blacklist regex (%(pattern)s) took too long to evaluate '
                'against zone name (%(zone_name)s',
                {
                    'pattern': blacklist.pattern,
                    'zone_name': zone_name
                })

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
        min_ttl = CONF['service:central'].min_ttl
        if min_ttl is not None and ttl < int(min_ttl):
            try:
                policy.check('use_low_ttl', context)
            except exceptions.Forbidden:
                raise exceptions.InvalidTTL('TTL is below the minimum: %s'
                                            % min_ttl)

    def _is_valid_project_id(self, project_id):
        if project_id is None:
            raise exceptions.MissingProjectID(
                "A project ID must be specified when not using a project "
                "scoped token.")

    # SOA Recordset Methods
    @staticmethod
    def _build_soa_record(zone, ns_records):
        return '%s %s. %d %d %d %d %d' % (
            ns_records[0]['hostname'],
            zone['email'].replace('@', '.'),
            zone['serial'],
            zone['refresh'],
            zone['retry'],
            zone['expire'],
            zone['minimum']
        )

    def _create_soa(self, context, zone):
        pool_ns_records = self._get_pool_ns_records(context, zone.pool_id)
        records = objects.RecordList(objects=[
            objects.Record(
                data=self._build_soa_record(zone, pool_ns_records),
                managed=True
            )
        ])
        return self._create_recordset_in_storage(
            context, zone,
            objects.RecordSet(
                name=zone['name'],
                type='SOA',
                records=records
            ), increment_serial=False
        )[0]

    def _update_soa(self, context, zone):
        # NOTE: We should not be updating SOA records when a zone is SECONDARY.
        if zone.type == constants.ZONE_SECONDARY:
            return

        # Get the pool for it's list of ns_records
        pool_ns_records = self._get_pool_ns_records(context, zone.pool_id)

        soa = self.find_recordset(
            context, criterion={
                'zone_id': zone['id'],
                'type': 'SOA'
            }
        )

        soa.records[0].data = self._build_soa_record(zone, pool_ns_records)

        self._update_recordset_in_storage(
            context, zone, soa, increment_serial=False
        )

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
            'type': 'NS',
            'records': recordlist
        }
        ns, zone = self._create_recordset_in_storage(
            context, zone, objects.RecordSet(**values),
            increment_serial=False
        )

        return ns

    def _add_ns(self, context, zone, ns_record):
        # Get NS recordset
        # If the zone doesn't have an NS recordset yet, create one
        try:
            recordset = self.find_recordset(
                context,
                criterion={
                    'zone_id': zone['id'],
                    'name': zone['name'],
                    'type': 'NS'
                }
            )
        except exceptions.RecordSetNotFound:
            self._create_ns(context, zone, [ns_record])
            return

        # Add new record to recordset based on the new nameserver
        recordset.records.append(
            objects.Record(data=ns_record, managed=True)
        )

        self._update_recordset_in_storage(context, zone, recordset,
                                          set_delayed_notify=True)

    def _delete_ns(self, context, zone, ns_record):
        recordset = self.find_recordset(
            context,
            criterion={
                'zone_id': zone['id'],
                'name': zone['name'],
                'type': 'NS'
            }
        )

        for record in list(recordset.records):
            if record.data == ns_record:
                recordset.records.remove(record)

        self._update_recordset_in_storage(context, zone, recordset,
                                          set_delayed_notify=True)

    # Quota Enforcement Methods
    def _enforce_zone_quota(self, context, tenant_id):
        criterion = {'tenant_id': tenant_id}
        count = self.storage.count_zones(context, criterion)

        # Check if adding one more zone would exceed the quota
        self.quota.limit_check(context, tenant_id, zones=count + 1)

    def _enforce_recordset_quota(self, context, zone):
        # Ensure the recordsets per zone quota is OK
        criterion = {'zone_id': zone.id}
        count = self.storage.count_recordsets(context, criterion)

        # Check if adding one more recordset would exceed the quota
        self.quota.limit_check(
            context, zone.tenant_id, zone_recordsets=count + 1)

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
                               recordset_records=len(recordset.records))

    # Misc Methods
    @rpc.expected_exceptions()
    def get_absolute_limits(self, context):
        # NOTE(Kiall): Currently, we only have quota based limits..
        return self.quota.get_quotas(context, context.project_id)

    # Quota Methods
    @rpc.expected_exceptions()
    def get_quotas(self, context, tenant_id):
        target = {constants.RBAC_PROJECT_ID: tenant_id,
                  'tenant_id': tenant_id,
                  'all_tenants': context.all_tenants}
        policy.check('get_quotas', context, target)
        # NOTE(tkajinam): get_quotas now requires project scope so we assume
        #                 the context should contain project_id
        if (tenant_id != context.project_id and not context.all_tenants):
            raise exceptions.Forbidden()

        return self.quota.get_quotas(context, tenant_id)

    @rpc.expected_exceptions()
    @transaction
    def set_quota(self, context, tenant_id, resource, hard_limit):
        target = {
            constants.RBAC_PROJECT_ID: tenant_id,
            'tenant_id': tenant_id,
            'resource': resource,
            'hard_limit': hard_limit,
        }

        policy.check('set_quota', context, target)
        # NOTE(tkajinam): set_quota now requires project scope so we assume
        #                 the context should contain project_id
        if (tenant_id != context.project_id and not context.all_tenants):
            raise exceptions.Forbidden()

        return self.quota.set_quota(context, tenant_id, resource, hard_limit)

    @transaction
    def reset_quotas(self, context, tenant_id):
        target = {constants.RBAC_PROJECT_ID: tenant_id,
                  'tenant_id': tenant_id}
        policy.check('reset_quotas', context, target)

        self.quota.reset_quotas(context, tenant_id)

    # TLD Methods
    @rpc.expected_exceptions()
    @notification.notify_type('dns.tld.create')
    @transaction
    def create_tld(self, context, tld):
        policy.check('create_tld', context)

        # The TLD is only created on central's storage and not on the backend.
        created_tld = self.storage.create_tld(context, tld)

        return created_tld

    @rpc.expected_exceptions()
    def find_tlds(self, context, criterion=None, marker=None, limit=None,
                  sort_key=None, sort_dir=None):
        policy.check('find_tlds', context)

        return self.storage.find_tlds(context, criterion, marker, limit,
                                      sort_key, sort_dir)

    @rpc.expected_exceptions()
    def get_tld(self, context, tld_id):
        policy.check('get_tld', context, {'tld_id': tld_id})

        return self.storage.get_tld(context, tld_id)

    @rpc.expected_exceptions()
    @notification.notify_type('dns.tld.update')
    @transaction
    def update_tld(self, context, tld):
        target = {
            'tld_id': tld.obj_get_original_value('id'),
        }
        policy.check('update_tld', context, target)

        tld = self.storage.update_tld(context, tld)

        return tld

    @rpc.expected_exceptions()
    @notification.notify_type('dns.tld.delete')
    @transaction
    def delete_tld(self, context, tld_id):
        policy.check('delete_tld', context, {'tld_id': tld_id})

        tld = self.storage.delete_tld(context, tld_id)

        return tld

    # TSIG Key Methods
    @rpc.expected_exceptions()
    @notification.notify_type('dns.tsigkey.create')
    @transaction
    def create_tsigkey(self, context, tsigkey):
        policy.check('create_tsigkey', context)

        created_tsigkey = self.storage.create_tsigkey(context, tsigkey)

        # TODO(Ron): this method needs to do more than update storage.

        return created_tsigkey

    @rpc.expected_exceptions()
    def find_tsigkeys(self, context, criterion=None, marker=None, limit=None,
                      sort_key=None, sort_dir=None):
        policy.check('find_tsigkeys', context)

        return self.storage.find_tsigkeys(context, criterion, marker,
                                          limit, sort_key, sort_dir)

    @rpc.expected_exceptions()
    def get_tsigkey(self, context, tsigkey_id):
        policy.check('get_tsigkey', context, {'tsigkey_id': tsigkey_id})

        return self.storage.get_tsigkey(context, tsigkey_id)

    @rpc.expected_exceptions()
    @notification.notify_type('dns.tsigkey.update')
    @transaction
    def update_tsigkey(self, context, tsigkey):
        target = {
            'tsigkey_id': tsigkey.obj_get_original_value('id'),
        }
        policy.check('update_tsigkey', context, target)

        tsigkey = self.storage.update_tsigkey(context, tsigkey)

        # TODO(Ron): this method needs to do more than update storage.

        return tsigkey

    @rpc.expected_exceptions()
    @notification.notify_type('dns.tsigkey.delete')
    @transaction
    def delete_tsigkey(self, context, tsigkey_id):
        policy.check('delete_tsigkey', context, {'tsigkey_id': tsigkey_id})

        tsigkey = self.storage.delete_tsigkey(context, tsigkey_id)

        # TODO(Ron): this method needs to do more than update storage.

        return tsigkey

    # Tenant Methods
    @rpc.expected_exceptions()
    def find_tenants(self, context):
        policy.check('find_tenants', context)
        return self.storage.find_tenants(context)

    @rpc.expected_exceptions()
    def get_tenant(self, context, tenant_id):
        target = {constants.RBAC_PROJECT_ID: tenant_id,
                  'tenant_id': tenant_id}

        policy.check('get_tenant', context, target)

        return self.storage.get_tenant(context, tenant_id)

    @rpc.expected_exceptions()
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
        assert CONF.default_soa_refresh_min is not None
        assert CONF.default_soa_refresh_max is not None
        dispersion = (CONF.default_soa_refresh_max -
                      CONF.default_soa_refresh_min) * random.random()
        refresh_time = CONF.default_soa_refresh_min + dispersion
        return int(refresh_time)

    def _get_pool_ns_records(self, context, pool_id):
        """Get pool ns_records using an elevated context and all_tenants = True

        :param pool_id: Pool ID
        :returns: ns_records
        """
        elevated_context = context.elevated(all_tenants=True)
        pool = self.storage.get_pool(elevated_context, pool_id)
        return pool.ns_records

    @rpc.expected_exceptions()
    @transaction
    @lock.synchronized_zone()
    def increment_zone_serial(self, context, zone):
        zone.serial = self.storage.increment_serial(context, zone.id)
        self._update_soa(context, zone)
        return zone.serial

    @rpc.expected_exceptions()
    @notification.notify_type('dns.domain.create')
    @notification.notify_type('dns.zone.create')
    @lock.synchronized_zone(new_zone=True)
    def create_zone(self, context, zone):
        """Create zone: perform checks and then call _create_zone()
        """

        # Default to creating in the current users tenant
        zone.tenant_id = zone.tenant_id or context.project_id

        target = {
            constants.RBAC_PROJECT_ID: zone.tenant_id,
            'tenant_id': zone.tenant_id,
            'zone_name': zone.name
        }

        policy.check('create_zone', context, target)

        self._enforce_catalog_zone_policy(context, zone)

        self._is_valid_project_id(zone.tenant_id)

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
                raise exceptions.IllegalChildZone('Unable to create '
                                                  'subzone in another '
                                                  'tenants zone')

        # Handle super-zones appropriately
        subzones = self._is_superzone(context, zone.name, zone.pool_id)
        msg = ('Unable to create zone because another tenant owns a subzone '
               'of the zone')
        if subzones:
            LOG.debug("Zone '%s' is a superzone.", zone.name)
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
            LOG.critical('No nameservers configured. Please create at least '
                         'one nameserver')
            raise exceptions.NoServersConfigured()

        # End of pre-flight checks, create zone
        return self._create_zone(context, zone, subzones)

    def _create_zone(self, context, zone, subzones):
        """Create zone straight away
        """

        if zone.type == constants.ZONE_SECONDARY and zone.serial is None:
            zone.serial = 1

        # randomize the zone refresh time
        zone.refresh = self._generate_soa_refresh_interval()

        zone = self._create_zone_in_storage(context, zone)

        if zone.type != constants.ZONE_CATALOG:
            self.worker_api.create_zone(context, zone)

        if zone.type == constants.ZONE_SECONDARY:
            self.worker_api.perform_zone_xfr(context, zone)

        # If zone is a superzone, update subzones
        # with new parent IDs
        for subzone in subzones:
            LOG.debug("Updating subzone '%s' parent ID using "
                      "superzone ID '%s'", subzone.name, zone.id)
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
                    context, zone, rrset, increment_serial=False
                )

        self._ensure_catalog_zone_serial_increment(context, zone)

        return zone

    @rpc.expected_exceptions()
    def get_zone(self, context, zone_id, apply_tenant_criteria=True):
        """Get a zone, even if flagged for deletion
        """
        zone = self.storage.get_zone(
            context, zone_id, apply_tenant_criteria=apply_tenant_criteria)

        # Save a DB round trip if we don't need to check for shared
        zone_shared = False
        if (context.project_id != zone.tenant_id) and not context.all_tenants:
            zone_shared = self.storage.is_zone_shared_with_project(
                zone_id, context.project_id)
            if not zone_shared:
                # Maintain consistency with the previous API and _find_zones()
                # and _find() when apply_tenant_criteria is True.
                raise exceptions.ZoneNotFound(
                    "Could not find %s" % zone.obj_name())

        # TODO(johnsom) This should account for all-projects context
        # it passes today due to ADMIN
        target = {
            'zone_id': zone_id,
            'zone_name': zone.name,
            'zone_shared': zone_shared,
            constants.RBAC_PROJECT_ID: zone.tenant_id,
            'tenant_id': zone.tenant_id
        }
        policy.check('get_zone', context, target)

        return zone

    @rpc.expected_exceptions()
    def get_zone_ns_records(self, context, zone_id=None, criterion=None):
        if zone_id is None:
            policy.check('get_zone_ns_records', context)
            pool_id = CONF['service:central'].default_pool_id
        else:
            zone = self.storage.get_zone(context, zone_id)

            target = {
                'zone_id': zone_id,
                'zone_name': zone.name,
                constants.RBAC_PROJECT_ID: zone.tenant_id,
                'tenant_id': zone.tenant_id
            }
            pool_id = zone.pool_id

            policy.check('get_zone_ns_records', context, target)

        # Need elevated context to get the pool
        elevated_context = context.elevated(all_tenants=True)

        # Get the pool for it's list of ns_records
        pool = self.storage.get_pool(elevated_context, pool_id)

        return pool.ns_records

    @rpc.expected_exceptions()
    def find_zones(self, context, criterion=None, marker=None, limit=None,
                   sort_key=None, sort_dir=None):
        """List existing zones including the ones flagged for deletion.
        """
        target = {constants.RBAC_PROJECT_ID: context.project_id,
                  'tenant_id': context.project_id}

        policy.check('find_zones', context, target)

        if 'admin' not in context.roles:
            if criterion is None:
                criterion = {}
            criterion['type'] = '!CATALOG'

        return self.storage.find_zones(context, criterion, marker, limit,
                                       sort_key, sort_dir)

    @rpc.expected_exceptions()
    @notification.notify_type('dns.domain.update')
    @notification.notify_type('dns.zone.update')
    @lock.synchronized_zone()
    def update_zone(self, context, zone, increment_serial=True):
        """Update zone. Perform checks and then call _update_zone()

        :returns: updated zone
        """
        target = {
            'zone_id': zone.obj_get_original_value('id'),
            'zone_name': zone.obj_get_original_value('name'),
            constants.RBAC_PROJECT_ID: (
                zone.obj_get_original_value('tenant_id')),
            'tenant_id': zone.obj_get_original_value('tenant_id')
        }

        policy.check('update_zone', context, target)
        self._enforce_catalog_zone_policy(context, zone)

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
            context, zone, increment_serial=increment_serial
        )

        # Fire off a XFR
        if zone.type == constants.ZONE_SECONDARY and 'masters' in changes:
            self.worker_api.perform_zone_xfr(context, zone)

        return zone

    @transaction
    def _update_zone_in_storage(self, context, zone,
                                increment_serial=True,
                                set_delayed_notify=False):
        zone.action = 'UPDATE'
        zone.status = 'PENDING'

        if increment_serial:
            zone.increment_serial = True
        if set_delayed_notify:
            zone.delayed_notify = True

        zone = self.storage.update_zone(context, zone)

        return zone

    @rpc.expected_exceptions()
    @notification.notify_type('dns.domain.delete')
    @notification.notify_type('dns.zone.delete')
    @lock.synchronized_zone()
    def delete_zone(self, context, zone_id):
        """Delete or abandon a zone
        On abandon, delete the zone from the DB immediately.
        Otherwise, set action to DELETE and status to PENDING and poke
        Pool Manager's "delete_zone" to update the resolvers. PM will then
        poke back to set action to NONE and status to DELETED
        """
        zone = self.storage.get_zone(context, zone_id)

        self._enforce_catalog_zone_policy(context, zone)

        target = {
            'zone_id': zone_id,
            'zone_name': zone.name,
            constants.RBAC_PROJECT_ID: zone.tenant_id,
            'tenant_id': zone.tenant_id
        }

        if hasattr(context, 'abandon') and context.abandon:
            policy.check('abandon_zone', context, target)
        else:
            policy.check('delete_zone', context, target)

        # Prevent the deletion of a shared zone if the delete-shares modifier
        # is not specified.
        if zone.shared and not context.delete_shares:
            raise exceptions.ZoneShared(
                'This zone is shared with other projects, please remove these '
                'shares before deletion or use the delete-shares modifier to '
                'override this warning.')

        # Prevent deletion of a zone which has child zones
        criterion = {'parent_zone_id': zone_id}

        # Look for child zones across all tenants with elevated context
        if self.storage.count_zones(context.elevated(all_tenants=True),
                                    criterion) > 0:
            raise exceptions.ZoneHasSubZone('Please delete any subzones '
                                            'before deleting this zone')

        # If the zone is shared and delete_shares was specified, remove all
        # of the zone shares in preparation for the zone delete.
        if zone.shared and context.delete_shares:
            self.storage.delete_zone_shares(zone.id)

        if hasattr(context, 'abandon') and context.abandon:
            LOG.info("Abandoning zone '%(zone)s'", {'zone': zone.name})
            zone = self.storage.delete_zone(context, zone.id)
        else:
            zone = self._delete_zone_in_storage(context, zone)
            delete_zonefile = False
            if context.hard_delete:
                delete_zonefile = True
            self.worker_api.delete_zone(context, zone,
                                        hard_delete=delete_zonefile)

        return zone

    @transaction
    def _delete_zone_in_storage(self, context, zone):
        """Set zone action to DELETE and status to PENDING
        to have the zone soft-deleted later on
        """

        zone.action = 'DELETE'
        zone.status = 'PENDING'

        zone = self.storage.update_zone(context, zone)

        self._ensure_catalog_zone_serial_increment(context, zone)

        return zone

    @rpc.expected_exceptions()
    def purge_zones(self, context, criterion, limit=None):
        """Purge deleted zones.
        :returns: number of purged zones
        """

        policy.check('purge_zones', context, criterion)

        LOG.debug("Performing purge with limit of %r and criterion of %r",
                  limit, criterion)

        return self.storage.purge_zones(context, criterion, limit)

    @rpc.expected_exceptions()
    def xfr_zone(self, context, zone_id):
        zone = self.storage.get_zone(context, zone_id)

        target = {
            'zone_id': zone_id,
            'zone_name': zone.name,
            constants.RBAC_PROJECT_ID: zone.tenant_id,
            'tenant_id': zone.tenant_id
        }

        policy.check('xfr_zone', context, target)

        if zone.type != constants.ZONE_SECONDARY:
            raise exceptions.BadRequest("Can't XFR a non Secondary zone.")

        # Ensure the format of the servers are correct, then poll the
        # serial
        srv = random.choice(zone.masters)
        status, serial = self.worker_api.get_serial_number(
            context, zone, srv.host, srv.port)

        # Perform XFR if serial's are not equal
        if serial is not None and serial > zone.serial:
            LOG.info("Serial %(srv_serial)d is not equal to zone's "
                     "%(serial)d, performing AXFR",
                     {"srv_serial": serial, "serial": zone.serial})
            self.worker_api.perform_zone_xfr(context, zone)

    @rpc.expected_exceptions()
    def count_zones(self, context, criterion=None):
        if criterion is None:
            criterion = {}

        target = {
            constants.RBAC_PROJECT_ID: criterion.get('tenant_id', None),
            'tenant_id': criterion.get('tenant_id', None)
        }

        policy.check('count_zones', context, target)

        return self.storage.count_zones(context, criterion)

    # Report combining all the count reports based on criterion
    @rpc.expected_exceptions()
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

    # Shared zones
    @rpc.expected_exceptions()
    @notification.notify_type('dns.zone.share')
    @transaction
    def share_zone(self, context, zone_id, shared_zone):
        # Ensure that zone exists and get the zone owner
        zone = self.storage.get_zone(context, zone_id)

        target = {constants.RBAC_PROJECT_ID: zone.tenant_id,
                  'tenant_id': zone.tenant_id}

        policy.check('share_zone', context, target)

        self._enforce_catalog_zone_policy(context, zone)
        self._is_valid_project_id(context.project_id)

        if zone.tenant_id == shared_zone.target_project_id:
            raise exceptions.BadRequest(
                'Cannot share the zone with the zone owner.')

        shared_zone['project_id'] = context.project_id
        shared_zone['zone_id'] = zone_id

        shared_zone = self.storage.share_zone(context, shared_zone)

        return shared_zone

    @rpc.expected_exceptions()
    @notification.notify_type('dns.zone.unshare')
    @transaction
    def unshare_zone(self, context, zone_id, zone_share_id):
        # Ensure the share exists and get the share owner
        shared_zone = self.get_shared_zone(context, zone_id, zone_share_id)

        target = {constants.RBAC_PROJECT_ID: shared_zone.project_id,
                  'tenant_id': shared_zone.project_id}

        policy.check('unshare_zone', context, target)

        # Prevent unsharing of a zone which has child zones in other tenants
        criterion = {
            'parent_zone_id': shared_zone.zone_id,
            'tenant_id': "%s" % shared_zone.target_project_id,
        }

        # Look for child zones across all tenants with elevated context
        if self.storage.count_zones(context.elevated(all_tenants=True),
                                    criterion) > 0:
            raise exceptions.SharedZoneHasSubZone(
                'Please delete all subzones owned by project %s '
                'before unsharing this zone' % shared_zone.target_project_id
            )

        # Prevent unsharing of a zone which has recordsets in other tenants
        criterion = {
            'zone_id': shared_zone.zone_id,
            'tenant_id': "%s" % shared_zone.target_project_id,
        }

        # Look for recordsets across all tenants with elevated context
        if self.storage.count_recordsets(
                context.elevated(all_tenants=True), criterion) > 0:
            raise exceptions.SharedZoneHasRecordSets(
                'Please delete all recordsets owned by project %s '
                'before unsharing this zone.' % shared_zone.target_project_id
            )

        shared_zone = self.storage.unshare_zone(
            context, zone_id, zone_share_id
        )

        return shared_zone

    @rpc.expected_exceptions()
    def find_shared_zones(self, context, criterion=None, marker=None,
                          limit=None, sort_key=None, sort_dir=None):

        # By default we will let any valid token through as the filter
        # criteria below will limit the scope of the results.
        policy.check('find_zone_shares', context)

        if not context.all_tenants and criterion:
            # Check that they are asking for another projects shares
            target = {constants.RBAC_PROJECT_ID: criterion.get(
                          'target_project_id', context.project_id),
                      'tenant_id': criterion.get(
                          'target_project_id', context.project_id)}

            policy.check('find_project_zone_share', context, target)

        shared_zones = self.storage.find_shared_zones(
            context, criterion, marker, limit, sort_key, sort_dir
        )

        return shared_zones

    @rpc.expected_exceptions()
    def get_shared_zone(self, context, zone_id, zone_share_id):
        # Ensure that share exists and get the share owner
        zone_share = self.storage.get_shared_zone(
            context, zone_id, zone_share_id)

        target = {constants.RBAC_PROJECT_ID: zone_share.project_id,
                  'tenant_id': zone_share.project_id}

        policy.check('get_zone_share', context, target)

        return zone_share

    def _check_zone_share_permission(self, context, zone):
        """
        Check if a request is acceptable for the requesting project ID.
        If the requestor is not the zone owner and the zone is not shared
        with them, return a 404 Not Found to match previous API versions.
        Otherwise, the later RBAC check will raise a 403 Forbidden.

        :param context: The security context for the request.
        :param zone: The zone the request is against.
        :return: If the zone is shared with the requesting project ID or not.
        """
        zone_shared = False
        if (context.project_id != zone.tenant_id) and not context.all_tenants:
            zone_shared = self.storage.is_zone_shared_with_project(
                zone.id, context.project_id)
            if not zone_shared:
                # Maintain consistency with the previous API and _find_zones()
                # and _find() when apply_tenant_criteria is True.
                raise exceptions.ZoneNotFound(
                    "Could not find %s" % zone.obj_name())
        return zone_shared

    @rpc.expected_exceptions()
    @notification.notify_type('dns.domain.update')
    @notification.notify_type('dns.zone.update')
    def pool_move_zone(self, context, zone_id, target_pool_id=None):
        """Move zone. Perform checks and then create zone in destination pool

        :returns: moved zone
        """
        target = {
            'zone_id': zone_id,
            constants.RBAC_PROJECT_ID: context.project_id,
            'tenant_id': context.project_id,
        }

        policy.check('pool_move_zone', context, target)

        # Get the destination pool
        zone = self.storage.get_zone(context, zone_id)
        orig_pool_id = zone.pool_id

        if target_pool_id is None:
            target_pool_id = self.scheduler.schedule_zone(context, zone)
            if target_pool_id == orig_pool_id:
                raise exceptions.BadRequest('No valid pool selected')
            # Update the orignal zone with new pool_id
            zone.pool_id = target_pool_id

        # Need elevated context to get the pool
        elevated_context = context.elevated(all_tenants=True)
        try:
            self.storage.get_pool(elevated_context, target_pool_id)
        except exceptions.PoolNotFound:
            raise exceptions.BadRequest('Target pool does not exist')

        target_pool_ns_records = self._get_pool_ns_records(context,
                                                           target_pool_id)
        if len(target_pool_ns_records) == 0:
            LOG.critical('No nameservers configured. Please create at least '
                         'one nameserver on target pool')
            raise exceptions.NoServersConfigured()

        orig_pool_ns_records = self._get_pool_ns_records(context,
                                                         orig_pool_id)

        target_ns = {n.hostname for n in target_pool_ns_records}
        orig_ns = {n.hostname for n in orig_pool_ns_records}
        create_ns = target_ns.difference(orig_ns)
        delete_ns = orig_ns.difference(target_ns)

        # Update target NS servers for the zone
        for ns_record in create_ns:
            self._add_ns(elevated_context, zone, ns_record)

        # Then handle the ns_records to delete
        for ns_record in delete_ns:
            self._delete_ns(elevated_context, zone, ns_record)

        zone = self._update_zone_in_storage(
                context, zone, increment_serial=False)

        LOG.info("Moving zone '%(zone)s' to pool '%(pool)s'",
                 {'zone': zone.name, 'pool': target_pool_id})
        zone.pool_id = target_pool_id
        zone.refresh = self._generate_soa_refresh_interval()
        zone.action = 'CREATE'
        zone.status = 'PENDING'
        self.worker_api.create_zone(context, zone)

        return zone

    # RecordSet Methods
    @rpc.expected_exceptions()
    @notification.notify_type('dns.recordset.create')
    def create_recordset(self, context, zone_id, recordset,
                         increment_serial=True):
        zone = self.storage.get_zone(context, zone_id,
                                     apply_tenant_criteria=False)

        self._enforce_catalog_zone_policy(context, zone)

        # Note this call must follow the get_zone call to maintain API response
        # code behavior.
        zone_shared = self._check_zone_share_permission(context, zone)

        # Don't allow updates to zones that are being deleted
        if zone.action == 'DELETE':
            raise exceptions.BadRequest('Can not update a deleting zone')

        target = {
            'zone_id': zone_id,
            'zone_name': zone.name,
            'zone_type': zone.type,
            'zone_shared': zone_shared,
            'recordset_name': recordset.name,
            constants.RBAC_PROJECT_ID: zone.tenant_id,
            'tenant_id': zone.tenant_id
        }

        policy.check('create_recordset', context, target)

        # Override the context to be all_tenants here as we have already
        # passed the RBAC check for this call and context checks in lower
        # layers will fail for shared zones.
        # TODO(johnsom) Remove once context checking is removed from the lower
        #               code layers.
        context = context.elevated(all_tenants=True)

        recordset, zone = self._create_recordset_in_storage(
            context, zone, recordset, increment_serial=increment_serial
        )

        recordset.zone_name = zone.name
        recordset.obj_reset_changes(['zone_name'])

        return recordset

    def _validate_recordset(self, context, zone, recordset):
        # Ensure TTL is above the minimum
        if not recordset.id:
            ttl = getattr(recordset, 'ttl', None)
        else:
            changes = recordset.obj_get_changes()
            ttl = changes.get('ttl', None)

        self._is_valid_ttl(context, ttl)

        # Ensure the recordset name and placement is valid
        self._is_valid_recordset_name(context, zone, recordset.name)

        self._is_valid_recordset_placement(
            context, zone, recordset.name, recordset.type, recordset.id)

        self._is_valid_recordset_placement_subzone(
            context, zone, recordset.name)

        # Validate the records
        self._is_valid_recordset_records(recordset)

    @transaction_shallow_copy
    def _create_recordset_in_storage(self, context, zone, recordset,
                                     increment_serial=True):
        # Ensure the tenant has enough quota to continue
        self._enforce_recordset_quota(context, zone)
        self._validate_recordset(context, zone, recordset)

        if recordset.obj_attr_is_set('records') and recordset.records:
            # Ensure the tenant has enough zone record quotas to
            # create new records
            self._enforce_record_quota(context, zone, recordset)

            for record in recordset.records:
                record.action = 'CREATE'
                record.status = 'PENDING'
                if not increment_serial:
                    record.serial = zone.serial
                else:
                    record.serial = timeutils.utcnow_ts()

        new_recordset = self.storage.create_recordset(context, zone.id,
                                                      recordset)
        if recordset.records and increment_serial:
            # update the zone's status and increment the serial
            zone = self._update_zone_in_storage(
                context, zone, increment_serial
            )

        # Return the zone too in case it was updated
        return new_recordset, zone

    @rpc.expected_exceptions()
    def get_recordset(self, context, zone_id, recordset_id):
        # apply_tenant_criteria=False here as we will gate visibility
        # with the RBAC rules below. This allows project that share the zone
        # to see all of the records of the zone.
        if zone_id:
            recordset = self.storage.find_recordset(
                context, criterion={'id': recordset_id, 'zone_id': zone_id},
                apply_tenant_criteria=False)
            zone = self.storage.get_zone(context, zone_id,
                                         apply_tenant_criteria=False)
            # Ensure the zone_id matches the record's zone_id
            if zone.id != recordset.zone_id:
                raise exceptions.RecordSetNotFound()
        else:
            recordset = self.storage.find_recordset(
                context, criterion={'id': recordset_id},
                apply_tenant_criteria=False)
            zone = self.storage.get_zone(context, recordset.zone_id,
                                         apply_tenant_criteria=False)

        # Note this call must follow the get_zone call to maintain API response
        # code behavior.
        zone_shared = self._check_zone_share_permission(context, zone)

        # TODO(johnsom) This should account for all_projects
        target = {
            'zone_id': zone.id,
            'zone_name': zone.name,
            'zone_shared': zone_shared,
            'recordset_id': recordset.id,
            constants.RBAC_PROJECT_ID: zone.tenant_id,
            'tenant_id': zone.tenant_id
        }

        policy.check('get_recordset', context, target)

        recordset.zone_name = zone.name
        recordset.obj_reset_changes(['zone_name'])
        recordset = recordset

        return recordset

    @rpc.expected_exceptions()
    def find_recordsets(self, context, criterion=None, marker=None, limit=None,
                        sort_key=None, sort_dir=None, force_index=False):
        zone = None
        zone_shared = False

        if criterion and criterion.get('zone_id', None):
            # NOTE: We need to ensure the zone actually exists, otherwise
            # we may return deleted recordsets instead of a zone not found
            zone = self.get_zone(context, criterion['zone_id'],
                                 apply_tenant_criteria=False)
            # Note this call must follow the get_zone call to maintain API
            # response code behavior.
            zone_shared = self._check_zone_share_permission(context, zone)

        # TODO(johnsom) Fix this to be useful
        target = {constants.RBAC_PROJECT_ID: context.project_id,
                  'tenant_id': context.project_id}

        policy.check('find_recordsets', context, target)

        apply_tenant_criteria = True
        # NOTE(imalinovskiy): Show all recordsets for zone owner or if the zone
        #                     is shared with this project.
        if (zone and zone.tenant_id == context.project_id) or zone_shared:
            apply_tenant_criteria = False

        recordsets = self.storage.find_recordsets(
            context, criterion, marker, limit, sort_key, sort_dir, force_index,
            apply_tenant_criteria=apply_tenant_criteria)

        return recordsets

    def find_recordset(self, context, criterion=None):
        # TODO(johnsom) Fix this to be useful
        target = {constants.RBAC_PROJECT_ID: context.project_id,
                  'tenant_id': context.project_id}
        policy.check('find_recordset', context, target)

        recordset = self.storage.find_recordset(context, criterion)

        return recordset

    @rpc.expected_exceptions()
    def create_managed_records(self, context, zone_id, records_values,
                               recordset_values):
        return self._create_or_update_managed_recordset(
            context, zone_id, records_values, recordset_values
        )

    @rpc.expected_exceptions()
    def delete_managed_records(self, context, zone_id, criterion):
        records = self.storage.find_records(context, criterion)
        for record in records:
            self._delete_or_update_managed_recordset(
                context, zone_id, record['recordset_id'], record['id']
            )

    @rpc.expected_exceptions()
    def export_zone(self, context, zone_id):
        zone = self.get_zone(context, zone_id)

        criterion = {'zone_id': zone_id}
        recordsets = self.storage.find_recordsets_export(context, criterion)

        return utils.render_template('export-zone.jinja2',
                                     zone=zone,
                                     recordsets=recordsets)

    @rpc.expected_exceptions()
    @notification.notify_type('dns.recordset.update')
    def update_recordset(self, context, recordset, increment_serial=True):
        zone_id = recordset.obj_get_original_value('zone_id')
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

        zone = self.storage.get_zone(context, zone_id,
                                     apply_tenant_criteria=False)

        self._enforce_catalog_zone_policy(context, zone)

        # Note this call must follow the get_zone call to maintain API response
        # code behavior.
        zone_shared = self._check_zone_share_permission(context, zone)

        # Don't allow updates to zones that are being deleted
        if zone.action == 'DELETE':
            raise exceptions.BadRequest('Can not update a deleting zone')

        # TODO(johnsom) This should account for all-projects context
        # it passes today due to ADMIN
        target = {
            'recordset_id': recordset.obj_get_original_value('id'),
            'recordset_project_id': recordset.obj_get_original_value(
                'tenant_id'),
            'zone_id': recordset.obj_get_original_value('zone_id'),
            'zone_name': zone.name,
            'zone_shared': zone_shared,
            'zone_type': zone.type,
            constants.RBAC_PROJECT_ID: zone.tenant_id,
            'tenant_id': zone.tenant_id
        }

        policy.check('update_recordset', context, target)

        if recordset.managed and not context.edit_managed_records:
            raise exceptions.BadRequest('Managed records may not be updated')

        # Override the context to be all_tenants here as we have already
        # passed the RBAC check for this call and context checks in lower
        # layers will fail for shared zones.
        # TODO(johnsom) Remove once context checking is removed from the lower
        #               code layers.
        context = context.elevated(all_tenants=True)

        recordset, zone = self._update_recordset_in_storage(
            context, zone, recordset, increment_serial=increment_serial)

        return recordset

    @transaction
    def _update_recordset_in_storage(self, context, zone, recordset,
                                     increment_serial=True,
                                     set_delayed_notify=False):

        self._validate_recordset(context, zone, recordset)

        if recordset.records:
            for record in recordset.records:
                if record.action == 'DELETE':
                    continue
                record.action = 'UPDATE'
                record.status = 'PENDING'
                if not increment_serial:
                    record.serial = zone.serial
                else:
                    record.serial = timeutils.utcnow_ts()

            # Ensure the tenant has enough zone record quotas to
            # create new records
            self._enforce_record_quota(context, zone, recordset)

        # Update the recordset
        new_recordset = self.storage.update_recordset(context, recordset)

        if increment_serial:
            # update the zone's status and increment the serial
            zone = self._update_zone_in_storage(
                context, zone,
                increment_serial=increment_serial,
                set_delayed_notify=set_delayed_notify)

        return new_recordset, zone

    @rpc.expected_exceptions()
    @notification.notify_type('dns.recordset.delete')
    def delete_recordset(self, context, zone_id, recordset_id,
                         increment_serial=True):
        # apply_tenant_criteria=False here as we will gate this delete
        # with the RBAC rules below. This allows the zone owner to delete
        # all of the recordsets of the zone.
        recordset = self.storage.find_recordset(
            context,
            {"id": recordset_id, "zone_id": zone_id},
            apply_tenant_criteria=False
        )
        zone = self.storage.get_zone(context, zone_id,
                                     apply_tenant_criteria=False)

        self._enforce_catalog_zone_policy(context, zone)

        # Don't allow updates to zones that are being deleted
        if zone.action == 'DELETE':
            raise exceptions.BadRequest('Can not update a deleting zone')

        # TODO(johnsom) should handle all_projects
        target = {
            'zone_id': zone_id,
            'zone_name': zone.name,
            'zone_type': zone.type,
            'recordset_id': recordset.id,
            'recordset_project_id': recordset.tenant_id,
            constants.RBAC_PROJECT_ID: zone.tenant_id,
            'tenant_id': zone.tenant_id
        }

        policy.check('delete_recordset', context, target)

        if recordset.managed and not context.edit_managed_records:
            raise exceptions.BadRequest('Managed records may not be deleted')

        # Override the context to be all_tenants here as we have already
        # passed the RBAC check for this call.
        # TODO(johnsom) Remove once context checking is removed from the lower
        #               code layers.
        context = context.elevated(all_tenants=True)

        recordset, zone = self._delete_recordset_in_storage(
            context, zone, recordset, increment_serial=increment_serial)

        recordset.zone_name = zone.name
        recordset.obj_reset_changes(['zone_name'])

        return recordset

    @transaction
    def _delete_recordset_in_storage(self, context, zone, recordset,
                                     increment_serial=True):
        if recordset.records:
            for record in recordset.records:
                record.action = 'DELETE'
                record.status = 'PENDING'
                if not increment_serial:
                    record.serial = zone.serial
                else:
                    record.serial = timeutils.utcnow_ts()

        # Update the recordset's action/status and then delete it
        self.storage.update_recordset(context, recordset)

        if increment_serial:
            # update the zone's status and increment the serial
            zone = self._update_zone_in_storage(
                context, zone, increment_serial)

        new_recordset = self.storage.delete_recordset(context, recordset.id)

        return new_recordset, zone

    @rpc.expected_exceptions()
    def count_recordsets(self, context, criterion=None):
        if criterion is None:
            criterion = {}

        target = {
            constants.RBAC_PROJECT_ID: criterion.get('tenant_id', None),
            'tenant_id': criterion.get('tenant_id', None)
        }

        policy.check('count_recordsets', context, target)

        return self.storage.count_recordsets(context, criterion)

    # Record Methods
    def find_records(self, context, criterion=None, marker=None, limit=None,
                     sort_key=None, sort_dir=None):

        target = {constants.RBAC_PROJECT_ID: context.project_id,
                  'tenant_id': context.project_id}
        policy.check('find_records', context, target)

        return self.storage.find_records(context, criterion, marker, limit,
                                         sort_key, sort_dir)

    @rpc.expected_exceptions()
    def count_records(self, context, criterion=None):
        if criterion is None:
            criterion = {}

        target = {
            constants.RBAC_PROJECT_ID: criterion.get('tenant_id', None),
            'tenant_id': criterion.get('tenant_id', None)
        }

        policy.check('count_records', context, target)
        return self.storage.count_records(context, criterion)

    def _determine_floatingips(self, context, fips, project_id=None):
        """
        Given the context or project, and fips it returns the valid
        floating ips either with an associated record or not. Deletes invalid
        records also.

        Returns a list of tuples with FloatingIPs and its Record.
        """
        project_id = project_id or context.project_id

        elevated_context = context.elevated(all_tenants=True,
                                            edit_managed_records=True)
        criterion = {
            'managed': True,
            'managed_resource_type': 'ptr:floatingip',
        }

        records = self.find_records(elevated_context, criterion)
        records = {r['managed_extra']: r for r in records}

        invalid = []
        data = {}
        # First populate the list of FIPS.
        for fip_key, fip_values in fips.items():
            # Check if the FIP has a record
            record = records.get(fip_values['address'])

            # NOTE: Now check if it's owned by the project that actually has
            # the FIP in the external service and if not invalidate it
            # (delete it) thus not returning it with in the tuple with the FIP,
            # but None.

            if record:
                record_project = record['managed_tenant_id']

                if record_project != project_id:
                    LOG.debug(
                        'Invalid FloatingIP %s belongs to %s but record '
                        'project %s', fip_key, project_id, record_project
                    )
                    invalid.append(record)
                    record = None
            data[fip_key] = (fip_values, record)

        return data, invalid

    def _invalidate_floatingips(self, context, records):
        """
        Utility method to delete a list of records.
        """
        if not records:
            return

        elevated_context = context.elevated(all_tenants=True,
                                            edit_managed_records=True)
        for record in records:
            LOG.debug('Deleting record %s for FIP %s',
                      record['id'], record['managed_resource_id'])
            self._delete_or_update_managed_recordset(
                elevated_context, record.zone_id, record.recordset_id,
                record['id']
            )

    def _list_floatingips(self, context, region=None):
        data = self.network_api.list_floatingips(context, region=region)
        return self._list_to_dict(data, keys=['region', 'id'])

    def _list_to_dict(self, data, keys=None):
        if keys is None:
            keys = ['id']
        new = {}
        for i in data:
            key = tuple([i[key] for key in keys])
            new[key] = i
        return new

    def _get_floatingip(self, context, region, floatingip_id, fips):
        if (region, floatingip_id) not in fips:
            raise exceptions.NotFound(
                'FloatingIP {} in {} is not associated for project '
                '"{}"'.format(
                    floatingip_id, region, context.project_id
                )
            )
        return fips[region, floatingip_id]

    # PTR ops
    @rpc.expected_exceptions()
    def list_floatingips(self, context):
        """
        List Floating IPs PTR

        A) We have service_catalog in the context and do a lookup using the
               token pr Neutron in the SC
        B) We lookup FIPs using the configured values for this deployment.
        """
        elevated_context = context.elevated(all_tenants=True,
                                            edit_managed_records=True)

        project_floatingips = self._list_floatingips(context)

        valid, invalid = self._determine_floatingips(
            elevated_context, project_floatingips
        )

        self._invalidate_floatingips(context, invalid)

        return self._create_floating_ip_list(context, valid)

    @rpc.expected_exceptions()
    def get_floatingip(self, context, region, floatingip_id):
        """
        Get Floating IP PTR
        """
        elevated_context = context.elevated(all_tenants=True)

        tenant_fips = self._list_floatingips(context, region=region)

        fip = self._get_floatingip(context, region, floatingip_id, tenant_fips)

        result = self._list_to_dict([fip], keys=['region', 'id'])

        valid, invalid = self._determine_floatingips(
            elevated_context, result
        )

        self._invalidate_floatingips(context, invalid)

        return self._create_floating_ip_list(context, valid)[0]

    def _set_floatingip_reverse(self, context, region, floatingip_id, values):
        """
        Set the FloatingIP's PTR record based on values.
        """

        elevated_context = context.elevated(all_tenants=True,
                                            edit_managed_records=True)

        project_fips = self._list_floatingips(context, region=region)

        fip = self._get_floatingip(
            context, region, floatingip_id, project_fips
        )

        zone_name = self.network_api.address_zone(fip['address'])

        try:
            zone = self.storage.find_zone(
                elevated_context, {'name': zone_name}
            )
        except exceptions.ZoneNotFound:
            LOG.info(
                'Creating zone for %(fip_id)s:%(region)s - %(fip_addr)s '
                'zone %(zonename)s',
                {
                    'fip_id': floatingip_id,
                    'region': region,
                    'fip_addr': fip['address'],
                    'zonename': zone_name
                })

            zone = self._create_ptr_zone(elevated_context, zone_name)

        record_name = self.network_api.address_name(fip['address'])
        recordset_values = {
            'name': record_name,
            'zone_id': zone['id'],
            'type': 'PTR',
            'ttl': values.get('ttl')
        }
        record_values = {
            'data': values['ptrdname'],
            'description': values['description'],
            'managed': True,
            'managed_extra': fip['address'],
            'managed_resource_id': floatingip_id,
            'managed_resource_region': region,
            'managed_resource_type': 'ptr:floatingip',
            'managed_tenant_id': context.project_id
        }
        recordset = self._create_or_update_managed_recordset(
            elevated_context, zone['id'], [record_values], recordset_values
        )
        return self._create_floating_ip(
            context, fip, recordset.records[0], zone=zone, recordset=recordset
        )

    @rpc.expected_exceptions()
    def _create_ptr_zone(self, elevated_context, zone_name):
        zone_values = {
            'type': 'PRIMARY',
            'name': zone_name,
            'email': CONF['service:central'].managed_resource_email,
            'tenant_id': CONF['service:central'].managed_resource_tenant_id
        }
        try:
            zone = self.create_zone(
                elevated_context, objects.Zone(**zone_values)
            )
        except exceptions.DuplicateZone:
            # NOTE(eandersson): This code is prone to race conditions, and
            #                   it does not hurt to try to handle this if it
            #                   fails.
            zone = self.storage.find_zone(
                elevated_context, {'name': zone_name}
            )

        return zone

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
            'managed_tenant_id': context.project_id
        }

        try:
            record = self.storage.find_record(
                elevated_context, criterion=criterion
            )
        except exceptions.RecordNotFound:
            msg = f'No such FloatingIP {region}:{floatingip_id}'
            raise exceptions.NotFound(msg)

        self._delete_or_update_managed_recordset(
            elevated_context, record.zone_id, record.recordset_id,
            record['id']
        )

    @rpc.expected_exceptions()
    def _create_floating_ip(self, context, fip, record,
                            zone=None, recordset=None):
        """
        Creates a FloatingIP based on floating ip and record data.
        """
        elevated_context = context.elevated(all_tenants=True)
        fip_ptr = objects.FloatingIP().from_dict({
            'address': fip['address'],
            'id': fip['id'],
            'region': fip['region'],
            'ptrdname': None,
            'ttl': None,
            'description': None,
            'action': constants.NONE,
            'status': constants.INACTIVE
        })

        # TTL population requires a present record in order to find the
        # Recordset or Zone.
        if not record:
            LOG.debug('No record information found for %s', fip['id'])
            return fip_ptr

        if not recordset:
            try:
                recordset = self.storage.find_recordset(
                    elevated_context, criterion={'id': record.recordset_id}
                )
            except exceptions.RecordSetNotFound:
                LOG.debug('No recordset found for %s', fip['id'])
                return fip_ptr

        if recordset.ttl is not None:
            fip_ptr['ttl'] = recordset.ttl
        else:
            if not zone:
                try:
                    zone = self.get_zone(
                        elevated_context, record.zone_id
                    )
                except exceptions.ZoneNotFound:
                    LOG.debug('No zone found for %s', fip['id'])
                    return fip_ptr

            fip_ptr['ttl'] = zone.ttl

        if recordset.action in constants.FLOATING_IP_ACTIONS:
            fip_ptr['action'] = recordset.action
        else:
            LOG.debug(
                'Action %s not valid for floating ip action', recordset.action
            )

        if recordset.status in constants.FLOATING_IP_STATUSES:
            fip_ptr['status'] = recordset.status
        else:
            LOG.debug(
                'Status %s not valid for floating ip status', recordset.status
            )

        fip_ptr['ptrdname'] = record.data
        fip_ptr['description'] = record.description

        return fip_ptr

    def _create_floating_ip_list(self, context, data):
        """
        Creates a FloatingIPList based on floating ips and records data.
        """
        fips = objects.FloatingIPList()
        for key, value in data.items():
            fip, record = value
            fip_ptr = self._create_floating_ip(context, fip, record)
            fips.append(fip_ptr)
        return fips

    @transaction
    def _delete_or_update_managed_recordset(self, context, zone_id,
                                            recordset_id,
                                            record_to_delete_id):
        criterion = {'id': recordset_id}
        if zone_id is not None:
            criterion['zone_id'] = zone_id

        try:
            recordset = self.storage.find_recordset(context, criterion)
            record_ids = [record['id'] for record in recordset.records]

            if record_to_delete_id not in record_ids:
                LOG.debug(
                    'Managed record %s not found in recordset %s',
                    record_to_delete_id, recordset_id
                )
                return

            for record in list(recordset.records):
                if record['id'] != record_to_delete_id:
                    continue
                recordset.records.remove(record)
                break

            if not recordset.records:
                self.delete_recordset(
                    context, zone_id or recordset.zone_id, recordset_id
                )
                return

            recordset.validate()
            self.update_recordset(context, recordset)
        except exceptions.RecordSetNotFound:
            pass

    @transaction
    def _create_or_update_managed_recordset(self, context, zone_id,
                                            records_values, recordset_values):
        name = recordset_values['name'].encode('idna').decode('utf-8')
        records = []
        for record_values in records_values:
            records.append(objects.Record(**record_values))

        try:

            recordset = self.storage.find_recordset(context, {
                'zone_id': zone_id,
                'name': name,
                'type': recordset_values['type'],
            })
            recordset.ttl = recordset_values.get('ttl')
            recordset.records = objects.RecordList(objects=records)
            recordset.validate()
            recordset = self.update_recordset(
                context, recordset
            )
        except exceptions.RecordSetNotFound:
            values = {
                'name': name,
                'type': recordset_values['type'],
                'ttl': recordset_values.get('ttl')
            }
            recordset = objects.RecordSet(**values)
            recordset.records = objects.RecordList(objects=records)
            recordset.validate()
            recordset = self.create_recordset(
                context, zone_id, recordset
            )
        return recordset

    @rpc.expected_exceptions()
    def update_floatingip(self, context, region, floatingip_id, values):
        """
        We strictly see if values['ptrdname'] is str or None and set / unset
        the requested FloatingIP's PTR record based on that.
        """
        if ('ptrdname' in values.obj_what_changed() and
                values['ptrdname'] is None):
            self._unset_floatingip_reverse(
                context, region, floatingip_id
            )
        elif isinstance(values['ptrdname'], str):
            return self._set_floatingip_reverse(
                context, region, floatingip_id, values
            )

    # Blacklisted zones
    @rpc.expected_exceptions()
    @notification.notify_type('dns.blacklist.create')
    @transaction
    def create_blacklist(self, context, blacklist):
        policy.check('create_blacklist', context)

        created_blacklist = self.storage.create_blacklist(context, blacklist)

        return created_blacklist

    @rpc.expected_exceptions()
    def get_blacklist(self, context, blacklist_id):
        policy.check('get_blacklist', context)

        blacklist = self.storage.get_blacklist(context, blacklist_id)

        return blacklist

    @rpc.expected_exceptions()
    def find_blacklists(self, context, criterion=None, marker=None,
                        limit=None, sort_key=None, sort_dir=None):
        policy.check('find_blacklists', context)

        blacklists = self.storage.find_blacklists(context, criterion,
                                                  marker, limit,
                                                  sort_key, sort_dir)

        return blacklists

    @rpc.expected_exceptions()
    @notification.notify_type('dns.blacklist.update')
    @transaction
    def update_blacklist(self, context, blacklist):
        target = {
            'blacklist_id': blacklist.id,
        }
        policy.check('update_blacklist', context, target)

        blacklist = self.storage.update_blacklist(context, blacklist)

        return blacklist

    @rpc.expected_exceptions()
    @notification.notify_type('dns.blacklist.delete')
    @transaction
    def delete_blacklist(self, context, blacklist_id):
        policy.check('delete_blacklist', context)

        blacklist = self.storage.delete_blacklist(context, blacklist_id)

        return blacklist

    # Server Pools
    @rpc.expected_exceptions()
    @notification.notify_type('dns.pool.create')
    @transaction
    def create_pool(self, context, pool):
        # Verify that there is a tenant_id
        if pool.tenant_id is None:
            pool.tenant_id = context.project_id

        policy.check('create_pool', context)

        created_pool = self.storage.create_pool(context, pool)

        return created_pool

    @rpc.expected_exceptions()
    def find_pools(self, context, criterion=None, marker=None, limit=None,
                   sort_key=None, sort_dir=None):

        policy.check('find_pools', context)

        return self.storage.find_pools(context, criterion, marker, limit,
                                       sort_key, sort_dir)

    @rpc.expected_exceptions()
    def find_pool(self, context, criterion=None):

        policy.check('find_pool', context)

        return self.storage.find_pool(context, criterion)

    @rpc.expected_exceptions()
    def get_pool(self, context, pool_id):

        policy.check('get_pool', context)

        return self.storage.get_pool(context, pool_id)

    @rpc.expected_exceptions()
    @notification.notify_type('dns.pool.update')
    @transaction
    def update_pool(self, context, pool):
        policy.check('update_pool', context)

        # If there is a nameserver, then additional steps need to be done
        # Since these are treated as mutable objects, we're only going to
        # be comparing the nameserver.value which is the FQDN
        elevated_context = context.elevated(all_tenants=True)

        # TODO(kiall): ListObjects should be able to give you their
        #              original set of values.
        original_pool_ns_records = self._get_pool_ns_records(
            context, pool.id
        )

        updated_pool = self.storage.update_pool(context, pool)

        if not pool.obj_attr_is_set('ns_records'):
            return updated_pool

        # Find the current NS hostnames
        existing_ns = {n.hostname for n in original_pool_ns_records}

        # Find the desired NS hostnames
        request_ns = {n.hostname for n in pool.ns_records}

        # Get the NS's to be created and deleted, ignoring the ones that
        # are in both sets, as those haven't changed.
        # TODO(kiall): Factor in priority
        create_ns = request_ns.difference(existing_ns)
        delete_ns = existing_ns.difference(request_ns)

        # After the update, handle new ns_records
        for ns_record in create_ns:
            # Create new NS recordsets for every zone
            zones = self.find_zones(
                context=elevated_context,
                criterion={'pool_id': pool.id, 'action': '!DELETE'})
            for zone in zones:
                self._add_ns(elevated_context, zone, ns_record)

        # Then handle the ns_records to delete
        for ns_record in delete_ns:
            # Cannot delete the last nameserver, so verify that first.
            if not pool.ns_records:
                raise exceptions.LastServerDeleteNotAllowed(
                    "Not allowed to delete last of servers"
                )

            # Delete the NS record for every zone
            zones = self.find_zones(
                context=elevated_context,
                criterion={'pool_id': pool.id}
            )
            for zone in zones:
                self._delete_ns(elevated_context, zone, ns_record)

        return updated_pool

    @rpc.expected_exceptions()
    @notification.notify_type('dns.pool.delete')
    @transaction
    def delete_pool(self, context, pool_id):

        policy.check('delete_pool', context)

        # Make sure that there are no existing zones in the pool
        elevated_context = context.elevated(all_tenants=True)
        zones = self.find_zones(
            context=elevated_context,
            criterion={'pool_id': pool_id, 'action': '!DELETE'})

        # If there are existing zones, do not delete the pool
        LOG.debug("Zones is None? %r", zones)
        if len(zones) == 0:
            pool = self.storage.delete_pool(context, pool_id)
        else:
            raise exceptions.InvalidOperation('pool must not contain zones')

        return pool

    # Pool Manager Integration
    @rpc.expected_exceptions()
    @notification.notify_type('dns.domain.update')
    @notification.notify_type('dns.zone.update')
    @transaction
    @lock.synchronized_zone()
    def update_status(self, context, zone_id, status, serial, action=None):
        """
        :param context: Security context information.
        :param zone_id: The ID of the designate zone.
        :param status: The status, 'SUCCESS' or 'ERROR'.
        :param serial: The consensus serial number for the zone.
        :param action: The action, 'CREATE', 'UPDATE', 'DELETE' or 'NONE'.
        :return: updated zone
        """
        zone = self.storage.get_zone(context, zone_id)
        if action is None or zone.action == action:
            if zone.action == 'DELETE' and zone.status != 'ERROR':
                status = 'NO_ZONE'
            zone = self._update_zone_or_record_status(
                zone, status, serial
            )
        else:
            LOG.debug(
                'Updated action different from current action. '
                '%(previous_action)s != %(current_action)s '
                '(%(status)s). Keeping current action %(current_action)s '
                'for %(zone_id)s',
                {
                    'previous_action': action,
                    'current_action': zone.action,
                    'status': zone.status,
                    'zone_id': zone.id,
                }
            )

        if zone.status == 'DELETED':
            LOG.debug(
                'Updated Status: Deleting %(zone_id)s',
                {
                    'zone_id': zone.id,
                }
            )
            self.storage.delete_zone(context, zone.id)
        else:
            LOG.debug(
                'Setting Zone: %(zone_id)s action: %(action)s '
                'status: %(status)s serial: %(serial)s',
                {
                    'zone_id': zone.id,
                    'action': zone.action,
                    'status': zone.status,
                    'serial': zone.serial,
                }
            )
            self.storage.update_zone(context, zone)

        self._update_record_status(context, zone_id, status, serial)

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
            record = self._update_zone_or_record_status(record, status, serial)

            if record.obj_what_changed():
                LOG.debug('Setting record %s, serial %s: action %s, '
                          'status %s', record.id, record.serial,
                          record.action, record.status)
                self.storage.update_record(context, record)

        return records

    @staticmethod
    def _update_zone_or_record_status(zone_or_record, status, serial):
        if status == 'SUCCESS':
            if (zone_or_record.status in ['PENDING', 'ERROR'] and
                    serial >= zone_or_record.serial):
                if zone_or_record.action in ['CREATE', 'UPDATE']:
                    zone_or_record.action = 'NONE'
                    zone_or_record.status = 'ACTIVE'
                elif zone_or_record.action == 'DELETE':
                    zone_or_record.action = 'NONE'
                    zone_or_record.status = 'DELETED'

        elif status == 'ERROR':
            if (zone_or_record.status == 'PENDING' and
                    (serial >= zone_or_record.serial or serial == 0)):
                zone_or_record.status = 'ERROR'

        elif status == 'NO_ZONE':
            if zone_or_record.action in ['CREATE', 'UPDATE']:
                zone_or_record.action = 'CREATE'
                zone_or_record.status = 'ERROR'
            elif zone_or_record.action == 'DELETE':
                zone_or_record.action = 'NONE'
                zone_or_record.status = 'DELETED'

        return zone_or_record

    # Zone Transfers
    def _transfer_key_generator(self, size=8):
        chars = string.ascii_uppercase + string.digits
        sysrand = SystemRandom()
        return ''.join(sysrand.choice(chars) for _ in range(size))

    @rpc.expected_exceptions()
    @notification.notify_type('dns.zone_transfer_request.create')
    @transaction
    def create_zone_transfer_request(self, context, zone_transfer_request):

        # get zone
        zone = self.get_zone(context, zone_transfer_request.zone_id)

        self._enforce_catalog_zone_policy(context, zone)

        # Don't allow transfers for zones that are being deleted
        if zone.action == 'DELETE':
            raise exceptions.BadRequest('Can not transfer a deleting zone')

        target = {constants.RBAC_PROJECT_ID: zone.tenant_id,
                  'tenant_id': zone.tenant_id}

        policy.check('create_zone_transfer_request', context, target)

        zone_transfer_request.key = self._transfer_key_generator()

        if zone_transfer_request.tenant_id is None:
            zone_transfer_request.tenant_id = context.project_id

        self._is_valid_project_id(zone_transfer_request.tenant_id)

        created_zone_transfer_request = (
            self.storage.create_zone_transfer_request(
                context, zone_transfer_request))

        return created_zone_transfer_request

    @rpc.expected_exceptions()
    def get_zone_transfer_request(self, context, zone_transfer_request_id):

        elevated_context = context.elevated(all_tenants=True)

        # Get zone transfer request
        zone_transfer_request = self.storage.get_zone_transfer_request(
            elevated_context, zone_transfer_request_id)

        LOG.info('Target Tenant ID found - using scoped policy')
        target = {
            constants.RBAC_TARGET_PROJECT_ID: (zone_transfer_request.
                                               target_tenant_id),
            constants.RBAC_PROJECT_ID: zone_transfer_request.tenant_id,
            'target_tenant_id': zone_transfer_request.target_tenant_id,
            'tenant_id': zone_transfer_request.tenant_id,
        }

        policy.check('get_zone_transfer_request', context, target)

        return zone_transfer_request

    @rpc.expected_exceptions()
    def find_zone_transfer_requests(self, context, criterion=None, marker=None,
                                    limit=None, sort_key=None, sort_dir=None):

        policy.check('find_zone_transfer_requests', context)

        requests = self.storage.find_zone_transfer_requests(
            context, criterion,
            marker, limit,
            sort_key, sort_dir)

        return requests

    @rpc.expected_exceptions()
    @notification.notify_type('dns.zone_transfer_request.update')
    @transaction
    def update_zone_transfer_request(self, context, zone_transfer_request):

        if 'zone_id' in zone_transfer_request.obj_what_changed():
            raise exceptions.InvalidOperation('Zone cannot be changed')

        target = {
            constants.RBAC_PROJECT_ID: zone_transfer_request.tenant_id,
            'tenant_id': zone_transfer_request.tenant_id,
        }
        policy.check('update_zone_transfer_request', context, target)
        request = self.storage.update_zone_transfer_request(
            context, zone_transfer_request)

        return request

    @rpc.expected_exceptions()
    @notification.notify_type('dns.zone_transfer_request.delete')
    @transaction
    def delete_zone_transfer_request(self, context, zone_transfer_request_id):
        # Get zone transfer request
        zone_transfer_request = self.storage.get_zone_transfer_request(
            context, zone_transfer_request_id)

        target = {
            constants.RBAC_PROJECT_ID: zone_transfer_request.tenant_id,
            'tenant_id': zone_transfer_request.tenant_id}

        policy.check('delete_zone_transfer_request', context, target)
        return self.storage.delete_zone_transfer_request(
            context,
            zone_transfer_request_id)

    @rpc.expected_exceptions()
    @notification.notify_type('dns.zone_transfer_accept.create')
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
            constants.RBAC_TARGET_PROJECT_ID: (
                zone_transfer_request.target_tenant_id),
            'target_tenant_id': zone_transfer_request.target_tenant_id
        }

        policy.check('create_zone_transfer_accept', context, target)

        if zone_transfer_accept.tenant_id is None:
            zone_transfer_accept.tenant_id = context.project_id

        self._is_valid_project_id(zone_transfer_accept.tenant_id)

        created_zone_transfer_accept = (
            self.storage.create_zone_transfer_accept(
                context, zone_transfer_accept))

        try:
            zone = self.storage.get_zone(
                elevated_context,
                zone_transfer_request.zone_id)

            # Don't allow transfers for zones that are being deleted
            if zone.action == 'DELETE':
                raise exceptions.BadRequest('Can not transfer a deleting zone')

            # Ensure the accepting tenant has enough quota to continue
            self._enforce_zone_quota(context,
                                     zone_transfer_accept.tenant_id)

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

    @rpc.expected_exceptions()
    def get_zone_transfer_accept(self, context, zone_transfer_accept_id):
        # Get zone transfer accept

        zone_transfer_accept = self.storage.get_zone_transfer_accept(
            context, zone_transfer_accept_id)

        target = {
            constants.RBAC_PROJECT_ID: zone_transfer_accept.tenant_id,
            'tenant_id': zone_transfer_accept.tenant_id
        }

        policy.check('get_zone_transfer_accept', context, target)

        return zone_transfer_accept

    @rpc.expected_exceptions()
    def find_zone_transfer_accepts(self, context, criterion=None, marker=None,
                                   limit=None, sort_key=None, sort_dir=None):
        policy.check('find_zone_transfer_accepts', context)
        return self.storage.find_zone_transfer_accepts(context, criterion,
                                                       marker, limit,
                                                       sort_key, sort_dir)

    # Zone Import Methods
    @rpc.expected_exceptions()
    @notification.notify_type('dns.zone_import.create')
    def create_zone_import(self, context, request_body):
        target = {constants.RBAC_PROJECT_ID: context.project_id,
                  'tenant_id': context.project_id}

        policy.check('create_zone_import', context, target)

        self._is_valid_project_id(context.project_id)

        values = {
            'status': 'PENDING',
            'message': None,
            'zone_id': None,
            'tenant_id': context.project_id,
            'task_type': 'IMPORT'
        }
        zone_import = objects.ZoneImport(**values)

        created_zone_import = self.storage.create_zone_import(context,
                                                              zone_import)

        self.tg.add_thread(self._import_zone, context, created_zone_import,
                           request_body)

        return created_zone_import

    @rpc.expected_exceptions()
    def _import_zone(self, context, zone_import, request_body):
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
                if rrset.type == 'SOA':
                    zone.recordsets.remove(rrset)
                # subdomain NS records should be kept
                elif rrset.type == 'NS' and rrset.name == zone.name:
                    zone.recordsets.remove(rrset)
        except dnszone.UnknownOrigin:
            zone_import.message = (
                'The $ORIGIN statement is required and must be the first '
                'statement in the zonefile.'
            )
            zone_import.status = 'ERROR'
        except dnsexception.SyntaxError:
            zone_import.message = 'Malformed zonefile.'
            zone_import.status = 'ERROR'
        except exceptions.BadRequest:
            zone_import.message = 'An SOA record is required.'
            zone_import.status = 'ERROR'
        except Exception as e:
            LOG.exception('An undefined error occurred during zone import')
            zone_import.message = (
                'An undefined error occurred. %s' % str(e)[:130]
            )
            zone_import.status = 'ERROR'

        # If the zone import was valid, create the zone
        if zone_import.status != 'ERROR':
            try:
                zone = self.create_zone(context, zone)
                zone_import.status = 'COMPLETE'
                zone_import.zone_id = zone.id
                zone_import.message = (
                    f'{zone.name} imported'
                )
            except exceptions.DuplicateZone:
                zone_import.status = 'ERROR'
                zone_import.message = 'Duplicate zone.'
            except exceptions.InvalidTTL as e:
                zone_import.status = 'ERROR'
                zone_import.message = str(e)
            except exceptions.OverQuota:
                zone_import.status = 'ERROR'
                zone_import.message = 'Quota exceeded during zone import.'
            except Exception as e:
                LOG.exception(
                    'An undefined error occurred during zone import creation'
                )
                zone_import.message = (
                    'An undefined error occurred. %s' % str(e)[:130]
                )
                zone_import.status = 'ERROR'

        self.update_zone_import(context, zone_import)

    @notification.notify_type('dns.zone_import.update')
    def update_zone_import(self, context, zone_import):
        target = {constants.RBAC_PROJECT_ID: zone_import.tenant_id,
                  'tenant_id': zone_import.tenant_id}
        policy.check('update_zone_import', context, target)

        return self.storage.update_zone_import(context, zone_import)

    @rpc.expected_exceptions()
    def find_zone_imports(self, context, criterion=None, marker=None,
                          limit=None, sort_key=None, sort_dir=None):

        target = {constants.RBAC_PROJECT_ID: context.project_id,
                  'tenant_id': context.project_id}

        policy.check('find_zone_imports', context, target)

        if not criterion:
            criterion = {
                'task_type': 'IMPORT'
            }
        else:
            criterion['task_type'] = 'IMPORT'

        return self.storage.find_zone_imports(context, criterion, marker,
                                              limit, sort_key, sort_dir)

    @rpc.expected_exceptions()
    def get_zone_import(self, context, zone_import_id):

        target = {constants.RBAC_PROJECT_ID: context.project_id,
                  'tenant_id': context.project_id}

        policy.check('get_zone_import', context, target)
        return self.storage.get_zone_import(context, zone_import_id)

    @rpc.expected_exceptions()
    @notification.notify_type('dns.zone_import.delete')
    @transaction
    def delete_zone_import(self, context, zone_import_id):

        target = {
                'zone_import_id': zone_import_id,
                constants.RBAC_PROJECT_ID: context.project_id,
                'tenant_id': context.project_id
        }

        policy.check('delete_zone_import', context, target)

        zone_import = self.storage.delete_zone_import(context, zone_import_id)

        return zone_import

    # Zone Export Methods
    @rpc.expected_exceptions()
    @notification.notify_type('dns.zone_export.create')
    def create_zone_export(self, context, zone_id):
        # Try getting the zone to ensure it exists
        zone = self.storage.get_zone(context, zone_id)

        target = {constants.RBAC_PROJECT_ID: zone.tenant_id,
                  'tenant_id': zone.tenant_id}

        policy.check('create_zone_export', context, target)

        self._is_valid_project_id(context.project_id)

        values = {
            'status': 'PENDING',
            'message': None,
            'zone_id': zone_id,
            'tenant_id': context.project_id,
            'task_type': 'EXPORT'
        }
        zone_export = objects.ZoneExport(**values)

        created_zone_export = self.storage.create_zone_export(context,
                                                              zone_export)

        export = copy.deepcopy(created_zone_export)
        self.worker_api.start_zone_export(context, zone, export)

        return created_zone_export

    @rpc.expected_exceptions()
    def find_zone_exports(self, context, criterion=None, marker=None,
                          limit=None, sort_key=None, sort_dir=None):

        target = {constants.RBAC_PROJECT_ID: context.project_id,
                  'tenant_id': context.project_id}
        policy.check('find_zone_exports', context, target)

        if not criterion:
            criterion = {
                'task_type': 'EXPORT'
            }
        else:
            criterion['task_type'] = 'EXPORT'

        return self.storage.find_zone_exports(context, criterion, marker,
                                              limit, sort_key, sort_dir)

    @rpc.expected_exceptions()
    def get_zone_export(self, context, zone_export_id):

        target = {constants.RBAC_PROJECT_ID: context.project_id,
                  'tenant_id': context.project_id}

        policy.check('get_zone_export', context, target)

        return self.storage.get_zone_export(context, zone_export_id)

    @rpc.expected_exceptions()
    @notification.notify_type('dns.zone_export.update')
    def update_zone_export(self, context, zone_export):

        target = {constants.RBAC_PROJECT_ID: zone_export.tenant_id,
                  'tenant_id': zone_export.tenant_id}

        policy.check('update_zone_export', context, target)

        return self.storage.update_zone_export(context, zone_export)

    @rpc.expected_exceptions()
    @notification.notify_type('dns.zone_export.delete')
    @transaction
    def delete_zone_export(self, context, zone_export_id):

        target = {
            'zone_export_id': zone_export_id,
            constants.RBAC_PROJECT_ID: context.project_id,
            'tenant_id': context.project_id
        }

        policy.check('delete_zone_export', context, target)

        zone_export = self.storage.delete_zone_export(context, zone_export_id)

        return zone_export

    @rpc.expected_exceptions()
    def find_service_statuses(self, context, criterion=None, marker=None,
                              limit=None, sort_key=None, sort_dir=None):
        """List service statuses.
        """
        policy.check('find_service_statuses', context)

        return self.storage.find_service_statuses(
            context, criterion, marker, limit, sort_key, sort_dir)

    @rpc.expected_exceptions()
    def find_service_status(self, context, criterion=None):
        policy.check('find_service_status', context)

        return self.storage.find_service_status(context, criterion)

    @rpc.expected_exceptions()
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
            LOG.info(
                "Creating new service status entry for %(service_name)s "
                "at %(hostname)s",
                {
                    'service_name': service_status.service_name,
                    'hostname': service_status.hostname
                }
            )
            return self.storage.create_service_status(
                context, service_status)

    def _ensure_catalog_zone_serial_increment(self, context, zone):
        if zone.type == constants.ZONE_CATALOG:
            return

        pool = self.storage.find_pool(context, criterion={'id': zone.pool_id})

        try:
            catalog_zone = self.storage.get_catalog_zone(context, pool)

            # Schedule batched serial increment
            self._update_zone_in_storage(context, catalog_zone)
        except exceptions.ZoneNotFound:
            pass

    def _enforce_catalog_zone_policy(self, context, zone):
        # Forbid for HTTP API, but allow for designate-manage
        if (
                zone.type == constants.ZONE_CATALOG and
                not (
                    context.is_admin and 'admin' in context.roles and
                    context.request_id == 'designate-manage'
                )
        ):
            raise exceptions.Forbidden(
                'This operation is not allowed for catalog zones.')
