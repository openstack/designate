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
import errno
import socket
import struct
import threading

import eventlet.debug
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_service import service
from oslo_service import sslutils
from oslo_service import wsgi
from oslo_utils import netutils

from designate.common.decorators import rpc as rpc_decorator
from designate.common import profiler
import designate.conf
from designate.i18n import _
from designate import policy
from designate import rpc
from designate import utils
from designate import version

CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class Service(service.Service):
    def __init__(self, name, threads=None):
        threads = threads or 1000
        super().__init__(threads)
        self.name = name
        self.host = CONF.host

        policy.init()

        if not rpc.initialized():
            rpc.init(CONF)

        profiler.setup_profiler((''.join(('designate-', self.name))),
                                self.host)

    def start(self):
        LOG.info('Starting %(name)s service (version: %(version)s)',
                 {
                     'name': self.name,
                     'version': version.version_info.version_string()
                 })
        super().start()

    def stop(self, graceful=True):
        LOG.info('Stopping %(name)s service', {'name': self.name})
        super().stop(graceful)


class RPCService(Service):
    def __init__(self, name, rpc_topic, threads=None):
        super().__init__(name, threads)
        LOG.debug("Creating RPC Server on topic '%s' for %s",
                  rpc_topic, self.name)

        self.endpoints = [self]
        self.exception_thread_local = rpc_decorator.ExceptionThreadLocal()
        self.notifier = None
        self.rpc_server = None
        self.rpc_topic = rpc_topic

    def start(self):
        super().start()
        target = messaging.Target(topic=self.rpc_topic, server=self.host)
        self.rpc_server = rpc.get_server(target, self.endpoints)
        self.rpc_server.start()
        self.notifier = rpc.get_notifier(self.name)

    def stop(self, graceful=True):
        if self.rpc_server:
            self.rpc_server.stop()
        super().stop(graceful)

    def wait(self):
        super().wait()


class WSGIService(Service):
    def __init__(self, app, name, listen, max_url_len=None):
        super().__init__(name)
        self.app = app
        self.name = name

        self.listen = listen

        self.servers = []

        for address in self.listen:
            host, port = netutils.parse_host_port(address)
            server = wsgi.Server(
                CONF, name, app,
                host=host,
                port=port,
                pool_size=CONF['service:api'].threads,
                backlog=CONF.backlog,
                use_ssl=sslutils.is_enabled(CONF),
                max_url_len=max_url_len
            )

            self.servers.append(server)

    def start(self):
        for server in self.servers:
            server.start()
        super().start()

    def stop(self, graceful=True):
        for server in self.servers:
            server.stop()
        super().stop(graceful)

    def wait(self):
        for server in self.servers:
            server.wait()
        super().wait()


class DNSService:
    _TCP_RECV_MAX_SIZE = 65535

    def __init__(self, app, tg, listen, tcp_backlog, tcp_keepidle,
                 tcp_recv_timeout):
        self._running = threading.Event()
        self.app = app
        self.tg = tg
        self.tcp_backlog = tcp_backlog
        self.tcp_keepidle = tcp_keepidle
        self.tcp_recv_timeout = tcp_recv_timeout
        self.listen = listen

        # Eventet will complain loudly about our use of multiple greentheads
        # reading/writing to the UDP socket at once. Disable this warning.
        eventlet.debug.hub_prevent_multiple_readers(False)

        self._dns_socks_tcp = []
        self._dns_socks_udp = []

    def start(self):
        self._running.set()

        addresses = map(
            netutils.parse_host_port,
            set(self.listen)
        )

        for address in addresses:
            self._start(address[0], address[1])

    def _start(self, host, port):
        sock_tcp = utils.bind_tcp(
            host, port, self.tcp_backlog, self.tcp_keepidle
        )
        sock_udp = utils.bind_udp(
            host, port
        )

        self._dns_socks_tcp.append(sock_tcp)
        self._dns_socks_udp.append(sock_udp)

        self.tg.add_thread(self._dns_handle_tcp, sock_tcp)
        self.tg.add_thread(self._dns_handle_udp, sock_udp)

    def stop(self):
        self._running.clear()

        for sock_tcp in self._dns_socks_tcp:
            sock_tcp.close()

        for sock_udp in self._dns_socks_udp:
            sock_udp.close()

    def _dns_handle_tcp(self, sock_tcp):
        LOG.info('_handle_tcp thread started')

        client = None
        while self._running.is_set():
            addr = None
            try:
                # handle a new TCP connection
                client, addr = sock_tcp.accept()

                if self.tcp_recv_timeout:
                    client.settimeout(self.tcp_recv_timeout)

                LOG.debug(
                    'Handling TCP Request from: %(host)s:%(port)d',
                    {
                        'host': addr[0],
                        'port': addr[1]
                    }
                )
                if len(addr) == 4:
                    LOG.debug(
                        'Flow info: %(host)s scope: %(port)d',
                        {
                            'host': addr[2],
                            'port': addr[3]
                        }
                    )

                # Dispatch a thread to handle the connection
                self.tg.add_thread(self._dns_handle_tcp_conn, addr, client)

            # NOTE: Any uncaught exceptions will result in the main loop
            # ending unexpectedly. Ensure proper ordering of blocks, and
            # ensure no exceptions are generated from within.
            except socket.timeout:
                pass
            except OSError as e:
                if client:
                    client.close()
                errname = errno.errorcode[e.args[0]]
                addr = addr or (None, 0)
                LOG.warning(
                    'Socket error %(err)s from: %(host)s:%(port)d',
                    {
                        'host': addr[0],
                        'port': addr[1],
                        'err': errname
                    }
                )
            except Exception:
                if client:
                    client.close()
                addr = addr or (None, 0)
                LOG.exception(
                    'Unknown exception handling TCP request from: '
                    '%(host)s:%(port)d',
                    {
                        'host': addr[0],
                        'port': addr[1]
                    }
                )

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
        :type client: socket.socket
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
                (expected_length,) = struct.unpack('!H', expected_length_raw)

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
                for response in self.app({'payload': query, 'addr': addr}):

                    # Send back a response only if present
                    if response is None:
                        continue

                    # Handle TCP Responses
                    msg_length = len(response)
                    tcp_response = struct.pack("!H", msg_length) + response
                    client.sendall(tcp_response)

        except socket.timeout:
            LOG.info(
                'TCP Timeout from: %(host)s:%(port)d',
                {
                    'host': host,
                    'port': port
                }
            )
        except OSError as e:
            errname = errno.errorcode[e.args[0]]
            LOG.warning(
                'Socket error %(err)s from: %(host)s:%(port)d',
                {
                    'host': host,
                    'port': port,
                    'err': errname
                }
            )
        except struct.error:
            LOG.warning(
                'Invalid packet from: %(host)s:%(port)d',
                {
                    'host': host,
                    'port': port
                }
            )
        except Exception:
            LOG.exception(
                'Unknown exception handling TCP request from: '
                '%(host)s:%(port)d',
                {
                    'host': host,
                    'port': port
                }
            )
        finally:
            client.close()

    def _dns_handle_udp(self, sock_udp):
        """Handle a DNS Query over UDP in a dedicated thread

        :param sock_udp: UDP socket
        :type sock_udp: socket.socket
        :raises: None
        """
        LOG.info('_handle_udp thread started')

        while self._running.is_set():
            addr = None
            try:
                # TODO(kiall): Determine the appropriate default value for
                #              UDP recvfrom.
                payload, addr = sock_udp.recvfrom(8192)

                LOG.debug(
                    'Handling UDP Request from: %(host)s:%(port)d',
                    {
                        'host': addr[0],
                        'port': addr[1]
                    }
                )

                # Dispatch a thread to handle the query
                self.tg.add_thread(self._dns_handle_udp_query, sock_udp, addr,
                                   payload)
            except socket.timeout:
                pass
            except OSError as e:
                errname = errno.errorcode[e.args[0]]
                addr = addr or (None, 0)
                LOG.warning(
                    'Socket error %(err)s from: %(host)s:%(port)d',
                    {
                        'host': addr[0],
                        'port': addr[1],
                        'err': errname
                    }
                )
            except Exception:
                addr = addr or (None, 0)
                LOG.exception(
                    'Unknown exception handling UDP request from: '
                    '%(host)s:%(port)d',
                    {
                        'host': addr[0],
                        'port': addr[1]
                    }
                )

    def _dns_handle_udp_query(self, sock, addr, payload):
        """
        Handle a DNS Query over UDP

        :param sock: UDP socket
        :type sock: socket.socket
        :param addr: Tuple of the client's (IP, Port)
        :type addr: tuple
        :param payload: Raw DNS query payload
        :type payload: string
        :raises: None
        """
        try:
            # Call into the DNS Application itself with the payload and addr
            for response in self.app({'payload': payload, 'addr': addr}):
                if response is not None:
                    sock.sendto(response, addr)
        except Exception:
            LOG.exception(
                'Unhandled exception while processing request from '
                '%(host)s:%(port)d',
                {
                    'host': addr[0],
                    'port': addr[1]
                }
            )


_launcher = None


def serve(server, workers=None):
    global _launcher
    if _launcher:
        raise RuntimeError(_('serve() can only be called once'))

    _launcher = service.launch(CONF, server, workers=workers,
                               restart_method='mutate')


def wait():
    try:
        _launcher.wait()
    except KeyboardInterrupt:
        LOG.debug('Caught KeyboardInterrupt, shutting down now')
    rpc.cleanup()
