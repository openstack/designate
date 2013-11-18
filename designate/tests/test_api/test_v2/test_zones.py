# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
from mock import patch
from designate import exceptions
from designate.central import service as central_service
from designate.openstack.common.rpc import common as rpc_common
from designate.tests.test_api.test_v2 import ApiV2TestCase


class ApiV2ZonesTest(ApiV2TestCase):
    def setUp(self):
        super(ApiV2ZonesTest, self).setUp()

        # Create a server
        self.create_server()

    def test_missing_accept(self):
        self.client.get('/zones/123', status=400)

    def test_bad_accept(self):
        self.client.get('/zones/123', headers={'Accept': 'test/goat'},
                        status=406)

    def test_missing_content_type(self):
        self.client.post('/zones', status=415)

    def test_bad_content_type(self):
        self.client.post('/zones', headers={'Content-type': 'test/goat'},
                         status=415)

    def test_create_zone(self):
        # Create a zone
        fixture = self.get_domain_fixture(0)
        response = self.client.post_json('/zones/', {'zone': fixture})

        # Check the headers are what we expect
        self.assertEqual(201, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('zone', response.json)
        self.assertIn('links', response.json['zone'])
        self.assertIn('self', response.json['zone']['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json['zone'])
        self.assertIn('created_at', response.json['zone'])
        self.assertEqual('ACTIVE', response.json['zone']['status'])
        self.assertIsNone(response.json['zone']['updated_at'])

        for k in fixture:
            self.assertEqual(fixture[k], response.json['zone'][k])

    def test_create_zone_validation(self):
        # NOTE: The schemas should be tested separatly to the API. So we
        #       don't need to test every variation via the API itself.
        # Fetch a fixture
        fixture = self.get_domain_fixture(0)

        # Add a junk field to the wrapper
        body = {'zone': fixture, 'junk': 'Junk Field'}

        # Ensure it fails with a 400
        response = self.client.post_json('/zones/', body, status=400)
        self.assertEqual(400, response.status_int)

        # Add a junk field to the body
        fixture['junk'] = 'Junk Field'

        # Ensure it fails with a 400
        body = {'zone': fixture}
        self.client.post_json('/zones/', body, status=400)

    @patch.object(central_service.Service, 'create_domain',
                  side_effect=rpc_common.Timeout())
    def test_create_zone_timeout(self, _):
        fixture = self.get_domain_fixture(0)

        body = {'zone': fixture}
        self.client.post_json('/zones/', body, status=504)

    @patch.object(central_service.Service, 'create_domain',
                  side_effect=exceptions.DuplicateDomain())
    def test_create_zone_duplicate(self, _):
        fixture = self.get_domain_fixture(0)

        body = {'zone': fixture}
        self.client.post_json('/zones/', body, status=409)

    def test_get_zones(self):
        response = self.client.get('/zones/')

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('zones', response.json)
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # We should start with 0 zones
        self.assertEqual(0, len(response.json['zones']))

        # Test with 1 zone
        self.create_domain()

        response = self.client.get('/zones/')

        self.assertIn('zones', response.json)
        self.assertEqual(1, len(response.json['zones']))

        # test with 2 zones
        self.create_domain(fixture=1)

        response = self.client.get('/zones/')

        self.assertIn('zones', response.json)
        self.assertEqual(2, len(response.json['zones']))

    @patch.object(central_service.Service, 'find_domains',
                  side_effect=rpc_common.Timeout())
    def test_get_zones_timeout(self, _):
        self.client.get('/zones/', status=504)

    def test_get_zone(self):
        # Create a zone
        zone = self.create_domain()

        response = self.client.get('/zones/%s' % zone['id'],
                                   headers=[('Accept', 'application/json')])

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('zone', response.json)
        self.assertIn('links', response.json['zone'])
        self.assertIn('self', response.json['zone']['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json['zone'])
        self.assertIn('created_at', response.json['zone'])
        self.assertEqual('ACTIVE', response.json['zone']['status'])
        self.assertIsNone(response.json['zone']['updated_at'])
        self.assertEqual(zone['name'], response.json['zone']['name'])
        self.assertEqual(zone['email'], response.json['zone']['email'])

    @patch.object(central_service.Service, 'get_domain',
                  side_effect=rpc_common.Timeout())
    def test_get_zone_timeout(self, _):
        self.client.get('/zones/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980',
                        headers={'Accept': 'application/json'},
                        status=504)

    @patch.object(central_service.Service, 'get_domain',
                  side_effect=exceptions.DomainNotFound())
    def test_get_zone_missing(self, _):
        self.client.get('/zones/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980',
                        headers={'Accept': 'application/json'},
                        status=404)

    def test_get_zone_invalid_id(self):
        self.skip('We don\'t guard against this in APIv2 yet')

        # The letter "G" is not valid in a UUID
        self.client.get('/zones/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff9GG',
                        headers={'Accept': 'application/json'},
                        status=404)

        # Badly formed UUID
        self.client.get('/zones/2fdadfb1cf964259ac6bbb7b6d2ff9GG',
                        headers={'Accept': 'application/json'},
                        status=404)

        # Integer
        self.client.get('/zones/12345',
                        headers={'Accept': 'application/json'},
                        status=404)

    def test_update_zone(self):
        # Create a zone
        zone = self.create_domain()

        # Prepare an update body
        body = {'zone': {'email': 'prefix-%s' % zone['email']}}

        response = self.client.patch_json('/zones/%s' % zone['id'], body,
                                          status=200)

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('zone', response.json)
        self.assertIn('links', response.json['zone'])
        self.assertIn('self', response.json['zone']['links'])
        self.assertIn('status', response.json['zone'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json['zone'])
        self.assertIsNotNone(response.json['zone']['updated_at'])
        self.assertEqual('prefix-%s' % zone['email'],
                         response.json['zone']['email'])

    def test_update_zone_validation(self):
        # NOTE: The schemas should be tested separatly to the API. So we
        #       don't need to test every variation via the API itself.
        # Create a zone
        zone = self.create_domain()

        # Prepare an update body with junk in the wrapper
        body = {'zone': {'email': 'prefix-%s' % zone['email']},
                'junk': 'Junk Field'}

        # Ensure it fails with a 400
        self.client.patch_json('/zones/%s' % zone['id'], body, status=400)

        # Prepare an update body with junk in the body
        body = {'zone': {'email': 'prefix-%s' % zone['email'],
                         'junk': 'Junk Field'}}

        # Ensure it fails with a 400
        self.client.patch_json('/zones/%s' % zone['id'], body, status=400)

    @patch.object(central_service.Service, 'get_domain',
                  side_effect=exceptions.DuplicateDomain())
    def test_update_zone_duplicate(self, _):
        # Prepare an update body
        body = {'zone': {'email': 'example@example.org'}}

        # Ensure it fails with a 409
        self.client.patch_json('/zones/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980',
                               body, status=409)

    @patch.object(central_service.Service, 'get_domain',
                  side_effect=rpc_common.Timeout())
    def test_update_zone_timeout(self, _):
        # Prepare an update body
        body = {'zone': {'email': 'example@example.org'}}

        # Ensure it fails with a 504
        self.client.patch_json('/zones/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980',
                               body, status=504)

    @patch.object(central_service.Service, 'get_domain',
                  side_effect=exceptions.DomainNotFound())
    def test_update_zone_missing(self, _):
        # Prepare an update body
        body = {'zone': {'email': 'example@example.org'}}

        # Ensure it fails with a 404
        self.client.patch_json('/zones/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980',
                               body, status=404)

    def test_update_zone_invalid_id(self):
        self.skip('We don\'t guard against this in APIv2 yet')

        # Prepare an update body
        body = {'zone': {'email': 'example@example.org'}}

        # The letter "G" is not valid in a UUID
        self.client.patch_json('/zones/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff9GG',
                               body, status=404)

        # Badly formed UUID
        self.client.patch_json('/zones/2fdadfb1cf964259ac6bbb7b6d2ff980',
                               body, status=404)

        # Integer
        self.client.patch_json('/zones/12345',
                               body, status=404)

    def test_delete_zone(self):
        zone = self.create_domain()

        self.client.delete('/zones/%s' % zone['id'], status=204)

    @patch.object(central_service.Service, 'delete_domain',
                  side_effect=rpc_common.Timeout())
    def test_delete_zone_timeout(self, _):
        self.client.delete('/zones/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980',
                           status=504)

    @patch.object(central_service.Service, 'delete_domain',
                  side_effect=exceptions.DomainNotFound())
    def test_delete_zone_missing(self, _):
        self.client.delete('/zones/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980',
                           status=404)

    def test_delete_zone_invalid_id(self):
        self.skip('We don\'t guard against this in APIv2 yet')

        # The letter "G" is not valid in a UUID
        self.client.delete('/zones/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff9GG',
                           status=404)

        # Badly formed UUID
        self.client.delete('/zones/2fdadfb1cf964259ac6bbb7b6d2ff980',
                           status=404)

        # Integer
        self.client.delete('/zones/12345', status=404)

    # Zone import/export
    def test_missing_origin(self):
        self.client.post('/zones',
                         self.get_zonefile_fixture(variant='noorigin'),
                         headers={'Content-type': 'text/dns'}, status=400)

    def test_missing_soa(self):
        self.client.post('/zones',
                         self.get_zonefile_fixture(variant='nosoa'),
                         headers={'Content-type': 'text/dns'}, status=400)

    def test_malformed_zonefile(self):
        self.client.post('/zones',
                         self.get_zonefile_fixture(variant='malformed'),
                         headers={'Content-type': 'text/dns'}, status=400)

    def test_import_export(self):
        # Since v2 doesn't support getting records, import and export the
        # fixture, making sure they're the same according to dnspython
        post_response = self.client.post('/zones',
                                         self.get_zonefile_fixture(),
                                         headers={'Content-type': 'text/dns'})
        get_response = self.client.get('/zones/%s' %
                                       post_response.json['zone']['id'],
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
        # Delete non-delegation NS, since they won't be the same
        imported.delete_rdataset(imported.origin, 'NS')
        exported.delete_rdataset(exported.origin, 'NS')
        self.assertEqual(imported, exported)
