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


class PoolTest(DesignateV2Test):
    def _create_pool(self, pool_model, user='admin'):
        resp, model = PoolClient.as_user(user).post_pool(pool_model)
        self.assertEqual(resp.status, 201)
        return resp, model

    def test_list_pools(self):
        self._create_pool(datagen.random_pool_data())
        resp, model = PoolClient.as_user('admin').list_pools()
        self.assertEqual(resp.status, 200)
        self.assertGreater(len(model.pools), 0)

    def test_create_pool(self):
        self._create_pool(datagen.random_pool_data(), user='admin')

    def test_update_pool(self):
        post_model = datagen.random_pool_data()
        resp, old_model = self._create_pool(post_model)

        patch_model = datagen.random_pool_data()
        resp, new_model = PoolClient.as_user('admin').patch_pool(
            old_model.id, patch_model)
        self.assertEqual(resp.status, 202)

        resp, model = PoolClient.as_user('admin').get_pool(new_model.id)
        self.assertEqual(resp.status, 200)
        self.assertEqual(new_model.id, old_model.id)
        self.assertEqual(new_model.name, patch_model.name)

    def test_delete_pool(self):
        resp, model = self._create_pool(datagen.random_pool_data())
        resp, model = PoolClient.as_user('admin').delete_pool(model.id)
        self.assertEqual(resp.status, 204)

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
