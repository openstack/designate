# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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
import oslo_messaging as messaging
from oslo_log import log as logging

from designate.pool_manager import rpcapi as pool_mngr_api
from designate.central import rpcapi as central_api
from designate.i18n import _LI

LOG = logging.getLogger(__name__)


class BaseEndpoint(object):
    # Endpoints which extend this base must provide these properties
    RPC_API_NAMESPACE = None
    RPC_API_VERSION = None

    def __init__(self, tg):
        LOG.info(_LI("Initialized mDNS %s endpoint"), self.RPC_API_NAMESPACE)
        self.tg = tg
        self.target = messaging.Target(
            namespace=self.RPC_API_NAMESPACE,
            version=self.RPC_API_VERSION)

    @property
    def central_api(self):
        return central_api.CentralAPI.get_instance()

    @property
    def pool_manager_api(self):
        return pool_mngr_api.PoolManagerAPI.get_instance()
