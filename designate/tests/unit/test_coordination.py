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


import shutil
import tempfile
from unittest import mock

from oslo_config import fixture as cfg_fixture
import oslotest.base
import tooz.coordination

import designate.conf
from designate import coordination
from designate.tests import base_fixtures


CONF = designate.conf.CONF


class TestCoordination(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))
        self.service_name = 'service_name'
        self.tg = mock.Mock()
        self.tempdir = tempfile.mkdtemp()
        CONF.set_override('backend_url', "file://%s" % self.tempdir,
                          group='coordination')
        self.addCleanup(shutil.rmtree, self.tempdir, ignore_errors=True)

    def test_retry_if_tooz_error(self):
        self.assertFalse(coordination._retry_if_tooz_error(Exception()))
        self.assertTrue(coordination._retry_if_tooz_error(
            tooz.coordination.ToozError('error'))
        )

    def test_start(self):
        service = coordination.Coordination(self.service_name, self.tg)
        service.start()
        self.assertTrue(service.started)
        service.stop()

    def test_start_with_grouping_enabled(self):
        service = coordination.Coordination(
            self.service_name, self.tg, grouping_enabled=True
        )
        service.start()
        self.assertTrue(service.started)
        self.assertIn(service.name,
                      service.coordinator.get_groups().get())
        self.assertIn(service.coordination_id,
                      service.coordinator.get_members(service.name).get())
        service.stop()

    def test_stop(self):
        service = coordination.Coordination(self.service_name, self.tg)
        service.start()
        service.stop()
        self.assertFalse(service.started)

    def test_stop_with_grouping_enabled(self):
        service = coordination.Coordination(
            self.service_name, self.tg, grouping_enabled=True
        )
        service.start()
        service.stop()
        self.assertFalse(service.started)

    def test_start_no_coordination(self):
        CONF.set_override('backend_url', None, group='coordination')
        # self.config(backend_url=None, group="coordination")
        service = coordination.Coordination(self.service_name, self.tg)
        service.start()
        self.assertIsNone(service.coordinator)

    def test_stop_no_coordination(self):
        CONF.set_override('backend_url', None, group='coordination')
        service = coordination.Coordination(self.service_name, self.tg)
        self.assertIsNone(service.coordinator)
        service.start()
        service.stop()

    def test_get_lock(self):
        service = coordination.Coordination(self.service_name, self.tg)
        service._coordinator = mock.Mock()

        service.get_lock(b'lock')

        service._coordinator.get_lock.assert_called_with(b'lock')

    def test_un_watchers(self):
        service = coordination.Coordination(self.service_name, self.tg)
        service._started = True
        service._coordinator = mock.Mock()

        service._coordinator_run_watchers()

        service._coordinator.run_watchers.assert_called_with()

    def test_run_watchers_not_started(self):
        service = coordination.Coordination(self.service_name, self.tg)
        service._started = False
        service._coordinator = mock.Mock()

        service._coordinator_run_watchers()

        service._coordinator.run_watchers.assert_not_called()

    def test_create_group(self):
        service = coordination.Coordination(self.service_name, self.tg)
        service._coordinator = mock.Mock()

        service._create_group()

        service._coordinator.create_group.assert_called_with(b'service_name')

    def test_create_group_already_exists(self):
        service = coordination.Coordination(self.service_name, self.tg)
        service._coordinator = mock.Mock()
        service._coordinator.create_group.side_effect = (
            tooz.coordination.GroupAlreadyExist('')
        )

        service._create_group()

        service._coordinator.create_group.assert_called_with(b'service_name')

    def test_disable_grouping(self):
        service = coordination.Coordination(self.service_name, self.tg)
        service._coordinator = mock.Mock()

        service._disable_grouping()

        service._coordinator.leave_group.assert_called_with(b'service_name')

    def test_disable_grouping_already_exists(self):
        service = coordination.Coordination(self.service_name, self.tg)
        service._coordinator = mock.Mock()
        service._coordinator.leave_group.side_effect = (
            tooz.coordination.GroupNotCreated('')
        )

        service._disable_grouping()

        service._coordinator.leave_group.assert_called_with(b'service_name')


@mock.patch('tenacity.nap.time', mock.Mock())
class TestPartitioner(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.tempdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tempdir, ignore_errors=True)

    def _get_partitioner(self, partitions, host=b'a'):
        fixture = self.useFixture(base_fixtures.CoordinatorFixture(
            "file://%s" % self.tempdir, host)
        )
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

    def test_get_members(self):
        partitioner = coordination.Partitioner(
            mock.Mock(), 'group', 'host', mock.Mock()
        )

        mock_get_members = mock.Mock()

        partitioner._coordinator.get_members = mock.Mock()
        partitioner._coordinator.get_members.return_value = mock_get_members

        partitioner._get_members('group_id')

        mock_get_members.get.assert_called_with()

    def test_get_members_group_not_created(self):
        partitioner = coordination.Partitioner(
            mock.Mock(), 'group', 'host', mock.Mock()
        )

        mock_get_members = mock.Mock()

        partitioner._coordinator.get_members = mock.Mock()
        partitioner._coordinator.get_members.return_value = mock_get_members

        mock_get_members.get.side_effect = tooz.coordination.GroupNotCreated(
            'group_id'
        )

        self.assertRaisesRegex(
            tooz.coordination.GroupNotCreated,
            'Group group_id does not exist',
            partitioner._get_members, 'group_id'
        )

    def test_get_members_tooz_error(self):
        partitioner = coordination.Partitioner(
            mock.Mock(), 'group', 'host', mock.Mock()
        )

        mock_get_members = mock.Mock()

        partitioner._coordinator.get_members = mock.Mock()
        partitioner._coordinator.get_members.return_value = mock_get_members

        mock_get_members.get.side_effect = tooz.coordination.ToozError(
            'error'
        )

        self.assertRaisesRegex(
            tooz.coordination.ToozError,
            'error',
            partitioner._get_members, 'group_id'
        )

    def test_unwatch_partition_change(self):
        partitioner = coordination.Partitioner(
            mock.Mock(), 'group', 'host', mock.Mock()
        )
        partitioner._callbacks = mock.Mock()

        partitioner.unwatch_partition_change('partition')

        partitioner._callbacks.remove.assert_called_with('partition')


class TestPartitionerWithoutBackend(oslotest.base.BaseTestCase):
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
