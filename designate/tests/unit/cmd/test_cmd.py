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
@mock.patch('oslo_log.log.setup')
@mock.patch('designate.utils.read_config')
class CmdTestCase(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

    @mock.patch('designate.api.service.Service')
    def test_api(self, mock_service, mock_read_config, mock_log_setup,
                 mock_serve, mock_wait):
        CONF.set_override('workers', 1, 'service:api')

        api.main()

        mock_read_config.assert_called_with('designate', mock.ANY)
        mock_log_setup.assert_called_with(mock.ANY, 'designate')
        mock_service.assert_called_with()
        mock_serve.assert_called_with(mock.ANY, workers=1)
        mock_wait.assert_called_with()

    @mock.patch('designate.central.service.Service')
    def test_central(self, mock_service, mock_read_config, mock_log_setup,
                     mock_serve, mock_wait):
        CONF.set_override('workers', 1, 'service:central')

        central.main()

        mock_read_config.assert_called_with('designate', mock.ANY)
        mock_log_setup.assert_called_with(mock.ANY, 'designate')
        mock_service.assert_called_with()
        mock_serve.assert_called_with(mock.ANY, workers=1)
        mock_wait.assert_called_with()

    @mock.patch('designate.mdns.service.Service')
    def test_mdns(self, mock_service, mock_read_config, mock_log_setup,
                  mock_serve, mock_wait):
        CONF.set_override('workers', 1, 'service:mdns')

        mdns.main()

        mock_read_config.assert_called_with('designate', mock.ANY)
        mock_log_setup.assert_called_with(mock.ANY, 'designate')
        mock_service.assert_called_with()
        mock_serve.assert_called_with(mock.ANY, workers=1)
        mock_wait.assert_called_with()

    @mock.patch('designate.producer.service.Service')
    def test_producer(self, mock_service, mock_read_config, mock_log_setup,
                      mock_serve, mock_wait):
        CONF.set_override('workers', 1, 'service:producer')

        producer.main()

        mock_read_config.assert_called_with('designate', mock.ANY)
        mock_log_setup.assert_called_with(mock.ANY, 'designate')
        mock_service.assert_called_with()
        mock_serve.assert_called_with(mock.ANY, workers=1)
        mock_wait.assert_called_with()

    @mock.patch('designate.sink.service.Service')
    def test_sink(self, mock_service, mock_read_config, mock_log_setup,
                  mock_serve, mock_wait):
        CONF.set_override('workers', 1, 'service:sink')

        sink.main()

        mock_read_config.assert_called_with('designate', mock.ANY)
        mock_log_setup.assert_called_with(mock.ANY, 'designate')
        mock_service.assert_called_with()
        mock_serve.assert_called_with(mock.ANY, workers=1)
        mock_wait.assert_called_with()

    @mock.patch('designate.worker.service.Service')
    def test_worker(self, mock_service, mock_read_config, mock_log_setup,
                    mock_serve, mock_wait):
        CONF.set_override('workers', 1, 'service:worker')

        worker.main()

        mock_read_config.assert_called_with('designate', mock.ANY)
        mock_log_setup.assert_called_with(mock.ANY, 'designate')
        mock_service.assert_called_with()
        mock_serve.assert_called_with(mock.ANY, workers=1)
        mock_wait.assert_called_with()

    @mock.patch('designate.api.service.Service')
    def test_api_rpc_already_initialized(self, mock_service, mock_read_config,
                                         mock_log_setup,
                                         mock_serve, mock_wait):
        CONF.set_override('workers', 1, 'service:api')

        api.main()

        mock_read_config.assert_called_with('designate', mock.ANY)
        mock_log_setup.assert_called_with(mock.ANY, 'designate')
        mock_service.assert_called_with()
        mock_serve.assert_called_with(mock.ANY, workers=1)
        mock_wait.assert_called_with()

    @mock.patch('designate.worker.service.Service')
    def test_worker_init_host_not_called_from_main(
            self, mock_service, mock_read_config, mock_log_setup,
            mock_serve, mock_wait):
        # init_host() must not be called in the parent process before
        # service.serve() forks the worker processes. Each forked worker
        # lazily calls it from its own start(), so every worker gets its
        # own RPC server instead of inheriting an unusable copy of one
        # only the parent ever started.
        CONF.set_override('workers', 1, 'service:worker')
        mock_server = mock.Mock()
        mock_service.return_value = mock_server

        worker.main()

        mock_server.init_host.assert_not_called()

    @mock.patch('designate.producer.service.Service')
    def test_producer_init_host_not_called_from_main(
            self, mock_service, mock_read_config, mock_log_setup,
            mock_serve, mock_wait):
        # See test_worker_init_host_not_called_from_main.
        CONF.set_override('workers', 1, 'service:producer')
        mock_server = mock.Mock()
        mock_service.return_value = mock_server

        producer.main()

        mock_server.init_host.assert_not_called()

    @mock.patch('designate.central.service.Service')
    def test_central_init_host_not_called_from_main(
            self, mock_service, mock_read_config, mock_log_setup,
            mock_serve, mock_wait):
        # See test_worker_init_host_not_called_from_main.
        CONF.set_override('workers', 1, 'service:central')
        mock_server = mock.Mock()
        mock_service.return_value = mock_server

        central.main()

        mock_server.init_host.assert_not_called()

    @mock.patch('designate.central.service.Service')
    def test_central_rpc_already_initialized(
            self, mock_service, mock_read_config, mock_log_setup,
            mock_serve, mock_wait):
        CONF.set_override('workers', 1, 'service:central')

        central.main()

        mock_serve.assert_called_with(mock.ANY, workers=1)

    @mock.patch('designate.mdns.service.Service')
    def test_mdns_rpc_already_initialized(
            self, mock_service, mock_read_config, mock_log_setup,
            mock_serve, mock_wait):
        CONF.set_override('workers', 1, 'service:mdns')

        mdns.main()

        mock_serve.assert_called_with(mock.ANY, workers=1)

    @mock.patch('designate.producer.service.Service')
    def test_producer_rpc_already_initialized(
            self, mock_service, mock_read_config, mock_log_setup,
            mock_serve, mock_wait):
        CONF.set_override('workers', 1, 'service:producer')

        producer.main()

        mock_serve.assert_called_with(mock.ANY, workers=1)

    @mock.patch('designate.sink.service.Service')
    def test_sink_rpc_already_initialized(
            self, mock_service, mock_read_config, mock_log_setup,
            mock_serve, mock_wait):
        CONF.set_override('workers', 1, 'service:sink')

        sink.main()

        mock_serve.assert_called_with(mock.ANY, workers=1)

    @mock.patch('designate.worker.service.Service')
    def test_worker_rpc_already_initialized(
            self, mock_service, mock_read_config, mock_log_setup,
            mock_serve, mock_wait):
        CONF.set_override('workers', 1, 'service:worker')

        worker.main()

        mock_serve.assert_called_with(mock.ANY, workers=1)
