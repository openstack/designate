# Copyright 2015 Rackspace Inc.
#
# Author: Tim Simmons <tim.simmons@rackspace.com>
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

ZONE_MANAGER_API = None


def reset():
    global ZONE_MANAGER_API
    ZONE_MANAGER_API = None


@rpc_logging(LOG, 'zone_manager')
class ZoneManagerAPI(object):
    """
    Client side of the zone manager RPC API.

    API version history:

        1.0 - Initial version
    """
    RPC_API_VERSION = '1.0'

    def __init__(self, topic=None):
        topic = topic if topic else cfg.CONF.zone_manager_topic

        target = messaging.Target(topic=topic, version=self.RPC_API_VERSION)
        self.client = rpc.get_client(target, version_cap='1.0')

    @classmethod
    def get_instance(cls):
        """
        The rpc.get_client() which is called upon the API object initialization
        will cause a assertion error if the designate.rpc.TRANSPORT isn't setup
        by rpc.init() before.

        This fixes that by creating the rpcapi when demanded.
        """
        global ZONE_MANAGER_API
        if not ZONE_MANAGER_API:
            ZONE_MANAGER_API = cls()
        return ZONE_MANAGER_API

    # Zone Export
    def start_zone_export(self, context, zone, export):
        return self.client.cast(context, 'start_zone_export', zone=zone,
                                export=export)

    def render_zone(self, context, zone_id):
        return self.client.call(context, 'render_zone',
                                zone_id=zone_id)
