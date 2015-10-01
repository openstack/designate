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

from functionaltests.api.v2.models.pool_model import PoolModel
from functionaltests.api.v2.models.pool_model import PoolListModel
from functionaltests.common.client import ClientMixin


class PoolClient(ClientMixin):

    def pools_uri(self, filters=None):
        return self.create_uri("/pools", filters=filters)

    def pool_uri(self, pool_id):
        return "{0}/{1}".format(self.pools_uri(), pool_id)

    def list_pools(self, filters=None, **kwargs):
        resp, body = self.client.get(self.pools_uri(filters), **kwargs)
        return self.deserialize(resp, body, PoolListModel)

    def get_pool(self, pool_id, **kwargs):
        resp, body = self.client.get(self.pool_uri(pool_id))
        return self.deserialize(resp, body, PoolModel)

    def post_pool(self, pool_model, **kwargs):
        resp, body = self.client.post(
            self.pools_uri(),
            body=pool_model.to_json(), **kwargs)
        return self.deserialize(resp, body, PoolModel)

    def patch_pool(self, pool_id, pool_model, **kwargs):
        resp, body = self.client.patch(
            self.pool_uri(pool_id),
            body=pool_model.to_json(), **kwargs)
        return self.deserialize(resp, body, PoolModel)

    def delete_pool(self, pool_id, **kwargs):
        return self.client.delete(self.pool_uri(pool_id), **kwargs)
