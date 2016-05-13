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
Unit tests
"""
import unittest
from datetime import datetime

from mock import call
from mock import Mock
from mock import MagicMock
from mock import patch
from oslotest import base as test

from designate import exceptions
from designate import objects
from designate.pool_manager.service import Service
from designate.tests.unit import RoObject
from designate.tests.unit import RwObject
import designate.pool_manager.service as pm_module


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


class PoolManagerInitTest(test.BaseTestCase):
    def __setUp(self):
        super(PoolManagerTest, self).setUp()

    @unittest.skip("fails occasionally")
    def test_init_no_pool_targets(self):
        with patch.object(objects.Pool, 'from_config',
                          return_value=MagicMock()):
            self.assertRaises(exceptions.NoPoolTargetsConfigured, Service)

    def test_init(self):
            Service()

    def test_start(self):
        with patch.object(objects.Pool, 'from_config',
                          return_value=Mock()):
            pm = Service()
            pm.tg.add_timer = Mock()
            pm._pool_election = Mock()
            with patch("designate.service.RPCService.start"):
                with patch.object(
                        pm.central_api,
                        'get_pool',
                        return_value=objects.Pool.from_dict(POOL_DICT)):
                    pm.start()

            call1 = pm.tg.add_timer.call_args_list[0][0]
            self.assertEqual(120, call1[0])
            self.assertEqual(120, call1[-1])
            call2 = pm.tg.add_timer.call_args_list[1][0]
            self.assertEqual(1800, call2[0])
            self.assertEqual(1800, call2[-1])

    def test_constant_retries(self):
        with patch.object(pm_module.time, 'sleep') as mock_zzz:
            gen = pm_module._constant_retries(5, 2)
            out = list(gen)
            self.assertEqual(
                [False, False, False, False, True],
                out
            )
            self.assertEqual(4, mock_zzz.call_count)
            mock_zzz.assert_called_with(2)


class PoolManagerTest(test.BaseTestCase):

    @patch.object(pm_module.DesignateContext, 'get_admin_context')
    @patch.object(pm_module.central_api.CentralAPI, 'get_instance')
    @patch.object(objects.Pool, 'from_config')
    @patch.object(Service, '_setup_target_backends')
    def setUp(self, *mocks):
        super(PoolManagerTest, self).setUp()
        self.pm = Service()
        self.pm.tg.add_timer = Mock()
        self.pm.pool = Mock()
        setattr(self.pm.pool, 'targets', ())
        setattr(self.pm.pool, 'also_notifies', ())
        setattr(self.pm.pool, 'nameservers', ())
        self.pm._pool_election = Mock()
        self.pm.target_backends = {}

    def test_get_failed_zones(self, *mocks):
        with patch.object(self.pm.central_api, 'find_zones') as \
                mock_find_zones:

            with patch.object(pm_module.utils, 'increment_serial',
                              return_value=1453758656):
                self.pm._get_failed_zones('ctx', pm_module.DELETE_ACTION)

            call_one = call('ctx', {'action': 'DELETE', 'status': 'ERROR',
                                    'pool_id':
                                    '794ccc2c-d751-44fe-b57f-8894c9f5c842'})
            call_two = call('ctx', {'action': 'DELETE', 'status': 'PENDING',
                                    'serial': '<1453758201',  # 1453758656-455
                                    'pool_id':
                                    '794ccc2c-d751-44fe-b57f-8894c9f5c842'})

            # any_order because Mock adds some random calls in
            mock_find_zones.assert_has_calls([call_one, call_two],
                any_order=True)

    @patch.object(pm_module.DesignateContext, 'get_admin_context')
    def test_periodic_recover(self, mock_get_ctx, *mocks):
        z = RoObject(name='a_zone')

        def mock_get_failed_zones(ctx, action):
            if action == pm_module.DELETE_ACTION:
                return [z] * 3
            if action == pm_module.CREATE_ACTION:
                return [z] * 4
            if action == pm_module.UPDATE_ACTION:
                return [z] * 5

        self.pm._get_failed_zones = mock_get_failed_zones
        self.pm.pool_manager_api.delete_zone = Mock()
        self.pm.pool_manager_api.create_zone = Mock()
        self.pm.pool_manager_api.update_zone = Mock()
        mock_ctx = mock_get_ctx.return_value

        self.pm.periodic_recovery()

        self.pm.pool_manager_api.delete_zone.assert_called_with(mock_ctx, z)
        self.assertEqual(3, self.pm.pool_manager_api.delete_zone.call_count)
        self.pm.pool_manager_api.create_zone.assert_called_with(mock_ctx, z)
        self.assertEqual(4, self.pm.pool_manager_api.create_zone.call_count)
        self.pm.pool_manager_api.update_zone.assert_called_with(mock_ctx, z)
        self.assertEqual(5, self.pm.pool_manager_api.update_zone.call_count)

    @patch.object(pm_module.DesignateContext, 'get_admin_context')
    def test_periodic_recover_exception(self, mock_get_ctx, *mocks):
        z = RoObject(name='a_zone')
        # Raise an exception half through the recovery

        def mock_get_failed_zones(ctx, action):
            if action == pm_module.DELETE_ACTION:
                return [z] * 3
            if action == pm_module.CREATE_ACTION:
                return [z] * 4

        self.pm._get_failed_zones = mock_get_failed_zones
        self.pm.pool_manager_api.delete_zone = Mock()
        self.pm.pool_manager_api.create_zone = Mock(
                side_effect=Exception('oops'))
        self.pm.pool_manager_api.update_zone = Mock()
        mock_ctx = mock_get_ctx.return_value

        self.pm.periodic_recovery()

        self.pm.pool_manager_api.delete_zone.assert_called_with(mock_ctx, z)
        self.assertEqual(3, self.pm.pool_manager_api.delete_zone.call_count)
        self.pm.pool_manager_api.create_zone.assert_called_with(mock_ctx, z)
        self.assertEqual(1, self.pm.pool_manager_api.create_zone.call_count)
        self.assertEqual(0, self.pm.pool_manager_api.update_zone.call_count)

    def test_periodic_sync(self, *mocks):
        def mock_fetch_healthy_zones(ctx):
            return [
                       RoObject(name='a_zone'),
                       RoObject(name='b_zone'),
                       RoObject(name='c_zone'),
                   ]

        self.pm._fetch_healthy_zones = mock_fetch_healthy_zones
        self.pm.update_zone = Mock()
        self.pm._exceed_or_meet_threshold = Mock(return_value=True)

        self.pm.periodic_sync()

        self.assertEqual(3, self.pm.update_zone.call_count)

    @patch.object(pm_module.DesignateContext, 'get_admin_context')
    def test_target_sync(self, mock_get_ctx, *mocks):
        mock_ctx = mock_get_ctx.return_value
        date = 1463154200
        older_date = datetime.fromtimestamp(1463154000)
        newer_date = datetime.fromtimestamp(1463154300)

        zones = [
            RwObject(name='a_zone', status='ACTIVE', created_at=older_date),
            RwObject(name='b_zone', status='ACTIVE', created_at=newer_date),
            RwObject(name='c_zone', status='DELETED', created_at=older_date,
                     serial=1),
        ]

        self.pm._delete_zone_on_target = Mock()
        self.pm._create_zone_on_target = Mock()
        self.pm._update_zone_on_target = Mock()
        self.pm.mdns_api.poll_for_serial_number = Mock()
        target = Mock()

        self.pm._target_sync(mock_ctx, zones, target, date)

        self.assertEqual(1, self.pm._delete_zone_on_target.call_count)
        self.assertEqual(1, self.pm._create_zone_on_target.call_count)
        self.assertEqual(1, self.pm._update_zone_on_target.call_count)

    @patch.object(pm_module.DesignateContext, 'get_admin_context')
    def test_create_zone(self, mock_get_ctx, *mocks):
        z = RwObject(name='a_zone', serial=1)

        mock_ctx = mock_get_ctx.return_value
        self.pm._exceed_or_meet_threshold = Mock(return_value=True)

        self.pm.create_zone(mock_ctx, z)

    @patch.object(pm_module.DesignateContext, 'get_admin_context')
    def test_update_zone(self, mock_get_ctx, *mocks):
        z = RwObject(name='a_zone', serial=1)

        mock_ctx = mock_get_ctx.return_value
        self.pm._exceed_or_meet_threshold = Mock(return_value=True)

        self.pm.update_zone(mock_ctx, z)

    @patch.object(pm_module.DesignateContext, 'get_admin_context')
    def test_delete_zone(self, mock_get_ctx, *mocks):
        z = RwObject(name='a_zone', serial=1)

        mock_ctx = mock_get_ctx.return_value
        self.pm._exceed_or_meet_threshold = Mock(return_value=True)

        self.pm.delete_zone(mock_ctx, z)
