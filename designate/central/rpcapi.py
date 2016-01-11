# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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
from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging

from designate.i18n import _LI
from designate import rpc


LOG = logging.getLogger(__name__)

CENTRAL_API = None


class CentralAPI(object):
    """
    Client side of the central RPC API.

    API version history:

        1.0 - Initial version
        1.1 - Add new finder methods
        1.2 - Add get_tenant and get_tenants
        1.3 - Add get_absolute_limits
        2.0 - Renamed most get_resources to find_resources
        2.1 - Add quota methods
        3.0 - RecordSet Changes
        3.1 - Add floating ip ptr methods
        3.2 - TLD Api changes
        3.3 - Add methods for blacklisted domains
        4.0 - Create methods now accept designate objects
        4.1 - Add methods for server pools
        4.2 - Add methods for pool manager integration
        4.3 - Added Zone Transfer Methods
        5.0 - Remove dead server code
        5.1 - Add xfr_zone
        5.2 - Add Zone Import methods
        5.3 - Add Zone Export method
        5.4 - Add asynchronous Zone Export methods
        5.5 - Add deleted zone purging task
        5.6 - Changed 'purge_zones' function args
        6.0 - Renamed domains to zones
    """
    RPC_API_VERSION = '6.0'

    def __init__(self, topic=None):
        topic = topic if topic else cfg.CONF.central_topic

        target = messaging.Target(topic=topic, version=self.RPC_API_VERSION)
        self.client = rpc.get_client(target, version_cap='6.0')

    @classmethod
    def get_instance(cls):
        """
        The rpc.get_client() which is called upon the API object initialization
        will cause a assertion error if the designate.rpc.TRANSPORT isn't setup
        by rpc.init() before.

        This fixes that by creating the rpcapi when demanded.
        """
        global CENTRAL_API
        if not CENTRAL_API:
            CENTRAL_API = cls()
        return CENTRAL_API

    # Misc Methods
    def get_absolute_limits(self, context):
        LOG.info(_LI("get_absolute_limits: "
                     "Calling central's get_absolute_limits."))

        return self.client.call(context, 'get_absolute_limits')

    # Quota Methods
    def get_quotas(self, context, tenant_id):
        LOG.info(_LI("get_quotas: Calling central's get_quotas."))

        return self.client.call(context, 'get_quotas', tenant_id=tenant_id)

    def get_quota(self, context, tenant_id, resource):
        LOG.info(_LI("get_quota: Calling central's get_quota."))

        return self.client.call(context, 'get_quota', tenant_id=tenant_id,
                                resource=resource)

    def set_quota(self, context, tenant_id, resource, hard_limit):
        LOG.info(_LI("set_quota: Calling central's set_quota."))

        return self.client.call(context, 'set_quota', tenant_id=tenant_id,
                                resource=resource, hard_limit=hard_limit)

    def reset_quotas(self, context, tenant_id):
        LOG.info(_LI("reset_quotas: Calling central's reset_quotas."))

        return self.client.call(context, 'reset_quotas', tenant_id=tenant_id)

    # TSIG Key Methods
    def create_tsigkey(self, context, tsigkey):
        LOG.info(_LI("create_tsigkey: Calling central's create_tsigkey."))
        return self.client.call(context, 'create_tsigkey', tsigkey=tsigkey)

    def find_tsigkeys(self, context, criterion=None, marker=None, limit=None,
                      sort_key=None, sort_dir=None):
        LOG.info(_LI("find_tsigkeys: Calling central's find_tsigkeys."))
        return self.client.call(context, 'find_tsigkeys', criterion=criterion,
                                marker=marker, limit=limit, sort_key=sort_key,
                                sort_dir=sort_dir)

    def get_tsigkey(self, context, tsigkey_id):
        LOG.info(_LI("get_tsigkey: Calling central's get_tsigkey."))
        return self.client.call(context, 'get_tsigkey', tsigkey_id=tsigkey_id)

    def update_tsigkey(self, context, tsigkey):
        LOG.info(_LI("update_tsigkey: Calling central's update_tsigkey."))
        return self.client.call(context, 'update_tsigkey', tsigkey=tsigkey)

    def delete_tsigkey(self, context, tsigkey_id):
        LOG.info(_LI("delete_tsigkey: Calling central's delete_tsigkey."))
        return self.client.call(context, 'delete_tsigkey',
                                tsigkey_id=tsigkey_id)

    # Tenant Methods
    def find_tenants(self, context):
        LOG.info(_LI("find_tenants: Calling central's find_tenants."))
        return self.client.call(context, 'find_tenants')

    def get_tenant(self, context, tenant_id):
        LOG.info(_LI("get_tenant: Calling central's get_tenant."))
        return self.client.call(context, 'get_tenant', tenant_id=tenant_id)

    def count_tenants(self, context):
        LOG.info(_LI("count_tenants: Calling central's count_tenants."))
        return self.client.call(context, 'count_tenants')

    # Zone Methods
    def create_zone(self, context, zone):
        LOG.info(_LI("create_zone: Calling central's create_zone."))
        return self.client.call(context, 'create_zone', zone=zone)

    def get_zone(self, context, zone_id):
        LOG.info(_LI("get_zone: Calling central's get_zone."))
        return self.client.call(context, 'get_zone', zone_id=zone_id)

    def get_zone_ns_records(self, context, zone_id):
        LOG.info(_LI("get_zone_ns_records: "
                     "Calling central's get_zone_ns_records."))
        return self.client.call(context, 'get_zone_ns_records',
                                zone_id=zone_id)

    def find_zones(self, context, criterion=None, marker=None, limit=None,
                   sort_key=None, sort_dir=None):
        LOG.info(_LI("find_zones: Calling central's find_zones."))
        return self.client.call(context, 'find_zones', criterion=criterion,
                                marker=marker, limit=limit, sort_key=sort_key,
                                sort_dir=sort_dir)

    def find_zone(self, context, criterion=None):
        LOG.info(_LI("find_zone: Calling central's find_zone."))
        return self.client.call(context, 'find_zone', criterion=criterion)

    def update_zone(self, context, zone, increment_serial=True):
        LOG.info(_LI("update_zone: Calling central's update_zone."))
        return self.client.call(context, 'update_zone', zone=zone,
                                increment_serial=increment_serial)

    def delete_zone(self, context, zone_id):
        LOG.info(_LI("delete_zone: Calling central's delete_zone."))
        return self.client.call(context, 'delete_zone', zone_id=zone_id)

    def purge_zones(self, context, criterion, limit=None):
        LOG.info(_LI(
            "purge_zones: Calling central's purge_zones."
        ))
        return self.client.call(context, 'purge_zones',
                          criterion=criterion, limit=limit)

    def count_zones(self, context, criterion=None):
        LOG.info(_LI("count_zones: Calling central's count_zones."))
        return self.client.call(context, 'count_zones', criterion=criterion)

    def touch_zone(self, context, zone_id):
        LOG.info(_LI("touch_zone: Calling central's touch_zone."))
        return self.client.call(context, 'touch_zone', zone_id=zone_id)

    # TLD Methods
    def create_tld(self, context, tld):
        LOG.info(_LI("create_tld: Calling central's create_tld."))
        return self.client.call(context, 'create_tld', tld=tld)

    def find_tlds(self, context, criterion=None, marker=None, limit=None,
                  sort_key=None, sort_dir=None):
        LOG.info(_LI("find_tlds: Calling central's find_tlds."))
        return self.client.call(context, 'find_tlds', criterion=criterion,
                                marker=marker, limit=limit, sort_key=sort_key,
                                sort_dir=sort_dir)

    def get_tld(self, context, tld_id):
        LOG.info(_LI("get_tld: Calling central's get_tld."))
        return self.client.call(context, 'get_tld', tld_id=tld_id)

    def update_tld(self, context, tld):
        LOG.info(_LI("update_tld: Calling central's update_tld."))
        return self.client.call(context, 'update_tld', tld=tld)

    def delete_tld(self, context, tld_id):
        LOG.info(_LI("delete_tld: Calling central's delete_tld."))
        return self.client.call(context, 'delete_tld', tld_id=tld_id)

    # RecordSet Methods
    def create_recordset(self, context, zone_id, recordset):
        LOG.info(_LI("create_recordset: Calling central's create_recordset."))
        return self.client.call(context, 'create_recordset',
                                zone_id=zone_id, recordset=recordset)

    def get_recordset(self, context, zone_id, recordset_id):
        LOG.info(_LI("get_recordset: Calling central's get_recordset."))
        return self.client.call(context, 'get_recordset', zone_id=zone_id,
                                recordset_id=recordset_id)

    def find_recordsets(self, context, criterion=None, marker=None, limit=None,
                        sort_key=None, sort_dir=None):
        LOG.info(_LI("find_recordsets: Calling central's find_recordsets."))
        return self.client.call(context, 'find_recordsets',
                                criterion=criterion, marker=marker,
                                limit=limit, sort_key=sort_key,
                                sort_dir=sort_dir)

    def find_recordset(self, context, criterion=None):
        LOG.info(_LI("find_recordset: Calling central's find_recordset."))
        return self.client.call(context, 'find_recordset', criterion=criterion)

    def export_zone(self, context, zone_id):
        LOG.info(_LI("export_zone: Calling central's export_zone."))
        return self.client.call(context, 'export_zone', zone_id=zone_id)

    def update_recordset(self, context, recordset, increment_serial=True):
        LOG.info(_LI("update_recordset: Calling central's update_recordset."))
        return self.client.call(context, 'update_recordset',
                                recordset=recordset,
                                increment_serial=increment_serial)

    def delete_recordset(self, context, zone_id, recordset_id,
                         increment_serial=True):
        LOG.info(_LI("delete_recordset: Calling central's delete_recordset."))
        return self.client.call(context, 'delete_recordset',
                                zone_id=zone_id,
                                recordset_id=recordset_id,
                                increment_serial=increment_serial)

    def count_recordsets(self, context, criterion=None):
        LOG.info(_LI("count_recordsets: Calling central's count_recordsets."))
        return self.client.call(context, 'count_recordsets',
                                criterion=criterion)

    # Record Methods
    def create_record(self, context, zone_id, recordset_id, record,
                      increment_serial=True):
        LOG.info(_LI("create_record: Calling central's create_record."))
        return self.client.call(context, 'create_record',
                                zone_id=zone_id,
                                recordset_id=recordset_id,
                                record=record,
                                increment_serial=increment_serial)

    def get_record(self, context, zone_id, recordset_id, record_id):
        LOG.info(_LI("get_record: Calling central's get_record."))
        return self.client.call(context, 'get_record',
                                zone_id=zone_id,
                                recordset_id=recordset_id,
                                record_id=record_id)

    def find_records(self, context, criterion=None, marker=None, limit=None,
                     sort_key=None, sort_dir=None):
        LOG.info(_LI("find_records: Calling central's find_records."))
        return self.client.call(context, 'find_records', criterion=criterion,
                                marker=marker, limit=limit, sort_key=sort_key,
                                sort_dir=sort_dir)

    def find_record(self, context, criterion=None):
        LOG.info(_LI("find_record: Calling central's find_record."))
        return self.client.call(context, 'find_record', criterion=criterion)

    def update_record(self, context, record, increment_serial=True):
        LOG.info(_LI("update_record: Calling central's update_record."))
        return self.client.call(context, 'update_record',
                                record=record,
                                increment_serial=increment_serial)

    def delete_record(self, context, zone_id, recordset_id, record_id,
                      increment_serial=True):
        LOG.info(_LI("delete_record: Calling central's delete_record."))
        return self.client.call(context, 'delete_record',
                                zone_id=zone_id,
                                recordset_id=recordset_id,
                                record_id=record_id,
                                increment_serial=increment_serial)

    def count_records(self, context, criterion=None):
        LOG.info(_LI("count_records: Calling central's count_records."))
        return self.client.call(context, 'count_records', criterion=criterion)

    # Misc. Report combining counts for tenants, zones and records
    def count_report(self, context, criterion=None):
        LOG.info(_LI("count_report: Calling central's count_report."))
        return self.client.call(context, 'count_report', criterion=criterion)

    # Sync Methods
    def sync_zones(self, context):
        LOG.info(_LI("sync_zones: Calling central's sync_zones."))
        return self.client.call(context, 'sync_zones')

    def sync_zone(self, context, zone_id):
        LOG.info(_LI("sync_zone: Calling central's sync_zones."))
        return self.client.call(context, 'sync_zone', zone_id=zone_id)

    def sync_record(self, context, zone_id, recordset_id, record_id):
        LOG.info(_LI("sync_record: Calling central's sync_record."))
        return self.client.call(context, 'sync_record',
                                zone_id=zone_id,
                                recordset_id=recordset_id,
                                record_id=record_id)

    def list_floatingips(self, context):
        LOG.info(_LI("list_floatingips: Calling central's list_floatingips."))
        return self.client.call(context, 'list_floatingips')

    def get_floatingip(self, context, region, floatingip_id):
        LOG.info(_LI("get_floatingip: Calling central's get_floatingip."))
        return self.client.call(context, 'get_floatingip', region=region,
                                floatingip_id=floatingip_id)

    def update_floatingip(self, context, region, floatingip_id, values):
        LOG.info(_LI("update_floatingip: "
                     "Calling central's update_floatingip."))
        return self.client.call(context, 'update_floatingip', region=region,
                                floatingip_id=floatingip_id, values=values)

    # Blacklisted Zone Methods
    def create_blacklist(self, context, blacklist):
        LOG.info(_LI("create_blacklist: Calling central's create_blacklist"))
        return self.client.call(context, 'create_blacklist',
                                blacklist=blacklist)

    def get_blacklist(self, context, blacklist_id):
        LOG.info(_LI("get_blacklist: Calling central's get_blacklist."))
        return self.client.call(context, 'get_blacklist',
                                blacklist_id=blacklist_id)

    def find_blacklists(self, context, criterion=None, marker=None, limit=None,
                        sort_key=None, sort_dir=None):
        LOG.info(_LI("find_blacklists: Calling central's find_blacklists."))
        return self.client.call(
            context, 'find_blacklists', criterion=criterion, marker=marker,
            limit=limit, sort_key=sort_key, sort_dir=sort_dir)

    def find_blacklist(self, context, criterion):
        LOG.info(_LI("find_blacklist: Calling central's find_blacklist."))
        return self.client.call(context, 'find_blacklist', criterion=criterion)

    def update_blacklist(self, context, blacklist):
        LOG.info(_LI("update_blacklist: Calling central's update_blacklist."))
        return self.client.call(context, 'update_blacklist',
                                blacklist=blacklist)

    def delete_blacklist(self, context, blacklist_id):
        LOG.info(_LI("delete_blacklist: Calling central's delete blacklist."))
        return self.client.call(context, 'delete_blacklist',
                                blacklist_id=blacklist_id)

    # Pool Server Methods
    def create_pool(self, context, pool):
        LOG.info(_LI("create_pool: Calling central's create_pool."))
        return self.client.call(context, 'create_pool', pool=pool)

    def find_pools(self, context, criterion=None, marker=None, limit=None,
                   sort_key=None, sort_dir=None):
        LOG.info(_LI("find_pools: Calling central's find_pools."))
        return self.client.call(context, 'find_pools', criterion=criterion,
                                marker=marker, limit=limit, sort_key=sort_key,
                                sort_dir=sort_dir)

    def find_pool(self, context, criterion=None):
        LOG.info(_LI("find_pool: Calling central's find_pool."))
        return self.client.call(context, 'find_pool', criterion=criterion)

    def get_pool(self, context, pool_id):
        LOG.info(_LI("get_pool: Calling central's get_pool."))
        return self.client.call(context, 'get_pool', pool_id=pool_id)

    def update_pool(self, context, pool):
        LOG.info(_LI("update_pool: Calling central's update_pool."))
        return self.client.call(context, 'update_pool', pool=pool)

    def delete_pool(self, context, pool_id):
        LOG.info(_LI("delete_pool: Calling central's delete_pool."))
        return self.client.call(context, 'delete_pool', pool_id=pool_id)

    # Pool Manager Integration Methods
    def update_status(self, context, zone_id, status, serial):
        LOG.info(_LI("update_status: Calling central's update_status "
                     "for %(zone_id)s : %(status)s : %(serial)s"),
                 {'zone_id': zone_id, 'status': status, 'serial': serial})
        self.client.cast(context, 'update_status', zone_id=zone_id,
                         status=status, serial=serial)

    # Zone Ownership Transfers
    def create_zone_transfer_request(self, context, zone_transfer_request):
        LOG.info(_LI("create_zone_transfer_request: \
                     Calling central's create_zone_transfer_request."))

        return self.client.call(
            context, 'create_zone_transfer_request',
            zone_transfer_request=zone_transfer_request)

    def get_zone_transfer_request(self, context, zone_transfer_request_id):
        LOG.info(_LI("get_zone_transfer_request: \
                     Calling central's get_zone_transfer_request."))
        return self.client.call(
            context,
            'get_zone_transfer_request',
            zone_transfer_request_id=zone_transfer_request_id)

    def find_zone_transfer_requests(self, context, criterion=None, marker=None,
                                    limit=None, sort_key=None, sort_dir=None):
        LOG.info(_LI("find_zone_transfer_requests: \
                     Calling central's find_zone_transfer_requests."))

        return self.client.call(
            context, 'find_zone_transfer_requests', criterion=criterion,
            marker=marker, limit=limit, sort_key=sort_key, sort_dir=sort_dir)

    def find_zone_transfer_request(self, context, zone_transfer_request):
        LOG.info(_LI("find_zone_transfer_request: \
                     Calling central's find_zone_transfer_request."))
        return self.client.call(
            context, 'find_zone_transfer_request',
            zone_transfer_request=zone_transfer_request)

    def update_zone_transfer_request(self, context, zone_transfer_request):
        LOG.info(_LI("update_zone_transfer_request: \
                     Calling central's update_zone_transfer_request."))
        return self.client.call(
            context, 'update_zone_transfer_request',
            zone_transfer_request=zone_transfer_request)

    def delete_zone_transfer_request(self, context, zone_transfer_request_id):
        LOG.info(_LI("delete_zone_transfer_request: \
                     Calling central's delete_zone_transfer_request."))
        return self.client.call(
            context,
            'delete_zone_transfer_request',
            zone_transfer_request_id=zone_transfer_request_id)

    def create_zone_transfer_accept(self, context, zone_transfer_accept):
        LOG.info(_LI("create_zone_transfer_accept: \
                     Calling central's create_zone_transfer_accept."))
        return self.client.call(
            context, 'create_zone_transfer_accept',
            zone_transfer_accept=zone_transfer_accept)

    def get_zone_transfer_accept(self, context, zone_transfer_accept_id):
        LOG.info(_LI("get_zone_transfer_accept: \
                     Calling central's get_zone_transfer_accept."))
        return self.client.call(
            context,
            'get_zone_transfer_accept',
            zone_transfer_accept_id=zone_transfer_accept_id)

    def find_zone_transfer_accepts(self, context, criterion=None, marker=None,
                                   limit=None, sort_key=None, sort_dir=None):
        LOG.info(_LI("find_zone_transfer_accepts: \
                     Calling central's find_zone_transfer_accepts."))
        return self.client.call(
            context, 'find_zone_transfer_accepts', criterion=criterion,
            marker=marker, limit=limit, sort_key=sort_key, sort_dir=sort_dir)

    def find_zone_transfer_accept(self, context, zone_transfer_accept):
        LOG.info(_LI("find_zone_transfer_accept: \
                     Calling central's find_zone_transfer_accept."))
        return self.client.call(
            context, 'find_zone_transfer_accept',
            zone_transfer_accept=zone_transfer_accept)

    def update_zone_transfer_accept(self, context, zone_transfer_accept):
        LOG.info(_LI("update_zone_transfer_accept: \
                     Calling central's update_zone_transfer_accept."))
        return self.client.call(
            context, 'update_zone_transfer_accept',
            zone_transfer_accept=zone_transfer_accept)

    def delete_zone_transfer_accept(self, context, zone_transfer_accept_id):
        LOG.info(_LI("delete_zone_transfer_accept: \
                     Calling central's delete_zone_transfer_accept."))
        return self.client.call(
            context,
            'delete_zone_transfer_accept',
            zone_transfer_accept_id=zone_transfer_accept_id)

    def xfr_zone(self, context, zone_id):
        LOG.info(_LI("xfr_zone: Calling central's xfr_zone"))
        return self.client.call(context, 'xfr_zone', zone_id=zone_id)

    # Zone Import Methods
    def create_zone_import(self, context, request_body):
        LOG.info(_LI("create_zone_import: Calling central's "
                     "create_zone_import."))
        return self.client.call(context, 'create_zone_import',
                                request_body=request_body)

    def find_zone_imports(self, context, criterion=None, marker=None,
                          limit=None, sort_key=None, sort_dir=None):
        LOG.info(_LI("find_zone_imports: Calling central's "
                     "find_zone_imports."))
        return self.client.call(context, 'find_zone_imports',
                                criterion=criterion, marker=marker,
                                limit=limit, sort_key=sort_key,
                                sort_dir=sort_dir)

    def get_zone_import(self, context, zone_import_id):
        LOG.info(_LI("get_zone_import: Calling central's get_zone_import."))
        return self.client.call(context, 'get_zone_import',
                                zone_import_id=zone_import_id)

    def update_zone_import(self, context, zone_import):
        LOG.info(_LI("update_zone_import: Calling central's "
                     "update_zone_import."))
        return self.client.call(context, 'update_zone_import',
                                zone_import=zone_import)

    def delete_zone_import(self, context, zone_import_id):
        LOG.info(_LI("delete_zone_import: Calling central's "
                     "delete_zone_import."))
        return self.client.call(context, 'delete_zone_import',
                                zone_import_id=zone_import_id)

    # Zone Export Methods
    def create_zone_export(self, context, zone_id):
        LOG.info(_LI("create_zone_export: Calling central's "
                     "create_zone_export."))
        return self.client.call(context, 'create_zone_export',
                                zone_id=zone_id)

    def find_zone_exports(self, context, criterion=None, marker=None,
                  limit=None, sort_key=None, sort_dir=None):
        LOG.info(_LI("find_zone_exports: Calling central's "
                     "find_zone_exports."))
        return self.client.call(context, 'find_zone_exports',
                                criterion=criterion, marker=marker,
                                limit=limit, sort_key=sort_key,
                                sort_dir=sort_dir)

    def get_zone_export(self, context, zone_export_id):
        LOG.info(_LI("get_zone_export: Calling central's get_zone_export."))
        return self.client.call(context, 'get_zone_export',
                                zone_export_id=zone_export_id)

    def update_zone_export(self, context, zone_export):
        LOG.info(_LI("update_zone_export: Calling central's "
                     "update_zone_export."))
        return self.client.call(context, 'update_zone_export',
                                zone_export=zone_export)

    def delete_zone_export(self, context, zone_export_id):
        LOG.info(_LI("delete_zone_export: Calling central's "
                     "delete_zone_export."))
        return self.client.call(context, 'delete_zone_export',
                                zone_export_id=zone_export_id)
