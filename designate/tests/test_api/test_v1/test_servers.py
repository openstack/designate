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
from mock import patch
from designate.openstack.common import log as logging
from designate.openstack.common.rpc import common as rpc_common
from designate import exceptions
from designate.central import service as central_service
from designate.tests.test_api.test_v1 import ApiV1Test


LOG = logging.getLogger(__name__)


class ApiV1ServersTest(ApiV1Test):
    def test_create_server(self):
        # Create a server
        fixture = self.get_server_fixture(0)

        response = self.post('servers', data=fixture)

        self.assertIn('id', response.json)
        self.assertIn('name', response.json)
        self.assertEqual(response.json['name'], fixture['name'])

    @patch.object(central_service.Service, 'create_server')
    def test_create_server_trailing_slash(self, mock):
        # Create a server with a trailing slash
        self.post('servers/', data=self.get_server_fixture(0))

        # verify that the central service is called
        self.assertTrue(mock.called)

    def test_create_server_junk(self):
        # Create a server
        fixture = self.get_server_fixture(0)

        # Add a junk property
        fixture['junk'] = 'Junk Field'

        # Ensure it fails with a 400
        self.post('servers', data=fixture, status_code=400)

    @patch.object(central_service.Service, 'create_server',
                  side_effect=rpc_common.Timeout())
    def test_create_server_timeout(self, _):
        # Create a server
        fixture = self.get_server_fixture(0)

        self.post('servers', data=fixture, status_code=504)

    @patch.object(central_service.Service, 'create_server',
                  side_effect=exceptions.DuplicateServer())
    def test_create_server_duplicate(self, _):
        # Create a server
        fixture = self.get_server_fixture(0)

        self.post('servers', data=fixture, status_code=409)

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

    @patch.object(central_service.Service, 'find_servers')
    def test_get_servers_trailing_slash(self, mock):
        self.get('servers/')

        # verify that the central service is called
        self.assertTrue(mock.called)

    @patch.object(central_service.Service, 'find_servers',
                  side_effect=rpc_common.Timeout())
    def test_get_servers_timeout(self, _):
        self.get('servers', status_code=504)

    def test_get_server(self):
        # Create a server
        server = self.create_server()

        response = self.get('servers/%s' % server['id'])

        self.assertIn('id', response.json)
        self.assertEqual(response.json['id'], server['id'])

    @patch.object(central_service.Service, 'get_server')
    def test_get_server_trailing_slash(self, mock):
        # Create a server
        server = self.create_server()

        self.get('servers/%s/' % server['id'])

        # verify that the central service is called
        self.assertTrue(mock.called)

    @patch.object(central_service.Service, 'get_server',
                  side_effect=rpc_common.Timeout())
    def test_get_server_timeout(self, _):
        # Create a server
        server = self.create_server()

        self.get('servers/%s' % server['id'], status_code=504)

    def test_get_server_missing(self):
        self.get('servers/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980',
                 status_code=404)

    def test_update_server(self):
        # Create a server
        server = self.create_server()

        data = {'name': 'test.example.org.'}

        response = self.put('servers/%s' % server['id'], data=data)

        self.assertIn('id', response.json)
        self.assertEqual(response.json['id'], server['id'])

        self.assertIn('name', response.json)
        self.assertEqual(response.json['name'], 'test.example.org.')

    @patch.object(central_service.Service, 'update_server')
    def test_update_server_trailing_slash(self, mock):
        # Create a server
        server = self.create_server()

        data = {'name': 'test.example.org.'}

        self.put('servers/%s/' % server['id'], data=data)

        # verify that the central service is called
        self.assertTrue(mock.called)

    def test_update_server_junk(self):
        # Create a server
        server = self.create_server()

        data = {'name': 'test.example.org.', 'junk': 'Junk Field'}

        self.put('servers/%s' % server['id'], data=data, status_code=400)

    @patch.object(central_service.Service, 'update_server',
                  side_effect=rpc_common.Timeout())
    def test_update_server_timeout(self, _):
        # Create a server
        server = self.create_server()

        data = {'name': 'test.example.org.'}

        self.put('servers/%s' % server['id'], data=data, status_code=504)

    @patch.object(central_service.Service, 'update_server',
                  side_effect=exceptions.DuplicateServer())
    def test_update_server_duplicate(self, _):
        server = self.create_server()

        data = {'name': 'test.example.org.'}

        self.put('servers/%s' % server['id'], data=data, status_code=409)

    def test_update_server_missing(self):
        data = {'name': 'test.example.org.'}

        self.get('servers/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980', data=data,
                 status_code=404)

    def test_delete_server(self):
        # Create a server
        server = self.create_server()

        # Create a second server so that we can delete the first
        # because the last remaining server is not allowed to be deleted
        server2 = self.create_server(fixture=1)

        # Now delete the server
        self.delete('servers/%s' % server['id'])

        # Ensure we can no longer fetch the deleted server
        self.get('servers/%s' % server['id'], status_code=404)

        # Also, verify we cannot delete last remaining server
        self.delete('servers/%s' % server2['id'], status_code=400)

    @patch.object(central_service.Service, 'delete_server')
    def test_delete_server_trailing_slash(self, mock):
        # Create a server
        server = self.create_server()

        self.delete('servers/%s/' % server['id'])

        # verify that the central service is called
        self.assertTrue(mock.called)

    @patch.object(central_service.Service, 'delete_server',
                  side_effect=rpc_common.Timeout())
    def test_delete_server_timeout(self, _):
        # Create a server
        server = self.create_server()

        self.delete('servers/%s' % server['id'], status_code=504)

    def test_delete_server_missing(self):
        self.delete('servers/9fdadfb1-cf96-4259-ac6b-bb7b6d2ff980',
                    status_code=404)
