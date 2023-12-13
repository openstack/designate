# (c) Copyright 2016 Hewlett Packard Enterprise Development Company LP.
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

from oslo_config import fixture as cfg_fixture
import oslotest.base

import designate.conf
from designate import exceptions
from designate import objects
from designate import scheduler


CONF = designate.conf.CONF


class SchedulerTest(oslotest.base.BaseTestCase):

    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))
        self.context = mock.Mock()
        self.zone = objects.Zone(
            name='example.com.',
            type='PRIMARY',
            email='hostmaster@example.com'
        )

    def test_default_operation(self):
        attrs = {
            'find_pools.return_value': objects.PoolList.from_list(
                [{'id': '794ccc2c-d751-44fe-b57f-8894c9f5c842'}])
        }
        mock_storage = mock.Mock(**attrs)

        test_scheduler = scheduler.get_scheduler(storage=mock_storage)

        self.zone.pool_id = test_scheduler.schedule_zone(self.context,
                                                         self.zone)

        self.assertEqual(self.zone.pool_id,
                         '794ccc2c-d751-44fe-b57f-8894c9f5c842')

    def test_multiple_pools(self):
        attrs = {
            'find_pools.return_value': objects.PoolList.from_list(
                [
                    {'id': '794ccc2c-d751-44fe-b57f-8894c9f5c842'},
                    {'id': '5fabcd37-262c-4cf3-8625-7f419434b6df'}
                ]
            )
        }

        mock_storage = mock.Mock(**attrs)

        test_scheduler = scheduler.get_scheduler(storage=mock_storage)

        self.zone.pool_id = test_scheduler.schedule_zone(self.context,
                                                         self.zone)

        self.assertIn(
            self.zone.pool_id,
            [
                '794ccc2c-d751-44fe-b57f-8894c9f5c842',
                '5fabcd37-262c-4cf3-8625-7f419434b6df',
            ]
        )

    def test_no_pools(self):
        attrs = {
            'find_pools.return_value': objects.PoolList()
        }
        mock_storage = mock.Mock(**attrs)

        CONF.set_override(
            'scheduler_filters', ['random'], 'service:central'
        )

        test_scheduler = scheduler.get_scheduler(storage=mock_storage)

        self.assertRaisesRegex(
            exceptions.NoValidPoolFound,
            'There are no pools that matched your request',
            test_scheduler.schedule_zone, self.context, self.zone,
        )

    def test_no_filters_enabled(self):
        CONF.set_override(
            'scheduler_filters', [], 'service:central'
        )

        attrs = {
            'find_pools.return_value': objects.PoolList()
        }
        mock_storage = mock.Mock(**attrs)

        self.assertRaisesRegex(
            exceptions.NoFiltersConfigured,
            'There are no scheduling filters configured',
            scheduler.get_scheduler, mock_storage,
        )

    def test_no_filters_when_scheduling_zone(self):
        test_scheduler = scheduler.get_scheduler(storage=mock.Mock())
        test_scheduler.filters = list()

        self.assertRaisesRegex(
            exceptions.NoFiltersConfigured,
            'There are no scheduling filters configured',
            test_scheduler.schedule_zone, self.context, self.zone,
        )
