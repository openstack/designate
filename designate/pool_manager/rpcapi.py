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
from oslo.config import cfg
from oslo import messaging

from designate.openstack.common import log as logging
from designate.i18n import _LI
from designate import rpc


LOG = logging.getLogger(__name__)

MNGR_API = None


class PoolManagerAPI(object):
    """
    Client side of the Pool Manager RPC API.

    API version history:

        API version history:

        1.0 - Initial version
    """
    RPC_API_VERSION = '1.0'

    def __init__(self, topic=None):
        topic = topic if topic else cfg.CONF.pool_manager_topic

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
        global MNGR_API
        if not MNGR_API:
            MNGR_API = cls()
        return MNGR_API

    def create_domain(self, context, domain):
        LOG.info(_LI("create_domain: Calling pool manager's create_domain."))
        return self.client.cast(
            context, 'create_domain', domain=domain)

    def delete_domain(self, context, domain):
        LOG.info(_LI("delete_domain: Calling pool manager's delete_domain."))
        return self.client.cast(
            context, 'delete_domain', domain=domain)

    def update_domain(self, context, domain):
        LOG.info(_LI("update_domain: Calling pool manager's update_domain."))
        return self.client.cast(
            context, 'update_domain', domain=domain)

    def update_status(self, context, domain, destination,
                      status, actual_serial):
        LOG.info(_LI("update_status: Calling pool manager's update_status."))
        return self.client.cast(
            context, 'update_status', domain=domain, destination=destination,
            status=status, actual_serial=actual_serial)
