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

from functionaltests.common import datagen
from functionaltests.api.v2.base import DesignateV2Test


class ZoneTest(DesignateV2Test):

    def setUp(self):
        super(ZoneTest, self).setUp()
        self.increase_quotas()

    def _create_zone(self, zone_model):
        resp, model = self.zone_client.post_zone(zone_model)
        self.assertEqual(resp.status, 202)
        self.wait_for_zone(model.id)
        return resp, model

    def test_list_zones(self):
        self._create_zone(datagen.random_zone_data())
        resp, model = self.zone_client.list_zones()
        self.assertEqual(resp.status, 200)
        self.assertGreater(len(model.zones), 0)

    def test_create_zone(self):
        self._create_zone(datagen.random_zone_data())

    def test_update_zone(self):
        post_model = datagen.random_zone_data()
        resp, old_model = self._create_zone(post_model)

        patch_model = datagen.random_zone_data()
        del patch_model.name  # don't try to override the zone name
        resp, new_model = self.zone_client.patch_zone(old_model.id,
                                                 patch_model)
        self.assertEqual(resp.status, 202)
        self.wait_for_zone(new_model.id)

        resp, model = self.zone_client.get_zone(new_model.id)
        self.assertEqual(resp.status, 200)
        self.assertEqual(new_model.id, old_model.id)
        self.assertEqual(new_model.name, old_model.name)
        self.assertEqual(new_model.ttl, patch_model.ttl)
        self.assertEqual(new_model.email, patch_model.email)

    def test_delete_zone(self):
        resp, model = self._create_zone(datagen.random_zone_data())
        resp, model = self.zone_client.delete_zone(model.id)
        self.assertEqual(resp.status, 202)
        self.wait_for_zone_404(model.id)
