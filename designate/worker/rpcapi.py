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
from oslo_log import log as logging
import oslo_messaging as messaging

from designate.common.decorators import rpc as rpc_decorator
from designate.common import profiler
import designate.conf
from designate import rpc


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)

WORKER_API = None


@profiler.trace_cls("rpc")
@rpc_decorator.rpc_logging(LOG, 'worker')
class WorkerAPI:
    """
    Client side of the worker RPC API.

    API version history:

        1.0 - Initial version
        1.1 - Added perform_zone_xfr and get_serial_number
        1.2 - Added hard_delete to delete_zone
    """
    RPC_API_VERSION = '1.2'

    def __init__(self, topic=None):
        self.topic = topic if topic else CONF['service:worker'].topic

        target = messaging.Target(topic=self.topic,
                                  version=self.RPC_API_VERSION)
        self.client = rpc.get_client(target, version_cap='1.2')

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

    def delete_zone(self, context, zone, hard_delete=False):
        return self.client.cast(
            context, 'delete_zone', zone=zone, hard_delete=hard_delete)

    def recover_shard(self, context, begin, end):
        return self.client.cast(
            context, 'recover_shard', begin=begin, end=end)

    def start_zone_export(self, context, zone, export):
        return self.client.cast(
            context, 'start_zone_export', zone=zone, export=export)

    def perform_zone_xfr(self, context, zone, servers=None):
        return self.client.cast(
            context, 'perform_zone_xfr', zone=zone, servers=servers)

    def get_serial_number(self, context, zone, host, port):
        return self.client.call(
            context, 'get_serial_number', zone=zone,
            host=host, port=port,
        )
