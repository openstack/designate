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
from urllib.parse import urlparse

import designate.conf
from designate.tests.functional.api import v2

CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class ApiV2ServiceStatusTest(v2.ApiV2TestCase):
    def setUp(self):
        super().setUp()

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

    def test_get_service_statuses_pagination_default_limit(self):
        self.policy({'find_service_statuses': '@'})

        # Set default_limit_v2 to a small value and create exactly that
        # many service statuses.
        limit = 5
        CONF.set_override('default_limit_v2', limit, 'service:api')

        for i in range(limit):
            self.update_service_status(
                hostname='host%s' % i, service_name='svc%s' % i)

        # Request without an explicit limit parameter so default_limit_v2
        # is used.
        response = self.client.get('/service_statuses/')

        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(limit, len(response.json['service_statuses']))

        first_ids = {s['id'] for s in response.json['service_statuses']}

        # If a 'next' link is present, following it must return an empty
        # list — not the same results again.
        if 'next' in response.json['links']:
            next_url = response.json['links']['next']
            parsed = urlparse(next_url)
            next_response = self.client.get(
                '%s?%s' % (parsed.path.replace('/v2', ''), parsed.query))

            self.assertEqual(200, next_response.status_int)

            next_ids = {
                s['id'] for s in next_response.json['service_statuses']
            }
            self.assertEqual(
                0, len(next_ids & first_ids),
                'Following the next link returned the same results — '
                'pagination parameters are not being passed to '
                'find_service_statuses()'
            )

    def test_legacy_list_service_status(self):
        """Test the legacy list service status path.

        Historically the Designate API reference showed the list
        service status URL path as /v2/service_status where the actual
        path was /v2/service_statuses.

        https://bugs.launchpad.net/designate/+bug/1919183

        A compatibility workaround was added as this was a published
        API reference. This test covers that alternate URL path.
        """

        # Set the policy file as this is an admin-only API
        self.policy({'find_service_statuses': '@'})

        response = self.client.get('/service_status/')

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

        self._assert_paging(data, '/service_status', key='service_statuses')

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
