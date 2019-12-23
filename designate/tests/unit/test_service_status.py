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
import mock
import oslotest.base
from oslo_config import cfg
from oslo_service import loopingcall

from designate import objects
from designate import service_status


class NoopEmitterTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super(NoopEmitterTest, self).setUp()

    @mock.patch.object(loopingcall, 'FixedIntervalLoopingCall')
    def test_start(self, mock_looping):
        mock_timer = mock.Mock()
        mock_looping.return_value = mock_timer

        emitter = service_status.NoopEmitter("svc")
        emitter.start()

        mock_timer.start.assert_called_once()

    @mock.patch.object(loopingcall, 'FixedIntervalLoopingCall')
    def test_stop(self, mock_looping):
        mock_timer = mock.Mock()
        mock_looping.return_value = mock_timer

        emitter = service_status.NoopEmitter("svc")
        emitter.start()
        emitter.stop()

        mock_timer.stop.assert_called_once()


class RpcEmitterTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super(RpcEmitterTest, self).setUp()

    @mock.patch.object(objects, "ServiceStatus")
    @mock.patch("designate.context.DesignateContext.get_admin_context")
    @mock.patch.object(loopingcall, 'FixedIntervalLoopingCall')
    def test_emit_no_status_factory(self, mock_looping, mock_context,
                                    mock_service_status):
        mock_timer = mock.Mock()
        mock_looping.return_value = mock_timer

        emitter = service_status.RpcEmitter("svc")
        emitter.start()

        mock_timer.start.assert_called_once()

        central = mock.Mock()
        with mock.patch("designate.central.rpcapi.CentralAPI.get_instance",
                        return_value=central):
            emitter._emit_heartbeat()

            mock_service_status.assert_called_once_with(
                service_name="svc",
                hostname=cfg.CONF.host,
                status=True,
                stats={},
                capabilities={},
                heartbeated_at=mock.ANY
            )

            central.update_service_status.assert_called_once_with(
                mock_context.return_value, mock_service_status.return_value
            )

    @mock.patch.object(objects, "ServiceStatus")
    @mock.patch("designate.context.DesignateContext.get_admin_context")
    @mock.patch.object(loopingcall, 'FixedIntervalLoopingCall')
    def test_emit_status_factory(self, mock_looping, mock_context,
                                 mock_service_status):
        mock_timer = mock.Mock()
        mock_looping.return_value = mock_timer

        status = False
        stats = {"a": 1}
        capabilities = {"b": 2}

        status_factory = mock.Mock(return_value=(status, stats, capabilities,))
        emitter = service_status.RpcEmitter("svc",
                                            status_factory=status_factory)
        emitter.start()

        mock_timer.start.assert_called_once()

        central = mock.Mock()
        with mock.patch("designate.central.rpcapi.CentralAPI.get_instance",
                        return_value=central):
            emitter._emit_heartbeat()

            mock_service_status.assert_called_once_with(
                service_name="svc",
                hostname=cfg.CONF.host,
                status=status,
                stats=stats,
                capabilities=capabilities,
                heartbeated_at=mock.ANY
            )

            central.update_service_status.assert_called_once_with(
                mock_context.return_value, mock_service_status.return_value
            )
