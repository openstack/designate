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

from designate.worker import processing


class TestProcessingExecutor(TestCase):

    def test_execute_multiple_tasks(self):
        def t1():
            return 1

        def t2():
            return 2

        tasks = [t1, t2, t1, t2, t1]
        exe = processing.Executor()

        results = exe.run(tasks)
        assert results == [1, 2, 1, 2, 1]

    def test_execute_single_task(self):
        def t1():
            return 1

        def t2():
            return 2

        exe = processing.Executor()

        results = exe.run(t1)
        assert results == [1]
