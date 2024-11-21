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

from oslo_log import log as logging

import designate.conf
from designate.context import DesignateContext
from designate.plugin import DriverPlugin


LOG = logging.getLogger(__name__)
CONF = designate.conf.CONF


class Backend(DriverPlugin):
    """Base class for backend implementations"""
    __plugin_type__ = 'backend'
    __plugin_ns__ = 'designate.backend'

    __backend_status__ = 'untested'

    def __init__(self, target):
        super().__init__()

        self.target = target
        self.options = target.options
        self.masters = target.masters

        # TODO(kiall): Context's should never be shared across requests.
        self.admin_context = DesignateContext.get_admin_context()
        self.admin_context.all_tenants = True

        # Options for sending NOTIFYs
        self.timeout = CONF['service:worker'].poll_timeout
        self.retry_interval = CONF['service:worker'].poll_retry_interval
        self.max_retries = CONF['service:worker'].poll_max_retries
        self.delay = CONF['service:worker'].poll_delay

    # Core Backend Interface
    @abc.abstractmethod
    def create_zone(self, context, zone):
        """
        Create a DNS zone.

        :param context: Security context information.
        :param zone: the DNS zone.
        """

    def update_zone(self, context, zone):
        """
        Update a DNS zone.

        :param context: Security context information.
        :param zone: the DNS zone.
        """
        LOG.debug('Update Zone')

    @abc.abstractmethod
    def delete_zone(self, context, zone, zone_params):
        """
        Delete a DNS zone.

        :param context: Security context information.
        :param zone: the DNS zone.
        """
