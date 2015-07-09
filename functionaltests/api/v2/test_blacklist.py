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
from functionaltests.api.v2.clients.blacklist_client import BlacklistClient


class BlacklistTest(DesignateV2Test):
    def _create_blacklist(self, blacklist_model, user='admin'):
        resp, model = BlacklistClient.as_user(user).post_blacklist(
            blacklist_model)
        self.assertEqual(resp.status, 201)
        return resp, model

    def test_list_blacklists(self):
        self._create_blacklist(datagen.random_blacklist_data())
        resp, model = BlacklistClient.as_user('admin').list_blacklists()
        self.assertEqual(resp.status, 200)
        self.assertGreater(len(model.blacklists), 0)

    def test_create_blacklist(self):
        self._create_blacklist(datagen.random_blacklist_data(), user='admin')

    def test_update_blacklist(self):
        post_model = datagen.random_blacklist_data()
        resp, old_model = self._create_blacklist(post_model)

        patch_model = datagen.random_blacklist_data()
        resp, new_model = BlacklistClient.as_user('admin').patch_blacklist(
            old_model.id, patch_model)
        self.assertEqual(resp.status, 200)

        resp, model = BlacklistClient.as_user('admin').get_blacklist(
            new_model.id)
        self.assertEqual(resp.status, 200)
        self.assertEqual(new_model.id, old_model.id)
        self.assertEqual(new_model.pattern, model.pattern)

    def test_delete_blacklist(self):
        resp, model = self._create_blacklist(datagen.random_blacklist_data())
        resp, model = BlacklistClient.as_user('admin').delete_blacklist(
            model.id)
        self.assertEqual(resp.status, 204)

    def test_get_blacklist_404(self):
        client = BlacklistClient.as_user('admin')
        self._assert_exception(
            exceptions.NotFound,
            'blacklist_not_found',
            404, client.get_blacklist,
            str(uuid.uuid4()))

    def test_update_blacklist_404(self):
        model = datagen.random_blacklist_data()

        client = BlacklistClient.as_user('admin')
        self._assert_exception(
            exceptions.NotFound,
            'blacklist_not_found',
            404,
            client.patch_blacklist,
            str(uuid.uuid4()), model)

    def test_delete_blacklist_404(self):
        client = BlacklistClient.as_user('admin')
        self._assert_exception(
            exceptions.NotFound,
            'blacklist_not_found',
            404,
            client.delete_blacklist,
            str(uuid.uuid4()))

    def test_get_blacklist_invalid_uuid(self):
        client = BlacklistClient.as_user('admin')
        self._assert_invalid_uuid(client.get_blacklist, 'fooo')

    def test_update_blacklist_invalid_uuid(self):
        model = datagen.random_blacklist_data()

        client = BlacklistClient.as_user('admin')
        self._assert_invalid_uuid(client.patch_blacklist, 'fooo', model)

    def test_delete_blacklist_invalid_uuid(self):
        client = BlacklistClient.as_user('admin')
        self._assert_invalid_uuid(client.get_blacklist, 'fooo')
