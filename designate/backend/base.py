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

from oslo_config import cfg
from oslo_log import log as logging

from designate.i18n import _LI
from designate.context import DesignateContext
from designate.plugin import DriverPlugin
from designate.mdns import rpcapi as mdns_api


LOG = logging.getLogger(__name__)
CONF = cfg.CONF

CONF.import_opt('pool_id', 'designate.pool_manager',
                group='service:pool_manager')


class Backend(DriverPlugin):
    """Base class for backend implementations"""
    __plugin_type__ = 'backend'
    __plugin_ns__ = 'designate.backend'

    __backend_status__ = 'untested'

    def __init__(self, target):
        super(Backend, self).__init__()

        self.target = target
        self.options = target.options
        self.masters = target.masters
        self.host = self.options.get('host', '127.0.0.1')
        self.port = int(self.options.get('port', 53))

        # TODO(kiall): Context's should never be shared across requests.
        self.admin_context = DesignateContext.get_admin_context()
        self.admin_context.all_tenants = True

        # Options for sending NOTIFYs
        self.timeout = CONF['service:pool_manager'].poll_timeout
        self.retry_interval = CONF['service:pool_manager'].poll_retry_interval
        self.max_retries = CONF['service:pool_manager'].poll_max_retries
        self.delay = CONF['service:pool_manager'].poll_delay

    def start(self):
        LOG.info(_LI('Starting %s backend'), self.get_canonical_name())

    def stop(self):
        LOG.info(_LI('Stopped %s backend'), self.get_canonical_name())

    @property
    def mdns_api(self):
        return mdns_api.MdnsAPI.get_instance()

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

        self.mdns_api.notify_zone_changed(
            context, zone, self.host, self.port, self.timeout,
            self.retry_interval, self.max_retries, self.delay)

    @abc.abstractmethod
    def delete_zone(self, context, zone):
        """
        Delete a DNS zone.

        :param context: Security context information.
        :param zone: the DNS zone.
        """

    def ping(self, context):
        """Ping the Backend service"""

        return {
            'status': None
        }
