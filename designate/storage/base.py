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
from designate.plugin import Plugin


class Storage(Plugin):
    """ Base class for storage plugins """
    __metaclass__ = abc.ABCMeta
    __plugin_ns__ = 'designate.storage'
    __plugin_type__ = 'storage'

    @abc.abstractmethod
    def create_quota(self, context, values):
        """
        Create a Quota.

        :param context: RPC Context.
        :param values: Values to create the new Quota from.
        """

    @abc.abstractmethod
    def get_quota(self, context, quota_id):
        """
        Get a Quota via ID.

        :param context: RPC Context.
        :param quota_id: Quota ID to get.
        """

    @abc.abstractmethod
    def find_quotas(self, context, criterion):
        """
        Find Quotas

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def find_quota(self, context, criterion):
        """
        Find a single Quota.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def update_quota(self, context, quota_id, values):
        """
        Update a Quota via ID

        :param context: RPC Context.
        :param quota_id: Quota ID to update.
        :param values: Values to update the Quota from
        """

    @abc.abstractmethod
    def delete_quota(self, context, quota_id):
        """
        Delete a Quota via ID.

        :param context: RPC Context.
        :param quota_id: Delete a Quota via ID
        """

    @abc.abstractmethod
    def create_server(self, context, values):
        """
        Create a Server.

        :param context: RPC Context.
        :param values: Values to create the new Domain from.
        """

    @abc.abstractmethod
    def find_servers(self, context, criterion=None):
        """
        Find Servers.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def get_server(self, context, server_id):
        """
        Get a Server via ID.

        :param context: RPC Context.
        :param server_id: Server ID to get.
        """

    @abc.abstractmethod
    def update_server(self, context, server_id, values):
        """
        Update a Server via ID

        :param context: RPC Context.
        :param server_id: Server ID to update.
        :param values: Values to update the Server from
        """

    @abc.abstractmethod
    def delete_server(self, context, server_id):
        """
        Delete a Server via ID.

        :param context: RPC Context.
        :param server_id: Delete a Server via ID
        """

    @abc.abstractmethod
    def create_tsigkey(self, context, values):
        """
        Create a TSIG Key.

        :param context: RPC Context.
        """

    @abc.abstractmethod
    def find_tsigkeys(self, context, criterion=None):
        """
        Find TSIG Keys.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def get_tsigkey(self, context, tsigkey_id):
        """
        Get a TSIG Key via ID.

        :param context: RPC Context.
        :param tsigkey_id: Server ID to get.
        """

    @abc.abstractmethod
    def update_tsigkey(self, context, tsigkey_id, values):
        """
        Update a TSIG Key via ID

        :param context: RPC Context.
        :param tsigkey_id: TSIG Key ID to update.
        :param values: Values to update the TSIG Key from
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
    def count_tenants(self, context, values):
        """
        Count tenants

        :param context: RPC Context.
        """

    @abc.abstractmethod
    def create_domain(self, context, values):
        """
        Create a new Domain.

        :param context: RPC Context.
        :param values: Values to create the new Domain from.
        """

    @abc.abstractmethod
    def get_domain(self, context, domain_id):
        """
        Get a Domain via its ID.

        :param context: RPC Context.
        :param domain_id: ID of the Domain.
        """

    @abc.abstractmethod
    def find_domains(self, context, criterion=None):
        """
        Find Domains

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def find_domain(self, context, criterion):
        """
        Find a single Domain.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def update_domain(self, context, domain_id, values):
        """
        Update a Domain via ID.

        :param context: RPC Context.
        :param domain_id: Values to update the Domain with
        :param values: Values to update the Domain from.
        """

    @abc.abstractmethod
    def delete_domain(self, context, domain_id):
        """
        Delete a Domain

        :param context: RPC Context.
        :param domain_id: Domain ID to delete.
        """

    @abc.abstractmethod
    def count_domains(self, context, criterion=None):
        """
        Count domains

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def create_record(self, context, domain_id, values):
        """
        Create a record on a given Domain ID

        :param context: RPC Context.
        :param domain_id: Domain ID to create the record in.
        :param values: Values to create the new Record from.
        """

    @abc.abstractmethod
    def get_record(self, context, record_id):
        """
        Get a record via ID

        :param context: RPC Context.
        :param record_id: Record ID to get
        """

    @abc.abstractmethod
    def find_records(self, context, criterion=None):
        """
        Find Records.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def find_record(self, context, criterion):
        """
        Find a single Record.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    @abc.abstractmethod
    def update_record(self, context, record_id, values):
        """
        Update a record via ID

        :param context: RPC Context
        :param record_id: Record ID to update
        """

    @abc.abstractmethod
    def delete_record(self, context, record_id):
        """
        Delete a record

        :param context: RPC Context
        :param record_id: Record ID to delete
        """

    @abc.abstractmethod
    def count_records(self, context, criterion=None):
        """
        Count records

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """

    def ping(self, context):
        """ Ping the Storage connection """
        return {
            'status': None
        }
