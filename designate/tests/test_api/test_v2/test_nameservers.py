# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
from oslo import messaging
from oslo_log import log as logging

from designate.central import service as central_service
from designate.tests.test_api.test_v2 import ApiV2TestCase


LOG = logging.getLogger(__name__)


class ApiV2NameServersTest(ApiV2TestCase):
    def setUp(self):
        super(ApiV2NameServersTest, self).setUp()

        # Create a domain
        self.domain = self.create_domain()

    def test_get_nameservers(self):
        url = '/zones/%s/nameservers' % self.domain['id']

        response = self.client.get(url)

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('nameservers', response.json)
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # We should start with 0 nameservers
        self.assertEqual(1, len(response.json['nameservers']))

        servers = self.central_service.get_domain_servers(
            self.admin_context, self.domain['id'])

        self.assertEqual(servers[0]['id'],
                         response.json['nameservers'][0]['id'])
        self.assertEqual(servers[0]['value'],
                         response.json['nameservers'][0]['name'])

        self.create_nameserver(value='nsx.mydomain.com.')

        response = self.client.get(url)

        self.assertEqual(2, len(response.json['nameservers']))

    def test_get_nameservers_invalid_id(self):
        self._assert_invalid_uuid(self.client.get, '/zones/%s/nameservers')

    @patch.object(central_service.Service, 'get_domain_servers',
                  side_effect=messaging.MessagingTimeout())
    def test_get_nameservers_timeout(self, _):
        url = '/zones/ba751950-6193-11e3-949a-0800200c9a66/nameservers'

        self._assert_exception('timeout', 504, self.client.get, url)
