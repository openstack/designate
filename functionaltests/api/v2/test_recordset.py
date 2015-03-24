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

from tempest_lib.exceptions import NotFound

from functionaltests.common import datagen
from functionaltests.common import utils
from functionaltests.api.v2.base import DesignateV2Test


@utils.parameterized_class
class RecordsetTest(DesignateV2Test):

    def setUp(self):
        super(RecordsetTest, self).setUp()
        self.increase_quotas()
        resp, self.zone = self.zone_client.post_zone(
            datagen.random_zone_data())
        self.wait_for_zone(self.zone.id)

    def wait_for_recordset(self, zone_id, recordset_id):
        self.wait_for_condition(
            lambda: self.is_recordset_active(zone_id, recordset_id))

    def wait_for_404(self, zone_id, recordset_id):
        self.wait_for_condition(
            lambda: self.is_recordset_404(zone_id, recordset_id))

    def is_recordset_active(self, zone_id, recordset_id):
        resp, model = self.recordset_client.get_recordset(
            zone_id, recordset_id)
        self.assertEqual(resp.status, 200)
        if model.status == 'ACTIVE':
            return True
        elif model.status == 'ERROR':
            raise Exception("Saw ERROR status")
        return False

    def is_recordset_404(self, zone_id, recordset_id):
        try:
            self.recordset_client.get_recordset(zone_id, recordset_id)
        except NotFound:
            return True
        return False

    def test_list_recordsets(self):
        resp, model = self.recordset_client.list_recordsets(self.zone.id)
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
        resp, post_resp_model = self.recordset_client.post_recordset(
            self.zone.id, post_model)
        self.assertEqual(resp.status, 202, "on post response")
        self.assertEqual(post_resp_model.status, "PENDING")
        self.assertEqual(post_resp_model.name, post_model.name)
        self.assertEqual(post_resp_model.records, post_model.records)
        self.assertEqual(post_resp_model.ttl, post_model.ttl)

        recordset_id = post_resp_model.id
        self.wait_for_recordset(self.zone.id, recordset_id)

        put_model = make_recordset(self.zone)
        del put_model.name  # don't try to update the name
        resp, put_resp_model = self.recordset_client.put_recordset(
            self.zone.id, recordset_id, put_model)
        self.assertEqual(resp.status, 202, "on put response")
        self.assertEqual(put_resp_model.status, "PENDING")
        self.assertEqual(put_resp_model.name, post_model.name)
        self.assertEqual(put_resp_model.records, put_model.records)
        self.assertEqual(put_resp_model.ttl, put_model.ttl)

        self.wait_for_recordset(self.zone.id, recordset_id)

        resp, delete_resp_model = self.recordset_client.delete_recordset(
            self.zone.id, recordset_id)
        self.assertEqual(resp.status, 202, "on delete response")
        self.wait_for_404(self.zone.id, recordset_id)
