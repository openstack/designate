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

from functionaltests.api.v2.base import DesignateV2Test
from functionaltests.api.v2.clients.recordset_client import RecordsetClient
from functionaltests.api.v2.clients.zone_client import ZoneClient
from functionaltests.api.v2.clients.zone_import_client import ZoneImportClient
from functionaltests.api.v2.clients.zone_export_client import ZoneExportClient
from functionaltests.api.v2.fixtures import ZoneFixture
from functionaltests.api.v2.fixtures import ZoneImportFixture
from functionaltests.api.v2.fixtures import ZoneExportFixture
from functionaltests.common.models import ZoneFileRecord


class ZoneImportTest(DesignateV2Test):

    def setUp(self):
        super(ZoneImportTest, self).setUp()
        self.increase_quotas(user='default')
        self.ensure_tld_exists('com')

    def test_import_domain(self):
        user = 'default'
        import_client = ZoneImportClient.as_user(user)
        zone_client = ZoneClient.as_user(user)

        fixture = self.useFixture(ZoneImportFixture(user=user))
        import_id = fixture.zone_import.id

        resp, model = import_client.get_zone_import(import_id)
        self.assertEqual(200, resp.status)
        self.assertEqual('COMPLETE', model.status)
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
        self.ensure_tld_exists('com')

    def test_export_domain(self):
        user = 'default'
        zone_fixture = self.useFixture(ZoneFixture(user=user))
        zone = zone_fixture.created_zone

        export_fixture = self.useFixture(ZoneExportFixture(zone.id, user=user))
        export_id = export_fixture.zone_export.id

        export_client = ZoneExportClient.as_user(user)

        resp, model = export_client.get_zone_export(export_id)
        self.assertEqual(200, resp.status)
        self.assertEqual('COMPLETE', model.status)

        # fetch the zone file
        resp, zone_file = export_client.get_exported_zone(export_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(zone.name, zone_file.origin)
        self.assertEqual(zone.ttl, zone_file.ttl)

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
