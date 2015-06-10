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
from functionaltests.common import utils
from functionaltests.api.v2.base import DesignateV2Test
from functionaltests.api.v2.clients.recordset_client import RecordsetClient
from functionaltests.api.v2.clients.zone_client import ZoneClient


@utils.parameterized_class
class RecordsetTest(DesignateV2Test):

    def setUp(self):
        super(RecordsetTest, self).setUp()
        self.increase_quotas(user='default')
        self.ensure_tld_exists('com')
        resp, self.zone = ZoneClient.as_user('default').post_zone(
            datagen.random_zone_data())
        ZoneClient.as_user('default').wait_for_zone(self.zone.id)
        self.client = RecordsetClient.as_user('default', with_token=False)

    def tearDown(self):
        super(RecordsetTest, self).tearDown()
        resp, self.zone = ZoneClient.as_user('default').delete_zone(
            self.zone.id)

    def test_create_a_recordset(self):
        post_model = datagen.random_a_recordset(self.zone.name)
        self.assertRaises(
            exceptions.Unauthorized, self.client.post_recordset, self.zone.id,
            post_model)

    def test_get_fake_recordset(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.get_recordset, self.zone.id,
            'junk')

    def test_get_existing_recordset(self):
        post_model = datagen.random_a_recordset(self.zone.name)
        resp, resp_model = RecordsetClient.as_user('default') \
            .post_recordset(self.zone.id, post_model)
        self.assertRaises(
            exceptions.Unauthorized, self.client.get_recordset, self.zone.id,
            resp_model.id)

    def test_list_recordsets(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.list_recordsets, self.zone.id)

    def test_update_fake_recordset(self):
        put_model = datagen.random_a_recordset(self.zone.name)
        self.assertRaises(
            exceptions.Unauthorized, self.client.put_recordset, self.zone.id,
            'junk', put_model)

    def test_update_existing_recordset(self):
        post_model = datagen.random_a_recordset(self.zone.name)
        resp, resp_model = RecordsetClient.as_user('default') \
            .post_recordset(self.zone.id, post_model)
        self.assertRaises(
            exceptions.Unauthorized, self.client.put_recordset, self.zone.id,
            resp_model.id, post_model)

    def test_delete_fake_recordset(self):
        self.assertRaises(
            exceptions.Unauthorized, self.client.delete_recordset,
            self.zone.id, 'junk')

    def test_delete_existing_recordset(self):
        post_model = datagen.random_a_recordset(self.zone.name)
        resp, resp_model = RecordsetClient.as_user('default') \
            .post_recordset(self.zone.id, post_model)
        self.assertRaises(
            exceptions.Unauthorized, self.client.delete_recordset,
            self.zone.id, resp_model.id)
