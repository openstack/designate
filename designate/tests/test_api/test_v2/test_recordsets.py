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
from mock import patch
from designate import exceptions
from designate.central import service as central_service
from designate.openstack.common.rpc import common as rpc_common
from designate.tests.test_api.test_v2 import ApiV2TestCase


class ApiV2RecordSetsTest(ApiV2TestCase):
    def setUp(self):
        super(ApiV2RecordSetsTest, self).setUp()

        # Create a domain
        self.domain = self.create_domain()

    def test_create_recordset(self):
        # Create a zone
        fixture = self.get_recordset_fixture(self.domain['name'], fixture=0)
        response = self.client.post_json(
            '/zones/%s/recordsets' % self.domain['id'], {'recordset': fixture})

        # Check the headers are what we expect
        self.assertEqual(201, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('recordset', response.json)
        self.assertIn('links', response.json['recordset'])
        self.assertIn('self', response.json['recordset']['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json['recordset'])
        self.assertIn('created_at', response.json['recordset'])
        self.assertIsNone(response.json['recordset']['updated_at'])

        for k in fixture:
            self.assertEqual(fixture[k], response.json['recordset'][k])

    def test_create_recordset_invalid_id(self):
        self._assert_invalid_uuid(self.client.post, '/zones/%s/recordsets')

    def test_create_recordset_validation(self):
        # NOTE: The schemas should be tested separatly to the API. So we
        #       don't need to test every variation via the API itself.
        # Fetch a fixture
        fixture = self.get_recordset_fixture(self.domain['name'], fixture=0)

        # Add a junk field to the wrapper
        body = {'recordset': fixture, 'junk': 'Junk Field'}

        url = '/zones/%s/recordsets' % self.domain['id']

        # Ensure it fails with a 400
        self._assert_exception(
            'invalid_object', 400, self.client.post_json, url, body)

        # Add a junk field to the body
        fixture['junk'] = 'Junk Field'
        body = {'recordset': fixture}

        # Ensure it fails with a 400
        self._assert_exception(
            'invalid_object', 400, self.client.post_json, url, body)

    @patch.object(central_service.Service, 'create_recordset',
                  side_effect=rpc_common.Timeout())
    def test_create_recordset_timeout(self, _):
        fixture = self.get_recordset_fixture(self.domain['name'], fixture=0)

        body = {'recordset': fixture}

        url = '/zones/%s/recordsets' % self.domain['id']

        self._assert_exception('timeout', 504, self.client.post_json, url,
                               body)

    @patch.object(central_service.Service, 'create_recordset',
                  side_effect=exceptions.DuplicateRecordSet())
    def test_create_recordset_duplicate(self, _):
        fixture = self.get_recordset_fixture(self.domain['name'], fixture=0)

        body = {'recordset': fixture}

        url = '/zones/%s/recordsets' % self.domain['id']

        self._assert_exception('duplicate_recordset', 409,
                               self.client.post_json, url, body)

    def test_create_recordset_invalid_domain(self):
        fixture = self.get_recordset_fixture(self.domain['name'], fixture=0)

        body = {'recordset': fixture}

        url = '/zones/ba751950-6193-11e3-949a-0800200c9a66/recordsets'

        self._assert_exception('domain_not_found', 404, self.client.post_json,
                               url, body)

    def test_recordsets_invalid_url(self):
        url = '/zones/recordsets'
        self._assert_exception('not_found', 404, self.client.get, url)
        self._assert_exception('not_found', 404, self.client.post_json, url)

        # Pecan returns a 405 for Patch and delete operations
        response = self.client.patch_json(url, status=405)
        self.assertEqual(405, response.status_int)

        response = self.client.delete(url, status=405)
        self.assertEqual(405, response.status_int)

    def test_get_recordsets(self):
        url = '/zones/%s/recordsets' % self.domain['id']

        response = self.client.get(url)

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('recordsets', response.json)
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # We should start with 0 recordsets
        self.assertEqual(0, len(response.json['recordsets']))

        data = [self.create_recordset(self.domain,
                name='x-%s.%s' % (i, self.domain['name']))
                for i in xrange(0, 10)]

        self._assert_paging(data, url, key='recordsets')

        self._assert_invalid_paging(data, url, key='recordsets')

    def test_get_recordsets_invalid_id(self):
        self._assert_invalid_uuid(self.client.get, '/zones/%s/recordsets')

    @patch.object(central_service.Service, 'find_recordsets',
                  side_effect=rpc_common.Timeout())
    def test_get_recordsets_timeout(self, _):
        url = '/zones/ba751950-6193-11e3-949a-0800200c9a66/recordsets'

        self._assert_exception('timeout', 504, self.client.get, url)

    def test_get_recordset(self):
        # Create a recordset
        recordset = self.create_recordset(self.domain)

        url = '/zones/%s/recordsets/%s' % (self.domain['id'], recordset['id'])
        response = self.client.get(url)

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('recordset', response.json)
        self.assertIn('links', response.json['recordset'])
        self.assertIn('self', response.json['recordset']['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json['recordset'])
        self.assertIn('created_at', response.json['recordset'])
        self.assertIsNone(response.json['recordset']['updated_at'])
        self.assertEqual(recordset['name'], response.json['recordset']['name'])
        self.assertEqual(recordset['type'], response.json['recordset']['type'])

    def test_get_recordset_invalid_id(self):
        self._assert_invalid_uuid(self.client.get, '/zones/%s/recordsets/%s')

    @patch.object(central_service.Service, 'get_recordset',
                  side_effect=rpc_common.Timeout())
    def test_get_recordset_timeout(self, _):
        url = '/zones/%s/recordsets/ba751950-6193-11e3-949a-0800200c9a66' % (
            self.domain['id'])

        self._assert_exception('timeout', 504, self.client.get, url,
                               headers={'Accept': 'application/json'})

    @patch.object(central_service.Service, 'get_recordset',
                  side_effect=exceptions.RecordSetNotFound())
    def test_get_recordset_missing(self, _):
        url = '/zones/%s/recordsets/ba751950-6193-11e3-949a-0800200c9a66' % (
            self.domain['id'])

        self._assert_exception('recordset_not_found', 404,
                               self.client.get, url,
                               headers={'Accept': 'application/json'})

    def test_update_recordset(self):
        # Create a recordset
        recordset = self.create_recordset(self.domain)

        # Prepare an update body
        body = {'recordset': {'description': 'Tester'}}

        url = '/zones/%s/recordsets/%s' % (recordset['domain_id'],
                                           recordset['id'])
        response = self.client.patch_json(url, body, status=200)

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('recordset', response.json)
        self.assertIn('links', response.json['recordset'])
        self.assertIn('self', response.json['recordset']['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json['recordset'])
        self.assertIsNotNone(response.json['recordset']['updated_at'])
        self.assertEqual('Tester', response.json['recordset']['description'])

    def test_update_recordset_invalid_id(self):
        self._assert_invalid_uuid(
            self.client.patch_json, '/zones/%s/recordsets/%s')

    def test_update_recordset_validation(self):
        # NOTE: The schemas should be tested separatly to the API. So we
        #       don't need to test every variation via the API itself.
        # Create a zone
        recordset = self.create_recordset(self.domain)

        # Prepare an update body with junk in the wrapper
        body = {'recordset': {'description': 'Tester'}, 'junk': 'Junk Field'}

        # Ensure it fails with a 400
        url = '/zones/%s/recordsets/%s' % (recordset['domain_id'],
                                           recordset['id'])

        self._assert_exception('invalid_object', 400, self.client.patch_json,
                               url, body)

        # Prepare an update body with junk in the body
        body = {'recordset': {'description': 'Tester', 'junk': 'Junk Field'}}

        # Ensure it fails with a 400
        self._assert_exception('invalid_object', 400, self.client.patch_json,
                               url, body)

    @patch.object(central_service.Service, 'get_recordset',
                  side_effect=exceptions.DuplicateRecordSet())
    def test_update_recordset_duplicate(self, _):
        # Prepare an update body
        body = {'recordset': {'description': 'Tester'}}

        # Ensure it fails with a 409
        url = ('/zones/%s/recordsets/ba751950-6193-11e3-949a-0800200c9a66'
               % (self.domain['id']))

        self._assert_exception('duplicate_recordset', 409,
                               self.client.patch_json, url, body)

    @patch.object(central_service.Service, 'get_recordset',
                  side_effect=rpc_common.Timeout())
    def test_update_recordset_timeout(self, _):
        # Prepare an update body
        body = {'recordset': {'description': 'Tester'}}

        # Ensure it fails with a 504
        url = ('/zones/%s/recordsets/ba751950-6193-11e3-949a-0800200c9a66'
               % (self.domain['id']))

        self._assert_exception('timeout', 504, self.client.patch_json, url,
                               body)

    @patch.object(central_service.Service, 'get_recordset',
                  side_effect=exceptions.RecordSetNotFound())
    def test_update_recordset_missing(self, _):
        # Prepare an update body
        body = {'recordset': {'description': 'Tester'}}

        # Ensure it fails with a 404
        url = ('/zones/%s/recordsets/ba751950-6193-11e3-949a-0800200c9a66'
               % (self.domain['id']))

        self._assert_exception('recordset_not_found', 404,
                               self.client.patch_json, url, body)

    def test_delete_recordset(self):
        recordset = self.create_recordset(self.domain)

        url = '/zones/%s/recordsets/%s' % (recordset['domain_id'],
                                           recordset['id'])
        self.client.delete(url, status=204)

    @patch.object(central_service.Service, 'delete_recordset',
                  side_effect=rpc_common.Timeout())
    def test_delete_recordset_timeout(self, _):
        url = ('/zones/%s/recordsets/ba751950-6193-11e3-949a-0800200c9a66'
               % (self.domain['id']))

        self._assert_exception('timeout', 504, self.client.delete, url)

    @patch.object(central_service.Service, 'delete_recordset',
                  side_effect=exceptions.RecordSetNotFound())
    def test_delete_recordset_missing(self, _):
        url = ('/zones/%s/recordsets/ba751950-6193-11e3-949a-0800200c9a66'
               % (self.domain['id']))

        self._assert_exception('recordset_not_found', 404,
                               self.client.delete, url)

    def test_delete_recordset_invalid_id(self):
        self._assert_invalid_uuid(
            self.client.delete, '/zones/%s/recordsets/%s')
