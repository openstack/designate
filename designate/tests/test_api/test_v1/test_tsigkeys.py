# Copyright 2015 NEC Corporation.  All rights reserved.
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

from mock import patch
import oslo_messaging as messaging
from oslo_log import log as logging

from designate.central import service as central_service
from designate.tests.test_api.test_v1 import ApiV1Test


LOG = logging.getLogger(__name__)


class ApiV1TsigkeysTest(ApiV1Test):
    def setUp(self):
        super(ApiV1TsigkeysTest, self).setUp()

        # Set the policy to accept everyone as an admin, as this is an
        # admin-only API
        self.policy({'admin': '@'})

    def test_get_tsigkey_schema(self):
        response = self.get('schemas/tsigkey')
        self.assertIn('description', response.json)
        self.assertIn('links', response.json)
        self.assertIn('title', response.json)
        self.assertIn('id', response.json)
        self.assertIn('additionalProperties', response.json)
        self.assertIn('properties', response.json)
        self.assertIn('name', response.json['properties'])
        self.assertIn('algorithm', response.json['properties'])
        self.assertIn('secret', response.json['properties'])

    def test_get_tsigkeys_schema(self):
        response = self.get('schemas/tsigkeys')
        self.assertIn('description', response.json)
        self.assertIn('title', response.json)
        self.assertIn('id', response.json)
        self.assertIn('additionalProperties', response.json)
        self.assertIn('properties', response.json)
        self.assertIn('tsigkeys', response.json['properties'])

    def test_create_tsigkeys(self):
        # Create a Tsigkey
        fixture = self.get_tsigkey_fixture(0)

        # V1 doesn't have these
        del fixture['scope']
        del fixture['resource_id']

        response = self.post('tsigkeys', data=fixture)
        self.assertIn('id', response.json)

        self.assertIn('name', response.json)
        self.assertEqual(response.json['name'], fixture['name'])

    def test_create_tsigkeys_junk(self):
        # Create a tsigkey
        fixture = self.get_tsigkey_fixture(0)

        # Add a junk property
        fixture['junk'] = 'Junk Field'

        # Ensure it fails with a 400
        self.post('tsigkeys', data=fixture, status_code=400)

    def test_create_tsigkey_name_missing(self):
        # Create tsigkey
        fixture = self.get_tsigkey_fixture(0)

        del fixture['name']

        self.post('tsigkeys', data=fixture, status_code=400)

    def test_create_tsigkey_algorithm_missing(self):
        # Create tsigkey
        fixture = self.get_tsigkey_fixture(0)

        del fixture['algorithm']

        self.post('tsigkeys', data=fixture, status_code=400)

    def test_create_tsigkey_secret_missing(self):
        # Create tsigkey
        fixture = self.get_tsigkey_fixture(0)

        del fixture['secret']

        self.post('tsigkeys', data=fixture, status_code=400)

    def test_create_tsigkey_name_too_long(self):
        # Create a tsigkey
        fixture = self.get_tsigkey_fixture(0)

        fixture['name'] = 'x' * 300

        self.post('tsigkeys', data=fixture, status_code=400)

    def test_create_tsigkey_secret_too_long(self):
        # Create a tsigkey
        fixture = self.get_tsigkey_fixture(0)

        fixture['secret'] = 'x' * 300

        self.post('tsigkeys', data=fixture, status_code=400)

    def test_delete_tsigkey(self):
        # Delete a tsigkey
        tsigkey = self.create_tsigkey()

        self.delete('/tsigkeys/%s' % tsigkey['id'], status=200)

    @patch.object(central_service.Service, 'find_tsigkeys',
                  side_effect=messaging.MessagingTimeout())
    def test_get_tsigkeys_timeout(self, _):
        self.get('tsigkeys', status_code=504)

    @patch.object(central_service.Service, 'find_tsigkeys',
                  side_effect=messaging.MessagingTimeout())
    def test_get_tsigkey_timeout(self, _):
        # Create a tsigkey
        tsigkey = self.create_tsigkey()

        self.get('tsigkeys/%s' % tsigkey['id'], status_code=504)
