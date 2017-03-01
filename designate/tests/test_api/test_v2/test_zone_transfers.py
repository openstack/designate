# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Graham Hayes <graham.hayes@hpe.com>
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

from designate.tests.test_api.test_v2 import ApiV2TestCase


class ApiV2ZoneTransfersTest(ApiV2TestCase):
    def setUp(self):
        super(ApiV2ZoneTransfersTest, self).setUp()

        self.zone = self.create_zone()
        self.tenant_1_context = self.get_context(tenant=1)
        self.tenant_2_context = self.get_context(tenant=2)
        self.policy({'admin': '@'})

    def test_create_zone_transfer_request(self):
        response = self.client.post_json(
            '/zones/%s/tasks/transfer_requests' % (self.zone.id),
            {})

        # Check the headers are what we expect
        self.assertEqual(201, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIn('created_at', response.json)
        self.assertEqual('ACTIVE', response.json['status'])
        self.assertEqual(
            self.zone.name,
            response.json['zone_name'])
        self.assertEqual(
            self.zone.id,
            response.json['zone_id'])
        self.assertIsNone(response.json['updated_at'])

    def test_create_zone_transfer_request_scoped(self):
        response = self.client.post_json(
            '/zones/%s/tasks/transfer_requests' % (self.zone.id),
            {'target_project_id': str(self.tenant_1_context.tenant)})

        # Check the headers are what we expect
        self.assertEqual(201, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIn('created_at', response.json)
        self.assertEqual('ACTIVE', response.json['status'])
        self.assertEqual(
            str(self.tenant_1_context.tenant),
            response.json['target_project_id'])
        self.assertEqual(
            self.zone.id,
            response.json['zone_id'])
        self.assertIsNone(response.json['updated_at'])

    def test_create_zone_transfer_request_empty_body(self):
        # Send an empty ("None") body
        response = self.client.post_json(
            '/zones/%s/tasks/transfer_requests' % (self.zone.id),
            None)

        # Check the headers are what we expect
        self.assertEqual(201, response.status_int)
        self.assertEqual('application/json', response.content_type)

    def test_get_zone_transfer_request(self):
        initial = self.client.post_json(
            '/zones/%s/tasks/transfer_requests' % (self.zone.id),
            {})

        response = self.client.get(
            '/zones/tasks/transfer_requests/%s' %
            (initial.json['id']))

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIn('created_at', response.json)
        self.assertEqual('ACTIVE', response.json['status'])
        self.assertEqual(
            self.zone.id,
            response.json['zone_id'])
        self.assertIn('updated_at', response.json)

    def test_get_zone_transfer_requests(self):
        response = self.client.get(
            '/zones/tasks/transfer_requests')

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('transfer_requests', response.json)
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # We should start with 0 transfer accepts
        self.assertEqual(0, len(response.json['transfer_requests']))

        self.client.post_json(
            '/zones/%s/tasks/transfer_requests' % (self.zone.id),
            {})

        data = self.client.get(
            '/zones/tasks/transfer_requests')

        self.assertEqual(1, len(data.json['transfer_requests']))

    def test_update_zone_transfer_request(self):
        initial = self.client.post_json(
            '/zones/%s/tasks/transfer_requests' % (self.zone.id),
            {})

        response = self.client.patch_json(
            '/zones/tasks/transfer_requests/%s' %
            (initial.json['id']),
            {"description": "TEST"})

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIn('created_at', response.json)
        self.assertEqual('ACTIVE', response.json['status'])
        self.assertEqual(
            self.zone.id,
            response.json['zone_id'])
        self.assertEqual(
            'TEST', response.json['description'])
        self.assertIn('updated_at', response.json)

    def test_delete_zone_transfer_request(self):
        initial = self.client.post_json(
            '/zones/%s/tasks/transfer_requests' % (self.zone.id),
            {})

        response = self.client.delete(
            '/zones/tasks/transfer_requests/%s' %
            (initial.json['id']))

        # Check the headers are what we expect
        self.assertEqual(204, response.status_int)

    def test_create_zone_transfer_accept(self):
        initial = self.client.post_json(
            '/zones/%s/tasks/transfer_requests' % (self.zone.id),
            {})

        response = self.client.post_json(
            '/zones/tasks/transfer_accepts',
            {
                'zone_transfer_request_id':
                    initial.json['id'],
                'key': initial.json['key']
            })

        new_ztr = self.client.get(
            '/zones/tasks/transfer_requests/%s' %
            (initial.json['id']))

        # Check the headers are what we expect
        self.assertEqual(201, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])
        self.assertIn('zone', response.json['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertEqual(
            'COMPLETE',
            response.json['status'])

        self.assertEqual(
            'COMPLETE',
            new_ztr.json['status'])

    def test_get_zone_transfer_accept(self):
        initial = self.client.post_json(
            '/zones/%s/tasks/transfer_requests' % (self.zone.id),
            {})

        transfer_accept = self.client.post_json(
            '/zones/tasks/transfer_accepts',
            {
                'zone_transfer_request_id':
                    initial.json['id'],
                'key': initial.json['key']
            })
        response = self.client.get(
            '/zones/tasks/transfer_accepts/%s' %
            (transfer_accept.json['id']))

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIn('created_at', response.json)
        self.assertEqual('COMPLETE', response.json['status'])
        self.assertEqual(
            self.zone.id,
            response.json['zone_id'])
        self.assertIn('updated_at', response.json)
        self.assertIn('key', response.json)
        self.assertIn(initial.json['id'],
                      response.json['zone_transfer_request_id'])

    def test_get_zone_transfer_accept_invalid_id(self):
        self._assert_invalid_uuid(self.client.get,
            '/zones/tasks/transfer_accepts/%s')

    def test_get_zone_transfer_accepts(self):
        response = self.client.get(
                       '/zones/tasks/transfer_accepts')

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('transfer_accepts', response.json)
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])
        self.assertIn('metadata', response.json)

        # We should start with 0 transfer accepts
        self.assertEqual(0, len(response.json['transfer_accepts']))

        initial = self.client.post_json(
            '/zones/%s/tasks/transfer_requests' % (self.zone.id),
            {})

        self.client.post_json(
            '/zones/tasks/transfer_accepts',
            {
                'zone_transfer_request_id':
                    initial.json['id'],
                'key': initial.json['key']
            })

        data = self.client.get(
                       '/zones/tasks/transfer_accepts')
        self.assertEqual(1, len(data.json['transfer_accepts']))

    def test_create_zone_transfer_request_deleting_zone(self):
        url = '/zones/%s/tasks/transfer_requests' % (self.zone.id)
        body = {}
        self.client.delete('/zones/%s' % self.zone['id'], status=202)
        self._assert_exception('bad_request', 400, self.client.post_json, url,
                               body)

    def test_create_zone_transfer_accept_deleting_zone(self):
        url = '/zones/%s/tasks/transfer_requests' % (self.zone.id)
        body = {}
        self.client.delete('/zones/%s' % self.zone['id'], status=202)
        self._assert_exception('bad_request', 400, self.client.post_json, url,
                               body)

    # Metadata tests
    def test_metadata_exists_zone_transfer_accepts(self):
        initial = self.client.post_json(
            '/zones/%s/tasks/transfer_requests' % (self.zone.id),
            {})

        self.client.post_json(
            '/zones/tasks/transfer_accepts',
            {
                'zone_transfer_request_id':
                    initial.json['id'],
                'key': initial.json['key']
            })

        result = self.client.get(
            '/zones/tasks/transfer_accepts')

        # Make sure the fields exist
        self.assertIn('metadata', result.json)
        self.assertIn('total_count', result.json['metadata'])

    def test_total_count_zone_transfer_accepts(self):
        initial = self.client.post_json(
            '/zones/%s/tasks/transfer_requests' % (self.zone.id),
            {})

        self.client.post_json(
            '/zones/tasks/transfer_accepts',
            {
                'zone_transfer_request_id':
                    initial.json['id'],
                'key': initial.json['key']
            })

        result = self.client.get(
            '/zones/tasks/transfer_accepts')

        # Make sure total_count picked it up
        self.assertEqual(1, result.json['metadata']['total_count'])
