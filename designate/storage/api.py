# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
import contextlib
from designate import storage
from designate.openstack.common import excutils


class StorageAPI(object):
    """ Storage API """

    def __init__(self):
        self.storage = storage.get_storage()

    def _extract_dict_subset(self, d, keys):
        return dict([(k, d[k]) for k in keys if k in d])

    @contextlib.contextmanager
    def create_quota(self, context, values):
        """
        Create a Quota.

        :param context: RPC Context.
        :param values: Values to create the new Quota from.
        """
        quota = self.storage.create_quota(context, values)

        try:
            yield quota
        except Exception:
            with excutils.save_and_reraise_exception():
                self.storage.delete_quota(context, quota['id'])

    def get_quota(self, context, quota_id):
        """
        Get a Quota via ID.

        :param context: RPC Context.
        :param quota_id: Quota ID to get.
        """
        return self.storage.get_quota(context, quota_id)

    def find_quotas(self, context, criterion=None):
        """
        Find Quotas

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        return self.storage.find_quotas(context, criterion)

    def find_quota(self, context, criterion):
        """
        Find a single Quota.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        return self.storage.find_quota(context, criterion)

    @contextlib.contextmanager
    def update_quota(self, context, quota_id, values):
        """
        Update a Quota via ID

        :param context: RPC Context.
        :param quota_id: Quota ID to update.
        :param values: Values to update the Quota from
        """
        backup = self.storage.get_quota(context, quota_id)
        quota = self.storage.update_quota(context, quota_id, values)

        try:
            yield quota
        except Exception:
            with excutils.save_and_reraise_exception():
                restore = self._extract_dict_subset(backup, values.keys())
                self.storage.update_quota(context, quota_id, restore)

    @contextlib.contextmanager
    def delete_quota(self, context, quota_id):
        """
        Delete a Quota via ID.

        :param context: RPC Context.
        :param quota_id: Delete a Quota via ID
        """
        yield self.storage.get_quota(context, quota_id)
        self.storage.delete_quota(context, quota_id)

    @contextlib.contextmanager
    def create_server(self, context, values):
        """
        Create a Server.

        :param context: RPC Context.
        :param values: Values to create the new Domain from.
        """
        server = self.storage.create_server(context, values)

        try:
            yield server
        except Exception:
            with excutils.save_and_reraise_exception():
                self.storage.delete_server(context, server['id'])

    def get_server(self, context, server_id):
        """
        Get a Server via ID.

        :param context: RPC Context.
        :param server_id: Server ID to get.
        """
        return self.storage.get_server(context, server_id)

    def find_servers(self, context, criterion=None):
        """
        Find Servers

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        return self.storage.find_servers(context, criterion)

    def find_server(self, context, criterion):
        """
        Find a single Server.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        return self.storage.find_server(context, criterion)

    @contextlib.contextmanager
    def update_server(self, context, server_id, values):
        """
        Update a Server via ID

        :param context: RPC Context.
        :param server_id: Server ID to update.
        :param values: Values to update the Server from
        """
        backup = self.storage.get_server(context, server_id)
        server = self.storage.update_server(context, server_id, values)

        try:
            yield server
        except Exception:
            with excutils.save_and_reraise_exception():
                restore = self._extract_dict_subset(backup, values.keys())
                self.storage.update_server(context, server_id, restore)

    @contextlib.contextmanager
    def delete_server(self, context, server_id):
        """
        Delete a Server via ID.

        :param context: RPC Context.
        :param server_id: Delete a Server via ID
        """
        yield self.storage.get_server(context, server_id)
        self.storage.delete_server(context, server_id)

    @contextlib.contextmanager
    def create_tsigkey(self, context, values):
        """
        Create a TSIG Key.

        :param context: RPC Context.
        """
        tsigkey = self.storage.create_tsigkey(context, values)

        try:
            yield tsigkey
        except Exception:
            with excutils.save_and_reraise_exception():
                self.storage.delete_tsigkey(context, tsigkey['id'])

    def get_tsigkey(self, context, tsigkey_id):
        """
        Get a TSIG Key via ID.

        :param context: RPC Context.
        :param tsigkey_id: Server ID to get.
        """
        return self.storage.get_tsigkey(context, tsigkey_id)

    def find_tsigkeys(self, context, criterion=None):
        """
        Find Tsigkey

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        return self.storage.find_tsigkeys(context, criterion)

    def find_tsigkey(self, context, criterion):
        """
        Find a single Tsigkey.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        return self.storage.find_tsigkey(context, criterion)

    @contextlib.contextmanager
    def update_tsigkey(self, context, tsigkey_id, values):
        """
        Update a TSIG Key via ID

        :param context: RPC Context.
        :param tsigkey_id: TSIG Key ID to update.
        :param values: Values to update the TSIG Key from
        """
        backup = self.storage.get_tsigkey(context, tsigkey_id)
        tsigkey = self.storage.update_tsigkey(context, tsigkey_id, values)

        try:
            yield tsigkey
        except Exception:
            with excutils.save_and_reraise_exception():
                restore = self._extract_dict_subset(backup, values.keys())
                self.storage.update_tsigkey(context, tsigkey_id, restore)

    @contextlib.contextmanager
    def delete_tsigkey(self, context, tsigkey_id):
        """
        Delete a TSIG Key via ID.

        :param context: RPC Context.
        :param tsigkey_id: Delete a TSIG Key via ID
        """
        yield self.storage.get_tsigkey(context, tsigkey_id)
        self.storage.delete_tsigkey(context, tsigkey_id)

    def find_tenants(self, context):
        """
        Find all Tenants.

        :param context: RPC Context.
        """
        return self.storage.find_tenants(context)

    def get_tenant(self, context, tenant_id):
        """
        Get all Tenants.

        :param context: RPC Context.
        :param tenant_id: ID of the Tenant.
        """
        return self.storage.get_tenant(context, tenant_id)

    def count_tenants(self, context):
        """
        Count tenants

        :param context: RPC Context.
        """
        return self.storage.count_tenants(context)

    @contextlib.contextmanager
    def create_domain(self, context, values):
        """
        Create a new Domain.

        :param context: RPC Context.
        :param values: Values to create the new Domain from.
        """
        domain = self.storage.create_domain(context, values)

        try:
            yield domain
        except Exception:
            with excutils.save_and_reraise_exception():
                self.storage.delete_domain(context, domain['id'])

    def get_domain(self, context, domain_id):
        """
        Get a Domain via its ID.

        :param context: RPC Context.
        :param domain_id: ID of the Domain.
        """
        return self.storage.get_domain(context, domain_id)

    def find_domains(self, context, criterion=None):
        """
        Find Domains

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        return self.storage.find_domains(context, criterion)

    def find_domain(self, context, criterion):
        """
        Find a single Domain.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        return self.storage.find_domain(context, criterion)

    @contextlib.contextmanager
    def update_domain(self, context, domain_id, values):
        """
        Update a Domain via ID.

        :param context: RPC Context.
        :param domain_id: Values to update the Domain with
        :param values: Values to update the Domain from.
        """
        backup = self.storage.get_domain(context, domain_id)
        domain = self.storage.update_domain(context, domain_id, values)

        try:
            yield domain
        except Exception:
            with excutils.save_and_reraise_exception():
                restore = self._extract_dict_subset(backup, values.keys())
                self.storage.update_domain(context, domain_id, restore)

    @contextlib.contextmanager
    def delete_domain(self, context, domain_id):
        """
        Delete a Domain

        :param context: RPC Context.
        :param domain_id: Domain ID to delete.
        """
        yield self.storage.get_domain(context, domain_id)
        self.storage.delete_domain(context, domain_id)

    def count_domains(self, context, criterion=None):
        """
        Count domains

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        return self.storage.count_domains(context, criterion)

    @contextlib.contextmanager
    def create_record(self, context, domain_id, values):
        """
        Create a record on a given Domain ID

        :param context: RPC Context.
        :param domain_id: Domain ID to create the record in.
        :param values: Values to create the new Record from.
        """
        record = self.storage.create_record(context, domain_id, values)

        try:
            yield record
        except Exception:
            with excutils.save_and_reraise_exception():
                self.storage.delete_record(context, record['id'])

    def get_record(self, context, record_id):
        """
        Get a record via ID

        :param context: RPC Context.
        :param record_id: Record ID to get
        """
        return self.storage.get_record(context, record_id)

    def find_records(self, context, criterion=None):
        """
        Find Records.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        return self.storage.find_records(context, criterion)

    def find_record(self, context, criterion=None):
        """
        Find a single Record.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        return self.storage.find_record(context, criterion)

    @contextlib.contextmanager
    def update_record(self, context, record_id, values):
        """
        Update a record via ID

        :param context: RPC Context
        :param record_id: Record ID to update
        """
        backup = self.storage.get_record(context, record_id)
        record = self.storage.update_record(context, record_id, values)

        try:
            yield record
        except Exception:
            with excutils.save_and_reraise_exception():
                restore = self._extract_dict_subset(backup, values.keys())
                self.storage.update_record(context, record_id, restore)

    @contextlib.contextmanager
    def delete_record(self, context, record_id):
        """
        Delete a record

        :param context: RPC Context
        :param record_id: Record ID to delete
        """
        yield self.storage.get_record(context, record_id)
        self.storage.delete_record(context, record_id)

    def count_records(self, context, criterion=None):
        """
        Count records

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        return self.storage.count_records(context, criterion)

    def ping(self, context):
        """ Ping the Storage connection """
        return self.storage.ping(context)
