# Copyright 2014 Hewlett-Packard Development Company, L.P.
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

import six
from tempest.api.dns import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest import test


class ServersAdminTestJSON(base.BaseDnsAdminTest):
    """
    Tests Servers API Create, Get, List and Delete
    that require admin privileges
    """

    @classmethod
    def setUpClass(cls):
        super(ServersAdminTestJSON, cls).setUpClass()
        cls.client = cls.os_adm.dns_servers_client
        cls.setup_servers = list()
        for i in range(2):
            name = data_utils.rand_name('dns-server') + '.com.'
            _, server = cls.client.create_server(name)
            cls.setup_servers.append(server)

    @classmethod
    def tearDownClass(cls):
        for server in cls.setup_servers:
            cls.client.delete_server(server['id'])
        super(ServersAdminTestJSON, cls).tearDownClass()

    def _delete_server(self, server_id):
        self.client.delete_server(server_id)
        self.assertRaises(exceptions.NotFound,
                          self.client.get_server, server_id)

    @test.attr(type='gate')
    def test_list_servers(self):
        # Get a list of servers
        _, servers = self.client.list_servers()
        # Verify servers created in setup class are in the list
        for server in self.setup_servers:
            self.assertIn(server['id'],
                          six.moves.map(lambda x: x['id'], servers))

    @test.attr(type='smoke')
    def test_create_update_get_delete_server(self):
        # Create Dns Server
        s_name1 = data_utils.rand_name('dns-server') + '.com.'
        _, server = self.client.create_server(s_name1)
        self.addCleanup(self._delete_server, server['id'])
        self.assertEqual(s_name1, server['name'])
        self.assertIsNotNone(server['id'])
        # Update Dns Server
        s_name2 = data_utils.rand_name('update-dns-server') + '.com.'
        _, update_server = self.client.update_server(server['id'],
                                                     name=s_name2)
        self.assertEqual(s_name2, update_server['name'])
        # Get the details of Server
        _, get_server = self.client.get_server(server['id'])
        self.assertEqual(update_server['name'], get_server['name'])
