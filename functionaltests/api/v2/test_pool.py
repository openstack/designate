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
