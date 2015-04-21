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

from tempest_lib.exceptions import RestClientException

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
        resp, self.zone = ZoneClient.as_user('default').post_zone(
            datagen.random_zone_data())
        ZoneClient.as_user('default').wait_for_zone(self.zone.id)

    def test_list_recordsets(self):
        resp, model = RecordsetClient.as_user('default') \
            .list_recordsets(self.zone.id)
        self.assertEqual(resp.status, 200)

    @utils.parameterized({
        'A': dict(
            make_recordset=lambda z: datagen.random_a_recordset(z.name)),
        'AAAA': dict(
            make_recordset=lambda z: datagen.random_aaaa_recordset(z.name)),
        'CNAME': dict(
            make_recordset=lambda z: datagen.random_cname_recordset(z.name)),
        'MX': dict(
            make_recordset=lambda z: datagen.random_mx_recordset(z.name)),
    })
    def test_crud_recordset(self, make_recordset):
        post_model = make_recordset(self.zone)
        resp, post_resp_model = RecordsetClient.as_user('default') \
            .post_recordset(self.zone.id, post_model)
        self.assertEqual(resp.status, 202, "on post response")
        self.assertEqual(post_resp_model.status, "PENDING")
        self.assertEqual(post_resp_model.name, post_model.name)
        self.assertEqual(post_resp_model.records, post_model.records)
        self.assertEqual(post_resp_model.ttl, post_model.ttl)

        recordset_id = post_resp_model.id
        RecordsetClient.as_user('default').wait_for_recordset(
            self.zone.id, recordset_id)

        put_model = make_recordset(self.zone)
        del put_model.name  # don't try to update the name
        resp, put_resp_model = RecordsetClient.as_user('default') \
            .put_recordset(self.zone.id, recordset_id, put_model)
        self.assertEqual(resp.status, 202, "on put response")
        self.assertEqual(put_resp_model.status, "PENDING")
        self.assertEqual(put_resp_model.name, post_model.name)
        self.assertEqual(put_resp_model.records, put_model.records)
        self.assertEqual(put_resp_model.ttl, put_model.ttl)

        RecordsetClient.as_user('default').wait_for_recordset(
            self.zone.id, recordset_id)

        resp, delete_resp_model = RecordsetClient.as_user('default') \
            .delete_recordset(self.zone.id, recordset_id)
        self.assertEqual(resp.status, 202, "on delete response")
        RecordsetClient.as_user('default').wait_for_404(
            self.zone.id, recordset_id)


class RecordsetOwnershipTest(DesignateV2Test):

    def setUp(self):
        super(RecordsetOwnershipTest, self).setUp()
        self.increase_quotas(user='default')
        self.increase_quotas(user='alt')

    def test_no_create_recordset_by_alt_tenant(self):
        resp, zone = ZoneClient.as_user('default').post_zone(
            datagen.random_zone_data())

        # try with name=A123456.zone.com.
        recordset = datagen.random_a_recordset(zone_name=zone.name)
        self.assertRaises(RestClientException,
            lambda: RecordsetClient.as_user('alt')
                    .post_recordset(zone.id, recordset))

        # try with name=zone.com.
        recordset.name = zone.name
        self.assertRaises(RestClientException,
            lambda: RecordsetClient.as_user('alt')
                    .post_recordset(zone.id, recordset))

    def test_no_create_super_recordsets(self):
        # default creates zone a.b.c.example.com.
        # alt fails to create record with name b.c.example.com
        zone_data = datagen.random_zone_data()
        recordset = datagen.random_a_recordset(zone_name=zone_data.name)
        recordset.name = 'b.c.' + zone_data.name
        zone_data.name = 'a.b.c.' + zone_data.name

        resp, zone = ZoneClient.as_user('default').post_zone(zone_data)
        self.assertRaises(RestClientException,
            lambda: RecordsetClient.as_user('alt')
                    .post_recordset(zone.id, recordset))

    def test_no_create_recordset_via_alt_domain(self):
        resp, zone = ZoneClient.as_user('default').post_zone(
            datagen.random_zone_data())
        resp, alt_zone = ZoneClient.as_user('alt').post_zone(
            datagen.random_zone_data())

        # alt attempts to create record with name A12345.{zone}
        recordset = datagen.random_a_recordset(zone_name=zone.name)
        self.assertRaises(RestClientException,
            lambda: RecordsetClient.as_user('alt')
                    .post_recordset(zone.id, recordset))
        self.assertRaises(RestClientException,
            lambda: RecordsetClient.as_user('alt')
                    .post_recordset(alt_zone.id, recordset))
