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
from oslo.config import cfg
from oslo_log import log as logging

from designate.tests.test_api.test_v2 import ApiV2TestCase

LOG = logging.getLogger(__name__)


def _attributes_to_api(attributes):
    result = {}
    for attribute in attributes:
        result[attribute['key']] = attribute['value']

    return result


class ApiV2PoolsTest(ApiV2TestCase):
    def setUp(self):
        super(ApiV2PoolsTest, self).setUp()

        # All Pool operations should be performed as an admin, so..
        # Override to policy to make everyone an admin.
        self.policy({'admin': '@'})

    def test_create_pool(self):
        # Prepare a Pool fixture
        fixture = self.get_pool_fixture(fixture=0)
        fixture['attributes'] = _attributes_to_api(fixture['attributes'])

        response = self.client.post_json(
            '/pools', fixture)

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
        self.assertEqual(response.json['name'], fixture['name'])
        self.assertEqual(
            response.json['description'], fixture['description'])
        self.assertEqual(
            response.json['attributes'], fixture['attributes'])
        self.assertEqual(
            response.json['ns_records'], fixture['ns_records'])

    def test_create_pool_validation(self):
        # NOTE: The schemas should be tested separatly to the API. So we
        #       don't need to test every variation via the API itself.
        # Fetch a fixture
        fixture = self.get_pool_fixture(fixture=0)

        # Set an invalid scope
        fixture['attributes'] = {
            'scope': 'INVALID'
        }

        body = {'pool': fixture}
        # Ensure it fails with a 400
        self._assert_exception(
            'invalid_object', 400, self.client.post_json, '/pools', body)

        # Reset the correct attributes
        fixture['attributes'] = self.get_pool_attribute_fixture(fixture=0)

        # Add a junk field to the body
        fixture['junk'] = 'Junk Field'
        body = fixture
        # Ensure it fails with a 400
        self._assert_exception(
            'invalid_object', 400, self.client.post_json, '/pools', body)

    def test_create_pool_duplicate(self):
        # Prepare a Pool fixture
        fixture = self.get_pool_fixture(fixture=0)
        fixture['attributes'] = _attributes_to_api(fixture['attributes'])

        body = fixture
        response = self.client.post_json('/pools', body)

        # Check that the create went through
        self.assertEqual(201, response.status_int)

        self._assert_exception('duplicate_pool', 409,
                               self.client.post_json, '/pools', body)

    def test_get_pools(self):
        response = self.client.get('/pools')

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('pools', response.json)
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # We should start with 1 default pool
        self.assertEqual(1, len(response.json['pools']))

        # GET the default pool
        pool_id = cfg.CONF['service:central'].default_pool_id
        default_pool = self.central_service.get_pool(self.admin_context,
                                                     pool_id)

        # Add the default pool into the list
        data = [self.create_pool(name='x-%s' % i) for i in xrange(0, 10)]
        data.insert(0, default_pool)

        # Test the paging of the list
        self._assert_paging(data, '/pools', key='pools')
        self._assert_invalid_paging(data, '/pools', key='pools')

    def test_get_pool(self):
        # Create a pool
        pool = self.create_pool()

        url = '/pools/%s' % pool['id']
        response = self.client.get(url)

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
        self.assertEqual(pool['name'], response.json['name'])
        self.assertEqual(pool['description'],
                         response.json['description'])

        self.assertEqual(len(pool['attributes']),
                         len(response.json['attributes']))
        for attribute in pool['attributes']:
            self.assertEqual(
                attribute['value'],
                response.json['attributes'][attribute['key']])

        self.assertEqual(len(pool['ns_records']),
                         len(response.json['ns_records']))
        self.assertEqual(
            [n.hostname for n in pool['ns_records']],
            [n['hostname'] for n in response.json['ns_records']])

    def test_update_pool(self):
        # Create a pool
        pool = self.create_pool()

        # Prepare an update body
        body = {'description': 'Tester'}

        url = '/pools/%s' % pool['id']
        response = self.client.patch_json(url, body, status=200)

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIsNotNone(response.json['updated_at'])
        self.assertEqual('Tester', response.json['description'])

        # Check the rest of the values are unchanged
        self.assertEqual(pool['name'], response.json['name'])
        self.assertEqual(len(pool['attributes']),
                         len(response.json['attributes']))
        for attribute in pool['attributes']:
            self.assertEqual(
                attribute['value'],
                response.json['attributes'][attribute['key']])

        self.assertEqual(len(pool['ns_records']),
                         len(response.json['ns_records']))
        self.assertEqual(
            [n.hostname for n in pool['ns_records']],
            [n['hostname'] for n in response.json['ns_records']])

    def test_update_pool_ns_records(self):
        # Create a pool
        pool = self.create_pool()

        # Prepare an update body
        body = {'ns_records': [
            {'priority': 1, 'hostname': 'new-ns1.example.org.'},
            {'priority': 2, 'hostname': 'new-ns2.example.org.'},
        ]}

        url = '/pools/%s' % pool['id']
        response = self.client.patch_json(url, body, status=200)

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('id', response.json)
        self.assertIn('links', response.json)

        # Check the values returned are what we expect
        self.assertEqual(2, len(response.json['ns_records']))
        self.assertEqual(['new-ns1.example.org.', 'new-ns2.example.org.'],
                         [n['hostname'] for n in
                          response.json['ns_records']])

    def test_update_pool_attributes(self):
        # Create a pool
        pool = self.create_pool()

        # Prepare an update body
        body = {"attributes": {"scope": "private"}}

        url = '/pools/%s' % pool['id']
        response = self.client.patch_json(url, body, status=200)

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the values returned are what we expect
        self.assertEqual(1, len(response.json['attributes']))
        self.assertEqual('private',
                         response.json['attributes']['scope'])

    def test_delete_pool(self):
        pool = self.create_pool()
        url = '/pools/%s' % pool['id']
        self.client.delete(url, status=204)
