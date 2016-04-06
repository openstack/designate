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

"""Unit-test Zone Manager service
"""

import mock
from oslotest import base as test

from designate import exceptions
from designate.tests.unit import RoObject
import designate.zone_manager.service as zms


@mock.patch.object(zms.rpcapi.CentralAPI, 'get_instance')
class ZoneManagerTest(test.BaseTestCase):

    def setUp(self):
        zms.CONF = RoObject({
            'service:zone_manager': RoObject({
                'enabled_tasks': None,  # enable all tasks
                'export_synchronous': True
            }),
            'zone_manager_task:zone_purge': '',
        })
        super(ZoneManagerTest, self).setUp()
        self.tm = zms.Service()
        self.tm._storage = mock.Mock()
        self.tm._rpc_server = mock.Mock()
        self.tm._quota = mock.Mock()
        self.tm.quota.limit_check = mock.Mock()

    def test_service_name(self, _):
        self.assertEqual('zone_manager', self.tm.service_name)

    def test_central_api(self, _):
        capi = self.tm.central_api
        assert isinstance(capi, mock.MagicMock)

    @mock.patch.object(zms.tasks, 'PeriodicTask')
    @mock.patch.object(zms.coordination, 'Partitioner')
    def test_stark(self, _, mock_partitioner, mock_PeriodicTask):
        self.tm.start()

    def test_start_zone_export(self, _):
        zone = RoObject(id=3)
        context = mock.Mock()
        export = {}
        self.tm.storage.count_recordsets.return_value = 1
        assert self.tm.storage.count_recordsets() == 1
        self.tm._determine_export_method = mock.Mock()
        self.tm.start_zone_export(context, zone, export)
        assert self.tm._determine_export_method.called
        assert self.tm.central_api.update_zone_export.called
        call_args = self.tm._determine_export_method.call_args_list[0][0]
        self.assertEqual((context, export, 1), call_args)

    def test_determine_export_method(self, _):
        context = mock.Mock()
        export = dict(location=None, id=4)
        size = mock.Mock()
        out = self.tm._determine_export_method(context, export, size)
        self.assertDictEqual(
            {
                'status': 'COMPLETE', 'id': 4,
                'location': 'designate://v2/zones/tasks/exports/4/export'
            },
            out
        )

    def test_exceed_size_quota(self, _):
        context = mock.Mock()
        export = dict(location=None, id=4)
        size = 9999999999

        self.tm.quota.limit_check.side_effect = exceptions.OverQuota()
        out = self.tm._determine_export_method(context, export, size)
        self.tm.quota.limit_check.side_effect = None

        self.assertDictEqual(
            {
                'status': 'ERROR',
                'id': 4,
                'location': None,
                'message': 'Zone is too large to export'
            },
            out
        )
