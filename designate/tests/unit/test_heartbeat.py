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
from oslo_config import fixture as cfg_fixture

from designate import service

CONF = cfg.CONF


class HeartbeatTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super(HeartbeatTest, self).setUp()
        self.useFixture(cfg_fixture.Config(CONF))

        CONF.set_override('emitter_type', 'noop', 'heartbeat_emitter')

        self.mock_tg = mock.Mock()
        self.heartbeat = service.Heartbeat('test', self.mock_tg)

    def test_get_status(self):
        self.assertEqual(('UP', {}, {},), self.heartbeat.get_status())

    def test_get_heartbeat_emitter(self):
        self.assertEqual(
            'noop', self.heartbeat.heartbeat_emitter.__plugin_name__
        )

    def test_start_heartbeat(self):
        self.assertFalse(self.heartbeat.heartbeat_emitter._running)

        self.heartbeat.start()

        self.assertTrue(self.heartbeat.heartbeat_emitter._running)

    def test_stop_heartbeat(self):
        self.assertFalse(self.heartbeat.heartbeat_emitter._running)

        self.heartbeat.start()
        self.heartbeat.stop()

        self.assertFalse(self.heartbeat.heartbeat_emitter._running)
