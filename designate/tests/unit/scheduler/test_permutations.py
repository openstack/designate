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

DEFAULT_POOL_ID = BRONZE_POOL_ID = '67d71c2a-645c-4dde-a6b8-60a172c9ede8'
SILVER_POOL_ID = '5fabcd37-262c-4cf3-8625-7f419434b6df'
GOLD_POOL_ID = '24702e43-8a52-440f-ab74-19fc16048860'


def build_test_pools():
    pools = objects.PoolList.from_list(
        [
            {'id': DEFAULT_POOL_ID},
            {'id': SILVER_POOL_ID},
            {'id': GOLD_POOL_ID},
        ]

    )

    # Pool 0 is also the default pool.
    pool_0_attributes = objects.PoolAttributeList.from_list([
        {
            'key': 'service_tier',
            'value': 'bronze'
        },
    ])
    pool_1_attributes = objects.PoolAttributeList.from_list([
        {
            'key': 'service_tier',
            'value': 'silver'
        },
    ])
    pool_2_attributes = objects.PoolAttributeList.from_list([
        {
            'key': 'service_tier',
            'value': 'gold'
        },
    ])

    pools[0].attributes = pool_0_attributes
    pools[1].attributes = pool_1_attributes
    pools[2].attributes = pool_2_attributes

    return pools


class AttributeSchedulerPermutationsTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.CONF = self.useFixture(cfg_fixture.Config(CONF)).conf
        self.context = mock.Mock()

        self.CONF.set_override(
            'scheduler_filters', ['attribute'], 'service:central'
        )
        self.CONF.set_override(
            'default_pool_id', DEFAULT_POOL_ID, 'service:central'
        )

        attrs = {
            'find_pools.return_value': build_test_pools()
        }
        mock_storage = mock.Mock(**attrs)

        self.scheduler = scheduler.get_scheduler(storage=mock_storage)

    def test_get_gold_tier(self):
        zone = objects.Zone(
            name='example.com.',
            type='PRIMARY',
            email='hostmaster@example.com',
            attributes=objects.ZoneAttributeList.from_list(
                [
                    {
                        'key': 'service_tier',
                        'value': 'gold'
                    },
                ]
            )
        )

        result = self.scheduler.schedule_zone(self.context, zone)

        self.assertEqual(GOLD_POOL_ID, result)

    def test_get_silver_tier(self):
        zone = objects.Zone(
            name='example.com.',
            type='PRIMARY',
            email='hostmaster@example.com',
            attributes=objects.ZoneAttributeList.from_list(
                [
                    {
                        'key': 'service_tier',
                        'value': 'silver'
                    },
                ]
            )
        )

        result = self.scheduler.schedule_zone(self.context, zone)

        self.assertEqual(SILVER_POOL_ID, result)

    def test_get_bronze_tier(self):
        zone = objects.Zone(
            name='example.com.',
            type='PRIMARY',
            email='hostmaster@example.com',
            attributes=objects.ZoneAttributeList.from_list(
                [
                    {
                        'key': 'service_tier',
                        'value': 'bronze'
                    },
                ]
            )
        )

        result = self.scheduler.schedule_zone(self.context, zone)

        self.assertEqual(BRONZE_POOL_ID, result)

    def test_tier_not_found_raises_exception(self):
        zone = objects.Zone(
            name='example.com.',
            type='PRIMARY',
            email='hostmaster@example.com',
            attributes=objects.ZoneAttributeList.from_list(
                [
                    {
                        'key': 'service_tier',
                        'value': 'blue'
                    },
                ]
            )
        )

        self.assertRaises(
            exceptions.NoValidPoolFound,
            self.scheduler.schedule_zone, self.context, zone
        )

    def test_no_tier_raises_exception(self):
        zone = objects.Zone(
            name='example.com.',
            type='PRIMARY',
            email='hostmaster@example.com',
            attributes=objects.ZoneAttributeList.from_list(
                []
            )
        )

        # When no attribute is requested it will return all available pools.
        # NOTE(eandersson): This is probably not intended behavior.
        #                   We probably want this to return NoValidPoolFound,
        #                   so that we can use a fallback filter with the
        #                   attribute filter.
        self.assertRaises(
            exceptions.MultiplePoolsFound,
            self.scheduler.schedule_zone, self.context, zone
        )


class DefaultSchedulerPermutationsTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.CONF = self.useFixture(cfg_fixture.Config(CONF)).conf
        self.context = mock.Mock()

        self.CONF.set_override(
            'scheduler_filters', ['default_pool'], 'service:central'
        )
        self.CONF.set_override(
            'default_pool_id', DEFAULT_POOL_ID, 'service:central'
        )

        attrs = {
            'find_pools.return_value': build_test_pools()
        }
        mock_storage = mock.Mock(**attrs)

        self.scheduler = scheduler.get_scheduler(storage=mock_storage)

    def test_get_default_pool(self):
        zone = objects.Zone(
            name='example.com.',
            type='PRIMARY',
            email='hostmaster@example.com',
        )

        result = self.scheduler.schedule_zone(self.context, zone)

        self.assertEqual(DEFAULT_POOL_ID, result)


class FallbackSchedulerPermutationsTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.CONF = self.useFixture(cfg_fixture.Config(CONF)).conf
        self.context = mock.Mock()

        self.CONF.set_override(
            'scheduler_filters', ['attribute', 'fallback'], 'service:central'
        )
        self.CONF.set_override(
            'default_pool_id', DEFAULT_POOL_ID, 'service:central'
        )

        attrs = {
            'find_pools.return_value': build_test_pools()
        }
        mock_storage = mock.Mock(**attrs)

        self.scheduler = scheduler.get_scheduler(storage=mock_storage)

    def test_tier_not_found_return_default(self):
        zone = objects.Zone(
            name='example.com.',
            type='PRIMARY',
            email='hostmaster@example.com',
            attributes=objects.ZoneAttributeList.from_list(
                [
                    {
                        'key': 'service_tier',
                        'value': 'that does not exist'
                    },
                ]
            )
        )

        result = self.scheduler.schedule_zone(self.context, zone)

        self.assertEqual(DEFAULT_POOL_ID, result)
