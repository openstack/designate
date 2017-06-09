# Copyright (c) 2014 Rackspace Hosting
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import six

from designate.tests.test_api.test_v2 import ApiV2TestCase


class ApiV2TldsTest(ApiV2TestCase):
    def setUp(self):
        super(ApiV2TldsTest, self).setUp()

    def test_create_tld(self):
        self.policy({'create_tld': '@'})
        fixture = self.get_tld_fixture(0)
        response = self.client.post_json('/tlds/', fixture)

        # Check the headers are what we expect
        self.assertEqual(201, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIn('created_at', response.json)
        self.assertIsNone(response.json['updated_at'])
        self.assertEqual(fixture['name'], response.json['name'])

    def test_create_tld_validation(self):
        self.policy({'create_tld': '@'})
        invalid_fixture = self.get_tld_fixture(-1)

        # Ensure it fails with a 400
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/tlds', invalid_fixture)

    def test_create_tld_name_is_missing(self):
        self.policy({'create_tld': '@'})
        fixture = self.get_tld_fixture(0)
        del fixture['name']
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/tlds', fixture)

    def test_create_tld_description_is_too_long(self):
        self.policy({'create_tld': '@'})
        fixture = self.get_tld_fixture(0)
        fixture['description'] = 'x' * 161
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/tlds', fixture)

    def test_create_tld_junk_attribute(self):
        self.policy({'create_tld': '@'})
        fixture = self.get_tld_fixture(0)
        fixture['junk'] = 'x'
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/tlds', fixture)

    def test_get_tlds(self):
        self.policy({'find_tlds': '@'})
        response = self.client.get('/tlds/')

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('tlds', response.json)
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # We should start with 0 tlds
        self.assertEqual(0, len(response.json['tlds']))

        data = [self.create_tld(name='tld%s' % i) for i in 'abcdefghijklmn']
        self._assert_paging(data, '/tlds', key='tlds')

    def test_get_tld(self):
        tld = self.create_tld(fixture=0)
        self.policy({'get_tld': '@'})

        response = self.client.get('/tlds/%s' % tld['id'],
                                   headers=[('Accept', 'application/json')])

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIn('created_at', response.json)
        self.assertIsNone(response.json['updated_at'])
        self.assertEqual(self.get_tld_fixture(0)['name'],
                         response.json['name'])

    def test_get_tld_invalid_id(self):
        self._assert_invalid_uuid(self.client.get, '/tlds/%s')

    def test_delete_tld(self):
        tld = self.create_tld(fixture=0)
        self.policy({'delete_tld': '@'})

        self.client.delete('/tlds/%s' % tld['id'], status=204)

    def test_delete_tld_invalid_id(self):
        self._assert_invalid_uuid(self.client.delete, '/tlds/%s')

    def test_update_tld(self):
        tld = self.create_tld(fixture=0)
        self.policy({'update_tld': '@'})

        # Prepare an update body
        body = {'description': 'prefix-%s' % tld['description']}

        response = self.client.patch_json('/tlds/%s' % tld['id'], body,
                                          status=200)

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIsNotNone(response.json['updated_at'])
        self.assertEqual('prefix-%s' % tld['description'],
                         response.json['description'])

    def test_update_tld_description_too_long(self):
        tld = self.create_tld(fixture=0)
        self.policy({'update_tld': '@'})
        body = {'description': 'x' * 161}
        self._assert_exception('invalid_object', 400, self.client.patch_json,
                               '/tlds/%s' % tld['id'], body)

    def test_update_tld_junk_attribute(self):
        tld = self.create_tld(fixture=0)
        self.policy({'update_tld': '@'})
        body = {'junk': 'x'}
        self._assert_exception('invalid_object', 400, self.client.patch_json,
                               '/tlds/%s' % tld['id'], body)

    def test_update_tld_invalid_id(self):
        self._assert_invalid_uuid(self.client.patch_json, '/tlds/%s')

    def test_get_tld_filter(self):
        self.policy({'create_tld': '@'})
        fixtures = [
            self.get_tld_fixture(0),
            self.get_tld_fixture(1)
        ]

        for fixture in fixtures:
            response = self.client.post_json('/tlds/', fixture)

        get_urls = [
            '/tlds?name=com',
            '/tlds?name=co*'
        ]

        correct_results = [1, 2]

        for get_url, correct_result in \
                six.moves.zip(get_urls, correct_results):

            self.policy({'find_tlds': '@'})
            response = self.client.get(get_url)

            # Check the headers are what we expect
            self.assertEqual(200, response.status_int)
            self.assertEqual('application/json', response.content_type)

            # Check that the correct number of tlds match
            self.assertEqual(correct_result, len(response.json['tlds']))

    def test_invalid_tld_filter(self):
        invalid_url = '/tlds?description=test'
        self._assert_exception(
            'bad_request', 400, self.client.get, invalid_url)
