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
import random
from moniker.openstack.common import log as logging
from moniker.tests.central import CentralTestCase
from moniker import exceptions

LOG = logging.getLogger(__name__)


class ServiceTest(CentralTestCase):
    def setUp(self):
        super(ServiceTest, self).setUp()
        self.config(rpc_backend='moniker.openstack.common.rpc.impl_fake')

    def test_init(self):
        self.get_central_service()

    def create_server(self, **kwargs):
        context = kwargs.pop('context', self.get_admin_context())
        service = kwargs.pop('service', self.get_central_service())

        values = dict(
            name='ns1.example.org',
            ipv4='192.0.2.1',
            ipv6='2001:db8::1',
        )

        values.update(kwargs)

        return service.create_server(context, values=values)

    def test_create_server(self):
        context = self.get_admin_context()
        service = self.get_central_service()

        values = dict(
            name='ns1.example.org',
            ipv4='192.0.2.1',
            ipv6='2001:db8::1',
        )

        # Create a server
        server = service.create_server(context, values=values)

        # Ensure all values have been set correctly
        self.assertIsNotNone(server['id'])
        self.assertEqual(server['name'], values['name'])
        self.assertEqual(str(server['ipv4']), values['ipv4'])
        self.assertEqual(str(server['ipv6']), values['ipv6'])

    def test_get_servers(self):
        context = self.get_admin_context()
        service = self.get_central_service()

        # Ensure we have no servers to start with.
        servers = service.get_servers(context)
        self.assertEqual(len(servers), 0)

        # Create a single server (using default values)
        self.create_server()

        # Ensure we can retrieve the newly created server
        servers = service.get_servers(context)
        self.assertEqual(len(servers), 1)
        self.assertEqual(servers[0]['name'], 'ns1.example.org')

        # Create a second server
        self.create_server(name='ns2.example.org', ipv4='192.0.2.2',
                           ipv6='2001:db8::2')

        # Ensure we can retrieve both servers
        servers = service.get_servers(context)
        self.assertEqual(len(servers), 2)
        self.assertEqual(servers[0]['name'], 'ns1.example.org')
        self.assertEqual(servers[1]['name'], 'ns2.example.org')

    def test_get_server(self):
        context = self.get_admin_context()
        service = self.get_central_service()

        # Create a server
        server_name = 'ns%d.example.org' % random.randint(10, 1000)
        expected_server = self.create_server(name=server_name)

        # Retrieve it, and ensure it's the same
        server = service.get_server(context, expected_server['id'])
        self.assertEqual(server['id'], expected_server['id'])
        self.assertEqual(server['name'], expected_server['name'])
        self.assertEqual(str(server['ipv4']), expected_server['ipv4'])
        self.assertEqual(str(server['ipv6']), expected_server['ipv6'])

    def test_update_server(self):
        context = self.get_admin_context()
        service = self.get_central_service()

        # Create a server
        expected_server = self.create_server()

        # Update the server
        values = dict(ipv4='127.0.0.1')
        service.update_server(context, expected_server['id'], values=values)

        # Fetch the server again
        server = service.get_server(context, expected_server['id'])

        # Ensure the server was updated correctly
        self.assertEqual(str(server['ipv4']), '127.0.0.1')

    def test_delete_server(self):
        context = self.get_admin_context()
        service = self.get_central_service()

        # Create a server
        server = self.create_server()

        # Delete the server
        service.delete_server(context, server['id'])

        # Fetch the server again, ensuring an exception is raised
        with self.assertRaises(exceptions.ServerNotFound):
            server = service.get_server(context, server['id'])
