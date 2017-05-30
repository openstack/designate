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

"""Unit-test Pool Scheduler
"""
import testtools
from mock import Mock
from oslotest import base as test
from oslo_config import cfg
from oslo_config import fixture as cfg_fixture

from designate import scheduler
from designate import objects
from designate import context
from designate import exceptions


class SchedulerTest(test.BaseTestCase):

    def setUp(self):
        super(SchedulerTest, self).setUp()

        self.context = context.DesignateContext()
        self.CONF = self.useFixture(cfg_fixture.Config(cfg.CONF)).conf

    def test_default_operation(self):
        zone = objects.Zone(
            name="example.com.",
            type="PRIMARY",
            email="hostmaster@example.com"
        )

        attrs = {
            'find_pools.return_value': objects.PoolList.from_list(
                [{"id": "794ccc2c-d751-44fe-b57f-8894c9f5c842"}])
        }
        mock_storage = Mock(**attrs)

        test_scheduler = scheduler.get_scheduler(storage=mock_storage)

        zone.pool_id = test_scheduler.schedule_zone(self.context, zone)

        self.assertEqual(zone.pool_id, "794ccc2c-d751-44fe-b57f-8894c9f5c842")

    def test_multiple_pools(self):
        zone = objects.Zone(
            name="example.com.",
            type="PRIMARY",
            email="hostmaster@example.com"
        )

        attrs = {
            'find_pools.return_value': objects.PoolList.from_list(
                [
                    {"id": "794ccc2c-d751-44fe-b57f-8894c9f5c842"},
                    {"id": "5fabcd37-262c-4cf3-8625-7f419434b6df"}
                ]
            )
        }

        mock_storage = Mock(**attrs)

        test_scheduler = scheduler.get_scheduler(storage=mock_storage)

        zone.pool_id = test_scheduler.schedule_zone(self.context, zone)

        self.assertIn(
            zone.pool_id,
            [
                "794ccc2c-d751-44fe-b57f-8894c9f5c842",
                "5fabcd37-262c-4cf3-8625-7f419434b6df",
            ]
        )

    def test_no_pools(self):
        zone = objects.Zone(
            name="example.com.",
            type="PRIMARY",
            email="hostmaster@example.com"
        )

        attrs = {
            'find_pools.return_value': objects.PoolList()
        }
        mock_storage = Mock(**attrs)

        cfg.CONF.set_override(
            'scheduler_filters',
            ['random'],
            'service:central')

        test_scheduler = scheduler.get_scheduler(storage=mock_storage)

        with testtools.ExpectedException(exceptions.NoValidPoolFound):
            test_scheduler.schedule_zone(self.context, zone)

    def test_no_filters_enabled(self):

        cfg.CONF.set_override(
            'scheduler_filters', [], 'service:central')

        attrs = {
            'find_pools.return_value': objects.PoolList()
        }
        mock_storage = Mock(**attrs)

        with testtools.ExpectedException(exceptions.NoFiltersConfigured):
            scheduler.get_scheduler(storage=mock_storage)
