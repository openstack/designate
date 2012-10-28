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


class StorageEngine(object):
    """
    Base class for storage engines
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def register_opts(self, conf):
        """
        Register any configuration options used by this engine.
        """

    @abc.abstractmethod
    def get_connection(self, conf):
        """
        Return a Connection instance based on the configuration settings.
        """


class Connection(object):
    """
    A Connection
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, conf):
        """
        Constructor...
        """

    @abc.abstractmethod
    def create_server(self, context):
        """
        Create a Server.

        :param context: RPC Context.
        """

    @abc.abstractmethod
    def get_servers(self, context):
        """
        Get Servers.

        :param context: RPC Context.
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
    def create_domain(self, context, values):
        """
        Create a new Domain.

        :param context: RPC Context.
        :param values: Values to create the new Domain from.
        """

    @abc.abstractmethod
    def get_domains(self, context):
        """
        Get all Domains.

        :param context: RPC Context.
        """

    @abc.abstractmethod
    def get_domain(self, context, domain_id):
        """
        Get a Domain via its ID.

        :param context: RPC Context.
        :param domain_id: ID of the Domain.
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
    def create_record(self, context, domain_id, values):
        """
        Create a record on a given Domain ID

        :param context: RPC Context.
        :param domain_id: Domain ID to create the record in.
        :param values: Values to create the new Record from.
        """

    @abc.abstractmethod
    def get_records(self, context, domain_id):
        """
        Get a list of records via a Domain's ID

        :param context: RPC Context.
        :param domain_id: Domain ID where the records recide.
        """

    @abc.abstractmethod
    def get_record(self, context, record_id):
        """
        Get a record via ID

        :param context: RPC Context.
        :param record_id: Record ID to get
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
