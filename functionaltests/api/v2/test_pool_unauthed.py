"""
Copyright 2015 Rackspace

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from tempest_lib import exceptions

from functionaltests.common import datagen
from functionaltests.api.v2.base import DesignateV2Test
from functionaltests.api.v2.clients.pool_client import PoolClient
from functionaltests.api.v2.fixtures import PoolFixture


class PoolTest(DesignateV2Test):

    def setUp(self):
        super(PoolTest, self).setUp()
        self.increase_quotas(user='admin')
        self.client = PoolClient.as_user('admin', with_token=False)
        self.fixture = self.useFixture(PoolFixture(user='admin'))

    def test_create_pool(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.post_pool,
            datagen.random_pool_data())

    def test_get_fake_pool(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.get_pool, 'junk')

    def test_get_existing_pool(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.get_pool,
            self.fixture.created_pool.id)

    def test_list_pools(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.list_pools)

    def test_update_fake_pool(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.patch_pool, 'junk',
            datagen.random_pool_data())

    def test_update_existing_pool(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.patch_pool,
            self.fixture.created_pool.id, datagen.random_pool_data())

    def test_delete_fake_pool(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.delete_pool, 'junk')

    def test_delete_existing_pool(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.delete_pool,
            self.fixture.created_pool.id)
