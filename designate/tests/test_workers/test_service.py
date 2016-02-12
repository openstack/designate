# Copyright 2016 Rackspace Inc.
#
# Author: Eric Larson <eric.larson@rackspace.com>
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
# under the License.mport threading
from unittest import TestCase

import mock

from designate.worker import service


class TestService(TestCase):

    def setUp(self):
        self.context = mock.Mock()
        self.zone = mock.Mock()
        self.service = service.Service()

    def test_create_zone(self):
        self.service._do_zone_action = mock.Mock()

        self.service.create_zone(self.context, self.zone)

        self.service._do_zone_action.assert_called_with(
            self.context, self.zone
        )

    def test_delete_zone(self):
        self.service._do_zone_action = mock.Mock()

        self.service.delete_zone(self.context, self.zone)

        self.service._do_zone_action.assert_called_with(
            self.context, self.zone
        )

    def test_update_zone(self):
        self.service._do_zone_action = mock.Mock()

        self.service.update_zone(self.context, self.zone)

        self.service._do_zone_action.assert_called_with(
            self.context, self.zone
        )

    @mock.patch.object(service.zonetasks, 'ZoneAction')
    def test_do_zone_action(self, ZoneAction):
        self.service._executor = mock.Mock()
        self.service._pool = mock.Mock()
        self.service.get_pool = mock.Mock()
        pool = mock.Mock()
        self.service.get_pool.return_value = pool

        self.service._do_zone_action(self.context, self.zone)

        ZoneAction.assert_called_with(
            self.service.executor,
            self.context,
            pool,
            self.zone,
            self.zone.action
        )

        self.service._executor.run.assert_called_with(ZoneAction())

    def test_get_pool(self):
        pool = mock.Mock()
        self.service.load_pool = mock.Mock()
        self.service.load_pool.return_value = pool
        self.service._pools_map = {'1': pool}

        assert self.service.get_pool('1') == pool
        assert self.service.get_pool('2') == pool

    @mock.patch.object(service.zonetasks, 'RecoverShard')
    def test_recover_shard(self, RecoverShard):
        self.service._executor = mock.Mock()
        self.service._pool = mock.Mock()

        self.service.recover_shard(self.context, 1, 10)

        RecoverShard.assert_called_with(
            self.service.executor,
            self.context,
            1, 10
        )

        self.service.executor.run.assert_called_with(RecoverShard())
