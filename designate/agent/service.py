# Copyright 2014 Rackspace Inc.
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
from oslo.config import cfg
from oslo_log import log as logging

from designate import dnsutils
from designate import service
from designate.agent import handler
from designate.backend import agent_backend
from designate.i18n import _LI


LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class Service(service.DNSService):
    def __init__(self, *args, **kwargs):
        super(Service, self).__init__(cfg.CONF['service:agent'], *args,
                                      **kwargs)

        backend_driver = cfg.CONF['service:agent'].backend_driver
        self.backend = agent_backend.get_backend(backend_driver, self)

        # Create an instance of the RequestHandler class
        self.application = handler.RequestHandler()

        self.application = dnsutils.DNSMiddleware(self.application)

    def start(self):
        super(Service, self).start()
        self.backend.start()
        LOG.info(_LI("Started Agent Service"))

    def stop(self):
        super(Service, self).stop()
        LOG.info(_LI("Stopped Agent Service"))
