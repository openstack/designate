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

from oslo.config import cfg
from oslo_log import log as logging

from designate.i18n import _LI
from designate.context import DesignateContext
from designate.plugin import DriverPlugin


LOG = logging.getLogger(__name__)
CONF = cfg.CONF

CONF.import_opt('pool_id', 'designate.pool_manager',
                group='service:pool_manager')


class Backend(DriverPlugin):
    """Base class for backend implementations"""
    __plugin_type__ = 'backend'
    __plugin_ns__ = 'designate.backend'

    def __init__(self, target):
        super(Backend, self).__init__()

        self.target = target
        self.options = target.options
        self.masters = target.masters

        # TODO(kiall): Context's should never be shared accross requests.
        self.admin_context = DesignateContext.get_admin_context()
        self.admin_context.all_tenants = True

    def start(self):
        LOG.info(_LI('Starting %s backend'), self.get_canonical_name())

    def stop(self):
        LOG.info(_LI('Stopped %s backend'), self.get_canonical_name())

    # Core Backend Interface
    @abc.abstractmethod
    def create_domain(self, context, domain):
        """
        Create a DNS domain.

        :param context: Security context information.
        :param domain: the DNS domain.
        """

    def update_domain(self, context, domain):
        """
        Update a DNS domain.

        :param context: Security context information.
        :param domain: the DNS domain.
        """

    @abc.abstractmethod
    def delete_domain(self, context, domain):
        """
        Delete a DNS domain.

        :param context: Security context information.
        :param domain: the DNS domain.
        """

    def ping(self, context):
        """Ping the Backend service"""

        return {
            'status': None
        }
