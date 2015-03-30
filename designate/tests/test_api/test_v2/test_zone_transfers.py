# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Graham Hayes <graham.hayes@hp.com>
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

        self.domain = self.create_domain()
        self.tenant_1_context = self.get_context(tenant=1)
        self.tenant_2_context = self.get_context(tenant=2)

    def test_create_zone_transfer_request(self):
        response = self.client.post_json(
            '/zones/%s/tasks/transfer_requests' % (self.domain.id),
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
            self.domain.id,
            response.json['zone_id'])
        self.assertIsNone(response.json['updated_at'])

    def test_create_zone_transfer_request_scoped(self):
        response = self.client.post_json(
            '/zones/%s/tasks/transfer_requests' % (self.domain.id),
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
            self.domain.id,
            response.json['zone_id'])
        self.assertIsNone(response.json['updated_at'])

    def test_get_zone_transfer_request(self):
        initial = self.client.post_json(
            '/zones/%s/tasks/transfer_requests' % (self.domain.id),
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
            self.domain.id,
            response.json['zone_id'])
        self.assertIn('updated_at', response.json)

    def test_update_zone_transfer_request(self):
        initial = self.client.post_json(
            '/zones/%s/tasks/transfer_requests' % (self.domain.id),
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
            self.domain.id,
            response.json['zone_id'])
        self.assertEqual(
            'TEST', response.json['description'])
        self.assertIn('updated_at', response.json)

    def test_delete_zone_transfer_request(self):
        initial = self.client.post_json(
            '/zones/%s/tasks/transfer_requests' % (self.domain.id),
            {})

        response = self.client.delete(
            '/zones/tasks/transfer_requests/%s' %
            (initial.json['id']))

        # Check the headers are what we expect
        self.assertEqual(204, response.status_int)

    def test_create_zone_transfer_accept(self):
        initial = self.client.post_json(
            '/zones/%s/tasks/transfer_requests' % (self.domain.id),
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

    def test_create_zone_transfer_request_deleting_zone(self):
        url = '/zones/%s/tasks/transfer_requests' % (self.domain.id)
        body = {}
        self.client.delete('/zones/%s' % self.domain['id'], status=202)
        self._assert_exception('bad_request', 400, self.client.post_json, url,
                               body)

    def test_create_zone_transfer_accept_deleting_zone(self):
        url = '/zones/%s/tasks/transfer_requests' % (self.domain.id)
        body = {}
        self.client.delete('/zones/%s' % self.domain['id'], status=202)
        self._assert_exception('bad_request', 400, self.client.post_json, url,
                               body)
