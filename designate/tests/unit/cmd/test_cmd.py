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
from unittest import mock

from oslo_config import fixture as cfg_fixture
import oslotest.base

from designate.cmd import api
from designate.cmd import central
from designate.cmd import mdns
from designate.cmd import producer
from designate.cmd import sink
from designate.cmd import worker
import designate.conf


CONF = designate.conf.CONF


@mock.patch('designate.service.wait')
@mock.patch('designate.service.serve')
@mock.patch('designate.heartbeat_emitter.get_heartbeat_emitter')
@mock.patch('oslo_log.log.setup')
@mock.patch('designate.utils.read_config')
class CmdTestCase(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

    @mock.patch('designate.api.service.Service')
    def test_api(self, mock_service, mock_read_config, mock_log_setup,
                 mock_heartbeat, mock_serve, mock_wait):
        CONF.set_override('workers', 1, 'service:api')

        api.main()

        mock_read_config.assert_called_with('designate', mock.ANY)
        mock_log_setup.assert_called_with(mock.ANY, 'designate')
        mock_service.assert_called_with()
        mock_heartbeat.assert_called()
        mock_serve.assert_called_with(mock.ANY, workers=1)
        mock_wait.assert_called_with()

    @mock.patch('designate.central.service.Service')
    def test_central(self, mock_service, mock_read_config, mock_log_setup,
                     mock_heartbeat, mock_serve, mock_wait):
        CONF.set_override('workers', 1, 'service:central')

        central.main()

        mock_read_config.assert_called_with('designate', mock.ANY)
        mock_log_setup.assert_called_with(mock.ANY, 'designate')
        mock_service.assert_called_with()
        mock_heartbeat.assert_called()
        mock_serve.assert_called_with(mock.ANY, workers=1)
        mock_wait.assert_called_with()

    @mock.patch('designate.mdns.service.Service')
    def test_mdns(self, mock_service, mock_read_config, mock_log_setup,
                  mock_heartbeat, mock_serve, mock_wait):
        CONF.set_override('workers', 1, 'service:mdns')

        mdns.main()

        mock_read_config.assert_called_with('designate', mock.ANY)
        mock_log_setup.assert_called_with(mock.ANY, 'designate')
        mock_service.assert_called_with()
        mock_heartbeat.assert_called()
        mock_serve.assert_called_with(mock.ANY, workers=1)
        mock_wait.assert_called_with()

    @mock.patch('designate.producer.service.Service')
    def test_producer(self, mock_service, mock_read_config, mock_log_setup,
                      mock_heartbeat, mock_serve, mock_wait):
        CONF.set_override('workers', 1, 'service:producer')

        producer.main()

        mock_read_config.assert_called_with('designate', mock.ANY)
        mock_log_setup.assert_called_with(mock.ANY, 'designate')
        mock_service.assert_called_with()
        mock_heartbeat.assert_called()
        mock_serve.assert_called_with(mock.ANY, workers=1)
        mock_wait.assert_called_with()

    @mock.patch('designate.sink.service.Service')
    def test_sink(self, mock_service, mock_read_config, mock_log_setup,
                  mock_heartbeat, mock_serve, mock_wait):
        CONF.set_override('workers', 1, 'service:sink')

        sink.main()

        mock_read_config.assert_called_with('designate', mock.ANY)
        mock_log_setup.assert_called_with(mock.ANY, 'designate')
        mock_service.assert_called_with()
        mock_heartbeat.assert_called()
        mock_serve.assert_called_with(mock.ANY, workers=1)
        mock_wait.assert_called_with()

    @mock.patch('designate.worker.service.Service')
    def test_worker(self, mock_service, mock_read_config, mock_log_setup,
                    mock_heartbeat, mock_serve, mock_wait):
        CONF.set_override('workers', 1, 'service:worker')

        worker.main()

        mock_read_config.assert_called_with('designate', mock.ANY)
        mock_log_setup.assert_called_with(mock.ANY, 'designate')
        mock_service.assert_called_with()
        mock_heartbeat.assert_called()
        mock_serve.assert_called_with(mock.ANY, workers=1)
        mock_wait.assert_called_with()
