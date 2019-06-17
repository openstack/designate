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

import mock
from oslo_config import cfg
from oslo_config import fixture as cfg_fixture
from oslotest import base as test

from designate.producer import service
from designate.tests.unit import RoObject

CONF = cfg.CONF


@mock.patch.object(service.rpcapi.CentralAPI, 'get_instance')
class ProducerTest(test.BaseTestCase):
    def setUp(self):
        self.useFixture(cfg_fixture.Config(CONF))

        service.CONF = RoObject({
            'service:producer': RoObject({
                'enabled_tasks': None,  # enable all tasks
            }),
            # TODO(timsim): Remove this
            'service:zone_manager': RoObject({
                'enabled_tasks': None,  # enable all tasks
                'export_synchronous': True
            }),
            'producer_task:zone_purge': '',
        })
        super(ProducerTest, self).setUp()
        self.service = service.Service()
        self.service._storage = mock.Mock()
        self.service._rpc_server = mock.Mock()
        self.service._quota = mock.Mock()
        self.service.quota.limit_check = mock.Mock()

    def test_service_name(self, _):
        self.assertEqual('producer', self.service.service_name)

    def test_producer_rpc_topic(self, _):
        CONF.set_override('topic', 'test-topic', 'service:producer')

        self.service = service.Service()

        self.assertEqual('test-topic', self.service._rpc_topic)
        self.assertEqual('producer', self.service.service_name)

    def test_central_api(self, _):
        capi = self.service.central_api
        self.assertIsInstance(capi, mock.MagicMock)

    @mock.patch.object(service.tasks, 'PeriodicTask')
    @mock.patch.object(service.coordination, 'Partitioner')
    def test_stark(self, _, mock_partitioner, mock_PeriodicTask):
        self.service.start()
