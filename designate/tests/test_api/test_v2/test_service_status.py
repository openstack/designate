# Copyright 2016 Hewlett Packard Enterprise Development Company LP
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
from oslo_log import log as logging

from designate.tests.test_api.test_v2 import ApiV2TestCase

LOG = logging.getLogger(__name__)


class ApiV2ServiceStatusTest(ApiV2TestCase):
    def setUp(self):
        super(ApiV2ServiceStatusTest, self).setUp()

    def test_get_service_statuses(self):
        # Set the policy file as this is an admin-only API
        self.policy({'find_service_statuses': '@'})

        response = self.client.get('/service_statuses/')

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('service_statuses', response.json)
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Test with 0 service_statuses
        # Seeing that Central is started there will be 1 here already..
        self.assertEqual(0, len(response.json['service_statuses']))

        data = [self.update_service_status(
            hostname="foo%s" % i, service_name="bar") for i in range(0, 10)]

        self._assert_paging(data, '/service_statuses', key='service_statuses')

    def test_get_service_status(self):
        service_status = self.update_service_status(fixture=0)

        # Set the policy file as this is an admin-only API
        self.policy({'find_service_status': '@'})

        response = self.client.get(
            '/service_statuses/%s' % service_status['id'],
            headers=[('Accept', 'application/json')])

        # Verify the headers
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Verify the body structure
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Verify the returned values
        self.assertIn('id', response.json)
        self.assertIn('created_at', response.json)
        self.assertIsNone(response.json['updated_at'])

        fixture = self.get_service_status_fixture(0)
        self.assertEqual(fixture['hostname'], response.json['hostname'])
        self.assertEqual(fixture['service_name'],
                        response.json['service_name'])
        self.assertEqual(fixture['capabilities'],
                        response.json['capabilities'])
        self.assertEqual(fixture['stats'], response.json['stats'])
        self.assertEqual(fixture['status'], response.json['status'])
        self.assertIsNone(response.json['heartbeated_at'])

    def test_get_service_status_invalid_id(self):
        self.policy({'find_service_status': '@'})
        self._assert_invalid_uuid(self.client.get, '/service_statuses/%s')
