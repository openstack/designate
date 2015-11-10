# Copyright (c) 2015 Rackspace Hosting
#
# Author: Mimi Lee <mimi.lee@rackspace.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from designate.tests.test_api.test_v2 import ApiV2TestCase


class ApiV2HostHeadersTest(ApiV2TestCase):
    def setUp(self):
        super(ApiV2HostHeadersTest, self).setUp()

        # Ensure v2 API and host headers are enabled
        self.config(enable_api_v2=True, group='service:api')
        self.config(enable_host_header=True, group='service:api')

    def test_host_header(self):
        # Create a zone with host header
        fixture = self.get_zone_fixture(fixture=0)
        response = self.client.post_json('/zones/',
                                         fixture,
                                         headers={'Host': 'testhost.com'})
        # Check the headers are what we expect
        self.assertEqual(202, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the host request header url
        self.assertIn('http://testhost.com/zones/',
                      response.json_body['links']['self'])

        # Get zone with host header
        response = self.client.get('/zones/',
                                   headers={'Host': 'testhost.com'})

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the host request header url
        self.assertIn('http://testhost.com/zones',
                      response.json_body['links']['self'])
