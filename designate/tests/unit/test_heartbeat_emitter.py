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
import time
from unittest import mock

from oslo_config import fixture as cfg_fixture
from oslo_service import loopingcall
import oslotest.base

import designate.conf
from designate import heartbeat_emitter
from designate import objects
from designate.tests import base_fixtures


CONF = designate.conf.CONF


class HeartbeatEmitterTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(self.stdlog)
        self.useFixture(cfg_fixture.Config(CONF))

        CONF.set_override('emitter_type', 'noop', 'heartbeat_emitter')
        CONF.set_override('heartbeat_interval', 0.1, 'heartbeat_emitter')
        CONF.set_override('host', '203.0.113.1')

    @mock.patch.object(loopingcall, 'FixedIntervalLoopingCall')
    def test_start(self, mock_looping):
        mock_timer = mock.Mock()
        mock_looping.return_value = mock_timer

        noop_emitter = heartbeat_emitter.get_heartbeat_emitter('svc')

        noop_emitter.start()

        mock_timer.start.assert_called_once()

    @mock.patch.object(loopingcall, 'FixedIntervalLoopingCall')
    def test_stop(self, mock_looping):
        mock_timer = mock.Mock()
        mock_looping.return_value = mock_timer

        noop_emitter = heartbeat_emitter.get_heartbeat_emitter('svc')

        noop_emitter.start()
        noop_emitter.stop()

        mock_timer.stop.assert_called_once()

    def test_get_status(self):
        noop_emitter = heartbeat_emitter.get_heartbeat_emitter('svc')

        self.assertEqual(('UP', {}, {},), noop_emitter.get_status())

    def test_emit(self):
        noop_emitter = heartbeat_emitter.get_heartbeat_emitter('svc')

        noop_emitter.start()

        time.sleep(0.125)

        noop_emitter.stop()

        self.assertIn(
            "<ServiceStatus service_name:'svc' hostname:'203.0.113.1' "
            "status:'UP'>",
            self.stdlog.logger.output
        )


class RpcEmitterTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()

    @mock.patch.object(objects, 'ServiceStatus')
    @mock.patch('designate.context.DesignateContext.get_admin_context')
    @mock.patch.object(loopingcall, 'FixedIntervalLoopingCall')
    def test_emit_heartbeat(self, mock_looping, mock_context,
                            mock_service_status):
        mock_timer = mock.Mock()
        mock_looping.return_value = mock_timer

        emitter = heartbeat_emitter.RpcEmitter('svc')
        emitter.start()

        mock_timer.start.assert_called_once()

        central = mock.Mock()
        with mock.patch('designate.central.rpcapi.CentralAPI.get_instance',
                        return_value=central):
            emitter._emit_heartbeat()

            mock_service_status.assert_called_once_with(
                service_name='svc',
                hostname=CONF.host,
                status='UP',
                stats={},
                capabilities={},
                heartbeated_at=mock.ANY
            )

            central.update_service_status.assert_called_once_with(
                mock_context.return_value, mock_service_status.return_value
            )
