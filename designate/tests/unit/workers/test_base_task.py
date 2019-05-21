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

from designate.worker.tasks import base


class TestTask(oslotest.base.BaseTestCase):
    def setUp(self):
        super(TestTask, self).setUp()
        self.task = base.Task(None)

    def test_constructor(self):
        self.assertTrue(self.task)

    def test_call(self):
        self.assertRaises(NotImplementedError, self.task)
