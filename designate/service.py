# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Justin Santa Barbara
# Copyright 2011 OpenStack Foundation
# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
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
import abc
import socket
import struct
import errno
import time

import six
import eventlet.wsgi
import eventlet.debug
import oslo_messaging as messaging
from oslo_config import cfg
from oslo_log import log as logging
from oslo_log import loggers
from oslo_service import service
from oslo_service import sslutils

from designate.i18n import _
from designate.i18n import _LE
from designate.i18n import _LI
from designate.i18n import _LW
from designate import rpc
from designate import policy
from designate import version
from designate import dnsutils

# TODO(kiall): These options have been cut+paste from the old WSGI code, and
#              should be moved into service:api etc..
wsgi_socket_opts = [
    cfg.IntOpt('backlog',
               default=4096,
               help="Number of backlog requests to configure the socket with"),
    cfg.IntOpt('tcp_keepidle',
               default=600,
               help="Sets the value of TCP_KEEPIDLE in seconds for each "
                    "server socket. Not supported on OS X."),
]

CONF = cfg.CONF
CONF.register_opts(wsgi_socket_opts)

LOG = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class Service(service.Service):
    """
    Service class to be shared among the diverse service inside of Designate.
    """
    def __init__(self, threads=None):
        threads = threads or 1000

        super(Service, self).__init__(threads)

        self._host = CONF.host
        self._service_config = CONF['service:%s' % self.service_name]

        policy.init()

        # NOTE(kiall): All services need RPC initialized, as this is used
        #              for clients AND servers. Hence, this is common to
        #              all Designate services.
        if not rpc.initialized():
            rpc.init(CONF)

    @abc.abstractproperty
    def service_name(self):
        pass

    def start(self):
        super(Service, self).start()

        LOG.info(_('Starting %(name)s service (version: %(version)s)') %
                 {'name': self.service_name,
                  'version': version.version_info.version_string()})

    def stop(self):
        LOG.info(_('Stopping %(name)s service') % {'name': self.service_name})

        super(Service, self).stop()


class RPCService(object):
    """
    RPC Service mixin used by all Designate RPC Services
    """
    def __init__(self, *args, **kwargs):
        super(RPCService, self).__init__(*args, **kwargs)

        LOG.debug("Creating RPC Server on topic '%s'" % self._rpc_topic)
        self._rpc_server = rpc.get_server(
            messaging.Target(topic=self._rpc_topic, server=self._host),
            self._rpc_endpoints)

    @property
    def _rpc_endpoints(self):
        return [self]

    @property
    def _rpc_topic(self):
        return self.service_name

    def start(self):
        super(RPCService, self).start()

        LOG.debug("Starting RPC server on topic '%s'" % self._rpc_topic)
        self._rpc_server.start()

        # TODO(kiall): This probably belongs somewhere else, maybe the base
        #              Service class?
        self.notifier = rpc.get_notifier(self.service_name)

        for e in self._rpc_endpoints:
            if e != self and hasattr(e, 'start'):
                e.start()

    def stop(self):
        LOG.debug("Stopping RPC server on topic '%s'" % self._rpc_topic)

        for e in self._rpc_endpoints:
            if e != self and hasattr(e, 'stop'):
                e.stop()

        # Try to shut the connection down, but if we get any sort of
        # errors, go ahead and ignore them.. as we're shutting down anyway
        try:
            self._rpc_server.stop()
        except Exception:
            pass

        super(RPCService, self).stop()

    def wait(self):
        for e in self._rpc_endpoints:
            if e != self and hasattr(e, 'wait'):
                e.wait()

        super(RPCService, self).wait()


@six.add_metaclass(abc.ABCMeta)
class WSGIService(object):
    """
    WSGI Service mixin used by all Designate WSGI Services
    """
    def __init__(self, *args, **kwargs):
        super(WSGIService, self).__init__(*args, **kwargs)

    @abc.abstractproperty
    def _wsgi_application(self):
        pass

    def start(self):
        super(WSGIService, self).start()

        socket = self._wsgi_get_socket()
        application = self._wsgi_application

        self.tg.add_thread(self._wsgi_handle, application, socket)

    def _wsgi_get_socket(self):
        # TODO(dims): eventlet's green dns/socket module does not actually
        # support IPv6 in getaddrinfo(). We need to get around this in the
        # future or monitor upstream for a fix
        info = socket.getaddrinfo(self._service_config.api_host,
                                  self._service_config.api_port,
                                  socket.AF_UNSPEC,
                                  socket.SOCK_STREAM)[0]
        family = info[0]
        bind_addr = info[-1]

        sock = None
        retry_until = time.time() + 30
        while not sock and time.time() < retry_until:
            try:
                # TODO(kiall): Backlog should be a service specific setting,
                #              rather than a global
                sock = eventlet.listen(bind_addr,
                                       backlog=cfg.CONF.backlog,
                                       family=family)
                if sslutils.is_enabled(CONF):
                    sock = sslutils.wrap(CONF, sock)

            except socket.error as err:
                if err.args[0] != errno.EADDRINUSE:
                    raise
                eventlet.sleep(0.1)
        if not sock:
            raise RuntimeError(_("Could not bind to %(host)s:%(port)s "
                               "after trying for 30 seconds") %
                               {'host': self._service_config.api_host,
                                'port': self._service_config.api_port})
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # sockets can hang around forever without keepalive
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        # This option isn't available in the OS X version of eventlet
        if hasattr(socket, 'TCP_KEEPIDLE'):
            sock.setsockopt(socket.IPPROTO_TCP,
                            socket.TCP_KEEPIDLE,
                            CONF.tcp_keepidle)

        return sock

    def _wsgi_handle(self, application, socket):
        logger = logging.getLogger('eventlet.wsgi')
        # Adjust wsgi MAX_HEADER_LINE to accept large tokens.
        eventlet.wsgi.MAX_HEADER_LINE = self._service_config.max_header_line

        eventlet.wsgi.server(socket,
                             application,
                             custom_pool=self.tg.pool,
                             log=loggers.WritableLogger(logger))


@six.add_metaclass(abc.ABCMeta)
class DNSService(object):
    """
    DNS Service mixin used by all Designate DNS Services
    """
    def __init__(self, *args, **kwargs):
        super(DNSService, self).__init__(*args, **kwargs)

        # Eventet will complain loudly about our use of multiple greentheads
        # reading/writing to the UDP socket at once. Disable this warning.
        eventlet.debug.hub_prevent_multiple_readers(False)

    @abc.abstractproperty
    def _dns_application(self):
        pass

    def start(self):
        super(DNSService, self).start()

        self._dns_sock_tcp = dnsutils.bind_tcp(
            self._service_config.host,
            self._service_config.port,
            self._service_config.tcp_backlog)

        self._dns_sock_udp = dnsutils.bind_udp(
            self._service_config.host,
            self._service_config.port)

        self.tg.add_thread(self._dns_handle_tcp)
        self.tg.add_thread(self._dns_handle_udp)

    def wait(self):
        super(DNSService, self).wait()

    def stop(self):
        # When the service is stopped, the threads for _handle_tcp and
        # _handle_udp are stopped too.
        super(DNSService, self).stop()

        if hasattr(self, '_dns_sock_tcp'):
            self._dns_sock_tcp.close()

        if hasattr(self, '_dns_sock_udp'):
            self._dns_sock_udp.close()

    def _dns_handle_tcp(self):
        LOG.info(_LI("_handle_tcp thread started"))

        while True:
            try:
                client, addr = self._dns_sock_tcp.accept()

                if self._service_config.tcp_recv_timeout:
                    client.settimeout(self._service_config.tcp_recv_timeout)

                LOG.debug("Handling TCP Request from: %(host)s:%(port)d" %
                          {'host': addr[0], 'port': addr[1]})

                # Prepare a variable for the payload to be buffered
                payload = ""

                # Receive the first 2 bytes containing the payload length
                expected_length_raw = client.recv(2)
                (expected_length, ) = struct.unpack('!H', expected_length_raw)

                # Keep receiving data until we've got all the data we expect
                while len(payload) < expected_length:
                    data = client.recv(65535)
                    if not data:
                        break
                    payload += data

            except socket.error as e:
                client.close()
                errname = errno.errorcode[e.args[0]]
                LOG.warn(_LW("Socket error %(err)s from: %(host)s:%(port)d") %
                         {'host': addr[0], 'port': addr[1], 'err': errname})

            except socket.timeout:
                client.close()
                LOG.warn(_LW("TCP Timeout from: %(host)s:%(port)d") %
                         {'host': addr[0], 'port': addr[1]})

            except struct.error:
                client.close()
                LOG.warn(_LW("Invalid packet from: %(host)s:%(port)d") %
                         {'host': addr[0], 'port': addr[1]})

            except Exception:
                client.close()
                LOG.exception(_LE("Unknown exception handling TCP request "
                                  "from: %(host)s:%(port)d") %
                              {'host': addr[0], 'port': addr[1]})

            else:
                # Dispatch a thread to handle the query
                self.tg.add_thread(self._dns_handle, addr, payload,
                                   client=client)

    def _dns_handle_udp(self):
        LOG.info(_LI("_handle_udp thread started"))

        while True:
            try:
                # TODO(kiall): Determine the appropriate default value for
                #              UDP recvfrom.
                payload, addr = self._dns_sock_udp.recvfrom(8192)

                LOG.debug("Handling UDP Request from: %(host)s:%(port)d" %
                         {'host': addr[0], 'port': addr[1]})

                # Dispatch a thread to handle the query
                self.tg.add_thread(self._dns_handle, addr, payload)

            except socket.error as e:
                errname = errno.errorcode[e.args[0]]
                LOG.warn(_LW("Socket error %(err)s from: %(host)s:%(port)d") %
                         {'host': addr[0], 'port': addr[1], 'err': errname})

            except Exception:
                LOG.exception(_LE("Unknown exception handling UDP request "
                                  "from: %(host)s:%(port)d") %
                              {'host': addr[0], 'port': addr[1]})

    def _dns_handle(self, addr, payload, client=None):
        """
        Handle a DNS Query

        :param addr: Tuple of the client's (IP, Port)
        :param payload: Raw DNS query payload
        :param client: Client socket (for TCP only)
        """
        try:
            # Call into the DNS Application itself with the payload and addr
            for response in self._dns_application(
                    {'payload': payload, 'addr': addr}):

                # Send back a response only if present
                if response is not None:
                    if client:
                        # Handle TCP Responses
                        msg_length = len(response)
                        tcp_response = struct.pack("!H", msg_length) + response
                        client.send(tcp_response)
                    else:
                        # Handle UDP Responses
                        self._dns_sock_udp.sendto(response, addr)

            # Close the TCP connection if we have one.
            if client:
                client.close()

        except Exception:
            LOG.exception(_LE("Unhandled exception while processing request "
                              "from %(host)s:%(port)d") %
                          {'host': addr[0], 'port': addr[1]})

_launcher = None


def serve(server, workers=None):
    global _launcher
    if _launcher:
        raise RuntimeError(_('serve() can only be called once'))

    _launcher = service.launch(CONF, server, workers=workers)


def wait():
    try:
        _launcher.wait()
    except KeyboardInterrupt:
        LOG.debug('Caught KeyboardInterrupt, shutting down now')
    rpc.cleanup()
