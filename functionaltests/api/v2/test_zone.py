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
from functionaltests.api.v2.clients.recordset_client import RecordsetClient
from functionaltests.api.v2.clients.zone_client import ZoneClient
from functionaltests.api.v2.clients.zone_import_client import ZoneImportClient
from functionaltests.api.v2.clients.zone_export_client import ZoneExportClient
from functionaltests.api.v2.fixtures import ZoneFixture
from functionaltests.api.v2.fixtures import ZoneImportFixture
from functionaltests.api.v2.fixtures import ZoneExportFixture
from functionaltests.common.models import ZoneFileRecord


class ZoneTest(DesignateV2Test):

    def setUp(self):
        super(ZoneTest, self).setUp()
        self.increase_quotas(user='default')
        self.fixture = self.useFixture(ZoneFixture(user='default'))

    def test_list_zones(self):
        resp, model = ZoneClient.as_user('default').list_zones()
        self.assertEqual(resp.status, 200)
        self.assertGreater(len(model.zones), 0)

    def test_create_zone(self):
        self.assertEqual(self.fixture.post_resp.status, 202)

    def test_update_zone(self):
        old_model = self.fixture.created_zone

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
        client = ZoneClient.as_user('default')
        resp, model = client.delete_zone(self.fixture.created_zone.id)
        self.assertEqual(resp.status, 202)
        client.wait_for_zone_404(model.id)


class ZoneOwnershipTest(DesignateV2Test):

    def setup(self):
        super(ZoneTest, self).setUp()
        self.increase_quotas(user='default')
        self.increase_quotas(user='alt')

    def test_no_create_duplicate_domain(self):
        post_model = self.useFixture(ZoneFixture(user='default')).post_model
        self.assertRaises(Conflict,
            lambda: ZoneClient.as_user('default').post_zone(post_model))
        self.assertRaises(Conflict,
            lambda: ZoneClient.as_user('alt').post_zone(post_model))

    def test_no_create_subdomain_by_alt_user(self):
        zone = self.useFixture(ZoneFixture(user='default')).post_model
        subzone = datagen.random_zone_data(name='sub.' + zone.name)
        subsubzone = datagen.random_zone_data(name='sub.sub.' + zone.name)
        self.assertRaises(Forbidden,
            lambda: ZoneClient.as_user('alt').post_zone(subzone))
        self.assertRaises(Forbidden,
            lambda: ZoneClient.as_user('alt').post_zone(subsubzone))

    def test_no_create_superdomain_by_alt_user(self):
        superzone = datagen.random_zone_data()
        zone = datagen.random_zone_data(name="a.b." + superzone.name)
        self.useFixture(ZoneFixture(zone, user='default'))
        self.assertRaises(Forbidden,
            lambda: ZoneClient.as_user('alt').post_zone(superzone))


class ZoneImportTest(DesignateV2Test):

    def setUp(self):
        super(ZoneImportTest, self).setUp()
        self.increase_quotas(user='default')

    def test_import_domain(self):
        user = 'default'
        import_client = ZoneImportClient.as_user(user)
        zone_client = ZoneClient.as_user(user)

        fixture = self.useFixture(ZoneImportFixture(user=user))
        import_id = fixture.zone_import.id

        resp, model = import_client.get_zone_import(import_id)
        self.assertEqual(resp.status, 200)
        self.assertEqual(model.status, 'COMPLETE')
        self.addCleanup(ZoneFixture.cleanup_zone, zone_client, model.zone_id)

        # Wait for the zone to become 'ACTIVE'
        zone_client.wait_for_zone(model.zone_id)
        resp, zone_model = zone_client.get_zone(model.zone_id)

        # Now make sure we can delete the zone_import
        import_client.delete_zone_import(import_id)
        self.assertRaises(NotFound,
            lambda: import_client.get_zone_import(model.id))


class ZoneExportTest(DesignateV2Test):

    def setUp(self):
        super(ZoneExportTest, self).setUp()
        self.increase_quotas(user='default')

    def test_export_domain(self):
        user = 'default'
        zone_fixture = self.useFixture(ZoneFixture(user=user))
        zone = zone_fixture.created_zone

        export_fixture = self.useFixture(ZoneExportFixture(zone.id, user=user))
        export_id = export_fixture.zone_export.id

        export_client = ZoneExportClient.as_user(user)

        resp, model = export_client.get_zone_export(export_id)
        self.assertEqual(resp.status, 200)
        self.assertEqual(model.status, 'COMPLETE')

        # fetch the zone file
        resp, zone_file = export_client.get_exported_zone(export_id)
        self.assertEqual(resp.status, 200)
        self.assertEqual(zone_file.origin, zone.name)
        self.assertEqual(zone_file.ttl, zone.ttl)

        # the list of records in the zone file must match the zone's recordsets
        # (in this case there should be only two records - a SOA and an NS?)
        recordset_client = RecordsetClient.as_user(user)
        resp, model = recordset_client.list_recordsets(zone.id)
        records = []
        for recordset in model.recordsets:
            records.extend(ZoneFileRecord.records_from_recordset(recordset))
        self.assertEqual(set(records), set(zone_file.records))

        export_client.delete_zone_export(export_id)
        self.assertRaises(NotFound,
            lambda: export_client.get_zone_export(export_id))
