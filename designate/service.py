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

from designate.openstack.common import service
from designate.openstack.common import log as logging
from designate.openstack.common.gettextutils import _
from designate import rpc
from designate import version

CONF = cfg.CONF

LOG = logging.getLogger(__name__)


class Service(service.Service):
    """
    Service class to be shared among the diverse service inside of Designate.

    Partially inspired by the code at cinder.service but for now without
    support for loading so called "endpoints" or "managers".
    """
    def __init__(self, host, binary, topic, service_name=None, manager=None):
        super(Service, self).__init__()

        if not rpc.initialized():
            rpc.init(CONF)

        self.host = host
        self.binary = binary
        self.topic = topic
        self.service_name = service_name

        # TODO(ekarlso): change this to be loadable via mod import or
        # stevedore?
        self.manager = manager or self

    def start(self):
        version_string = version.version_info.version_string()
        LOG.audit(_('Starting %(topic)s node (version %(version_string)s)'),
                  {'topic': self.topic, 'version_string': version_string})

        LOG.debug(_("Creating RPC server on topic '%s'") % self.topic)

        manager = self.manager or self
        endpoints = [manager]
        if hasattr(manager, 'additional_endpoints'):
            endpoints.extend(self.manager.additional_endpoints)

        target = messaging.Target(topic=self.topic, server=self.host)
        self.rpcserver = rpc.get_server(target, endpoints)
        self.rpcserver.start()

        self.notifier = rpc.get_notifier(self.service_name)

    @classmethod
    def create(cls, host=None, binary=None, topic=None, service_name=None,
               manager=None):
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
                          manager=manager)
        return service_obj

    def stop(self):
        # Try to shut the connection down, but if we get any sort of
        # errors, go ahead and ignore them.. as we're shutting down anyway
        try:
            self.rpcserver.stop()
        except Exception:
            pass
        super(Service, self).stop()


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
