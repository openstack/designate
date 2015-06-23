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

from tempest_lib.exceptions import Conflict
from tempest_lib.exceptions import Forbidden
from tempest_lib.exceptions import NotFound

from functionaltests.common import datagen
from functionaltests.api.v2.base import DesignateV2Test
from functionaltests.api.v2.clients.zone_client import ZoneClient
from functionaltests.api.v2.clients.zone_import_client import ZoneImportClient


class ZoneTest(DesignateV2Test):

    def setUp(self):
        super(ZoneTest, self).setUp()
        self.increase_quotas(user='default')

    def _create_zone(self, zone_model, user='default'):
        resp, model = ZoneClient.as_user(user).post_zone(zone_model)
        self.assertEqual(resp.status, 202)
        ZoneClient.as_user(user).wait_for_zone(model.id)
        return resp, model

    def test_list_zones(self):
        self._create_zone(datagen.random_zone_data())
        resp, model = ZoneClient.as_user('default').list_zones()
        self.assertEqual(resp.status, 200)
        self.assertGreater(len(model.zones), 0)

    def test_create_zone(self):
        self._create_zone(datagen.random_zone_data(), user='default')

    def test_update_zone(self):
        post_model = datagen.random_zone_data()
        resp, old_model = self._create_zone(post_model)

        patch_model = datagen.random_zone_data()
        del patch_model.name  # don't try to override the zone name
        resp, new_model = ZoneClient.as_user('default').patch_zone(
            old_model.id, patch_model)
        self.assertEqual(resp.status, 202)
        ZoneClient.as_user('default').wait_for_zone(new_model.id)

        resp, model = ZoneClient.as_user('default').get_zone(new_model.id)
        self.assertEqual(resp.status, 200)
        self.assertEqual(new_model.id, old_model.id)
        self.assertEqual(new_model.name, old_model.name)
        self.assertEqual(new_model.ttl, patch_model.ttl)
        self.assertEqual(new_model.email, patch_model.email)

    def test_delete_zone(self):
        resp, model = self._create_zone(datagen.random_zone_data())
        resp, model = ZoneClient.as_user('default').delete_zone(model.id)
        self.assertEqual(resp.status, 202)
        ZoneClient.as_user('default').wait_for_zone_404(model.id)


class ZoneOwnershipTest(DesignateV2Test):

    def setup(self):
        super(ZoneTest, self).setUp()
        self.increase_quotas(user='default')
        self.increase_quotas(user='alt')

    def _create_zone(self, zone_model, user):
        resp, model = ZoneClient.as_user(user).post_zone(zone_model)
        self.assertEqual(resp.status, 202)
        ZoneClient.as_user(user).wait_for_zone(model.id)
        return resp, model

    def test_no_create_duplicate_domain(self):
        zone = datagen.random_zone_data()
        self._create_zone(zone, user='default')
        self.assertRaises(Conflict,
            lambda: self._create_zone(zone, user='default'))
        self.assertRaises(Conflict,
            lambda: self._create_zone(zone, user='alt'))

    def test_no_create_subdomain_by_alt_user(self):
        zone = datagen.random_zone_data()
        subzone = datagen.random_zone_data(name='sub.' + zone.name)
        subsubzone = datagen.random_zone_data(name='sub.sub.' + zone.name)
        self._create_zone(zone, user='default')
        self.assertRaises(Forbidden,
            lambda: self._create_zone(subzone, user='alt'))
        self.assertRaises(Forbidden,
            lambda: self._create_zone(subsubzone, user='alt'))

    def test_no_create_superdomain_by_alt_user(self):
        superzone = datagen.random_zone_data()
        zone = datagen.random_zone_data(name="a.b." + superzone.name)
        self._create_zone(zone, user='default')
        self.assertRaises(Forbidden,
            lambda: self._create_zone(superzone, user='alt'))


class ZoneImportTest(DesignateV2Test):

    def setUp(self):
        super(ZoneImportTest, self).setUp()

    def test_import_domain(self):
        user = 'default'
        import_client = ZoneImportClient.as_user(user)
        zone_client = ZoneClient.as_user(user)

        zonefile = datagen.random_zonefile_data()
        resp, model = import_client.post_zone_import(
            zonefile)
        import_id = model.id
        self.assertEqual(resp.status, 202)
        self.assertEqual(model.status, 'PENDING')
        import_client.wait_for_zone_import(import_id)

        resp, model = import_client.get_zone_import(
            model.id)
        self.assertEqual(resp.status, 200)
        self.assertEqual(model.status, 'COMPLETE')

        # Wait for the zone to become 'ACTIVE'
        zone_client.wait_for_zone(model.zone_id)
        resp, zone_model = zone_client.get_zone(model.zone_id)

        # Now make sure we can delete the zone_import
        import_client.delete_zone_import(import_id)
        self.assertRaises(NotFound,
            lambda: import_client.get_zone_import(model.id))
