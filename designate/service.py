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

import six
import eventlet.wsgi
import eventlet.debug
import oslo_messaging as messaging
from oslo_config import cfg
from oslo_log import log as logging
from oslo_service import service
from oslo_service import sslutils
from oslo_utils import netutils

from designate.i18n import _
from designate.i18n import _LE
from designate.i18n import _LI
from designate.i18n import _LW
from designate.metrics import metrics
from designate import policy
from designate import rpc
from designate import service_status
from designate import version
from designate import utils


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
        metrics.init()

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

        LOG.info(_('Starting %(name)s service (version: %(version)s)'),
                 {'name': self.service_name,
                  'version': version.version_info.version_string()})

    def stop(self):
        LOG.info(_('Stopping %(name)s service'), {'name': self.service_name})

        super(Service, self).stop()

    def _get_listen_on_addresses(self, default_port):
        """
        Helper Method to handle migration from singular host/port to
        multiple binds
        """
        try:
            # The API service uses "api_host", and "api_port", others use
            # just host and port.
            host = self._service_config.api_host
            port = self._service_config.api_port

        except cfg.NoSuchOptError:
            host = self._service_config.host
            port = self._service_config.port

        if host or port is not None:
            LOG.warning(_LW("host and port config options used, the 'listen' "
                            "option has been ignored"))

            host = host or "0.0.0.0"
            # "port" might be 0 to pick a free port, usually during testing
            port = default_port if port is None else port

            return [(host, port)]

        else:

            return map(
                netutils.parse_host_port,
                set(self._service_config.listen)
            )


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

        emitter_cls = service_status.HeartBeatEmitter.get_driver(
            cfg.CONF.heartbeat_emitter.emitter_type
        )
        self.heartbeat_emitter = emitter_cls(
            self.service_name, self.tg, status_factory=self._get_status
        )

    def _get_status(self):
        status = "UP"
        stats = {}
        capabilities = {}
        return status, stats, capabilities

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

        self.heartbeat_emitter.start()

    def stop(self):
        LOG.debug("Stopping RPC server on topic '%s'" % self._rpc_topic)
        self.heartbeat_emitter.stop()

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

        self._wsgi_socks = []

    @abc.abstractproperty
    def _wsgi_application(self):
        pass

    def start(self):
        super(WSGIService, self).start()

        addresses = self._get_listen_on_addresses(9001)

        for address in addresses:
            self._start(address[0], address[1])

    def _start(self, host, port):
        wsgi_sock = utils.bind_tcp(
            host, port, CONF.backlog, CONF.tcp_keepidle)

        if sslutils.is_enabled(CONF):
            wsgi_sock = sslutils.wrap(CONF, wsgi_sock)

        self._wsgi_socks.append(wsgi_sock)

        self.tg.add_thread(self._wsgi_handle, wsgi_sock)

    def _wsgi_handle(self, wsgi_sock):
        logger = logging.getLogger('eventlet.wsgi')
        # Adjust wsgi MAX_HEADER_LINE to accept large tokens.
        eventlet.wsgi.MAX_HEADER_LINE = self._service_config.max_header_line

        eventlet.wsgi.server(wsgi_sock,
                             self._wsgi_application,
                             custom_pool=self.tg.pool,
                             log=logger)


@six.add_metaclass(abc.ABCMeta)
class DNSService(object):
    """
    DNS Service mixin used by all Designate DNS Services
    """

    _TCP_RECV_MAX_SIZE = 65535

    def __init__(self, *args, **kwargs):
        super(DNSService, self).__init__(*args, **kwargs)

        # Eventet will complain loudly about our use of multiple greentheads
        # reading/writing to the UDP socket at once. Disable this warning.
        eventlet.debug.hub_prevent_multiple_readers(False)

        self._dns_socks_tcp = []
        self._dns_socks_udp = []

    @abc.abstractproperty
    def _dns_application(self):
        pass

    def start(self):
        super(DNSService, self).start()

        addresses = self._get_listen_on_addresses(self._dns_default_port)

        for address in addresses:
            self._start(address[0], address[1])

    def _start(self, host, port):
        sock_tcp = utils.bind_tcp(
            host, port, self._service_config.tcp_backlog)

        sock_udp = utils.bind_udp(
            host, port)

        self._dns_socks_tcp.append(sock_tcp)
        self._dns_socks_udp.append(sock_udp)

        self.tg.add_thread(self._dns_handle_tcp, sock_tcp)
        self.tg.add_thread(self._dns_handle_udp, sock_udp)

    def wait(self):
        super(DNSService, self).wait()

    def stop(self):
        # When the service is stopped, the threads for _handle_tcp and
        # _handle_udp are stopped too.
        super(DNSService, self).stop()

        for sock_tcp in self._dns_socks_tcp:
            sock_tcp.close()

        for sock_udp in self._dns_socks_udp:
            sock_udp.close()

    def _dns_handle_tcp(self, sock_tcp):
        LOG.info(_LI("_handle_tcp thread started"))

        while True:
            try:
                # handle a new TCP connection
                client, addr = sock_tcp.accept()

                if self._service_config.tcp_recv_timeout:
                    client.settimeout(self._service_config.tcp_recv_timeout)

                LOG.debug("Handling TCP Request from: %(host)s:%(port)d" %
                          {'host': addr[0], 'port': addr[1]})
                if len(addr) == 4:
                    LOG.debug("Flow info: %(host)s scope: %(port)d" %
                              {'host': addr[2], 'port': addr[3]})

                # Dispatch a thread to handle the connection
                self.tg.add_thread(self._dns_handle_tcp_conn, addr, client)

            # NOTE: Any uncaught exceptions will result in the main loop
            # ending unexpectedly. Ensure proper ordering of blocks, and
            # ensure no exceptions are generated from within.
            except socket.timeout:
                client.close()
                LOG.warning(_LW("TCP Timeout from: %(host)s:%(port)d") %
                            {'host': addr[0], 'port': addr[1]})

            except socket.error as e:
                client.close()
                errname = errno.errorcode[e.args[0]]
                LOG.warning(
                    _LW("Socket error %(err)s from: %(host)s:%(port)d") %
                    {'host': addr[0], 'port': addr[1], 'err': errname})

            except Exception:
                client.close()
                LOG.exception(_LE("Unknown exception handling TCP request "
                                  "from: %(host)s:%(port)d") %
                              {'host': addr[0], 'port': addr[1]})

    def _dns_handle_tcp_conn(self, addr, client):
        """
        Handle a DNS Query over TCP. Multiple queries can be pipelined
        through the same TCP connection but they will be processed
        sequentially.
        See https://tools.ietf.org/html/draft-ietf-dnsop-5966bis-03
        Raises no exception: it's to be run in an eventlet green thread

        :param addr: Tuple of the client's (IPv4 addr, Port) or
                     (IPv6 addr, Port, Flow info, Scope ID)
        :type addr: tuple
        :param client: Client socket
        :type client: socket
        :raises: None
        """
        host, port = addr[:2]
        try:
            # The whole loop lives in a try/except block. On exceptions, the
            # connection is closed: there would be little chance to save
            # the connection after a struct error, a socket error.
            while True:
                # Decode the first 2 bytes containing the query length
                expected_length_raw = client.recv(2)
                if len(expected_length_raw) == 0:
                    break
                (expected_length, ) = struct.unpack('!H', expected_length_raw)

                # Keep receiving data until we've got all the data we expect
                # The buffer contains only one query at a time
                buf = b''
                while len(buf) < expected_length:
                    recv_size = min(expected_length - len(buf),
                                    self._TCP_RECV_MAX_SIZE)
                    data = client.recv(recv_size)
                    if not data:
                        break
                    buf += data

                query = buf

                # Call into the DNS Application itself with payload and addr
                for response in self._dns_application(
                        {'payload': query, 'addr': addr}):

                    # Send back a response only if present
                    if response is None:
                        continue

                    # Handle TCP Responses
                    msg_length = len(response)
                    tcp_response = struct.pack("!H", msg_length) + response
                    client.sendall(tcp_response)

        except socket.timeout:
            LOG.info(_LI("TCP Timeout from: %(host)s:%(port)d"),
                     {'host': host, 'port': port})

        except socket.error as e:
            errname = errno.errorcode[e.args[0]]
            LOG.warning(_LW("Socket error %(err)s from: %(host)s:%(port)d"),
                        {'host': host, 'port': port, 'err': errname})

        except struct.error:
            LOG.warning(_LW("Invalid packet from: %(host)s:%(port)d"),
                        {'host': host, 'port': port})

        except Exception:
            LOG.exception(_LE("Unknown exception handling TCP request "
                              "from: %(host)s:%(port)d"),
                          {'host': host, 'port': port})
        finally:
            client.close()

    def _dns_handle_udp(self, sock_udp):
        """Handle a DNS Query over UDP in a dedicated thread

        :param sock_udp: UDP socket
        :type sock_udp: socket
        :raises: None
        """
        LOG.info(_LI("_handle_udp thread started"))

        while True:
            try:
                # TODO(kiall): Determine the appropriate default value for
                #              UDP recvfrom.
                payload, addr = sock_udp.recvfrom(8192)

                LOG.debug("Handling UDP Request from: %(host)s:%(port)d" %
                         {'host': addr[0], 'port': addr[1]})

                # Dispatch a thread to handle the query
                self.tg.add_thread(self._dns_handle_udp_query, sock_udp, addr,
                                   payload)

            except socket.error as e:
                errname = errno.errorcode[e.args[0]]
                LOG.warning(
                    _LW("Socket error %(err)s from: %(host)s:%(port)d") %
                    {'host': addr[0], 'port': addr[1], 'err': errname})

            except Exception:
                LOG.exception(_LE("Unknown exception handling UDP request "
                                  "from: %(host)s:%(port)d") %
                              {'host': addr[0], 'port': addr[1]})

    def _dns_handle_udp_query(self, sock, addr, payload):
        """
        Handle a DNS Query over UDP

        :param sock: UDP socket
        :type sock: socket
        :param addr: Tuple of the client's (IP, Port)
        :type addr: tuple
        :param payload: Raw DNS query payload
        :type payload: string
        :raises: None
        """
        try:
            # Call into the DNS Application itself with the payload and addr
            for response in self._dns_application(
                    {'payload': payload, 'addr': addr}):

                # Send back a response only if present
                if response is not None:
                    sock.sendto(response, addr)

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
