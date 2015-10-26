# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hp.com>
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

import uuid

from tempest_lib import exceptions

from functionaltests.common import datagen
from functionaltests.api.v2.base import DesignateV2Test
from functionaltests.api.v2.clients.pool_client import PoolClient
from functionaltests.api.v2.fixtures import PoolFixture


class PoolTest(DesignateV2Test):

    def test_list_pools(self):
        self.useFixture(PoolFixture())
        resp, model = PoolClient.as_user('admin').list_pools()
        self.assertEqual(200, resp.status)
        self.assertGreater(len(model.pools), 0)

    def test_create_pool(self):
        fixture = self.useFixture(PoolFixture())
        post_model = fixture.post_model
        created_pool = fixture.created_pool

        self.assertEqual(post_model.name, created_pool.name)
        self.assertEqual(post_model.ns_records, created_pool.ns_records)

    def test_update_pool(self):
        old_model = self.useFixture(PoolFixture()).created_pool

        patch_model = datagen.random_pool_data()
        resp, new_model = PoolClient.as_user('admin').patch_pool(
            old_model.id, patch_model)
        self.assertEqual(202, resp.status)

        resp, model = PoolClient.as_user('admin').get_pool(new_model.id)
        self.assertEqual(200, resp.status)
        self.assertEqual(old_model.id, new_model.id)
        self.assertEqual(patch_model.name, new_model.name)

    def test_delete_pool(self):
        pool = self.useFixture(PoolFixture()).created_pool
        resp, model = PoolClient.as_user('admin').delete_pool(pool.id)
        self.assertEqual(204, resp.status)

    def test_get_pool_404(self):
        client = PoolClient.as_user('admin')
        self._assert_exception(
            exceptions.NotFound, 'pool_not_found', 404, client.get_pool,
            str(uuid.uuid4()))

    def test_update_pool_404(self):
        model = datagen.random_pool_data()

        client = PoolClient.as_user('admin')
        self._assert_exception(
            exceptions.NotFound, 'pool_not_found', 404, client.patch_pool,
            str(uuid.uuid4()), model)

    def test_delete_pool_404(self):
        client = PoolClient.as_user('admin')
        self._assert_exception(
            exceptions.NotFound, 'pool_not_found', 404, client.delete_pool,
            str(uuid.uuid4()))

    def test_get_pool_invalid_uuid(self):
        client = PoolClient.as_user('admin')
        self._assert_invalid_uuid(client.get_pool, 'fooo')

    def test_update_pool_invalid_uuid(self):
        model = datagen.random_pool_data()

        client = PoolClient.as_user('admin')
        self._assert_invalid_uuid(client.patch_pool, 'fooo', model)

    def test_delete_pool_invalid_uuid(self):
        client = PoolClient.as_user('admin')
        self._assert_invalid_uuid(client.get_pool, 'fooo')
