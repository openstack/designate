# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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
import oslo_messaging as messaging

from designate import exceptions
from designate.central import service as central_service
from designate.tests.test_api.test_v2 import ApiV2TestCase


class ApiV2TsigKeysTest(ApiV2TestCase):
    def setUp(self):
        super(ApiV2TsigKeysTest, self).setUp()

        # Set the policy to accept everyone as an admin, as this is an
        # admin-only API
        self.policy({'admin': '@'})

    def test_create_tsigkey(self):
        # Create a TSIG Key
        fixture = self.get_tsigkey_fixture(0)
        response = self.client.post_json('/tsigkeys/', fixture)

        # Check the headers are what we expect
        self.assertEqual(201, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Check the generated values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIn('created_at', response.json)
        self.assertIsNone(response.json['updated_at'])

        # Check the supplied values returned are what we expect
        self.assertDictContainsSubset(fixture, response.json)

    def test_create_tsigkey_validation(self):
        # NOTE: The schemas should be tested separately to the API. So we
        #       don't need to test every variation via the API itself.
        # Fetch a fixture
        fixture = self.get_tsigkey_fixture(0)

        # Add a junk field to the body
        fixture['junk'] = 'Junk Field'

        # Ensure it fails with a 400
        body = fixture

        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/tsigkeys', body)

    def test_create_tsigkey_name_missing(self):
        fixture = self.get_tsigkey_fixture(0)
        del fixture['name']
        body = fixture
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/tsigkeys', body)

    def test_create_tsigkey_name_too_long(self):
        fixture = self.get_tsigkey_fixture(0)
        fixture['name'] = 'test-key-' + 'x' * 160
        body = fixture
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/tsigkeys', body)

    def test_create_tsigkey_algorithm_missing(self):
        fixture = self.get_tsigkey_fixture(0)
        del fixture['algorithm']
        body = fixture
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/tsigkeys', body)

    def test_create_tsigkey_algorithm_invalid_type(self):
        fixture = self.get_tsigkey_fixture(0)
        fixture['algorithm'] = "ABC"
        body = fixture
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/tsigkeys', body)

    def test_create_tsigkey_secret_missing(self):
        fixture = self.get_tsigkey_fixture(0)
        del fixture['secret']
        body = fixture
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/tsigkeys', body)

    def test_create_tsigkey_secret_too_long(self):
        fixture = self.get_tsigkey_fixture(0)
        fixture['secret'] = 'x' * 161
        body = fixture
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/tsigkeys', body)

    def test_create_tsigkey_scope_missing(self):
        fixture = self.get_tsigkey_fixture(0)
        del fixture['scope']
        body = fixture
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/tsigkeys', body)

    def test_create_tsigkey_scope_invalid_type(self):
        fixture = self.get_tsigkey_fixture(0)
        fixture['scope'] = "ABC"
        body = fixture
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/tsigkeys', body)

    def test_create_tsigkey_resource_id_missing(self):
        fixture = self.get_tsigkey_fixture(0)
        del fixture['resource_id']
        body = fixture
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/tsigkeys', body)

    def test_create_tsigkey_invalid_resource_id(self):
        fixture = self.get_tsigkey_fixture(0)
        fixture['resource_id'] = "xyz"
        body = fixture
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/tsigkeys', body)

    def test_create_tsigkey_duplicate(self):
        # Prepare a TSIG Key fixture
        fixture = self.get_tsigkey_fixture(0)
        body = fixture

        # Create the first TSIG Key
        response = self.client.post_json('/tsigkeys', body)
        self.assertEqual(201, response.status_int)

        self._assert_exception('duplicate_tsigkey', 409,
                               self.client.post_json, '/tsigkeys', body)

    def test_get_tsigkeys(self):
        response = self.client.get('/tsigkeys/')

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('tsigkeys', response.json)
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # We should start with 0 tsigkeys
        self.assertEqual(0, len(response.json['tsigkeys']))

        data = [self.create_tsigkey(name='tsigkey-%s' % i)
                for i in range(1, 10)]
        self._assert_paging(data, '/tsigkeys', key='tsigkeys')
        self._assert_invalid_paging(data, '/tsigkeys', key='tsigkeys')

    @patch.object(central_service.Service, 'find_tsigkeys',
                  side_effect=messaging.MessagingTimeout())
    def test_get_tsigkeys_timeout(self, _):
        self._assert_exception('timeout', 504, self.client.get, '/tsigkeys/')

    def test_get_tsigkey(self):
        # Create a tsigkey
        tsigkey = self.create_tsigkey()

        response = self.client.get('/tsigkeys/%s' % tsigkey.id,
                                   headers=[('Accept', 'application/json')])

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Check the generated values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIn('created_at', response.json)
        self.assertIsNone(response.json['updated_at'])

        # Check the supplied values returned are what we expect
        self.assertEqual(tsigkey.name, response.json['name'])
        self.assertEqual(
            tsigkey.algorithm, response.json['algorithm'])
        self.assertEqual(tsigkey.secret, response.json['secret'])
        self.assertEqual(tsigkey.scope, response.json['scope'])
        self.assertEqual(
            tsigkey.resource_id, response.json['resource_id'])

    def test_get_tsigkey_invalid_id(self):
        self._assert_invalid_uuid(self.client.get, '/tsigkeys/%s')

    @patch.object(central_service.Service, 'get_tsigkey',
                  side_effect=messaging.MessagingTimeout())
    def test_get_tsigkey_timeout(self, _):
        url = '/tsigkeys/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980'
        self._assert_exception('timeout', 504, self.client.get, url,
                               headers={'Accept': 'application/json'})

    @patch.object(central_service.Service, 'get_tsigkey',
                  side_effect=exceptions.TsigKeyNotFound())
    def test_get_tsigkey_missing(self, _):
        url = '/tsigkeys/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980'
        self._assert_exception('tsigkey_not_found', 404, self.client.get, url,
                               headers={'Accept': 'application/json'})

    def test_update_tsigkey(self):
        # Create a TSIG Key
        tsigkey = self.create_tsigkey()

        # Prepare an update body
        body = {'secret': 'prefix-%s' % tsigkey.secret}

        response = self.client.patch_json('/tsigkeys/%s' % tsigkey.id, body)

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIsNotNone(response.json['updated_at'])
        self.assertEqual('prefix-%s' % tsigkey['secret'],
                         response.json['secret'])

    def test_update_tsigkey_invalid_id(self):
        self._assert_invalid_uuid(self.client.patch_json, '/tsigkeys/%s')

    @patch.object(central_service.Service, 'get_tsigkey',
                  side_effect=exceptions.DuplicateTsigKey())
    def test_update_tsigkey_duplicate(self, _):
        # Prepare an update body
        body = {'name': 'AnyOldName'}

        url = '/tsigkeys/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980'

        # Ensure it fails with a 409
        self._assert_exception('duplicate_tsigkey', 409,
                               self.client.patch_json, url, body)

    def test_update_tsigkey_secret_too_long(self):
        tsigkey = self.create_tsigkey()
        body = {'secret': 'x' * 161}
        url = '/tsigkeys/%s' % tsigkey.id
        self._assert_exception('invalid_object', 400,
                               self.client.patch_json, url, body)

    def test_update_tsigkey_invalid_scope_type(self):
        tsigkey = self.create_tsigkey()
        body = {'scope': 'abc'}
        url = '/tsigkeys/%s' % tsigkey.id
        self._assert_exception('invalid_object', 400,
                               self.client.patch_json, url, body)

    def test_update_tsigkey_invalid_algorithm(self):
        tsigkey = self.create_tsigkey()
        body = {'algorithm': 'abc'}
        url = '/tsigkeys/%s' % tsigkey.id
        self._assert_exception('invalid_object', 400,
                               self.client.patch_json, url, body)

    def test_update_tsigkey_junk_field(self):
        tsigkey = self.create_tsigkey()
        body = {'junk': 'abc'}
        url = '/tsigkeys/%s' % tsigkey.id
        self._assert_exception('invalid_object', 400,
                               self.client.patch_json, url, body)

    @patch.object(central_service.Service, 'get_tsigkey',
                  side_effect=messaging.MessagingTimeout())
    def test_update_tsigkey_timeout(self, _):
        # Prepare an update body
        body = {'name': 'AnyOldName'}

        url = '/tsigkeys/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980'

        # Ensure it fails with a 504
        self._assert_exception('timeout', 504, self.client.patch_json,
                               url, body)

    @patch.object(central_service.Service, 'get_tsigkey',
                  side_effect=exceptions.TsigKeyNotFound())
    def test_update_tsigkey_missing(self, _):
        # Prepare an update body
        body = {'name': 'AnyOldName'}

        url = '/tsigkeys/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980'

        # Ensure it fails with a 404
        self._assert_exception('tsigkey_not_found', 404,
                               self.client.patch_json, url, body)

    def test_delete_tsigkey(self):
        tsigkey = self.create_tsigkey()

        self.client.delete('/tsigkeys/%s' % tsigkey['id'], status=204)

    def test_delete_tsigkey_invalid_id(self):
        self._assert_invalid_uuid(self.client.delete, '/tsigkeys/%s')

    @patch.object(central_service.Service, 'delete_tsigkey',
                  side_effect=messaging.MessagingTimeout())
    def test_delete_tsigkey_timeout(self, _):
        url = '/tsigkeys/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980'

        self._assert_exception('timeout', 504, self.client.delete, url)

    @patch.object(central_service.Service, 'delete_tsigkey',
                  side_effect=exceptions.TsigKeyNotFound())
    def test_delete_tsigkey_missing(self, _):
        url = '/tsigkeys/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980'

        self._assert_exception('tsigkey_not_found', 404, self.client.delete,
                               url)
