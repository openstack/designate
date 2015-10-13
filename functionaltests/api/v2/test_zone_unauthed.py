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
from functionaltests.api.v2.clients.zone_client import ZoneClient
from functionaltests.api.v2.fixtures import ZoneFixture


class ZoneTest(DesignateV2Test):

    def setUp(self):
        super(ZoneTest, self).setUp()
        self.increase_quotas(user='default')
        self.client = ZoneClient.as_user('default', with_token=False)
        self.fixture = self.useFixture(ZoneFixture(user='default'))

    def test_create_zone(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.post_zone,
            datagen.random_zone_data())

    def test_get_fake_zone(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.get_zone, 'junk')

    def test_get_existing_zone(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.get_zone,
            self.fixture.created_zone.id)

    def test_list_zones(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.list_zones)

    def test_update_fake_zone(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.patch_zone, 'junk',
            datagen.random_zone_data())

    def test_update_existing_zone(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.patch_zone,
            self.fixture.created_zone.id, datagen.random_zone_data())

    def test_delete_fake_zone(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.delete_zone, 'junk')

    def test_delete_existing_zone(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.delete_zone,
            self.fixture.created_zone.id)
