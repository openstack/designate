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
from oslo_utils import timeutils

import designate.conf
from designate import context
from designate import objects
from designate import plugin
from designate.central import rpcapi as central_rpcapi


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class HeartBeatEmitter(plugin.DriverPlugin):
    __plugin_ns__ = 'designate.heartbeat_emitter'
    __plugin_type__ = 'heartbeat_emitter'

    def __init__(self, service, thread_group, status_factory=None,
                 *args, **kwargs):
        super(HeartBeatEmitter, self).__init__()

        self._service = service
        self._hostname = CONF.host

        self._running = False
        self._tg = thread_group
        self._tg.add_timer(
            CONF.heartbeat_emitter.heartbeat_interval,
            self._emit_heartbeat)

        self._status_factory = status_factory

    def _get_status(self):
        if self._status_factory is not None:
            return self._status_factory()

        return True, {}, {}

    def _emit_heartbeat(self):
        """
        Returns Status, Stats, Capabilities
        """
        if not self._running:
            return

        status, stats, capabilities = self._get_status()

        service_status = objects.ServiceStatus(
            service_name=self._service,
            hostname=self._hostname,
            status=status,
            stats=stats,
            capabilities=capabilities,
            heartbeated_at=timeutils.utcnow()
        )

        LOG.trace("Emitting %s", service_status)

        self._transmit(service_status)

    @abc.abstractmethod
    def _transmit(self, status):
        pass

    def start(self):
        self._running = True

    def stop(self):
        self._running = False


class NoopEmitter(HeartBeatEmitter):
    __plugin_name__ = 'noop'

    def _transmit(self, status):
        LOG.debug(status)


class RpcEmitter(HeartBeatEmitter):
    __plugin_name__ = 'rpc'

    def __init__(self, service, thread_group, rpc_api=None, *args, **kwargs):
        super(RpcEmitter, self).__init__(
            service, thread_group, *args, **kwargs)
        self.rpc_api = rpc_api

    def _transmit(self, status):
        admin_context = context.DesignateContext.get_admin_context()
        api = self.rpc_api or central_rpcapi.CentralAPI.get_instance()
        api.update_service_status(admin_context, status)
