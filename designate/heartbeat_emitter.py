# Copyright 2016 Hewlett Packard Enterprise Development Company LP
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
import abc

from oslo_log import log as logging
from oslo_service import loopingcall
from oslo_utils import timeutils

from designate.central import rpcapi as central_rpcapi
import designate.conf
from designate import context
from designate import objects
from designate import plugin


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


def get_heartbeat_emitter(service_name, **kwargs):
    cls = HeartbeatEmitter.get_driver(
        CONF.heartbeat_emitter.emitter_type
    )
    return cls(service_name, **kwargs)


class HeartbeatEmitter(plugin.DriverPlugin):
    __plugin_ns__ = 'designate.heartbeat_emitter'
    __plugin_type__ = 'heartbeat_emitter'

    def __init__(self, service_name, **kwargs):
        super().__init__()

        self._status = 'UP'
        self._stats = {}
        self._capabilities = {}

        self._service_name = service_name
        self._hostname = CONF.host

        self._timer = loopingcall.FixedIntervalLoopingCall(
            self._emit_heartbeat
        )

    def start(self):
        self._timer.start(
            CONF.heartbeat_emitter.heartbeat_interval,
            stop_on_exception=False
        )

    def stop(self):
        self._timer.stop()

    def get_status(self):
        return self._status, self._stats, self._capabilities

    @abc.abstractmethod
    def transmit(self, status):
        """
        Transmit heartbeat
        """

    def _emit_heartbeat(self):
        """
        Returns Status, Stats, Capabilities
        """
        status, stats, capabilities = self.get_status()

        service_status = objects.ServiceStatus(
            service_name=self._service_name,
            hostname=self._hostname,
            status=status,
            stats=stats,
            capabilities=capabilities,
            heartbeated_at=timeutils.utcnow()
        )

        LOG.trace('Emitting %s', service_status)

        self.transmit(service_status)


class NoopEmitter(HeartbeatEmitter):
    __plugin_name__ = 'noop'

    def transmit(self, status):
        LOG.info(status)


class RpcEmitter(HeartbeatEmitter):
    __plugin_name__ = 'rpc'

    def __init__(self, service_name, rpc_api=None, **kwargs):
        super().__init__(service_name, **kwargs)
        self.rpc_api = rpc_api

    def transmit(self, status):
        admin_context = context.DesignateContext.get_admin_context()
        api = self.rpc_api or central_rpcapi.CentralAPI.get_instance()
        api.update_service_status(admin_context, status)
