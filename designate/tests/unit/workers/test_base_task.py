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
import oslotest.base
from unittest import mock

from designate import exceptions
from designate import objects
from designate.worker.tasks import base


class TestTask(oslotest.base.BaseTestCase):
    def setUp(self):
        super(TestTask, self).setUp()
        self.context = mock.Mock()
        self.task = base.Task(None)
        self.storage = self.task._storage = mock.Mock()

    def test_constructor(self):
        self.assertTrue(self.task)

    def test_call(self):
        self.assertRaises(NotImplementedError, self.task)

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
