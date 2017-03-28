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

from designate import rpc
from designate.loggingutils import rpc_logging

LOG = logging.getLogger(__name__)

CENTRAL_API = None


def reset():
    global CENTRAL_API
    CENTRAL_API = None


@rpc_logging(LOG, 'central')
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
        6.1 - Add ServiceStatus methods
        6.2 - Changed 'find_recordsets' method args
    """
    RPC_API_VERSION = '6.2'

    # This allows us to mark some methods as not logged.
    # This can be for a few reasons - some methods my not actually call over
    # RPC, or may be so noisy that logging them is not useful
    # This should be an array of strings that match the function names
    LOGGING_BLACKLIST = ['update_service_status']

    def __init__(self, topic=None):
        topic = topic if topic else cfg.CONF['service:central'].central_topic

        target = messaging.Target(topic=topic, version=self.RPC_API_VERSION)
        self.client = rpc.get_client(target, version_cap='6.2')

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
        return self.client.call(context, 'get_absolute_limits')

    # Quota Methods
    def get_quotas(self, context, tenant_id):
        return self.client.call(context, 'get_quotas', tenant_id=tenant_id)

    def get_quota(self, context, tenant_id, resource):
        return self.client.call(context, 'get_quota', tenant_id=tenant_id,
                                resource=resource)

    def set_quota(self, context, tenant_id, resource, hard_limit):
        return self.client.call(context, 'set_quota', tenant_id=tenant_id,
                                resource=resource, hard_limit=hard_limit)

    def reset_quotas(self, context, tenant_id):
        return self.client.call(context, 'reset_quotas', tenant_id=tenant_id)

    # TSIG Key Methods
    def create_tsigkey(self, context, tsigkey):
        return self.client.call(context, 'create_tsigkey', tsigkey=tsigkey)

    def find_tsigkeys(self, context, criterion=None, marker=None, limit=None,
                      sort_key=None, sort_dir=None):
        return self.client.call(context, 'find_tsigkeys', criterion=criterion,
                                marker=marker, limit=limit, sort_key=sort_key,
                                sort_dir=sort_dir)

    def get_tsigkey(self, context, tsigkey_id):
        return self.client.call(context, 'get_tsigkey', tsigkey_id=tsigkey_id)

    def update_tsigkey(self, context, tsigkey):
        return self.client.call(context, 'update_tsigkey', tsigkey=tsigkey)

    def delete_tsigkey(self, context, tsigkey_id):
        return self.client.call(context, 'delete_tsigkey',
                                tsigkey_id=tsigkey_id)

    # Tenant Methods
    def find_tenants(self, context):
        return self.client.call(context, 'find_tenants')

    def get_tenant(self, context, tenant_id):
        return self.client.call(context, 'get_tenant', tenant_id=tenant_id)

    def count_tenants(self, context):
        return self.client.call(context, 'count_tenants')

    # Zone Methods
    def create_zone(self, context, zone):
        return self.client.call(context, 'create_zone', zone=zone)

    def get_zone(self, context, zone_id):
        return self.client.call(context, 'get_zone', zone_id=zone_id)

    def get_zone_ns_records(self, context, zone_id):
        return self.client.call(context, 'get_zone_ns_records',
                                zone_id=zone_id)

    def find_zones(self, context, criterion=None, marker=None, limit=None,
                   sort_key=None, sort_dir=None):
        return self.client.call(context, 'find_zones', criterion=criterion,
                                marker=marker, limit=limit, sort_key=sort_key,
                                sort_dir=sort_dir)

    def find_zone(self, context, criterion=None):
        return self.client.call(context, 'find_zone', criterion=criterion)

    def update_zone(self, context, zone, increment_serial=True):
        return self.client.call(context, 'update_zone', zone=zone,
                                increment_serial=increment_serial)

    def delete_zone(self, context, zone_id):
        return self.client.call(context, 'delete_zone', zone_id=zone_id)

    def purge_zones(self, context, criterion, limit=None):
        return self.client.call(context, 'purge_zones',
                                criterion=criterion, limit=limit)

    def count_zones(self, context, criterion=None):
        return self.client.call(context, 'count_zones', criterion=criterion)

    def touch_zone(self, context, zone_id):
        return self.client.call(context, 'touch_zone', zone_id=zone_id)

    # TLD Methods
    def create_tld(self, context, tld):
        return self.client.call(context, 'create_tld', tld=tld)

    def find_tlds(self, context, criterion=None, marker=None, limit=None,
                  sort_key=None, sort_dir=None):
        return self.client.call(context, 'find_tlds', criterion=criterion,
                                marker=marker, limit=limit, sort_key=sort_key,
                                sort_dir=sort_dir)

    def get_tld(self, context, tld_id):
        return self.client.call(context, 'get_tld', tld_id=tld_id)

    def update_tld(self, context, tld):
        return self.client.call(context, 'update_tld', tld=tld)

    def delete_tld(self, context, tld_id):
        return self.client.call(context, 'delete_tld', tld_id=tld_id)

    # RecordSet Methods
    def create_recordset(self, context, zone_id, recordset):
        return self.client.call(context, 'create_recordset',
                                zone_id=zone_id, recordset=recordset)

    def get_recordset(self, context, zone_id, recordset_id):
        return self.client.call(context, 'get_recordset', zone_id=zone_id,
                                recordset_id=recordset_id)

    def find_recordsets(self, context, criterion=None, marker=None, limit=None,
                        sort_key=None, sort_dir=None, force_index=False):
        return self.client.call(context, 'find_recordsets',
                                criterion=criterion, marker=marker,
                                limit=limit, sort_key=sort_key,
                                sort_dir=sort_dir, force_index=force_index)

    def find_recordset(self, context, criterion=None):
        return self.client.call(context, 'find_recordset', criterion=criterion)

    def export_zone(self, context, zone_id):
        return self.client.call(context, 'export_zone', zone_id=zone_id)

    def update_recordset(self, context, recordset, increment_serial=True):
        return self.client.call(context, 'update_recordset',
                                recordset=recordset,
                                increment_serial=increment_serial)

    def delete_recordset(self, context, zone_id, recordset_id,
                         increment_serial=True):
        return self.client.call(context, 'delete_recordset',
                                zone_id=zone_id,
                                recordset_id=recordset_id,
                                increment_serial=increment_serial)

    def count_recordsets(self, context, criterion=None):
        return self.client.call(context, 'count_recordsets',
                                criterion=criterion)

    # Record Methods
    def create_record(self, context, zone_id, recordset_id, record,
                      increment_serial=True):
        return self.client.call(context, 'create_record',
                                zone_id=zone_id,
                                recordset_id=recordset_id,
                                record=record,
                                increment_serial=increment_serial)

    def get_record(self, context, zone_id, recordset_id, record_id):
        return self.client.call(context, 'get_record',
                                zone_id=zone_id,
                                recordset_id=recordset_id,
                                record_id=record_id)

    def find_records(self, context, criterion=None, marker=None, limit=None,
                     sort_key=None, sort_dir=None):
        return self.client.call(context, 'find_records', criterion=criterion,
                                marker=marker, limit=limit, sort_key=sort_key,
                                sort_dir=sort_dir)

    def find_record(self, context, criterion=None):
        return self.client.call(context, 'find_record', criterion=criterion)

    def update_record(self, context, record, increment_serial=True):
        return self.client.call(context, 'update_record',
                                record=record,
                                increment_serial=increment_serial)

    def delete_record(self, context, zone_id, recordset_id, record_id,
                      increment_serial=True):
        return self.client.call(context, 'delete_record',
                                zone_id=zone_id,
                                recordset_id=recordset_id,
                                record_id=record_id,
                                increment_serial=increment_serial)

    def count_records(self, context, criterion=None):
        return self.client.call(context, 'count_records', criterion=criterion)

    # Misc. Report combining counts for tenants, zones and records
    def count_report(self, context, criterion=None):
        return self.client.call(context, 'count_report', criterion=criterion)

    # Sync Methods
    def sync_zones(self, context):
        return self.client.call(context, 'sync_zones')

    def sync_zone(self, context, zone_id):
        return self.client.call(context, 'sync_zone', zone_id=zone_id)

    def sync_record(self, context, zone_id, recordset_id, record_id):
        return self.client.call(context, 'sync_record',
                                zone_id=zone_id,
                                recordset_id=recordset_id,
                                record_id=record_id)

    def list_floatingips(self, context):
        return self.client.call(context, 'list_floatingips')

    def get_floatingip(self, context, region, floatingip_id):
        return self.client.call(context, 'get_floatingip', region=region,
                                floatingip_id=floatingip_id)

    def update_floatingip(self, context, region, floatingip_id, values):
        return self.client.call(context, 'update_floatingip', region=region,
                                floatingip_id=floatingip_id, values=values)

    # Blacklisted Zone Methods
    def create_blacklist(self, context, blacklist):
        return self.client.call(context, 'create_blacklist',
                                blacklist=blacklist)

    def get_blacklist(self, context, blacklist_id):
        return self.client.call(context, 'get_blacklist',
                                blacklist_id=blacklist_id)

    def find_blacklists(self, context, criterion=None, marker=None, limit=None,
                        sort_key=None, sort_dir=None):
        return self.client.call(
            context, 'find_blacklists', criterion=criterion, marker=marker,
            limit=limit, sort_key=sort_key, sort_dir=sort_dir)

    def find_blacklist(self, context, criterion):
        return self.client.call(context, 'find_blacklist', criterion=criterion)

    def update_blacklist(self, context, blacklist):
        return self.client.call(context, 'update_blacklist',
                                blacklist=blacklist)

    def delete_blacklist(self, context, blacklist_id):
        return self.client.call(context, 'delete_blacklist',
                                blacklist_id=blacklist_id)

    # Pool Server Methods
    def create_pool(self, context, pool):
        return self.client.call(context, 'create_pool', pool=pool)

    def find_pools(self, context, criterion=None, marker=None, limit=None,
                   sort_key=None, sort_dir=None):
        return self.client.call(context, 'find_pools', criterion=criterion,
                                marker=marker, limit=limit, sort_key=sort_key,
                                sort_dir=sort_dir)

    def find_pool(self, context, criterion=None):
        return self.client.call(context, 'find_pool', criterion=criterion)

    def get_pool(self, context, pool_id):
        return self.client.call(context, 'get_pool', pool_id=pool_id)

    def update_pool(self, context, pool):
        return self.client.call(context, 'update_pool', pool=pool)

    def delete_pool(self, context, pool_id):
        return self.client.call(context, 'delete_pool', pool_id=pool_id)

    # Pool Manager Integration Methods
    def update_status(self, context, zone_id, status, serial):
        self.client.cast(context, 'update_status', zone_id=zone_id,
                         status=status, serial=serial)

    # Zone Ownership Transfers
    def create_zone_transfer_request(self, context, zone_transfer_request):
        return self.client.call(
            context, 'create_zone_transfer_request',
            zone_transfer_request=zone_transfer_request)

    def get_zone_transfer_request(self, context, zone_transfer_request_id):
        return self.client.call(
            context,
            'get_zone_transfer_request',
            zone_transfer_request_id=zone_transfer_request_id)

    def find_zone_transfer_requests(self, context, criterion=None, marker=None,
                                    limit=None, sort_key=None, sort_dir=None):
        return self.client.call(
            context, 'find_zone_transfer_requests', criterion=criterion,
            marker=marker, limit=limit, sort_key=sort_key, sort_dir=sort_dir)

    def find_zone_transfer_request(self, context, zone_transfer_request):
        return self.client.call(
            context, 'find_zone_transfer_request',
            zone_transfer_request=zone_transfer_request)

    def update_zone_transfer_request(self, context, zone_transfer_request):
        return self.client.call(
            context, 'update_zone_transfer_request',
            zone_transfer_request=zone_transfer_request)

    def delete_zone_transfer_request(self, context, zone_transfer_request_id):
        return self.client.call(
            context,
            'delete_zone_transfer_request',
            zone_transfer_request_id=zone_transfer_request_id)

    def create_zone_transfer_accept(self, context, zone_transfer_accept):
        return self.client.call(
            context, 'create_zone_transfer_accept',
            zone_transfer_accept=zone_transfer_accept)

    def get_zone_transfer_accept(self, context, zone_transfer_accept_id):
        return self.client.call(
            context,
            'get_zone_transfer_accept',
            zone_transfer_accept_id=zone_transfer_accept_id)

    def find_zone_transfer_accepts(self, context, criterion=None, marker=None,
                                   limit=None, sort_key=None, sort_dir=None):
        return self.client.call(
            context, 'find_zone_transfer_accepts', criterion=criterion,
            marker=marker, limit=limit, sort_key=sort_key, sort_dir=sort_dir)

    def find_zone_transfer_accept(self, context, zone_transfer_accept):
        return self.client.call(
            context, 'find_zone_transfer_accept',
            zone_transfer_accept=zone_transfer_accept)

    def update_zone_transfer_accept(self, context, zone_transfer_accept):
        return self.client.call(
            context, 'update_zone_transfer_accept',
            zone_transfer_accept=zone_transfer_accept)

    def delete_zone_transfer_accept(self, context, zone_transfer_accept_id):
        return self.client.call(
            context,
            'delete_zone_transfer_accept',
            zone_transfer_accept_id=zone_transfer_accept_id)

    def xfr_zone(self, context, zone_id):
        return self.client.call(context, 'xfr_zone', zone_id=zone_id)

    # Zone Import Methods
    def create_zone_import(self, context, request_body):
        return self.client.call(context, 'create_zone_import',
                                request_body=request_body)

    def find_zone_imports(self, context, criterion=None, marker=None,
                          limit=None, sort_key=None, sort_dir=None):
        return self.client.call(context, 'find_zone_imports',
                                criterion=criterion, marker=marker,
                                limit=limit, sort_key=sort_key,
                                sort_dir=sort_dir)

    def get_zone_import(self, context, zone_import_id):
        return self.client.call(context, 'get_zone_import',
                                zone_import_id=zone_import_id)

    def update_zone_import(self, context, zone_import):
        return self.client.call(context, 'update_zone_import',
                                zone_import=zone_import)

    def delete_zone_import(self, context, zone_import_id):
        return self.client.call(context, 'delete_zone_import',
                                zone_import_id=zone_import_id)

    # Zone Export Methods
    def create_zone_export(self, context, zone_id):
        return self.client.call(context, 'create_zone_export',
                                zone_id=zone_id)

    def find_zone_exports(self, context, criterion=None, marker=None,
                          limit=None, sort_key=None, sort_dir=None):
        return self.client.call(context, 'find_zone_exports',
                                criterion=criterion, marker=marker,
                                limit=limit, sort_key=sort_key,
                                sort_dir=sort_dir)

    def get_zone_export(self, context, zone_export_id):
        return self.client.call(context, 'get_zone_export',
                                zone_export_id=zone_export_id)

    def update_zone_export(self, context, zone_export):
        return self.client.call(context, 'update_zone_export',
                                zone_export=zone_export)

    def delete_zone_export(self, context, zone_export_id):
        return self.client.call(context, 'delete_zone_export',
                                zone_export_id=zone_export_id)

    def find_service_status(self, context, criterion=None):
        return self.client.call(context, 'find_service_status',
                                criterion=criterion)

    def find_service_statuses(self, context, criterion=None, marker=None,
                              limit=None, sort_key=None, sort_dir=None):
        return self.client.call(context, 'find_service_statuses',
                                criterion=criterion, marker=marker,
                                limit=limit, sort_key=sort_key,
                                sort_dir=sort_dir)

    def update_service_status(self, context, service_status):
        self.client.cast(context, 'update_service_status',
                         service_status=service_status)
