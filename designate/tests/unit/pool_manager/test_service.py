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
import time
from datetime import datetime

import mock

from designate import exceptions
from designate import objects
from designate import tests
from designate.pool_manager import service

POOL_DICT = {
    'also_notifies': [
        {
            'host': u'192.0.2.4',
            'pool_id': u'cf2e8eab-76cd-4162-bf76-8aeee3556de0',
            'port': 53,
        }
    ],
    'attributes': [],
    'description': u'Default PowerDNS Pool',
    'id': u'cf2e8eab-76cd-4162-bf76-8aeee3556de0',
    'name': u'default',
    'nameservers': [
        {
            'host': u'192.0.2.2',
            'pool_id': u'cf2e8eab-76cd-4162-bf76-8aeee3556de0',
            'port': 53,
        },
        {
            'host': u'192.0.2.3',
            'pool_id': u'cf2e8eab-76cd-4162-bf76-8aeee3556de0',
            'port': 53,
        }
    ],
    'ns_records': [
        {
            'hostname': u'ns1-1.example.org.',
            'pool_id': u'cf2e8eab-76cd-4162-bf76-8aeee3556de0',
            'priority': 1,
        },
        {
            'hostname': u'ns1-2.example.org.',
            'pool_id': u'cf2e8eab-76cd-4162-bf76-8aeee3556de0',
            'priority': 2,
        }
    ],
    'provisioner': u'UNMANAGED',
    'targets': [
        {
            'description': u'PowerDNS Database Cluster',
            'masters': [],
            'options': [],
            'type': 'fake',
            'pool_id': u'cf2e8eab-76cd-4162-bf76-8aeee3556de0',
        }
    ]
}


class PoolManagerInitTest(tests.TestCase):
    def setUp(self):
        super(PoolManagerInitTest, self).setUp()
        self.service = service.Service()

    def test_init_no_pool_targets(self):
        pool_dict = dict(POOL_DICT)
        pool_dict['targets'] = []

        self.service.pool = objects.Pool.from_dict(pool_dict)
        self.assertRaises(
            exceptions.NoPoolTargetsConfigured,
            self.service._setup_target_backends
        )

    def test_service_name(self):
        self.assertEqual('pool_manager', self.service.service_name)

    @mock.patch('designate.service.RPCService.start')
    def test_start(self, mock_rpc_start):
        self.service.tg.add_timer = mock.Mock()
        self.service._pool_election = mock.Mock()

        with mock.patch.object(
                self.service.central_api,
                'get_pool',
                return_value=objects.Pool.from_dict(POOL_DICT)):
            self.service.start()

        call1 = self.service.tg.add_timer.call_args_list[0][0]
        self.assertEqual(120, call1[0])
        self.assertEqual(120, call1[-1])

        call2 = self.service.tg.add_timer.call_args_list[1][0]
        self.assertEqual(1800, call2[0])
        self.assertEqual(1800, call2[-1])

    @mock.patch.object(time, 'sleep')
    def test_constant_retries(self, mock_sleep):
        gen = service._constant_retries(5, 2)
        out = list(gen)
        self.assertEqual(
            [False, False, False, False, True],
            out
        )
        self.assertEqual(4, mock_sleep.call_count)
        mock_sleep.assert_called_with(2)


class PoolManagerTest(tests.TestCase):
    def setUp(self):
        super(PoolManagerTest, self).setUp()
        self.context = self.get_context()
        self.zone = objects.Zone(
            name="example.com.",
            type="PRIMARY",
            email="hostmaster@example.com",
            serial=1,
        )

        self.service = service.Service()
        self.service.tg.add_timer = mock.Mock()
        self.service.pool = mock.Mock()
        setattr(self.service.pool, 'targets', ())
        setattr(self.service.pool, 'also_notifies', ())
        setattr(self.service.pool, 'nameservers', ())
        self.service._pool_election = mock.Mock()
        self.service.target_backends = {}

    @mock.patch.object(service.central_api.CentralAPI, 'find_zones')
    @mock.patch.object(service.utils, 'increment_serial')
    def test_get_failed_zones(self, mock_increment_serial, mock_find_zones):
        mock_increment_serial.return_value = 1453758656

        self.service._get_failed_zones(self.context, service.DELETE_ACTION)

        call_one = mock.call(
            self.context,
            {
                'action': 'DELETE',
                'status': 'ERROR',
                'pool_id': '794ccc2c-d751-44fe-b57f-8894c9f5c842'
            }
        )

        call_two = mock.call(
            self.context,
            {
                'action': 'DELETE',
                'status': 'PENDING',
                'serial': '<1453758201',  # 1453758656-455
                'pool_id': '794ccc2c-d751-44fe-b57f-8894c9f5c842'
            }
        )

        # any_order because Mock adds some random calls in
        mock_find_zones.assert_has_calls([call_one, call_two],
                                         any_order=True)

    def test_periodic_recover(self):
        def mock_get_failed_zones(ctx, action):
            if action == service.DELETE_ACTION:
                return [self.zone] * 3
            if action == service.CREATE_ACTION:
                return [self.zone] * 4
            if action == service.UPDATE_ACTION:
                return [self.zone] * 5

        self.service._get_admin_context_all_tenants = mock.Mock(
            return_value=self.context
        )
        self.service._get_failed_zones = mock_get_failed_zones
        self.service.pool_manager_api.delete_zone = mock.Mock()
        self.service.pool_manager_api.create_zone = mock.Mock()
        self.service.pool_manager_api.update_zone = mock.Mock()

        self.service.periodic_recovery()

        self.service.pool_manager_api.delete_zone.assert_called_with(
            self.context, self.zone
        )

        self.assertEqual(
            3, self.service.pool_manager_api.delete_zone.call_count
        )

        self.service.pool_manager_api.create_zone.assert_called_with(
            self.context, self.zone
        )
        self.assertEqual(
            4, self.service.pool_manager_api.create_zone.call_count
        )

        self.service.pool_manager_api.update_zone.assert_called_with(
            self.context, self.zone
        )

        self.assertEqual(
            5, self.service.pool_manager_api.update_zone.call_count
        )

    def test_periodic_recover_exception(self):
        # Raise an exception half through the recovery

        def mock_get_failed_zones(ctx, action):
            if action == service.DELETE_ACTION:
                return [self.zone] * 3
            if action == service.CREATE_ACTION:
                return [self.zone] * 4

        self.service._get_admin_context_all_tenants = mock.Mock(
            return_value=self.context
        )
        self.service._get_failed_zones = mock_get_failed_zones
        self.service.pool_manager_api.delete_zone = mock.Mock()
        self.service.pool_manager_api.create_zone = mock.Mock(
            side_effect=Exception('oops')
        )
        self.service.pool_manager_api.update_zone = mock.Mock()

        self.service.periodic_recovery()

        self.service.pool_manager_api.delete_zone.assert_called_with(
            self.context, self.zone
        )

        self.assertEqual(
            3, self.service.pool_manager_api.delete_zone.call_count
        )

        self.service.pool_manager_api.create_zone.assert_called_with(
            self.context, self.zone
        )

        self.assertEqual(
            1, self.service.pool_manager_api.create_zone.call_count
        )

        self.assertEqual(
            0, self.service.pool_manager_api.update_zone.call_count
        )

    def test_periodic_sync(self, ):
        self.service._fetch_healthy_zones = mock.Mock(return_value=[
            objects.Zone(name='a_zone.'),
            objects.Zone(name='b_zone.'),
            objects.Zone(name='c_zone.'),
        ])

        self.service.update_zone = mock.Mock()
        self.service._exceed_or_meet_threshold = mock.Mock(return_value=True)

        self.service.periodic_sync()

        self.assertEqual(3, self.service.update_zone.call_count)

    def test_target_sync(self):
        date = 1463154200
        older_date = datetime.fromtimestamp(1463154000)
        newer_date = datetime.fromtimestamp(1463154300)

        zones = [
            objects.Zone(name='a_zone.', status='ACTIVE',
                         created_at=older_date),
            objects.Zone(name='b_zone.', status='ACTIVE',
                         created_at=newer_date),
            objects.Zone(name='c_zone.', status='DELETED',
                         created_at=older_date, serial=1),
        ]

        self.service._delete_zone_on_target = mock.Mock()
        self.service._create_zone_on_target = mock.Mock()
        self.service._update_zone_on_target = mock.Mock()
        self.service.mdns_api.poll_for_serial_number = mock.Mock()

        target = mock.Mock()

        self.service._target_sync(self.context, zones, target, date)

        self.assertEqual(1, self.service._delete_zone_on_target.call_count)
        self.assertEqual(1, self.service._create_zone_on_target.call_count)
        self.assertEqual(1, self.service._update_zone_on_target.call_count)

    def test_create_zone(self):
        self.service._exceed_or_meet_threshold = mock.Mock(return_value=True)

        self.service.create_zone(self.context, self.zone)

    def test_update_zone(self, ):
        self.service._exceed_or_meet_threshold = mock.Mock(return_value=True)

        self.service.update_zone(self.context, self.zone)

    def test_delete_zone(self):
        self.service._exceed_or_meet_threshold = mock.Mock(return_value=True)

        self.service.delete_zone(self.context, self.zone)
