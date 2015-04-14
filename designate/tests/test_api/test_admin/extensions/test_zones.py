# COPYRIGHT 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from dns import zone as dnszone
from oslo.config import cfg

from designate.tests.test_api.test_admin import AdminApiTestCase

cfg.CONF.import_opt('enabled_extensions_admin', 'designate.api.admin',
                    group='service:api')


class AdminApiZoneImportExportTest(AdminApiTestCase):
    def setUp(self):
        self.config(enabled_extensions_admin=['zones'], group='service:api')
        super(AdminApiZoneImportExportTest, self).setUp()

    # Zone import/export
    def test_missing_origin(self):
        self.policy({'zone_import': '@'})
        fixture = self.get_zonefile_fixture(variant='noorigin')

        self._assert_exception('bad_request', 400, self.client.post,
                               '/zones/import',
                               fixture, headers={'Content-type': 'text/dns'})

    def test_missing_soa(self):
        self.policy({'zone_import': '@'})
        fixture = self.get_zonefile_fixture(variant='nosoa')

        self._assert_exception('bad_request', 400, self.client.post,
                               '/zones/import',
                               fixture, headers={'Content-type': 'text/dns'})

    def test_malformed_zonefile(self):
        self.policy({'zone_import': '@'})
        fixture = self.get_zonefile_fixture(variant='malformed')

        self._assert_exception('bad_request', 400, self.client.post,
                               '/zones/import',
                               fixture, headers={'Content-type': 'text/dns'})

    def test_import_export(self):
        self.policy({'default': '@'})
        # Since v2 doesn't support getting records, import and export the
        # fixture, making sure they're the same according to dnspython
        post_response = self.client.post('/zones/import',
                                         self.get_zonefile_fixture(),
                                         headers={'Content-type': 'text/dns'})
        get_response = self.client.get('/zones/export/%s' %
                                       post_response.json['id'],
                                       headers={'Accept': 'text/dns'})

        exported_zonefile = get_response.body
        imported = dnszone.from_text(self.get_zonefile_fixture())
        exported = dnszone.from_text(exported_zonefile)
        # Compare SOA emails, since zone comparison takes care of origin
        imported_soa = imported.get_rdataset(imported.origin, 'SOA')
        imported_email = imported_soa[0].rname.to_text()
        exported_soa = exported.get_rdataset(exported.origin, 'SOA')
        exported_email = exported_soa[0].rname.to_text()
        self.assertEqual(imported_email, exported_email)
        # Delete SOAs since they have, at the very least, different serials,
        # and dnspython considers that to be not equal.
        imported.delete_rdataset(imported.origin, 'SOA')
        exported.delete_rdataset(exported.origin, 'SOA')
        # Delete NS records, since they won't be the same
        imported.delete_rdataset(imported.origin, 'NS')
        exported.delete_rdataset(exported.origin, 'NS')
        imported.delete_rdataset('delegation', 'NS')
        self.assertEqual(imported, exported)
