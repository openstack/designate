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
from functionaltests.api.v2.clients.blacklist_client import BlacklistClient
from functionaltests.api.v2.fixtures import BlacklistFixture


class BlacklistTest(DesignateV2Test):

    def setUp(self):
        super(BlacklistTest, self).setUp()
        self.increase_quotas(user='admin')
        self.client = BlacklistClient.as_user('admin', with_token=False)
        self.fixture = self.useFixture(BlacklistFixture(user='admin'))

    def test_create_blacklist(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.post_blacklist,
            datagen.random_blacklist_data())

    def test_get_fake_blacklist(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.get_blacklist, 'junk')

    def test_get_existing_blacklist(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.get_blacklist,
            self.fixture.created_blacklist.id)

    def test_list_blacklists(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.list_blacklists)

    def test_update_fake_blacklist(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.patch_blacklist, 'junk',
            datagen.random_blacklist_data())

    def test_update_existing_blacklist(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.patch_blacklist,
            self.fixture.created_blacklist.id, datagen.random_blacklist_data())

    def test_delete_fake_blacklist(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.delete_blacklist, 'junk')

    def test_delete_existing_blacklist(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.delete_blacklist,
            self.fixture.created_blacklist.id)
