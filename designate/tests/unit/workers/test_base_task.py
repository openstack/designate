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
from oslo_config import fixture as cfg_fixture
import oslotest.base
from unittest import mock

from designate.central import rpcapi as central_rpcapi
import designate.conf
from designate import exceptions
from designate import objects
import designate.quota.base
from designate import rpc
from designate import storage
from designate.worker import rpcapi as worker_rpcapi
from designate.worker.tasks import base


CONF = designate.conf.CONF


class TestTask(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))
        self.context = mock.Mock()
        self.task = base.Task(None)
        self.storage = self.task._storage = mock.Mock()

    def test_constructor(self):
        self.assertTrue(self.task)

    @mock.patch.object(storage, 'get_storage', mock.Mock())
    def test_quota(self):
        self.assertIsInstance(self.task.quota, designate.quota.base.Quota)

    @mock.patch.object(rpc, 'get_client', mock.Mock())
    def test_central_api(self):
        self.assertIsInstance(self.task.central_api, central_rpcapi.CentralAPI)

    @mock.patch.object(rpc, 'get_client', mock.Mock())
    def test_worker_api(self):
        self.assertIsNone(self.task._worker_api)
        self.assertIsInstance(self.task.worker_api, worker_rpcapi.WorkerAPI)
        self.assertIsNotNone(self.task._worker_api)
        self.assertIsInstance(self.task.worker_api, worker_rpcapi.WorkerAPI)

    def test_compare_threshold_at_50_percentage(self):
        CONF.set_override('threshold_percentage', 50, 'service:worker')

        self.assertFalse(self.task.compare_threshold(0, 0))
        self.assertTrue(self.task.compare_threshold(3, 3))
        self.assertFalse(self.task.compare_threshold(1, 3))
        self.assertFalse(self.task.compare_threshold(2, 5))
        self.assertTrue(self.task.compare_threshold(4, 5))

    def test_compare_threshold_at_100_percentage(self):
        CONF.set_override('threshold_percentage', 100, 'service:worker')

        self.assertFalse(self.task.compare_threshold(0, 0))
        self.assertTrue(self.task.compare_threshold(3, 3))
        self.assertFalse(self.task.compare_threshold(1, 3))
        self.assertFalse(self.task.compare_threshold(2, 5))
        self.assertFalse(self.task.compare_threshold(4, 5))

    def test_current_action_is_valid(self):
        self.storage.get_zone = mock.Mock(
            return_value=objects.Zone(action='UPDATE')
        )
        self.assertTrue(
            self.task.is_current_action_valid(
                self.context, 'UPDATE', objects.Zone(action='UPDATE'))
        )

        self.storage.get_zone = mock.Mock(
            return_value=objects.Zone(action='CREATE')
        )
        self.assertTrue(
            self.task.is_current_action_valid(
                self.context, 'CREATE', objects.Zone(action='CREATE'))
        )

        self.storage.get_zone = mock.Mock(
            return_value=objects.Zone(action='UPDATE')
        )
        self.assertTrue(
            self.task.is_current_action_valid(
                self.context, 'CREATE', objects.Zone(action='CREATE'))
        )

        self.storage.get_zone = mock.Mock(
            return_value=objects.Zone(action='DELETE')
        )
        self.assertTrue(
            self.task.is_current_action_valid(
                self.context, 'DELETE', objects.Zone(action='DELETE'))
        )

    def test_current_action_delete_always_valid(self):
        self.assertTrue(
            self.task.is_current_action_valid(
                self.context, 'DELETE', None)
        )

    def test_current_action_bad_storage_always_valid(self):
        self.storage.get_zone = mock.Mock(
            side_effect=exceptions.DesignateException()
        )
        self.assertTrue(
            self.task.is_current_action_valid(
                self.context, 'CREATE', objects.Zone(action='CREATE'))
        )

    def test_current_action_is_not_valid_none(self):
        self.storage.get_zone = mock.Mock(
            return_value=objects.Zone(action='NONE')
        )
        self.assertFalse(
            self.task.is_current_action_valid(
                self.context, 'UPDATE', objects.Zone(action='UPDATE'))
        )

    def test_current_action_is_not_valid_deleted(self):
        self.storage.get_zone = mock.Mock(
            return_value=objects.Zone(action='DELETE')
        )
        self.assertFalse(
            self.task.is_current_action_valid(
                self.context, 'UPDATE', objects.Zone(action='UPDATE'))
        )

    def test_current_action_is_not_found(self):
        self.storage.get_zone = mock.Mock(
            side_effect=exceptions.ZoneNotFound()
        )
        self.assertTrue(
            self.task.is_current_action_valid(
                self.context, 'CREATE', objects.Zone(action='CREATE'))
        )

        self.storage.get_zone = mock.Mock(
            side_effect=exceptions.ZoneNotFound()
        )
        self.assertFalse(
            self.task.is_current_action_valid(
                self.context, 'UPDATE', objects.Zone(action='UPDATE'))
        )

    def test_call(self):
        self.assertRaises(NotImplementedError, self.task)
