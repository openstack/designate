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

import oslotest.base

from designate.common import profiler
from designate import policy
from designate import rpc
from designate import service as designate_service


@mock.patch.object(policy, 'init')
@mock.patch.object(rpc, 'init')
@mock.patch.object(profiler, 'setup_profiler')
class TestDesignateServiceInit(oslotest.base.BaseTestCase):
    def test_service_init(self, mock_setup_profiler, mock_rpc_init,
                          mock_policy_init):
        service = designate_service.Service('test-service')

        mock_policy_init.assert_called_once()
        mock_rpc_init.assert_called_once()
        mock_setup_profiler.assert_called_once()

        self.assertEqual('test-service', service.name)

    def test_rpc_service_init(self, mock_setup_profiler, mock_rpc_init,
                              mock_policy_init):
        service = designate_service.RPCService(
            'test-rpc-service', 'test-topic'
        )

        mock_policy_init.assert_called_once()
        mock_rpc_init.assert_called_once()
        mock_setup_profiler.assert_called_once()

        self.assertEqual([service], service.endpoints)
        self.assertEqual('test-topic', service.rpc_topic)
        self.assertEqual('test-rpc-service', service.name)


class TestDesignateRpcService(oslotest.base.BaseTestCase):
    @mock.patch.object(policy, 'init')
    @mock.patch.object(rpc, 'init')
    @mock.patch.object(profiler, 'setup_profiler')
    def setUp(self, mock_setup_profiler, mock_rpc_init,
              mock_policy_init):
        super(TestDesignateRpcService, self).setUp()
        self.service = designate_service.RPCService(
            'test-rpc-service', 'test-topic'
        )

        mock_policy_init.assert_called_once()
        mock_rpc_init.assert_called_once()
        mock_setup_profiler.assert_called_once()

    @mock.patch.object(rpc, 'get_server')
    @mock.patch.object(rpc, 'get_notifier')
    def test_rpc_service_start(self, mock_rpc_get_server,
                               mock_rpc_get_notifier):
        self.assertIsNone(self.service.start())

        mock_rpc_get_server.assert_called_once()
        mock_rpc_get_notifier.assert_called_once()

        self.service.rpc_server.start.assert_called_once()

    @mock.patch.object(rpc, 'get_server')
    @mock.patch.object(rpc, 'get_notifier')
    def test_rpc_service_stop(self, mock_rpc_get_server,
                              mock_rpc_get_notifier):
        self.assertIsNone(self.service.start())

        mock_rpc_get_server.assert_called_once()
        mock_rpc_get_notifier.assert_called_once()

        self.assertIsNone(self.service.stop())

        self.service.rpc_server.stop.assert_called_once()

    def test_rpc_service_wait(self):
        self.assertIsNone(self.service.wait())
