# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Federico Ceratto <federico.ceratto@hpe.com>
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


from unittest import mock

from oslo_config import fixture as cfg_fixture
import oslotest.base

import designate.conf
from designate import exceptions
from designate import policy
from designate.producer import service
from designate import rpc
import designate.service
from designate.tests import base_fixtures


CONF = designate.conf.CONF


@mock.patch.object(service.rpcapi.CentralAPI, 'get_instance', mock.Mock())
class ProducerServiceTest(oslotest.base.BaseTestCase):
    @mock.patch.object(policy, 'init')
    @mock.patch.object(rpc, 'get_client')
    @mock.patch.object(rpc, 'init')
    @mock.patch.object(rpc, 'initialized')
    def setUp(self, mock_rpc_initialized, mock_rpc_init, mock_rpc_get_client,
              mock_policy_init):
        super().setUp()

        self.useFixture(cfg_fixture.Config(CONF))
        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(self.stdlog)

        mock_rpc_initialized.return_value = False

        self.tg = mock.Mock()
        self.service = service.Service()
        self.service.coordination = mock.Mock()
        self.service.tg = self.tg

        mock_policy_init.assert_called_once()
        mock_rpc_initialized.assert_called_once()
        mock_rpc_init.assert_called_once()

    @mock.patch.object(rpc, 'get_notifier', mock.Mock())
    @mock.patch.object(service.coordination, 'Partitioner')
    @mock.patch.object(designate.service.RPCService, 'start')
    def test_service_start(self, mock_rpc_start, mock_partitioner):
        CONF.set_override('enabled_tasks', None, 'service:producer')

        mock_partition = mock.Mock()
        mock_partitioner.return_value = mock_partition

        self.service.start()

        mock_rpc_start.assert_called_with()
        mock_partition.watch_partition_change.assert_called()
        mock_partition.start.assert_called()

        # Make sure that tasks were added to the tg timer.
        self.tg.add_timer_args.assert_called()
        self.assertEqual(6, self.tg.add_timer_args.call_count)

    @mock.patch.object(service.coordination, 'Partitioner')
    @mock.patch.object(designate.service.RPCService, 'start')
    def test_service_start_all_extension_disabled(self, mock_rpc_start,
                                                  mock_partitioner):
        CONF.set_override('enabled_tasks', [], 'service:producer')
        self.assertRaisesRegex(
            exceptions.ConfigurationError,
            r'No periodic tasks found matching: \[\]',
            self.service.start,
        )

        CONF.set_override('enabled_tasks', ['None'], 'service:producer')
        self.assertRaisesRegex(
            exceptions.ConfigurationError,
            r'No periodic tasks found matching: \[\'None\'\]',
            self.service.start,
        )

    def test_service_stop(self):
        self.service.stop()

        self.service.coordination.stop.assert_called()

        self.assertIn('Stopping producer service', self.stdlog.logger.output)

    def test_service_name(self):
        self.assertEqual('producer', self.service.service_name)

    @mock.patch.object(policy, 'init', mock.Mock())
    @mock.patch.object(rpc, 'get_client', mock.Mock())
    @mock.patch.object(rpc, 'init', mock.Mock())
    @mock.patch.object(rpc, 'initialized', mock.Mock(return_value=False))
    @mock.patch.object(rpc, 'get_notifier', mock.Mock())
    def test_producer_rpc_topic(self):
        CONF.set_override('topic', 'test-topic', 'service:producer')

        self.service = service.Service()

        self.assertEqual('test-topic', self.service.rpc_topic)
        self.assertEqual('producer', self.service.service_name)

    def test_central_api(self):
        self.assertIsInstance(self.service.central_api, mock.Mock)
