# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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
from oslo_log import log as logging

from designate import utils
from designate import service
from designate import dnsutils
from designate.mdns import handler
from designate.mdns import notify

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class Service(service.DNSService, service.RPCService, service.Service):
    def __init__(self, threads=None):
        super(Service, self).__init__(threads=threads)

    @property
    def service_name(self):
        return 'mdns'

    @property
    @utils.cache_result
    def _rpc_endpoints(self):
        return [notify.NotifyEndpoint()]

    @property
    @utils.cache_result
    def _dns_application(self):
        # Create an instance of the RequestHandler class
        application = handler.RequestHandler()
        application = dnsutils.ContextMiddleware(application)
        application = dnsutils.SerializationMiddleware(application)

        return application
