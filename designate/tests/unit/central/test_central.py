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

from designate.central import service
from designate.common import profiler
import designate.conf
from designate import exceptions
from designate.objects import record
from designate.objects import zone
from designate import policy
from designate import rpc


CONF = designate.conf.CONF


class CentralTestCase(oslotest.base.BaseTestCase):
    @mock.patch.object(policy, 'init')
    @mock.patch.object(rpc, 'init')
    @mock.patch.object(rpc, 'initialized')
    @mock.patch.object(profiler, 'setup_profiler')
    def setUp(self, mock_setup_profiler, mock_rpc_initialized,
              mock_rpc_init, mock_policy_init):
        super().setUp()

        mock_rpc_initialized.return_value = False

        self.storage = mock.Mock()

        self.service = service.Service()
        self.service.coordination = mock.Mock()
        self.service._storage = self.storage
        self.context = mock.Mock()

        mock_setup_profiler.assert_called()
        mock_rpc_init.assert_called()
        mock_policy_init.assert_called()

    @mock.patch.object(rpc, 'get_server')
    @mock.patch.object(rpc, 'get_notifier')
    def test_service_start(self, mock_get_notifier, mock_get_server):
        self.service.start()

        mock_get_server.assert_called()
        mock_get_notifier.assert_called_with('central')
        self.service.coordination.start.assert_called()

    @mock.patch.object(rpc, 'get_server')
    @mock.patch.object(rpc, 'get_notifier')
    def test_service_start_with_managed_tenant_id_set(self, mock_get_notifier,
                                                      mock_get_server):
        CONF.set_override(
            'managed_resource_tenant_id',
            '24d1c4be-eb2d-44bb-bc49-fc5eced95e3d',
            'service:central'
        )

        self.service.start()

        mock_get_server.assert_called()
        mock_get_notifier.assert_called_with('central')
        self.service.coordination.start.assert_called()

    def test_is_valid_project_id(self):
        self.assertIsNone(self.service._is_valid_project_id('1'))

    def test_is_valid_project_id_missing_project_id(self):
        self.assertRaisesRegex(
            exceptions.MissingProjectID,
            'A project ID must be specified when not using a project '
            'scoped token.',
            self.service._is_valid_project_id, None
        )

    def test_is_valid_zone_name_invalid_object(self):
        self.assertRaisesRegex(
            exceptions.InvalidObject,
            '',
            self.service._is_valid_zone_name, self.context, None
        )

    def test_list_to_dict(self):
        result = self.service._list_to_dict([{'region': 'foo', 'id': '1'}])
        self.assertEqual(('1',), result.popitem()[0])

    def test_check_zone_share_permission_raise_when_not_shared(self):
        new_zone = zone.Zone()
        new_zone.tenant_id = '2'
        self.context.project_id = '1'
        self.context.all_tenants = False
        self.storage.is_zone_shared_with_project.return_value = False

        self.assertRaisesRegex(
            exceptions.ZoneNotFound, 'Could not find Zone',
            self.service._check_zone_share_permission, self.context, new_zone
        )


class ZoneAndRecordStatusTestCase(oslotest.base.BaseTestCase):
    @mock.patch.object(policy, 'init')
    @mock.patch.object(rpc, 'init')
    @mock.patch.object(rpc, 'initialized')
    @mock.patch.object(profiler, 'setup_profiler')
    def setUp(self, mock_setup_profiler, mock_rpc_initialized,
              mock_rpc_init, mock_policy_init):
        super().setUp()

        mock_rpc_initialized.return_value = False

        self.service = service.Service()

        mock_setup_profiler.assert_called()
        mock_rpc_init.assert_called()
        mock_policy_init.assert_called()

    def test_success_pending(self):
        new_zone = zone.Zone(action='CREATE', status='PENDING', serial=100)
        result = self.service._update_zone_or_record_status(
            new_zone, 'SUCCESS', 101
        )

        self.assertEqual('ACTIVE', result.status)
        self.assertEqual('NONE', result.action)

        new_record = record.Record(action='CREATE', status='PENDING',
                                   serial=100)
        result = self.service._update_zone_or_record_status(
            new_record, 'SUCCESS', 101
        )

        self.assertEqual('ACTIVE', result.status)
        self.assertEqual('NONE', result.action)

    def test_success_error(self):
        new_zone = zone.Zone(action='CREATE', status='ERROR', serial=100)
        result = self.service._update_zone_or_record_status(
            new_zone, 'SUCCESS', 101
        )

        self.assertEqual('ACTIVE', result.status)
        self.assertEqual('NONE', result.action)

        new_record = record.Record(action='CREATE', status='ERROR', serial=100)
        result = self.service._update_zone_or_record_status(
            new_record, 'SUCCESS', 101
        )

        self.assertEqual('ACTIVE', result.status)
        self.assertEqual('NONE', result.action)

    def test_success_delete(self):
        new_zone = zone.Zone(action='DELETE', status='PENDING', serial=100)
        result = self.service._update_zone_or_record_status(
            new_zone, 'SUCCESS', 101
        )

        self.assertEqual('DELETED', result.status)
        self.assertEqual('NONE', result.action)

        new_record = record.Record(action='DELETE', status='PENDING',
                                   serial=100)
        result = self.service._update_zone_or_record_status(
            new_record, 'SUCCESS', 101
        )

        self.assertEqual('DELETED', result.status)
        self.assertEqual('NONE', result.action)

    def test_success_do_nothing(self):
        new_zone = zone.Zone(action='CREATE', status='PENDING', serial=2)
        result = self.service._update_zone_or_record_status(
            new_zone, 'SUCCESS', 1
        )

        self.assertEqual('PENDING', result.status)
        self.assertEqual('CREATE', result.action)

        new_record = record.Record(action='NONE', status='PENDING', serial=100)
        result = self.service._update_zone_or_record_status(
            new_record, 'SUCCESS', 101
        )

        self.assertEqual('PENDING', result.status)
        self.assertEqual('NONE', result.action)

    def test_error_pending(self):
        new_zone = zone.Zone(action='CREATE', status='PENDING', serial=1)
        result = self.service._update_zone_or_record_status(
            new_zone, 'ERROR', 2
        )

        self.assertEqual('ERROR', result.status)
        self.assertEqual('CREATE', result.action)

        new_record = record.Record(action='DELETE', status='PENDING', serial=1)
        result = self.service._update_zone_or_record_status(
            new_record, 'ERROR', 2
        )

        self.assertEqual('ERROR', result.status)
        self.assertEqual('DELETE', result.action)

    def test_error_pending_do_nothing(self):
        new_zone = zone.Zone(action='CREATE', status='PENDING', serial=100)
        result = self.service._update_zone_or_record_status(
            new_zone, 'ERROR', 0
        )

        self.assertEqual('ERROR', result.status)
        self.assertEqual('CREATE', result.action)

        new_record = record.Record(action='CREATE', status='PENDING',
                                   serial=100)
        result = self.service._update_zone_or_record_status(
            new_record, 'ERROR', 0
        )

        self.assertEqual('ERROR', result.status)
        self.assertEqual('CREATE', result.action)

    def test_error_create_do_nothing(self):
        new_zone = zone.Zone(action='CREATE', status='ACTIVE', serial=1)
        result = self.service._update_zone_or_record_status(
            new_zone, 'ERROR', 2
        )

        self.assertEqual('ACTIVE', result.status)
        self.assertEqual('CREATE', result.action)

        new_record = record.Record(action='CREATE', status='ACTIVE', serial=1)
        result = self.service._update_zone_or_record_status(
            new_record, 'ERROR', 2
        )

        self.assertEqual('ACTIVE', result.status)
        self.assertEqual('CREATE', result.action)

    def test_no_zone_create(self):
        new_zone = zone.Zone(action='CREATE', status='PENDING', serial=100)
        result = self.service._update_zone_or_record_status(
            new_zone, 'NO_ZONE', 1
        )

        self.assertEqual('ERROR', result.status)
        self.assertEqual('CREATE', result.action)

        new_record = record.Record(action='CREATE', status='PENDING',
                                   serial=100)
        result = self.service._update_zone_or_record_status(
            new_record, 'NO_ZONE', 1
        )

        self.assertEqual('ERROR', result.status)
        self.assertEqual('CREATE', result.action)

    def test_no_zone_update(self):
        new_zone = zone.Zone(action='UPDATE', status='PENDING', serial=100)
        result = self.service._update_zone_or_record_status(
            new_zone, 'NO_ZONE', 1
        )

        self.assertEqual('ERROR', result.status)
        self.assertEqual('CREATE', result.action)

        new_record = record.Record(action='UPDATE', status='PENDING',
                                   serial=100)
        result = self.service._update_zone_or_record_status(
            new_record, 'NO_ZONE', 1
        )

        self.assertEqual('ERROR', result.status)
        self.assertEqual('CREATE', result.action)

    def test_no_zone_delete(self):
        new_zone = zone.Zone(action='DELETE', status='PENDING', serial=100)
        result = self.service._update_zone_or_record_status(
            new_zone, 'NO_ZONE', 1
        )

        self.assertEqual('DELETED', result.status)
        self.assertEqual('NONE', result.action)

        new_record = record.Record(action='DELETE', status='PENDING',
                                   serial=100)
        result = self.service._update_zone_or_record_status(
            new_record, 'NO_ZONE', 1
        )

        self.assertEqual('DELETED', result.status)
        self.assertEqual('NONE', result.action)

    def test_no_zone_do_nothing(self):
        new_zone = zone.Zone(action='NONE', status='SUCCESS', serial=100)
        result = self.service._update_zone_or_record_status(
            new_zone, 'NO_ZONE', 1
        )

        self.assertEqual('SUCCESS', result.status)
        self.assertEqual('NONE', result.action)

        new_record = record.Record(action='NONE', status='ACTIVE', serial=100)
        result = self.service._update_zone_or_record_status(
            new_record, 'NO_ZONE', 1
        )

        self.assertEqual('ACTIVE', result.status)
        self.assertEqual('NONE', result.action)

    def test_do_nothing(self):
        new_zone = zone.Zone(action='NONE', status='SUCCESS', serial=100)
        result = self.service._update_zone_or_record_status(
            new_zone, None, None
        )

        self.assertEqual('SUCCESS', result.status)
        self.assertEqual('NONE', result.action)

        new_record = record.Record(action='NONE', status='ACTIVE', serial=100)
        result = self.service._update_zone_or_record_status(
            new_record, None, None
        )

        self.assertEqual('ACTIVE', result.status)
        self.assertEqual('NONE', result.action)
