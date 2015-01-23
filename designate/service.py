# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Justin Santa Barbara
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
import os
import inspect

from oslo import messaging
from oslo.config import cfg
from oslo_log import log as logging

from designate.openstack.common import service
from designate.openstack.deprecated import wsgi
from designate.i18n import _
from designate import rpc
from designate import policy
from designate import version
from designate import dnsutils


CONF = cfg.CONF

LOG = logging.getLogger(__name__)


class Service(service.Service):
    """
    Service class to be shared among the diverse service inside of Designate.
    """
    def __init__(self, threads=1000):
        super(Service, self).__init__(threads)

        policy.init()

        # NOTE(kiall): All services need RPC initialized, as this is used
        #              for clients AND servers. Hence, this is common to
        #              all Designate services.
        if not rpc.initialized():
            rpc.init(CONF)


class RPCService(Service):
    """
    Service class to be shared by all Designate RPC Services
    """
    def __init__(self, host, binary, topic, service_name=None, endpoints=None):
        super(RPCService, self).__init__()

        self.host = host
        self.binary = binary
        self.topic = topic
        self.service_name = service_name

        # TODO(ekarlso): change this to be loadable via mod import or
        # stevedore?
        self.endpoints = endpoints or [self]

    def start(self):
        super(RPCService, self).start()

        version_string = version.version_info.version_string()
        LOG.info(_('Starting %(topic)s node (version %(version_string)s)') %
                 {'topic': self.topic, 'version_string': version_string})

        LOG.debug(_("Creating RPC server on topic '%s'") % self.topic)

        target = messaging.Target(topic=self.topic, server=self.host)
        self.rpcserver = rpc.get_server(target, self.endpoints)
        self.rpcserver.start()

        self.notifier = rpc.get_notifier(self.service_name)

        for e in self.endpoints:
            if e != self and hasattr(e, 'start'):
                e.start()

    @classmethod
    def create(cls, host=None, binary=None, topic=None, service_name=None,
               endpoints=None):
        """Instantiates class and passes back application object.

        :param host: defaults to CONF.host
        :param binary: defaults to basename of executable
        :param topic: defaults to bin_name - 'cinder-' part
        """
        if not host:
            host = CONF.host
        if not binary:
            binary = os.path.basename(inspect.stack()[-1][1])
        if not topic:
            name = "_".join(binary.split('-')[1:]) + '_topic'
            topic = CONF.get(name)

        service_obj = cls(host, binary, topic, service_name=service_name,
                          endpoints=endpoints)
        return service_obj

    def stop(self):
        for e in self.endpoints:
            if e != self and hasattr(e, 'stop'):
                e.stop()

        # Try to shut the connection down, but if we get any sort of
        # errors, go ahead and ignore them.. as we're shutting down anyway
        try:
            self.rpcserver.stop()
        except Exception:
            pass

        super(RPCService, self).stop()

    def wait(self):
        for e in self.endpoints:
            if e != self and hasattr(e, 'wait'):
                e.wait()

        super(RPCService, self).wait()


class WSGIService(wsgi.Service, Service):
    """
    Service class to be shared by all Designate WSGI Services
    """
    def __init__(self, application, port, host='0.0.0.0', backlog=4096,
                 threads=1000):
        # NOTE(kiall): We avoid calling super(cls, self) here, as our parent
        #              classes have different argspecs. Additionally, if we
        #              manually call both parent's __init__, the openstack
        #              common Service class's __init__ method will be called
        #              twice. As a result, we only call the designate base
        #              Service's __init__ method, and duplicate the
        #              wsgi.Service's constructor functionality here.
        #
        Service.__init__(self, threads)

        self.application = application
        self._port = port
        self._host = host
        self._backlog = backlog if backlog else CONF.backlog


class DNSService(Service):
    """
    Service class to be used for a service that only works in TCP
    """
    def __init__(self, config, host=None, binary=None, service_name=None,
                 endpoints=None, threads=1000):
        super(DNSService, self).__init__(threads)

        self.host = host
        self.binary = binary
        self.service_name = service_name

        self.endpoints = endpoints or [self]
        self.config = config

        self._sock_tcp = dnsutils.bind_tcp(
            self.config.host, self.config.port,
            self.config.tcp_backlog)

        self._sock_udp = dnsutils.bind_udp(
            self.config.host, self.config.port)

    @classmethod
    def create(cls, host=None, binary=None, service_name=None,
               endpoints=None):
        """Instantiates class and passes back application object.

        :param host: defaults to CONF.host
        :param binary: defaults to basename of executable
        """
        if not host:
            host = CONF.host
        if not binary:
            binary = os.path.basename(inspect.stack()[-1][1])

        service_obj = cls(host, binary, service_name=service_name,
                          endpoints=endpoints)
        return service_obj

    def start(self):
        for e in self.endpoints:
            if e != self and hasattr(e, 'start'):
                e.start()

        self.tg.add_thread(
            dnsutils.handle_tcp, self._sock_tcp, self.tg, dnsutils.handle,
            self.application, timeout=self.config.tcp_recv_timeout)
        self.tg.add_thread(
            dnsutils.handle_udp, self._sock_udp, self.tg, dnsutils.handle,
            self.application)

        super(DNSService, self).start()

    def stop(self):
        for e in self.endpoints:
            if e != self and hasattr(e, 'stop'):
                e.stop()

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
