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

"""
Unit-test Producer service
"""

from unittest import mock

from oslo_config import cfg
from oslo_config import fixture as cfg_fixture
import oslotest.base

from designate.producer import service
import designate.service
from designate.tests import fixtures
from designate.tests.unit import RoObject

CONF = cfg.CONF


@mock.patch.object(service.rpcapi.CentralAPI, 'get_instance', mock.Mock())
class ProducerTest(oslotest.base.BaseTestCase):
    def setUp(self):
        conf = self.useFixture(cfg_fixture.Config(CONF))
        conf.conf([], project='designate')

        service.CONF = RoObject({
            'service:producer': RoObject({
                'enabled_tasks': None,  # enable all tasks
            }),
            'producer_task:zone_purge': '',
        })
        super(ProducerTest, self).setUp()
        self.stdlog = fixtures.StandardLogging()
        self.useFixture(self.stdlog)

        self.service = service.Service()
        self.service.rpc_server = mock.Mock()
        self.service._storage = mock.Mock()
        self.service._quota = mock.Mock()
        self.service._quota.limit_check = mock.Mock()

    @mock.patch.object(service.tasks, 'PeriodicTask')
    @mock.patch.object(service.coordination, 'Partitioner')
    @mock.patch.object(designate.service.RPCService, 'start')
    def test_service_start(self, mock_rpc_start, mock_partitioner,
                           mock_periodic_task):
        self.service.coordination = mock.Mock()

        self.service.start()

        self.assertTrue(mock_rpc_start.called)

    def test_service_stop(self):
        self.service.coordination.stop = mock.Mock()

        self.service.stop()

        self.assertTrue(self.service.coordination.stop.called)

        self.assertIn('Stopping producer service', self.stdlog.logger.output)

    def test_service_name(self):
        self.assertEqual('producer', self.service.service_name)

    def test_producer_rpc_topic(self):
        CONF.set_override('topic', 'test-topic', 'service:producer')

        self.service = service.Service()

        self.assertEqual('test-topic', self.service.rpc_topic)
        self.assertEqual('producer', self.service.service_name)

    def test_central_api(self):
        self.assertIsInstance(self.service.central_api, mock.Mock)
