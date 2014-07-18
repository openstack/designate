# Copyright (c) 2014 Rackspace Hosting
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from oslo.config import cfg
from oslo import messaging

from designate.openstack.common import log as logging
from designate.i18n import _LI
from designate import rpc


LOG = logging.getLogger(__name__)


class MdnsAPI(object):
    """
    Client side of the mdns RPC API.

    Notify API version history:

        0.1 - Initial version under development.  This will be bumped to 1.0
        after a reasonably usable version is implemented.
    """
    RPC_NOTIFY_API_VERSION = '0.1'

    def __init__(self, topic=None):
        topic = topic if topic else cfg.CONF.mdns_topic

        notify_target = messaging.Target(topic=topic,
                                         namespace='notify',
                                         version=self.RPC_NOTIFY_API_VERSION)
        self.notify_client = rpc.get_client(notify_target, version_cap='0.1')

    def notify_zone_changed(self, context, zone_name):
        LOG.info(_LI("notify_zone_changed: Calling mdns's notify_zone_changed "
                     "for zone '%(zone_name)s'") % {'zone_name': zone_name})
        # The notify_zone_changed method is a cast rather than a call since the
        # caller need not wait for the notify to complete.
        return self.notify_client.cast(
            context, 'notify_zone_changed', zone_name=zone_name)
