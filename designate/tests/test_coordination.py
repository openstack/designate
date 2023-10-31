# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hpe.com>
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
from unittest import mock

from designate import coordination
from designate.tests import fixtures
from designate.tests import TestCase


class TestCoordination(TestCase):
    def setUp(self):
        super().setUp()
        self.name = 'coordination'
        self.tg = mock.Mock()
        self.config(backend_url="zake://", group="coordination")

    def test_start(self):
        service = coordination.Coordination(self.name, self.tg)
        service.start()
        self.assertTrue(service.started)
        service.stop()

    def test_start_with_grouping_enabled(self):
        service = coordination.Coordination(
            self.name, self.tg, grouping_enabled=True
        )
        service.start()
        self.assertTrue(service.started)
        self.assertIn(self.name.encode('utf-8'),
                      service.coordinator.get_groups().get())
        self.assertIn(service.coordination_id.encode('utf-8'),
                      service.coordinator.get_members(
                          self.name.encode('utf-8')).get())
        service.stop()

    def test_stop(self):
        service = coordination.Coordination(self.name, self.tg)
        service.start()
        service.stop()
        self.assertFalse(service.started)

    def test_stop_with_grouping_enabled(self):
        service = coordination.Coordination(
            self.name, self.tg, grouping_enabled=True
        )
        service.start()
        service.stop()
        self.assertFalse(service.started)

    def test_start_no_coordination(self):
        self.config(backend_url=None, group="coordination")
        service = coordination.Coordination(self.name, self.tg)
        service.start()
        self.assertIsNone(service.coordinator)

    def test_stop_no_coordination(self):
        self.config(backend_url=None, group="coordination")
        service = coordination.Coordination(self.name, self.tg)
        self.assertIsNone(service.coordinator)
        service.start()
        service.stop()


class TestPartitioner(TestCase):
    def _get_partitioner(self, partitions, host=b'a'):
        fixture = self.useFixture(fixtures.CoordinatorFixture(
            'zake://', host))
        group = 'group'
        fixture.coordinator.create_group(group)
        fixture.coordinator.join_group(group)

        return coordination.Partitioner(fixture.coordinator, group, host,
                                        partitions), fixture.coordinator

    def test_callbacks(self):
        cb1 = mock.Mock()
        cb2 = mock.Mock()
        partitions = list(range(0, 10))

        p_one, c_one = self._get_partitioner(partitions)
        p_one.start()
        p_one.watch_partition_change(cb1)
        p_one.watch_partition_change(cb2)

        # Initial partitions are calucated upon service bootup
        cb1.assert_called_with(partitions, None, None)
        cb2.assert_called_with(partitions, None, None)

        cb1.reset_mock()
        cb2.reset_mock()

        # Startup a new partioner that will cause the cb's to be called
        p_two, c_two = self._get_partitioner(partitions, host=b'b')
        p_two.start()

        # We'll get the 5 first partition ranges
        c_one.run_watchers()
        cb1.assert_called_with(partitions[:5], [b'a', b'b'], mock.ANY)
        cb2.assert_called_with(partitions[:5], [b'a', b'b'], mock.ANY)

    def test_two_even_partitions(self):
        partitions = list(range(0, 10))

        p_one, c_one = self._get_partitioner(partitions)
        p_two, c_two = self._get_partitioner(partitions, host=b'b')

        p_one.start()
        p_two.start()

        # Call c_one watchers making it refresh it's partitions
        c_one.run_watchers()

        self.assertEqual([0, 1, 2, 3, 4], p_one.my_partitions)
        self.assertEqual([5, 6, 7, 8, 9], p_two.my_partitions)

    def test_two_odd_partitions(self):
        partitions = list(range(0, 11))

        p_one, c_one = self._get_partitioner(partitions)
        p_two, c_two = self._get_partitioner(partitions, host=b'b')

        p_one.start()
        p_two.start()

        # Call c_one watchers making it refresh it's partitions
        c_one.run_watchers()

        self.assertEqual([0, 1, 2, 3, 4, 5], p_one.my_partitions)
        self.assertEqual([6, 7, 8, 9, 10], p_two.my_partitions)

    def test_three_even_partitions(self):
        partitions = list(range(0, 10))

        p_one, c_one = self._get_partitioner(partitions)
        p_two, c_two = self._get_partitioner(partitions, host=b'b')
        p_three, c_three = self._get_partitioner(partitions, host=b'c')

        p_one.start()
        p_two.start()
        p_three.start()

        # Call c_one watchers making it refresh it's partitions
        c_one.run_watchers()
        c_two.run_watchers()

        self.assertEqual([0, 1, 2, 3], p_one.my_partitions)
        self.assertEqual([4, 5, 6, 7], p_two.my_partitions)
        self.assertEqual([8, 9], p_three.my_partitions)

    def test_three_odd_partitions(self):
        partitions = list(range(0, 11))

        p_one, c_one = self._get_partitioner(partitions)
        p_two, c_two = self._get_partitioner(partitions, host=b'b')
        p_three, c_three = self._get_partitioner(partitions, host=b'c')

        p_one.start()
        p_two.start()
        p_three.start()

        c_one.run_watchers()
        c_two.run_watchers()

        self.assertEqual([0, 1, 2, 3], p_one.my_partitions)
        self.assertEqual([4, 5, 6, 7], p_two.my_partitions)
        self.assertEqual([8, 9, 10], p_three.my_partitions)


class TestPartitionerWithoutBackend(TestCase):
    def test_start(self):
        # We test starting the partitioner and calling the watch func first
        partitions = list(range(0, 10))

        cb1 = mock.Mock()
        cb2 = mock.Mock()
        partitioner = coordination.Partitioner(
            None, 'group', 'meme', partitions)
        partitioner.watch_partition_change(cb1)
        partitioner.watch_partition_change(cb2)
        partitioner.start()
        cb1.assert_called_with(partitions, None, None)
        cb2.assert_called_with(partitions, None, None)

    def test_cb_on_watch(self):
        partitions = list(range(0, 10))
        cb = mock.Mock()

        partitioner = coordination.Partitioner(
            None, 'group', 'meme', partitions)
        partitioner.start()
        partitioner.watch_partition_change(cb)
        cb.assert_called_with(partitions, None, None)
