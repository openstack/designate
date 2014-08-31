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
import socket
import struct

import dns
from oslo.config import cfg

from designate import service
from designate.mdns import handler
from designate.mdns import middleware
from designate.mdns import notify
from designate.openstack.common import log as logging
from designate.i18n import _LE
from designate.i18n import _LI
from designate.i18n import _LW

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class Service(service.Service):
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

        # Bind to the TCP port
        LOG.info(_LI('Opening TCP Listening Socket on %(host)s:%(port)d') %
                 {'host': CONF['service:mdns'].host,
                  'port': CONF['service:mdns'].port})
        self._sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self._sock_tcp.bind((CONF['service:mdns'].host,
                             CONF['service:mdns'].port))
        self._sock_tcp.listen(CONF['service:mdns'].tcp_backlog)

        # Bind to the UDP port
        LOG.info(_LI('Opening UDP Listening Socket on %(host)s:%(port)d') %
                 {'host': CONF['service:mdns'].host,
                  'port': CONF['service:mdns'].port})
        self._sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock_udp.bind((CONF['service:mdns'].host,
                             CONF['service:mdns'].port))

    def start(self):
        super(Service, self).start()

        self.tg.add_thread(self._handle_tcp)
        self.tg.add_thread(self._handle_udp)
        LOG.info(_LI("started mdns service"))

    def stop(self):
        # When the service is stopped, the threads for _handle_tcp and
        # _handle_udp are stopped too.
        super(Service, self).stop()

    def _deserialize_request(self, payload, addr):
        """
        Deserialize a DNS Request Packet

        :param payload: Raw DNS query payload
        :param addr: Tuple of the client's (IP, Port)
        """
        try:
            request = dns.message.from_wire(payload)
        except dns.exception.DNSException:
            LOG.error(_LE("Failed to deserialize packet from "
                          "%(host)s:%(port)d") %
                      {'host': addr[0], 'port': addr[1]})
            return None
        else:
            # Create + Attach the initial "environ" dict. This is similar to
            # the environ dict used in typical WSGI middleware.
            request.environ = {'addr': addr}
            return request

    def _serialize_response(self, response):
        """
        Serialize a DNS Response Packet

        :param response: DNS Response Message
        """
        return response.to_wire()

    def _handle_tcp(self):
        LOG.info(_LI("_handle_tcp thread started"))
        while True:
            client, addr = self._sock_tcp.accept()
            LOG.warn(_LW("Handling TCP Request from: %(host)s:%(port)d") %
                     {'host': addr[0], 'port': addr[1]})

            payload = client.recv(65535)
            (expected_length,) = struct.unpack('!H', payload[0:2])
            actual_length = len(payload[2:])

            # For now we assume all requests are one packet
            # TODO(vinod): Handle multipacket requests
            if (expected_length != actual_length):
                LOG.warn(_LW("got a packet with unexpected length from "
                             "%(host)s:%(port)d. Expected length=%(elen)d. "
                             "Actual length=%(alen)d.") %
                         {'host': addr[0], 'port': addr[1],
                          'elen': expected_length, 'alen': actual_length})
                client.close()
            else:
                self.tg.add_thread(self._handle, addr, payload[2:], client)

    def _handle_udp(self):
        LOG.info(_LI("_handle_udp thread started"))
        while True:
            # TODO(kiall): Determine the appropriate default value for
            #              UDP recvfrom.
            payload, addr = self._sock_udp.recvfrom(8192)
            LOG.warn(_LW("Handling UDP Request from: %(host)s:%(port)d") %
                     {'host': addr[0], 'port': addr[1]})

            self.tg.add_thread(self._handle, addr, payload)

    def _handle(self, addr, payload, client=None):
        """
        Handle a DNS Query

        :param addr: Tuple of the client's (IP, Port)
        :param payload: Raw DNS query payload
        :param client: Client socket (for TCP only)
        """
        try:
            request = self._deserialize_request(payload, addr)

            if request is None:
                # We failed to deserialize the request, generate a failure
                # response using a made up request.
                response = dns.message.make_response(
                    dns.message.make_query('unknown', dns.rdatatype.A))
                response.set_rcode(dns.rcode.FORMERR)
            else:
                response = self.application(request)

            # send back a response only if present
            if response:
                response = self._serialize_response(response)

                if client is not None:
                    # Handle TCP Responses
                    msg_length = len(response)
                    tcp_response = struct.pack("!H", msg_length) + response
                    client.send(tcp_response)
                    client.close()
                else:
                    # Handle UDP Responses
                    self._sock_udp.sendto(response, addr)
        except Exception:
            LOG.exception(_LE("Unhandled exception while processing request "
                              "from %(host)s:%(port)d") %
                          {'host': addr[0], 'port': addr[1]})
