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
import unittest

import six
from dns import zone as dnszone
from webtest import TestApp
from oslo_config import cfg

from designate.api import admin as admin_api
from designate.api import middleware
from designate.tests.test_api.test_v2 import ApiV2TestCase


cfg.CONF.import_opt('enabled_extensions_admin', 'designate.api.admin',
                    group='service:api')


class APIV2ZoneImportExportTest(ApiV2TestCase):
    def setUp(self):
        super(APIV2ZoneImportExportTest, self).setUp()

        self.config(enable_api_admin=True, group='service:api')
        self.config(enabled_extensions_admin=['zones'], group='service:api')
        # Create the application
        adminapp = admin_api.factory({})
        # Inject the NormalizeURIMiddleware middleware
        adminapp = middleware.NormalizeURIMiddleware(adminapp)
        # Inject the FaultWrapper middleware
        adminapp = middleware.FaultWrapperMiddleware(adminapp)
        # Inject the TestContext middleware
        adminapp = middleware.TestContextMiddleware(
            adminapp, self.admin_context.tenant,
            self.admin_context.tenant)
        # Obtain a test client
        self.adminclient = TestApp(adminapp)

    # # Zone import/export
    def test_missing_origin(self):
        fixture = self.get_zonefile_fixture(variant='noorigin')

        response = self.client.post_json('/zones/tasks/imports', fixture,
                        headers={'Content-type': 'text/dns'})

        import_id = response.json_body['id']
        self.wait_for_import(import_id, errorok=True)

        url = '/zones/tasks/imports/%s' % import_id

        response = self.client.get(url)
        self.assertEqual('ERROR', response.json['status'])
        origin_msg = ("The $ORIGIN statement is required and must be the"
                     " first statement in the zonefile.")
        self.assertEqual(origin_msg, response.json['message'])

    def test_missing_soa(self):
        fixture = self.get_zonefile_fixture(variant='nosoa')

        response = self.client.post_json('/zones/tasks/imports', fixture,
                        headers={'Content-type': 'text/dns'})

        import_id = response.json_body['id']
        self.wait_for_import(import_id, errorok=True)

        url = '/zones/tasks/imports/%s' % import_id

        response = self.client.get(url)
        self.assertEqual('ERROR', response.json['status'])
        origin_msg = ("Malformed zonefile.")
        self.assertEqual(origin_msg, response.json['message'])

    def test_malformed_zonefile(self):
        fixture = self.get_zonefile_fixture(variant='malformed')

        response = self.client.post_json('/zones/tasks/imports', fixture,
                        headers={'Content-type': 'text/dns'})

        import_id = response.json_body['id']
        self.wait_for_import(import_id, errorok=True)

        url = '/zones/tasks/imports/%s' % import_id

        response = self.client.get(url)
        self.assertEqual('ERROR', response.json['status'])
        origin_msg = ("Malformed zonefile.")
        self.assertEqual(origin_msg, response.json['message'])

    def test_import_export(self):
        # Since v2 doesn't support getting records, import and export the
        # fixture, making sure they're the same according to dnspython
        post_response = self.client.post('/zones/tasks/imports',
                                         self.get_zonefile_fixture(),
                                         headers={'Content-type': 'text/dns'})

        import_id = post_response.json_body['id']
        self.wait_for_import(import_id)

        url = '/zones/tasks/imports/%s' % import_id
        response = self.client.get(url)

        self.policy({'zone_export': '@'})
        get_response = self.adminclient.get('/zones/export/%s' %
                                       response.json['zone_id'],
                                       headers={'Accept': 'text/dns'})
        if six.PY2:
            exported_zonefile = get_response.body
        else:
            exported_zonefile = get_response.body.decode('utf-8')

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

    # Metadata tests
    def test_metadata_exists_imports(self):
        response = self.client.get('/zones/tasks/imports')

        # Make sure the fields exist
        self.assertIn('metadata', response.json)
        self.assertIn('total_count', response.json['metadata'])

    def test_metadata_exists_exports(self):
        response = self.client.get('/zones/tasks/imports')

        # Make sure the fields exist
        self.assertIn('metadata', response.json)
        self.assertIn('total_count', response.json['metadata'])

    @unittest.skip("See bug 1582241 and 1570859")
    def test_total_count_imports(self):
        response = self.client.get('/zones/tasks/imports')

        # There are no imported zones by default
        self.assertEqual(0, response.json['metadata']['total_count'])

        # Create a zone import
        response = self.client.post('/zones/tasks/imports',
                                    self.get_zonefile_fixture(),
                                    headers={'Content-type': 'text/dns'})

        response = self.client.get('/zones/tasks/imports')

        # Make sure total_count picked it up
        self.assertEqual(1, response.json['metadata']['total_count'])

    def test_total_count_exports(self):
        response = self.client.get('/zones/tasks/exports')

        # There are no exported zones by default
        self.assertEqual(0, response.json['metadata']['total_count'])
