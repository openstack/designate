# Copyright 2014 eBay Inc.
#
# Author: Ron Rickard <rrickard@ebaysf.com>
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

from designate.i18n import _LI
from designate import rpc
from designate.loggingutils import rpc_logging


LOG = logging.getLogger(__name__)

MNGR_API = None


def reset():
    global MNGR_API
    MNGR_API = None


@rpc_logging(LOG, 'pool_manager')
class PoolManagerAPI(object):
    """
    Client side of the Pool Manager RPC API.

    API version history:

        API version history:

        1.0 - Initial version
        2.0 - Rename domains to zones
        2.1 - Add target_sync
    """
    RPC_API_VERSION = '2.1'

    def __init__(self, topic=None):
        self.topic = topic if topic \
            else cfg.CONF['service:pool_manager'].pool_manager_topic

        target = messaging.Target(topic=self.topic,
                                  version=self.RPC_API_VERSION)
        self.client = rpc.get_client(target, version_cap='2.1')

    @classmethod
    def get_instance(cls):
        """
        The rpc.get_client() which is called upon the API object initialization
        will cause a assertion error if the designate.rpc.TRANSPORT isn't setup
        by rpc.init() before.

        This fixes that by creating the rpcapi when demanded.
        """
        global MNGR_API
        if not MNGR_API:
            MNGR_API = cls()
        return MNGR_API

    def target_sync(self, context, pool_id, target_id, timestamp):
        LOG.info(_LI("target_sync: Syncing target %(target) since "
                     "%(timestamp)d."),
                 {'target': target_id, 'timestamp': timestamp})

        # Modifying the topic so it is pool manager instance specific.
        topic = '%s.%s' % (self.topic, pool_id)
        cctxt = self.client.prepare(topic=topic)
        return cctxt.call(
            context, 'target_sync', pool_id=pool_id, target_id=target_id,
            timestamp=timestamp)

    def create_zone(self, context, zone):
        # Modifying the topic so it is pool manager instance specific.
        topic = '%s.%s' % (self.topic, zone.pool_id)
        cctxt = self.client.prepare(topic=topic)
        return cctxt.cast(
            context, 'create_zone', zone=zone)

    def delete_zone(self, context, zone):
        # Modifying the topic so it is pool manager instance specific.
        topic = '%s.%s' % (self.topic, zone.pool_id)
        cctxt = self.client.prepare(topic=topic)
        return cctxt.cast(
            context, 'delete_zone', zone=zone)

    def update_zone(self, context, zone):
        # Modifying the topic so it is pool manager instance specific.
        topic = '%s.%s' % (self.topic, zone.pool_id)
        cctxt = self.client.prepare(topic=topic)
        return cctxt.cast(
            context, 'update_zone', zone=zone)

    def update_status(self, context, zone, nameserver, status,
                      actual_serial):

        # Modifying the topic so it is pool manager instance specific.
        topic = '%s.%s' % (self.topic, zone.pool_id)
        cctxt = self.client.prepare(topic=topic)
        return cctxt.cast(
            context, 'update_status', zone=zone, nameserver=nameserver,
            status=status, actual_serial=actual_serial)
