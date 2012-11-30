# Copyright 2012 Managed I.T.
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
from moniker.openstack.common import log as logging
from moniker.openstack.common import jsonutils as json
from moniker.tests.test_api.test_v1 import ApiV1Test


LOG = logging.getLogger(__name__)


class ApiV1DomainsTest(ApiV1Test):
    __test__ = True

    def test_list_servers(self):
        response = self.client.get('servers')
        response_body = json.loads(response.data)

        self.assertEquals(200, response.status_code)
        self.assertIn('servers', response_body)
        self.assertEqual(0, len(response_body['servers']))

        # Create a server
        self.create_server()

        response = self.client.get('servers')
        response_body = json.loads(response.data)

        self.assertEquals(200, response.status_code)
        self.assertIn('servers', response_body)
        self.assertEqual(1, len(response_body['servers']))

        # Create a second server
        self.create_server(name='ns2.example.org', ipv4='192.0.2.2',
                           ipv6='2001:db8::2')

        response = self.client.get('servers')
        response_body = json.loads(response.data)

        self.assertEquals(200, response.status_code)
        self.assertIn('servers', response_body)
        self.assertEqual(2, len(response_body['servers']))
