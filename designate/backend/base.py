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
from designate.openstack.common import log as logging
from designate import exceptions
from designate.context import DesignateContext
from designate.plugin import Plugin


LOG = logging.getLogger(__name__)


class Backend(Plugin):
    """ Base class for backend implementations """
    __plugin_type__ = 'backend'
    __plugin_ns__ = 'designate.backend'

    def __init__(self, central_service):
        super(Backend, self).__init__()
        self.central_service = central_service
        self.admin_context = DesignateContext.get_admin_context()

    def create_tsigkey(self, context, tsigkey):
        """ Create a TSIG Key """
        raise exceptions.NotImplemented(
            'TSIG is not supported by this backend')

    def update_tsigkey(self, context, tsigkey):
        """ Update a TSIG Key """
        raise exceptions.NotImplemented(
            'TSIG is not supported by this backend')

    def delete_tsigkey(self, context, tsigkey):
        """ Delete a TSIG Key """
        raise exceptions.NotImplemented(
            'TSIG is not supported by this backend')

    @abc.abstractmethod
    def create_domain(self, context, domain):
        """ Create a DNS domain """

    @abc.abstractmethod
    def update_domain(self, context, domain):
        """ Update a DNS domain """

    @abc.abstractmethod
    def delete_domain(self, context, domain):
        """ Delete a DNS domain """

    @abc.abstractmethod
    def create_record(self, context, domain, record):
        """ Create a DNS record """

    @abc.abstractmethod
    def update_record(self, context, domain, record):
        """ Update a DNS record """

    @abc.abstractmethod
    def delete_record(self, context, domain, record):
        """ Delete a DNS record """

    @abc.abstractmethod
    def create_server(self, context, server):
        """ Create a DNS server """

    @abc.abstractmethod
    def update_server(self, context, server):
        """ Update a DNS server """

    @abc.abstractmethod
    def delete_server(self, context, server):
        """ Delete a DNS server """

    def sync_domain(self, context, domain, records):
        """
        Re-Sync a DNS domain

        This is the default, naive, domain synchronization implementation.
        """
        # First up, delete the domain from the backend.
        try:
            self.delete_domain(context, domain)
        except exceptions.DomainNotFound as e:
            # NOTE(Kiall): This means a domain was missing from the backend.
            #              Good thing we're doing a sync!
            LOG.warn("Failed to delete domain '%s' during sync. Message: %s",
                     domain['id'], str(e))

        # Next, re-create the domain in the backend.
        self.create_domain(context, domain)

        # Finally, re-create the records for the domain.
        for record in records:
            # Re-create the record in the backend.
            self.create_record(context, domain, record)

    def sync_record(self, context, domain, record):
        """
        Re-Sync a DNS record.

        This is the default, naive, record synchronization implementation.
        """
        # First up, delete the record from the backend.
        try:
            self.delete_record(context, domain, record)
        except exceptions.RecordNotFound as e:
            # NOTE(Kiall): This means a record was missing from the backend.
            #              Good thing we're doing a sync!
            LOG.warn("Failed to delete record '%s' in domain '%s' during sync."
                     " Message: %s", record['id'], domain['id'], str(e))

        # Finally, re-create the record in the backend.
        self.create_record(context, domain, record)

    def ping(self, context):
        """ Ping the Backend service """

        return {
            'status': None
        }
