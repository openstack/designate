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

from mock import Mock
from mock import MagicMock
from mock import patch
from oslotest import base as test

from designate import exceptions
from designate import objects
from designate.pool_manager.service import Service
from designate.tests.unit import RoObject
import designate.pool_manager.service as pm_module


class PoolManagerInitTest(test.BaseTestCase):
    def __setUp(self):
        super(PoolManagerTest, self).setUp()

    def test_init_no_pool_targets(self):
        with patch.object(objects.Pool, 'from_config',
                          return_value=MagicMock()):
            self.assertRaises(exceptions.NoPoolTargetsConfigured, Service)

    def test_init(self):
        with patch.object(objects.Pool, 'from_config',
                          return_value=Mock()):
            Service._setup_target_backends = Mock()
            Service()

    def test_start(self):
        with patch.object(objects.Pool, 'from_config',
                          return_value=Mock()):
            Service._setup_target_backends = Mock()
            pm = Service()
            pm.pool.targets = ()
            pm.tg.add_timer = Mock()
            pm._pool_election = Mock()
            with patch("designate.service.RPCService.start"):
                pm.start()

            call1 = pm.tg.add_timer.call_args_list[0][0]
            self.assertEqual(120, call1[0])
            self.assertEqual(120, call1[-1])
            call2 = pm.tg.add_timer.call_args_list[1][0]
            self.assertEqual(1800, call2[0])
            self.assertEqual(1800, call2[-1])


class PoolManagerTest(test.BaseTestCase):

    @patch.object(pm_module.DesignateContext, 'get_admin_context')
    @patch.object(pm_module.central_api.CentralAPI, 'get_instance')
    @patch.object(objects.Pool, 'from_config')
    @patch.object(Service, '_setup_target_backends')
    def setUp(self, *mocks):
        super(PoolManagerTest, self).setUp()
        self.pm = Service()
        self.pm.pool.targets = ()
        self.pm.tg.add_timer = Mock()
        self.pm._pool_election = Mock()
        self.pm.target_backends = {}

    def test_get_failed_zones(self, *mocks):
        with patch.object(self.pm.central_api, 'find_zones') as \
                mock_find_zones:
            self.pm._get_failed_zones('ctx', pm_module.DELETE_ACTION)

            mock_find_zones.assert_called_once_with(
                'ctx', {'action': 'DELETE', 'status': 'ERROR', 'pool_id':
                        '794ccc2c-d751-44fe-b57f-8894c9f5c842'})

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
        self.pm.delete_zone = Mock()
        self.pm.create_zone = Mock()
        self.pm.update_zone = Mock()
        mock_ctx = mock_get_ctx.return_value

        self.pm.periodic_recovery()

        self.pm.delete_zone.assert_called_with(mock_ctx, z)
        self.assertEqual(3, self.pm.delete_zone.call_count)
        self.pm.create_zone.assert_called_with(mock_ctx, z)
        self.assertEqual(4, self.pm.create_zone.call_count)
        self.pm.update_zone.assert_called_with(mock_ctx, z)
        self.assertEqual(5, self.pm.update_zone.call_count)

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
        self.pm.delete_zone = Mock()
        self.pm.create_zone = Mock(side_effect=Exception('oops'))
        self.pm.update_zone = Mock()
        mock_ctx = mock_get_ctx.return_value

        self.pm.periodic_recovery()

        self.pm.delete_zone.assert_called_with(mock_ctx, z)
        self.assertEqual(3, self.pm.delete_zone.call_count)
        self.pm.create_zone.assert_called_with(mock_ctx, z)
        self.assertEqual(1, self.pm.create_zone.call_count)
        self.assertEqual(0, self.pm.update_zone.call_count)
