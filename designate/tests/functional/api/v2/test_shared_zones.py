# Copyright 2020 Cloudification GmbH. All rights reserved.
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
from designate.tests.functional.api import v2


class ApiV2SharedZonesTest(v2.ApiV2TestCase):
    def setUp(self):
        super().setUp()

        self.zone = self.create_zone()
        self.target_project_id = '2'
        self.endpoint_url = '/zones/{}/shares'

    def _create_valid_shared_zone(self):
        return self.client.post_json(
            self.endpoint_url.format(self.zone.id),
            {
                'target_project_id': self.target_project_id,
            }, headers={'X-Test-Role': 'member'}
        )

    def test_share_zone(self):
        response = self._create_valid_shared_zone()

        # Check the headers are what we expect
        self.assertEqual(201, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIn('created_at', response.json)
        self.assertEqual(
            self.target_project_id,
            response.json['target_project_id'])
        self.assertEqual(
            self.zone.id,
            response.json['zone_id'])
        self.assertIsNone(response.json['updated_at'])

    def test_share_zone_with_no_target_id_no_zone_id(self):
        self._assert_exception(
            'invalid_uuid', 400, self.client.post_json,
            self.endpoint_url.format(""), {"target_project_id": ""},
            headers={'X-Test-Role': 'member'}
        )

    def test_share_zone_with_target_id_no_zone_id(self):
        self._assert_exception(
            'invalid_uuid', 400, self.client.post_json,
            self.endpoint_url.format(""), {"target_project_id": "2"},
            headers={'X-Test-Role': 'member'}
        )

    def test_share_zone_with_invalid_zone_id(self):
        self._assert_exception(
            'invalid_uuid', 400, self.client.post_json,
            self.endpoint_url.format("invalid"), {"target_project_id": "2"},
            headers={'X-Test-Role': 'member'}
        )

    def test_get_zone_share(self):
        shared_zone = self._create_valid_shared_zone()

        response = self.client.get(
            '{}/{}'.format(self.endpoint_url.format(self.zone.id),
                           shared_zone.json['id']),
            headers={'X-Test-Role': 'member'}
        )

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIn('created_at', response.json)
        self.assertEqual(
            self.target_project_id,
            response.json['target_project_id'])
        self.assertEqual(
            self.zone.id,
            response.json['zone_id'])
        self.assertIn('updated_at', response.json)

    def test_list_zone_shares(self):
        response = self.client.get(self.endpoint_url.format(self.zone.id),
                                   headers={'X-Test-Role': 'member'})

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('shared_zones', response.json)
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # We should start with 0 zone shars
        self.assertEqual(0, len(response.json['shared_zones']))

        self._create_valid_shared_zone()

        data = self.client.get(self.endpoint_url.format(self.zone.id),
                               headers={'X-Test-Role': 'member'})

        self.assertEqual(1, len(data.json['shared_zones']))

    def test_delete_zone_share(self):
        shared_zone = self._create_valid_shared_zone()

        response = self.client.delete(
            '{}/{}'.format(self.endpoint_url.format(self.zone.id),
                           shared_zone.json['id']),
            headers={'X-Test-Role': 'member'}
        )

        # Check the headers are what we expect
        self.assertEqual(204, response.status_int)
