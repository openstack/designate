# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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

from designate import utils
from designate import service
from designate import storage
from designate import dnsutils
from designate.mdns import handler
from designate.mdns import notify
from designate.mdns import xfr
from designate.utils import DEFAULT_MDNS_PORT

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class Service(service.DNSService, service.RPCService, service.Service):
    _dns_default_port = DEFAULT_MDNS_PORT

    @property
    def storage(self):
        if not hasattr(self, '_storage'):
            # Get a storage connection
            self._storage = storage.get_storage(
                CONF['service:mdns'].storage_driver
            )
        return self._storage

    @property
    def service_name(self):
        return cfg.CONF['service:mdns'].mdns_topic

    @property
    @utils.cache_result
    def _rpc_endpoints(self):
        return [notify.NotifyEndpoint(self.tg), xfr.XfrEndpoint(self.tg)]

    @property
    @utils.cache_result
    def _dns_application(self):
        # Create an instance of the RequestHandler class and wrap with
        # necessary middleware.
        application = handler.RequestHandler(self.storage, self.tg)
        application = dnsutils.TsigInfoMiddleware(application, self.storage)
        application = dnsutils.SerializationMiddleware(
            application, dnsutils.TsigKeyring(self.storage))

        return application
