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
from moniker.openstack.common import log as logging
from moniker.plugin import Plugin


LOG = logging.getLogger(__name__)


class Backend(Plugin):
    """ Base class for backend implementations """
    __plugin_type__ = 'backend'
    __plugin_ns__ = 'moniker.backend'

    @abc.abstractmethod
    def create_domain(self, context, domain, servers):
        """ Create a DNS domain """

    @abc.abstractmethod
    def update_domain(self, context, domain, servers):
        """ Update a DNS domain """

    @abc.abstractmethod
    def delete_domain(self, context, domain, servers):
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

    def ping(self, context):
        """ Ping the Backend service """
        return {
            'status': None
        }
