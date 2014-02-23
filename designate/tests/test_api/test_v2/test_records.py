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


class ApiV2RecordsTest(ApiV2TestCase):
    def setUp(self):
        super(ApiV2RecordsTest, self).setUp()

        # Create a domain
        self.domain = self.create_domain()

        name = 'www.%s' % self.domain['name']
        self.rrset = self.create_recordset(self.domain, name=name)

    def test_create(self):
        # Create a zone
        fixture = self.get_record_fixture(self.rrset['type'], fixture=0)

        url = '/zones/%s/recordsets/%s/records' % (
            self.domain['id'], self.rrset['id'])

        response = self.client.post_json(url, {'record': fixture})
        self.assertIn('record', response.json)
        self.assertIn('links', response.json['record'])
        self.assertIn('self', response.json['record']['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json['record'])
        self.assertIn('created_at', response.json['record'])
        self.assertIsNone(response.json['record']['updated_at'])

        for k in fixture:
            self.assertEqual(fixture[k], response.json['record'][k])

    def test_create_validation(self):
        fixture = self.get_record_fixture(self.rrset['type'], fixture=0)

        # Add a junk field to the wrapper
        body = {'record': fixture, 'junk': 'Junk Field'}

        url = '/zones/%s/recordsets/%s/records' % (
            self.domain['id'], self.rrset['id'])

        # Ensure it fails with a 400
        response = self.client.post_json(url, body, status=400)

        self.assertEqual(400, response.status_int)

        # Add a junk field to the body
        fixture['junk'] = 'Junk Field'
        body = {'record': fixture}

        url = '/zones/%s/recordsets/%s/records' % (
            self.domain['id'], self.rrset['id'])

        # Ensure it fails with a 400
        response = self.client.post_json(url, body, status=400)

    @patch.object(central_service.Service, 'create_record',
                  side_effect=rpc_common.Timeout())
    def test_create_recordset_timeout(self, _):
        fixture = self.get_record_fixture(self.rrset['type'], fixture=0)

        body = {'record': fixture}

        url = '/zones/%s/recordsets/%s/records' % (
            self.domain['id'], self.rrset['id'])

        response = self.client.post_json(url, body, status=504)
        self.assertEqual(504, response.json['code'])
        self.assertEqual('timeout', response.json['type'])

    @patch.object(central_service.Service, 'create_record',
                  side_effect=exceptions.DuplicateRecord())
    def test_create_record_duplicate(self, _):

        fixture = self.get_record_fixture(self.rrset['type'], fixture=0)

        body = {'record': fixture}

        url = '/zones/%s/recordsets/%s/records' % (
            self.domain['id'], self.rrset['id'])

        response = self.client.post_json(url, body, status=409)
        self.assertEqual(409, response.json['code'])
        self.assertEqual('duplicate_record', response.json['type'])

    def test_create_record_invalid_domain(self):
        fixture = self.get_record_fixture(self.rrset['type'], fixture=0)

        body = {'record': fixture}

        url = '/zones/ba751950-6193-11e3-949a-0800200c9a66/recordsets/' \
            'ba751950-6193-11e3-949a-0800200c9a66/records'
        response = self.client.post_json(url, body, status=404)
        self.assertEqual(404, response.json['code'])
        self.assertEqual('domain_not_found', response.json['type'])

    def test_create_record_invalid_rrset(self):
        fixture = self.get_record_fixture(self.rrset['type'], fixture=0)

        body = {'record': fixture}

        url = '/zones/%s/recordsets/' \
            'ba751950-6193-11e3-949a-0800200c9a66/records' % self.domain['id']
        response = self.client.post_json(url, body, status=404)
        self.assertEqual(404, response.json['code'])
        self.assertEqual('recordset_not_found', response.json['type'])

    def test_get_records(self):
        url = '/zones/%s/recordsets/%s/records' % (
            self.domain['id'], self.rrset['id'])
        response = self.client.get(url)

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('records', response.json)
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # We should start with 0 recordsets
        self.assertEqual(0, len(response.json['records']))

        data = [self.create_record(self.domain, self.rrset,
                data='192.168.0.%s' % i) for i in xrange(2, 10)]

        self._assert_paging(data, url, key='records')

    @patch.object(central_service.Service, 'find_records',
                  side_effect=rpc_common.Timeout())
    def test_get_records_timeout(self, _):
        url = '/zones/ba751950-6193-11e3-949a-0800200c9a66/recordsets/' \
            'ba751950-6193-11e3-949a-0800200c9a66/records'

        response = self.client.get(url, status=504)
        self.assertEqual(504, response.json['code'])
        self.assertEqual('timeout', response.json['type'])

    def test_get_record(self):
        # Create a record
        record = self.create_record(self.domain, self.rrset)

        url = '/zones/%s/recordsets/%s/records/%s' % (
            self.domain['id'], self.rrset['id'], record['id'])
        response = self.client.get(url)

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('record', response.json)
        self.assertIn('links', response.json['record'])
        self.assertIn('self', response.json['record']['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json['record'])
        self.assertIn('created_at', response.json['record'])
        self.assertIn('version', response.json['record'])
        self.assertIsNone(response.json['record']['updated_at'])
        self.assertEqual(record['data'], response.json['record']['data'])

    @patch.object(central_service.Service, 'get_record',
                  side_effect=rpc_common.Timeout())
    def test_get_record_timeout(self, _):
        url = '/zones/%s/recordsets/%s/records/' \
            'ba751950-6193-11e3-949a-0800200c9a66' % (
                self.domain['id'], self.rrset['id'])
        response = self.client.get(url, headers={'Accept': 'application/json'},
                                   status=504)
        self.assertEqual(504, response.json['code'])
        self.assertEqual('timeout', response.json['type'])

    @patch.object(central_service.Service, 'get_record',
                  side_effect=exceptions.RecordNotFound())
    def test_get_record_missing(self, _):
        url = '/zones/%s/recordsets/%s/records/' \
            'ba751950-6193-11e3-949a-0800200c9a66' % (
                self.domain['id'], self.rrset['id'])
        response = self.client.get(url, headers={'Accept': 'application/json'},
                                   status=404)
        self.assertEqual(404, response.json['code'])
        self.assertEqual('record_not_found', response.json['type'])

    def test_get_record_invalid_id(self):
        url = '/zones/%s/recordsets/%s/records/%s'
        self._assert_invalid_uuid(self.client.get, url)

    def test_update_record(self):
        # Create a recordset
        record = self.create_record(self.domain, self.rrset)

        # Prepare an update body
        body = {'record': {'description': 'Tester'}}

        url = '/zones/%s/recordsets/%s/records/%s' % (
            self.domain['id'], self.rrset['id'], record['id'])
        response = self.client.patch_json(url, body, status=200)

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('record', response.json)
        self.assertIn('links', response.json['record'])
        self.assertIn('self', response.json['record']['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json['record'])
        self.assertIsNotNone(response.json['record']['updated_at'])
        self.assertEqual('Tester', response.json['record']['description'])

    def test_update_record_validation(self):
        # NOTE: The schemas should be tested separatly to the API. So we
        #       don't need to test every variation via the API itself.
        # Create a zone
        record = self.create_record(self.domain, self.rrset)

        url = '/zones/%s/recordsets/%s/records/%s' % (
            self.domain['id'], self.rrset['id'], record['id'])

        # Prepare an update body with junk in the wrapper
        body = {'record': {'description': 'Tester'}, 'junk': 'Junk Field'}

        # Ensure it fails with a 400
        self.client.patch_json(url, body, status=400)

        # Prepare an update body with junk in the body
        body = {'record': {'description': 'Tester', 'junk': 'Junk Field'}}

        # Ensure it fails with a 400
        self.client.patch_json(url, body, status=400)

    @patch.object(central_service.Service, 'get_record',
                  side_effect=exceptions.DuplicateRecord())
    def test_update_record_duplicate(self, _):
        url = '/zones/%s/recordsets/%s/records/' \
            'ba751950-6193-11e3-949a-0800200c9a66' % (
                self.domain['id'], self.rrset['id'])

        # Prepare an update body
        body = {'record': {'description': 'Tester'}}

        # Ensure it fails with a 409
        response = self.client.patch_json(url, body, status=409)
        self.assertEqual(409, response.json['code'])
        self.assertEqual('duplicate_record', response.json['type'])

    @patch.object(central_service.Service, 'get_record',
                  side_effect=rpc_common.Timeout())
    def test_update_record_timeout(self, _):
        url = '/zones/%s/recordsets/%s/records/' \
            'ba751950-6193-11e3-949a-0800200c9a66' % (
                self.domain['id'], self.rrset['id'])

        # Prepare an update body
        body = {'record': {'description': 'Tester'}}

        # Ensure it fails with a 504
        response = self.client.patch_json(url, body, status=504)
        self.assertEqual(504, response.json['code'])
        self.assertEqual('timeout', response.json['type'])

    @patch.object(central_service.Service, 'get_record',
                  side_effect=exceptions.RecordNotFound())
    def test_update_record_missing(self, _):
        url = '/zones/%s/recordsets/%s/records/' \
            'ba751950-6193-11e3-949a-0800200c9a66' % (
                self.domain['id'], self.rrset['id'])

        # Prepare an update body
        body = {'record': {'description': 'Tester'}}

        # Ensure it fails with a 404
        response = self.client.patch_json(url, body, status=404)
        self.assertEqual(404, response.json['code'])
        self.assertEqual('record_not_found', response.json['type'])

    def test_update_record_invalid_id(self):
        url = '/zones/%s/recordsets/%s/records/%s'
        self._assert_invalid_uuid(self.client.patch_json, url)

    def test_delete_record(self):
        record = self.create_record(self.domain, self.rrset)

        url = '/zones/%s/recordsets/%s/records/%s' % (
            self.domain['id'], self.rrset['id'], record['id'])

        self.client.delete(url, status=204)

    @patch.object(central_service.Service, 'delete_record',
                  side_effect=rpc_common.Timeout())
    def test_delete_record_timeout(self, _):
        url = '/zones/%s/recordsets/%s/records/' \
            'ba751950-6193-11e3-949a-0800200c9a66' % (
                self.domain['id'], self.rrset['id'])

        self.client.delete(url, status=504)

    @patch.object(central_service.Service, 'delete_record',
                  side_effect=exceptions.RecordNotFound())
    def test_delete_record_missing(self, _):
        url = '/zones/%s/recordsets/%s/records/' \
            'ba751950-6193-11e3-949a-0800200c9a66' % (
                self.domain['id'], self.rrset['id'])
        self.client.delete(url, status=404)

    def test_delete_record_invalid_id(self):
        url = '/zones/%s/recordsets/%s/records/%s'
        self._assert_invalid_uuid(self.client.delete, url)
