# Copyright 2016 Rackspace Inc.
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

WORKER_API = None


@rpc_logging(LOG, 'worker')
class WorkerAPI(object):
    """
    Client side of the worker RPC API.

    API version history:

        1.0 - Initial version
    """
    RPC_API_VERSION = '1.0'

    def __init__(self, topic=None):
        topic = topic if topic else cfg.CONF['service:worker'].worker_topic

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
        global WORKER_API
        if not WORKER_API:
            WORKER_API = cls()
        return WORKER_API

    def create_zone(self, context, zone):
        return self.client.cast(
            context, 'create_zone', zone=zone)

    def update_zone(self, context, zone):
        return self.client.cast(
            context, 'update_zone', zone=zone)

    def delete_zone(self, context, zone):
        return self.client.cast(
            context, 'delete_zone', zone=zone)

    def recover_shard(self, context, begin, end):
        return self.client.cast(
            context, 'recover_shard', begin=begin, end=end)

    def start_zone_export(self, context, zone, export):
        return self.client.cast(
            context, 'start_zone_export', zone=zone, export=export)
