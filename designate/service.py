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
import errno
import time

import six
import eventlet.wsgi
from oslo import messaging
from oslo.config import cfg
from oslo_log import log as logging
from oslo_log import loggers

from designate.openstack.common import service
from designate.openstack.common import sslutils
from designate.i18n import _
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


class RPCService(Service):
    """
    Service class to be shared by all Designate RPC Services
    """
    def __init__(self, threads=None):
        super(RPCService, self).__init__(threads)

        LOG.debug(_("Creating RPC Server on topic '%s'") % self._rpc_topic)
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

        LOG.debug(_("Starting RPC server on topic '%s'") % self._rpc_topic)
        self._rpc_server.start()

        # TODO(kiall): This probably belongs somewhere else, maybe the base
        #              Service class?
        self.notifier = rpc.get_notifier(self.service_name)

        for e in self._rpc_endpoints:
            if e != self and hasattr(e, 'start'):
                e.start()

    def stop(self):
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
class WSGIService(Service):
    """
    Service class to be shared by all Designate WSGI Services
    """
    def __init__(self, threads=None):
        super(WSGIService, self).__init__(threads)

    @abc.abstractproperty
    def _wsgi_application(self):
        pass

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
                if sslutils.is_enabled():
                    sock = sslutils.wrap(sock)

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

    def start(self):
        super(WSGIService, self).start()

        socket = self._wsgi_get_socket()
        application = self._wsgi_application

        self.tg.add_thread(self._wsgi_handle, application, socket)

    def _wsgi_handle(self, application, socket):
        logger = logging.getLogger('eventlet.wsgi')
        eventlet.wsgi.server(socket,
                             application,
                             custom_pool=self.tg.pool,
                             log=loggers.WritableLogger(logger))


@six.add_metaclass(abc.ABCMeta)
class DNSService(Service):
    """
    Service class to be used for a service that only works in TCP
    """
    def __init__(self, threads=None):
        super(DNSService, self).__init__(threads)

        self._dns_sock_tcp = dnsutils.bind_tcp(
            self._service_config.host,
            self._service_config.port,
            self._service_config.tcp_backlog)

        self._dns_sock_udp = dnsutils.bind_udp(
            self._service_config.host,
            self._service_config.port)

    @abc.abstractproperty
    def _dns_application(self):
        pass

    def start(self):
        super(DNSService, self).start()

        self.tg.add_thread(
            dnsutils.handle_tcp, self._dns_sock_tcp, self.tg, dnsutils.handle,
            self._dns_application, self._service_config.tcp_recv_timeout)

        self.tg.add_thread(
            dnsutils.handle_udp, self._dns_sock_udp, self.tg, dnsutils.handle,
            self._dns_application)

    def wait(self):
        super(DNSService, self).wait()

    def stop(self):
        # When the service is stopped, the threads for _handle_tcp and
        # _handle_udp are stopped too.
        super(DNSService, self).stop()


_launcher = None


def serve(server, workers=None):
    global _launcher
    if _launcher:
        raise RuntimeError(_('serve() can only be called once'))

    _launcher = service.launch(server, workers=workers)


def wait():
    try:
        _launcher.wait()
    except KeyboardInterrupt:
        _launcher.stop()
    rpc.cleanup()
