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
from oslotest import base as test

from designate.tests.unit import RoObject
import designate.producer.service as ps


@mock.patch.object(ps.rpcapi.CentralAPI, 'get_instance')
class ProducerTest(test.BaseTestCase):

    def setUp(self):
        ps.CONF = RoObject({
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
        self.tm = ps.Service()
        self.tm._storage = mock.Mock()
        self.tm._rpc_server = mock.Mock()
        self.tm._quota = mock.Mock()
        self.tm.quota.limit_check = mock.Mock()

    def test_service_name(self, _):
        self.assertEqual('producer', self.tm.service_name)

    def test_central_api(self, _):
        capi = self.tm.central_api
        assert isinstance(capi, mock.MagicMock)

    @mock.patch.object(ps.tasks, 'PeriodicTask')
    @mock.patch.object(ps.coordination, 'Partitioner')
    def test_stark(self, _, mock_partitioner, mock_PeriodicTask):
        self.tm.start()
