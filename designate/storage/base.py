# Copyright 2012 Managed I.T.
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
import abc

import six

from designate.plugin import DriverPlugin


@six.add_metaclass(abc.ABCMeta)
class Storage(DriverPlugin):

    """Base class for storage plugins"""
    __plugin_ns__ = 'designate.storage'
    __plugin_type__ = 'storage'

    @abc.abstractmethod
    def create_quota(self, context, quota):
        """
        Create a Quota.

        :param context: RPC Context.
        :param quota: Quota object with the values to be created.
        """

    @abc.abstractmethod
    def get_quota(self, context, quota_id):
        """
        Get a Quota via ID.

        :param context: RPC Context.
        :param quota_id: Quota ID to get.
        """

    @abc.abstractmethod
    def find_quotas(self, context, criterion=None, marker=None,
                    limit=None, sort_key=None, sort_dir=None):
        """
        Find Quotas

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param marker: Resource ID from which after the requested page will
                       start after
        :param limit: Integer limit of objects of the page size after the
                      marker
        :param sort_key: Key from which to sort after.
        :param sort_dir: Direction to sort after using sort_key.
        """

    @abc.abstractmethod
    def find_quota(self, context, criterion):
        """
        Find a single Quota.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def update_quota(self, context, quota):
        """
        Update a Quota

        :param context: RPC Context.
        :param quota: Quota to update.
        """

    @abc.abstractmethod
    def delete_quota(self, context, quota_id):
        """
        Delete a Quota via ID.

        :param context: RPC Context.
        :param quota_id: Delete a Quota via ID
        """

    @abc.abstractmethod
    def create_tld(self, context, tld):
        """
        Create a TLD.

        :param context: RPC Context.
        :param tld: Tld object with the values to be created.
        """

    @abc.abstractmethod
    def get_tld(self, context, tld_id):
        """
        Get a TLD via ID.

        :param context: RPC Context.
        :param tld_id: TLD ID to get.
        """

    @abc.abstractmethod
    def find_tlds(self, context, criterion=None, marker=None,
                  limit=None, sort_key=None, sort_dir=None):
        """
        Find TLDs

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param marker: Resource ID from which after the requested page will
                       start after
        :param limit: Integer limit of objects of the page size after the
                      marker
        :param sort_key: Key from which to sort after.
        :param sort_dir: Direction to sort after using sort_key.
        """

    @abc.abstractmethod
    def find_tld(self, context, criterion):
        """
        Find a single TLD.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def update_tld(self, context, tld):
        """
        Update a TLD

        :param context: RPC Context.
        :param tld: TLD to update.
        """

    @abc.abstractmethod
    def delete_tld(self, context, tld_id):
        """
        Delete a TLD via ID.

        :param context: RPC Context.
        :param tld_id: Delete a TLD via ID
        """

    @abc.abstractmethod
    def create_tsigkey(self, context, tsigkey):
        """
        Create a TSIG Key.

        :param context: RPC Context.
        :param tsigkey: TsigKey object with the values to be created.
        """

    @abc.abstractmethod
    def find_tsigkeys(self, context, criterion=None,
                      marker=None, limit=None, sort_key=None, sort_dir=None):
        """
        Find TSIG Keys.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param marker: Resource ID from which after the requested page will
                       start after
        :param limit: Integer limit of objects of the page size after the
                      marker
        :param sort_key: Key from which to sort after.
        :param sort_dir: Direction to sort after using sort_key.
        """

    @abc.abstractmethod
    def get_tsigkey(self, context, tsigkey_id):
        """
        Get a TSIG Key via ID.

        :param context: RPC Context.
        :param tsigkey_id: Server ID to get.
        """

    @abc.abstractmethod
    def update_tsigkey(self, context, tsigkey):
        """
        Update a TSIG Key

        :param context: RPC Context.
        :param tsigkey: TSIG Keyto update.
        """

    @abc.abstractmethod
    def delete_tsigkey(self, context, tsigkey_id):
        """
        Delete a TSIG Key via ID.

        :param context: RPC Context.
        :param tsigkey_id: Delete a TSIG Key via ID
        """

    @abc.abstractmethod
    def find_tenants(self, context):
        """
        Find all Tenants.

        :param context: RPC Context.
        """

    @abc.abstractmethod
    def get_tenant(self, context, tenant_id):
        """
        Get all Tenants.

        :param context: RPC Context.
        :param tenant_id: ID of the Tenant.
        """

    @abc.abstractmethod
    def count_tenants(self, context):
        """
        Count tenants

        :param context: RPC Context.
        """

    @abc.abstractmethod
    def create_zone(self, context, zone):
        """
        Create a new Zone.

        :param context: RPC Context.
        :param zone: Zone object with the values to be created.
        """

    @abc.abstractmethod
    def get_zone(self, context, zone_id):
        """
        Get a Zone via its ID.

        :param context: RPC Context.
        :param zone_id: ID of the Zone.
        """

    @abc.abstractmethod
    def find_zones(self, context, criterion=None, marker=None,
                   limit=None, sort_key=None, sort_dir=None):
        """
        Find zones

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param marker: Resource ID from which after the requested page will
                       start after
        :param limit: Integer limit of objects of the page size after the
                      marker
        :param sort_key: Key from which to sort after.
        :param sort_dir: Direction to sort after using sort_key.
        """

    @abc.abstractmethod
    def find_zone(self, context, criterion):
        """
        Find a single Zone.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def update_zone(self, context, zone):
        """
        Update a Zone

        :param context: RPC Context.
        :param zone: Zone object.
        """

    @abc.abstractmethod
    def delete_zone(self, context, zone_id):
        """
        Delete a Zone

        :param context: RPC Context.
        :param zone_id: Zone ID to delete.
        """

    @abc.abstractmethod
    def purge_zone(self, context, zone):
        """
        Purge a Zone

        :param context: RPC Context.
        :param zone: Zone to delete.
        """

    @abc.abstractmethod
    def count_zones(self, context, criterion=None):
        """
        Count zones

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def create_recordset(self, context, zone_id, recordset):
        """
        Create a recordset on a given Zone ID

        :param context: RPC Context.
        :param zone_id: Zone ID to create the recordset in.
        :param recordset: RecordSet object with the values to be created.
        """

    @abc.abstractmethod
    def get_recordset(self, context, recordset_id):
        """
        Get a recordset via ID

        :param context: RPC Context.
        :param recordset_id: RecordSet ID to get
        """

    @abc.abstractmethod
    def find_recordsets(self, context, criterion=None, marker=None, limit=None,
                        sort_key=None, sort_dir=None, force_index=False):
        """
        Find RecordSets.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param marker: Resource ID from which after the requested page will
                       start after
        :param limit: Integer limit of objects of the page size after the
                      marker
        :param sort_key: Key from which to sort after.
        :param sort_dir: Direction to sort after using sort_key.
        """

    @abc.abstractmethod
    def find_recordsets_axfr(self, context, criterion=None):
        """
        Find RecordSets.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def find_recordset(self, context, criterion):
        """
        Find a single RecordSet.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def update_recordset(self, context, recordset):
        """
        Update a recordset

        :param context: RPC Context.
        :param recordset: RecordSet to update
        """

    @abc.abstractmethod
    def delete_recordset(self, context, recordset_id):
        """
        Delete a recordset

        :param context: RPC Context.
        :param recordset_id: RecordSet ID to delete
        """

    @abc.abstractmethod
    def count_recordsets(self, context, criterion=None):
        """
        Count recordsets

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def create_record(self, context, zone_id, recordset_id, record):
        """
        Create a record on a given Zone ID

        :param context: RPC Context.
        :param zone_id: Zone ID to create the record in.
        :param recordset_id: RecordSet ID to create the record in.
        :param record: Record object with the values to be created.
        """

    @abc.abstractmethod
    def get_record(self, context, record_id):
        """
        Get a record via ID

        :param context: RPC Context.
        :param record_id: Record ID to get
        """

    @abc.abstractmethod
    def find_records(self, context, criterion=None, marker=None,
                     limit=None, sort_key=None, sort_dir=None):
        """
        Find Records.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param marker: Resource ID from which after the requested page will
                       start after
        :param limit: Integer limit of objects of the page size after the
                      marker
        :param sort_key: Key from which to sort after.
        :param sort_dir: Direction to sort after using sort_key.
        """

    @abc.abstractmethod
    def find_record(self, context, criterion):
        """
        Find a single Record.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def update_record(self, context, record):
        """
        Update a record

        :param context: RPC Context.
        :param record: Record to update
        """

    @abc.abstractmethod
    def delete_record(self, context, record_id):
        """
        Delete a record

        :param context: RPC Context.
        :param record_id: Record ID to delete
        """

    @abc.abstractmethod
    def count_records(self, context, criterion=None):
        """
        Count records

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def create_blacklist(self, context, blacklist):
        """
        Create a Blacklist.

        :param context: RPC Context.
        :param blacklist: Blacklist object with the values to be created.
        """

    @abc.abstractmethod
    def get_blacklist(self, context, blacklist_id):
        """
        Get a Blacklist via ID.

        :param context: RPC Context.
        :param blacklist_id: Blacklist ID to get.
        """

    @abc.abstractmethod
    def find_blacklists(self, context, criterion=None, marker=None,
                        limit=None, sort_key=None, sort_dir=None):
        """
        Find Blacklists

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param marker: Resource ID from which after the requested page will
                       start after
        :param limit: Integer limit of objects of the page size after the
                      marker
        :param sort_key: Key from which to sort after.
        :param sort_dir: Direction to sort after using sort_key.
        """

    @abc.abstractmethod
    def find_blacklist(self, context, criterion):
        """
        Find a single Blacklist.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def update_blacklist(self, context, blacklist):
        """
        Update a Blacklist

        :param context: RPC Context.
        :param blacklist: Blacklist to update.
        """

    @abc.abstractmethod
    def delete_blacklist(self, context, blacklist_id):
        """
        Delete a Blacklist via ID.

        :param context: RPC Context.
        :param blacklist_id: Delete a Blacklist via ID
        """

    @abc.abstractmethod
    def create_pool(self, context, pool):
        """
        Create a Pool.

        :param context: RPC Context.
        :param pool: Pool object with the values to be created.
        """

    @abc.abstractmethod
    def find_pools(self, context, criterion=None, marker=None,
                   limit=None, sort_key=None, sort_dir=None):
        """
        Find all Pools

        :param context: RPC Context.
        :param criterion: Criteria by which to filter
        :param marker: Resource ID used by paging. The next page will start
                       at the next resource after the marker
        :param limit: Integer limit of objects on the page
        :param sort_key: Key used to sort the returned list
        :param sort_dir: Directions to sort after using sort_key
        """

    @abc.abstractmethod
    def find_pool(self, context, criterion):
        """
        Find a single Pool.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def get_pool(self, context, pool_id):
        """
        Get a Pool via the id

        :param context: RPC Context.
        :param pool_id: The ID of the pool to get
        """

    @abc.abstractmethod
    def update_pool(self, context, pool):
        """
        Update the specified pool

        :param context: RPC Context.
        :param pool: Pool to update.
        """

    @abc.abstractmethod
    def delete_pool(self, context, pool_id):
        """
        Delete the pool with the matching id

        :param context: RPC Context.
        :param pool_id: The ID of the pool to be deleted
        """

    @abc.abstractmethod
    def create_pool_attribute(self, context, pool_id, pool_attribute):
        """
        Create a PoolAttribute.

        :param context: RPC Context.
        :param pool_id: The ID of the pool to which the attribute belongs.
        :param pool_attribute: PoolAttribute object with the values created.
        """

    @abc.abstractmethod
    def find_pool_attributes(self, context, criterion=None, marker=None,
                             limit=None, sort_key=None, sort_dir=None):
        """
        Find all PoolAttributes

        :param context: RPC Context
        :param criterion: Criteria by which to filer
        :param marker: Resource ID used by paging. The next page will start
                       at the next resource after the marker
        :param limit: Integer limit of objects on the page
        :param sort_key: Key used to sort the returned list
        :param sort_dir: Directions to sort after using sort_key
        """

    @abc.abstractmethod
    def find_pool_attribute(self, context, criterion):
        """
        Find a single PoolAttribute

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def get_pool_attribute(self, context, pool_attribute_id):
        """
        Get a PoolAttribute via the ID

        :param context: RPC Context.
        :param pool_attribute_id: The ID of the PoolAttribute to get
        """

    @abc.abstractmethod
    def update_pool_attribute(self, context, pool_attribute):
        """
        Update the specified pool

        :param context: RPC Context.
        :param pool_attribute: PoolAttribute to update
        """

    @abc.abstractmethod
    def delete_pool_attribute(self, context, pool_attribute_id):
        """
        Delete the pool with the matching id

        :param context: RPC Context.
        :param pool_attribute_id: The ID of the PoolAttribute to be deleted
        """

    @abc.abstractmethod
    def create_zone_import(self, context, zone_import):
        """
        Create a Zone Import.

        :param context: RPC Context.
        :param zone_import: Zone Import object with the values to be created.
        """

    @abc.abstractmethod
    def get_zone_import(self, context, zone_import_id):
        """
        Get a Zone Import via ID.

        :param context: RPC Context.
        :param zone_import_id: Zone Import ID to get.
        """

    @abc.abstractmethod
    def find_zone_imports(self, context, criterion=None, marker=None,
                          limit=None, sort_key=None, sort_dir=None):
        """
        Find Zone Imports

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param marker: Resource ID from which after the requested page will
                       start after
        :param limit: Integer limit of objects of the page size after the
                      marker
        :param sort_key: Key from which to sort after.
        :param sort_dir: Direction to sort after using sort_key.
        """

    @abc.abstractmethod
    def find_zone_import(self, context, criterion):
        """
        Find a single Zone Import.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def update_zone_import(self, context, zone_import):
        """
        Update a Zone Import

        :param context: RPC Context.
        :param zone_import: Zone Import to update.
        """

    @abc.abstractmethod
    def delete_zone_import(self, context, zone_import_id):
        """
        Delete a Zone Import via ID.

        :param context: RPC Context.
        :param zone_import_id: Delete a Zone Import via ID
        """

    @abc.abstractmethod
    def create_zone_export(self, context, zone_export):
        """
        Create a Zone Export.

        :param context: RPC Context.
        :param zone_export: Zone Export object with the values to be created.
        """

    @abc.abstractmethod
    def get_zone_export(self, context, zone_export_id):
        """
        Get a Zone Export via ID.

        :param context: RPC Context.
        :param zone_export_id: Zone Export ID to get.
        """

    @abc.abstractmethod
    def find_zone_exports(self, context, criterion=None, marker=None,
                  limit=None, sort_key=None, sort_dir=None):
        """
        Find Zone Exports

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param marker: Resource ID from which after the requested page will
                       start after
        :param limit: Integer limit of objects of the page size after the
                      marker
        :param sort_key: Key from which to sort after.
        :param sort_dir: Direction to sort after using sort_key.
        """

    @abc.abstractmethod
    def find_zone_export(self, context, criterion):
        """
        Find a single Zone Export.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def update_zone_export(self, context, zone_export):
        """
        Update a Zone Export

        :param context: RPC Context.
        :param zone_export: Zone Export to update.
        """

    @abc.abstractmethod
    def delete_zone_export(self, context, zone_export_id):
        """
        Delete a Zone Export via ID.

        :param context: RPC Context.
        :param zone_export_id: Delete a Zone Export via ID
        """

    def ping(self, context):
        """Ping the Storage connection"""
        return {
            'status': None
        }

    @abc.abstractmethod
    def find_service_statuses(self, context, criterion=None, marker=None,
                            limit=None, sort_key=None, sort_dir=None):
        """
        Retrieve status for services

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param marker: Resource ID from which after the requested page will
                       start after
        :param limit: Integer limit of objects of the page size after the
                      marker
        :param sort_key: Key from which to sort after.
        :param sort_dir: Direction to sort after using sort_key.
        """

    @abc.abstractmethod
    def find_service_status(self, context, criterion):
        """
        Find a single Service Status.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def update_service_status(self, context, service_status):
        """
        Update the Service status for a service.

        :param context: RPC Context.
        :param service_status: Set the status for a service.
        """
