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
from moniker.tests.test_api.test_v1 import ApiV1Test


LOG = logging.getLogger(__name__)


class ApiV1ServersTest(ApiV1Test):
    __test__ = True

    def test_create_server(self):
        # Create a server
        fixture = self.get_server_fixture(0)

        response = self.post('servers', data=fixture)

        self.assertIn('id', response.json)
        self.assertIn('name', response.json)
        self.assertEqual(response.json['name'], fixture['name'])

    def test_get_servers(self):
        response = self.get('servers')

        self.assertIn('servers', response.json)
        self.assertEqual(0, len(response.json['servers']))

        # Create a server
        self.create_server()

        response = self.get('servers')

        self.assertIn('servers', response.json)
        self.assertEqual(1, len(response.json['servers']))

        # Create a second server
        self.create_server(fixture=1)

        response = self.get('servers')

        self.assertIn('servers', response.json)
        self.assertEqual(2, len(response.json['servers']))

    def test_get_server(self):
        # Create a server
        server = self.create_server()

        response = self.get('servers/%s' % server['id'])

        self.assertIn('id', response.json)
        self.assertEqual(response.json['id'], server['id'])

    def test_update_server(self):
        # Create a server
        server = self.create_server()

        data = {'name': 'test.example.org.'}

        response = self.put('servers/%s' % server['id'], data=data)

        self.assertIn('id', response.json)
        self.assertEqual(response.json['id'], server['id'])

        self.assertIn('name', response.json)
        self.assertEqual(response.json['name'], 'test.example.org.')

    def test_delete_server(self):
        # Create a server
        server = self.create_server()

        self.delete('servers/%s' % server['id'])

        # Esnure we can no longer fetch the server
        self.get('servers/%s' % server['id'], status_code=404)
