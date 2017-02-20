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
import fixtures
import testtools
from mock import Mock
from oslotest import base as test

from designate.scheduler.filters import default_pool_filter
from designate.scheduler.filters import fallback_filter
from designate.scheduler.filters import pool_id_attribute_filter
from designate.scheduler.filters import attribute_filter
from designate.scheduler.filters import in_doubt_default_pool_filter
from designate import objects
from designate import context
from designate import policy
from designate import exceptions


class SchedulerFilterTest(test.BaseTestCase):

    def setUp(self):
        super(SchedulerFilterTest, self).setUp()

        self.context = context.DesignateContext()

        self.zone = objects.Zone(
            name="example.com.",
            type="PRIMARY",
            email="hostmaster@example.com"
        )

        attrs = {
            'get_pool.return_value': objects.Pool(
                id="6c346011-e581-429b-a7a2-6cdf0aba91c3")
        }

        mock_storage = Mock(**attrs)

        self.test_filter = self.FILTER(storage=mock_storage)


class SchedulerDefaultPoolFilterTest(SchedulerFilterTest):

    FILTER = default_pool_filter.DefaultPoolFilter

    def test_default_operation(self):
        pools = objects.PoolList.from_list(
            [{"id": "794ccc2c-d751-44fe-b57f-8894c9f5c842"}]
        )
        pools = self.test_filter.filter(self.context, pools, self.zone)

        self.assertEqual(pools[0].id, "794ccc2c-d751-44fe-b57f-8894c9f5c842")

    def test_multiple_pools(self):
        pools = objects.PoolList.from_list(
            [
                {"id": "794ccc2c-d751-44fe-b57f-8894c9f5c842"},
                {"id": "5fabcd37-262c-4cf3-8625-7f419434b6df"}
            ]
        )
        pools = self.test_filter.filter(self.context, pools, self.zone)

        self.assertEqual(pools[0].id, "794ccc2c-d751-44fe-b57f-8894c9f5c842")

    def test_no_pools(self):
        pools = objects.PoolList()
        pools = self.test_filter.filter(self.context, pools, self.zone)

        self.assertEqual(pools[0].id, "794ccc2c-d751-44fe-b57f-8894c9f5c842")


class SchedulerFallbackFilterTest(SchedulerFilterTest):

    FILTER = fallback_filter.FallbackFilter

    def test_default_operation(self):
        pools = objects.PoolList.from_list(
            [{"id": "794ccc2c-d751-44fe-b57f-8894c9f5c842"}]
        )
        pools = self.test_filter.filter(self.context, pools, self.zone)

        self.assertEqual(pools[0].id, "794ccc2c-d751-44fe-b57f-8894c9f5c842")

    def test_multiple_pools(self):
        pools = objects.PoolList.from_list(
            [
                {"id": "6c346011-e581-429b-a7a2-6cdf0aba91c3"},
                {"id": "5fabcd37-262c-4cf3-8625-7f419434b6df"}
            ]
        )
        pools = self.test_filter.filter(self.context, pools, self.zone)

        self.assertEqual(len(pools), 2)

        for pool in pools:
            self.assertIn(
                pool.id,
                [
                    "6c346011-e581-429b-a7a2-6cdf0aba91c3",
                    "5fabcd37-262c-4cf3-8625-7f419434b6df",
                ]
            )

    def test_no_pools(self):
        pools = objects.PoolList()
        pools = self.test_filter.filter(self.context, pools, self.zone)

        self.assertEqual(pools[0].id, "794ccc2c-d751-44fe-b57f-8894c9f5c842")


class SchedulerPoolIDAttributeFilterTest(SchedulerFilterTest):

    FILTER = pool_id_attribute_filter.PoolIDAttributeFilter

    def setUp(self):
        super(SchedulerPoolIDAttributeFilterTest, self).setUp()

        self.zone = objects.Zone(
            name="example.com.",
            type="PRIMARY",
            email="hostmaster@example.com",
            attributes=objects.ZoneAttributeList.from_list(
                [
                    {
                        "key": "pool_id",
                        "value": "6c346011-e581-429b-a7a2-6cdf0aba91c3"
                    }
                ]
            )
        )

    def test_default_operation(self):
        pools = objects.PoolList.from_list(
            [{"id": "6c346011-e581-429b-a7a2-6cdf0aba91c3"}]
        )
        self.useFixture(fixtures.MockPatchObject(
            policy, 'check',
            return_value=None
        ))

        pools = self.test_filter.filter(self.context, pools, self.zone)

        self.assertEqual("6c346011-e581-429b-a7a2-6cdf0aba91c3", pools[0].id)

    def test_multiple_pools(self):
        pools = objects.PoolList.from_list(
            [
                {"id": "6c346011-e581-429b-a7a2-6cdf0aba91c3"},
                {"id": "5fabcd37-262c-4cf3-8625-7f419434b6df"}
            ]
        )

        self.useFixture(fixtures.MockPatchObject(
            policy, 'check',
            return_value=None
        ))

        pools = self.test_filter.filter(self.context, pools, self.zone)

        self.assertEqual(len(pools), 1)

        self.assertEqual("6c346011-e581-429b-a7a2-6cdf0aba91c3", pools[0].id)

    def test_no_pools(self):
        pools = objects.PoolList()

        self.useFixture(fixtures.MockPatchObject(
            policy, 'check',
            return_value=None
        ))

        pools = self.test_filter.filter(self.context, pools, self.zone)

        self.assertEqual(len(pools), 0)

    def test_policy_failure(self):
        pools = objects.PoolList.from_list(
            [{"id": "6c346011-e581-429b-a7a2-6cdf0aba91c3"}]
        )

        self.useFixture(fixtures.MockPatchObject(
            policy, 'check',
            side_effect=exceptions.Forbidden
        ))

        with testtools.ExpectedException(exceptions.Forbidden):
            self.test_filter.filter(self.context, pools, self.zone)

        policy.check.assert_called_once_with(
            'zone_create_forced_pool',
            self.context,
            pools[0])


class SchedulerAttributeFilterTest(SchedulerFilterTest):

    FILTER = attribute_filter.AttributeFilter

    def setUp(self):
        super(SchedulerAttributeFilterTest, self).setUp()

        self.zone = objects.Zone(
            name="example.com.",
            type="PRIMARY",
            email="hostmaster@example.com",
            attributes=objects.ZoneAttributeList.from_list(
                [
                    {
                        "key": "attribute_one",
                        "value": "True"
                    },
                    {
                        "key": "attribute_two",
                        "value": "False"
                    },
                    {
                        "key": "attribute_three",
                        "value": "foo"
                    }
                ]
            )
        )

    def test_default_operation(self):
        pools = objects.PoolList.from_list(
            [
                {
                    "id": "6c346011-e581-429b-a7a2-6cdf0aba91c3",
                }
            ]
        )

        pools[0].attributes = objects.PoolAttributeList.from_list(
            [
                {
                    "key": "attribute_one",
                    "value": "True"
                },
                {
                    "key": "attribute_two",
                    "value": "False"
                },
                {
                    "key": "attribute_three",
                    "value": "foo"
                }
            ])

        pools = self.test_filter.filter(self.context, pools, self.zone)

        self.assertEqual("6c346011-e581-429b-a7a2-6cdf0aba91c3", pools[0].id)

    def test_multiple_pools_all_match(self):
        pools = objects.PoolList.from_list(
            [
                {"id": "6c346011-e581-429b-a7a2-6cdf0aba91c3"},
                {"id": "5fabcd37-262c-4cf3-8625-7f419434b6df"}
            ]

        )

        attributes = objects.PoolAttributeList.from_list(
            [
                {
                    "key": "attribute_one",
                    "value": "True"
                },
                {
                    "key": "attribute_two",
                    "value": "False"
                },
                {
                    "key": "attribute_three",
                    "value": "foo"
                }
            ])

        pools[0].attributes = attributes
        pools[1].attributes = attributes

        pools = self.test_filter.filter(self.context, pools, self.zone)

        self.assertEqual(2, len(pools))

    def test_multiple_pools_one_match(self):
        pools = objects.PoolList.from_list(
            [
                {"id": "6c346011-e581-429b-a7a2-6cdf0aba91c3"},
                {"id": "5fabcd37-262c-4cf3-8625-7f419434b6df"}
            ]

        )

        pool_0_attributes = objects.PoolAttributeList.from_list(
            [
                {
                    "key": "attribute_one",
                    "value": "True"
                },
                {
                    "key": "attribute_two",
                    "value": "False"
                },
                {
                    "key": "attribute_three",
                    "value": "foo"
                }
            ])

        pool_1_attributes = objects.PoolAttributeList.from_list(
            [
                {
                    "key": "attribute_four",
                    "value": "True"
                },
                {
                    "key": "attribute_five",
                    "value": "False"
                },
                {
                    "key": "attribute_three",
                    "value": "foo"
                }
            ])

        pools[0].attributes = pool_0_attributes
        pools[1].attributes = pool_1_attributes

        pools = self.test_filter.filter(self.context, pools, self.zone)

        self.assertEqual(1, len(pools))
        self.assertEqual("6c346011-e581-429b-a7a2-6cdf0aba91c3", pools[0].id)

    def test_multiple_pools_no_match(self):
        pools = objects.PoolList.from_list(
            [
                {"id": "6c346011-e581-429b-a7a2-6cdf0aba91c3"},
                {"id": "5fabcd37-262c-4cf3-8625-7f419434b6df"}
            ]

        )

        pool_0_attributes = objects.PoolAttributeList.from_list(
            [
                {
                    "key": "attribute_six",
                    "value": "True"
                },
                {
                    "key": "attribute_two",
                    "value": "False"
                },
                {
                    "key": "attribute_seven",
                    "value": "foo"
                }
            ])

        pool_1_attributes = objects.PoolAttributeList.from_list(
            [
                {
                    "key": "attribute_four",
                    "value": "True"
                },
                {
                    "key": "attribute_five",
                    "value": "False"
                },
                {
                    "key": "attribute_three",
                    "value": "foo"
                }
            ])

        pools[0].attributes = pool_0_attributes
        pools[1].attributes = pool_1_attributes

        pools = self.test_filter.filter(self.context, pools, self.zone)

        self.assertEqual(0, len(pools))

    def test_no_match_non_bool(self):
        pools = objects.PoolList.from_list(
            [
                {"id": "6c346011-e581-429b-a7a2-6cdf0aba91c3"},
            ]

        )

        pool_0_attributes = objects.PoolAttributeList.from_list(
            [
                {
                    "key": "attribute_one",
                    "value": "True"
                },
                {
                    "key": "attribute_two",
                    "value": "False"
                },
                {
                    "key": "attribute_three",
                    "value": "bar"
                }
            ])

        pools[0].attributes = pool_0_attributes

        pools = self.test_filter.filter(self.context, pools, self.zone)

        self.assertEqual(0, len(pools))


class SchedulerInDoubtDefaultPoolFilterTest(SchedulerFilterTest):

    FILTER = in_doubt_default_pool_filter.InDoubtDefaultPoolFilter

    def test_pools_with_default(self):
        pools = objects.PoolList.from_list(
            [
                {"id": "6c346011-e581-429b-a7a2-6cdf0aba91c3"},
                {"id": "5fabcd37-262c-4cf3-8625-7f419434b6df"}
            ]
        )
        pools = self.test_filter.filter(self.context, pools, self.zone)

        self.assertEqual(1, len(pools))
        self.assertEqual(pools[0].id, "6c346011-e581-429b-a7a2-6cdf0aba91c3")

    def test_pools_without_default(self):
        pools = objects.PoolList.from_list(
            [
                {"id": "24702e43-8a52-440f-ab74-19fc16048860"},
                {"id": "5fabcd37-262c-4cf3-8625-7f419434b6df"}
            ]
        )
        pools = self.test_filter.filter(self.context, pools, self.zone)

        self.assertEqual(2, len(pools))

    def test_no_pools(self):
        pools = objects.PoolList()
        pools = self.test_filter.filter(self.context, pools, self.zone)

        self.assertEqual(0, len(pools))
