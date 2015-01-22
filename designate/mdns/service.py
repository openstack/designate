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

from designate import dnsutils
from designate import service
from designate.mdns import handler
from designate.mdns import middleware
from designate.mdns import notify
from designate.i18n import _LI

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class Service(service.RPCService):
    def __init__(self, *args, **kwargs):
        notify_endpoint = notify.NotifyEndpoint()
        kwargs['endpoints'] = [notify_endpoint]

        super(Service, self).__init__(*args, **kwargs)

        # Create an instance of the RequestHandler class
        self.application = handler.RequestHandler()

        # Wrap the application in any middleware required
        # TODO(kiall): In the future, we want to allow users to pick+choose
        #              the middleware to be applied, similar to how we do this
        #              in the API.
        self.application = middleware.ContextMiddleware(self.application)

        self._sock_tcp = dnsutils.bind_tcp(
            CONF['service:mdns'].host, CONF['service:mdns'].port,
            CONF['service:mdns'].tcp_backlog)

        self._sock_udp = dnsutils.bind_udp(
            CONF['service:mdns'].host, CONF['service:mdns'].port)

    def start(self):
        super(Service, self).start()

        self.tg.add_thread(
            dnsutils.handle_tcp, self._sock_tcp, self.tg, dnsutils.handle,
            self.application, timeout=CONF['service:mdns'].tcp_recv_timeout)
        self.tg.add_thread(
            dnsutils.handle_udp, self._sock_udp, self.tg, dnsutils.handle,
            self.application)
        LOG.info(_LI("started mdns service"))

    def stop(self):
        # When the service is stopped, the threads for _handle_tcp and
        # _handle_udp are stopped too.
        super(Service, self).stop()
        LOG.info(_LI("stopped mdns service"))
