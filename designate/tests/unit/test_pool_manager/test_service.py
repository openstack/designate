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

from mock import Mock
from mock import MagicMock
from mock import patch
from oslotest import base as test

from designate import exceptions
from designate import objects
from designate.pool_manager.service import Service


class PoolManagerTest(test.BaseTestCase):
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
