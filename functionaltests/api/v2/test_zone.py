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

from functionaltests.api.v2.clients.zone_client import ZoneClient
from functionaltests.api.v2.clients.quotas_client import QuotasClient
from functionaltests.api.v2.models.quotas_model import QuotasModel
from functionaltests.common import datagen
from functionaltests.common.base import BaseDesignateTest


class ZoneTest(BaseDesignateTest):

    def __init__(self, *args, **kwargs):
        super(ZoneTest, self).__init__(*args, **kwargs)
        self.client = ZoneClient(self.base_client)
        self.quotas_client = QuotasClient(self.base_client)

    def setUp(self):
        super(ZoneTest, self).setUp()
        self.quotas_client.patch_quotas(
            self.quotas_client.client.tenant_id,
            QuotasModel.from_dict({
                'quota': {
                    'zones': 9999999,
                    'recordset_records': 9999999,
                    'zone_records': 9999999,
                    'zone_recordsets': 9999999}}))

    def wait_for_zone(self, zone_id):
        self.wait_for_condition(lambda: self.is_zone_active(zone_id))

    def wait_for_404(self, zone_id):
        self.wait_for_condition(lambda: self.is_zone_404(zone_id))

    def _create_zone(self, zone_model):
        resp, model = self.client.post_zone(zone_model)
        self.assertEqual(resp.status, 202)
        self.wait_for_zone(model.zone.id)
        return resp, model

    def test_list_zones(self):
        self._create_zone(datagen.random_zone_data())
        resp, model = self.client.list_zones()
        self.assertEqual(resp.status, 200)
        self.assertGreater(len(model.zones), 0)

    def test_create_zone(self):
        self._create_zone(datagen.random_zone_data())

    def test_update_zone(self):
        post_model = datagen.random_zone_data()
        resp, old_model = self._create_zone(post_model)

        patch_model = datagen.random_zone_data()
        del patch_model.zone.name  # don't try to override the zone name
        resp, new_model = self.client.patch_zone(old_model.zone.id,
                                                 patch_model)
        self.assertEqual(resp.status, 202)
        self.wait_for_zone(new_model.zone.id)

        resp, model = self.client.get_zone(new_model.zone.id)
        self.assertEqual(resp.status, 200)
        self.assertEqual(new_model.zone.id, old_model.zone.id)
        self.assertEqual(new_model.zone.name, old_model.zone.name)
        self.assertEqual(new_model.zone.ttl, patch_model.zone.ttl)
        self.assertEqual(new_model.zone.email, patch_model.zone.email)

    def test_delete_zone(self):
        resp, model = self._create_zone(datagen.random_zone_data())
        resp, model = self.client.delete_zone(model.zone.id)
        self.assertEqual(resp.status, 202)
        self.wait_for_404(model.zone.id)
