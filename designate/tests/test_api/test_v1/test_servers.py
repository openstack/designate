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
import oslo_messaging as messaging
from oslo_config import cfg
from oslo_log import log as logging

from designate import exceptions
from designate import objects
from designate.central import service as central_service
from designate.tests.test_api.test_v1 import ApiV1Test

cfg.CONF.import_opt('default_pool_id',
                    'designate.central',
                    group='service:central')
default_pool_id = cfg.CONF['service:central'].default_pool_id

LOG = logging.getLogger(__name__)


class ApiV1ServersTest(ApiV1Test):
    def setUp(self):
        super(ApiV1ServersTest, self).setUp()

        # All Server Checks should be performed as an admin, so..
        # Override to policy to make everyone an admin.

        self.policy({'admin': '@'})

    def test_get_server_schema(self):
        response = self.get('schemas/server')
        self.assertIn('description', response.json)
        self.assertIn('id', response.json)
        self.assertIn('title', response.json)
        self.assertIn('additionalProperties', response.json)
        self.assertIn('properties', response.json)
        self.assertIn('name', response.json['properties'])
        self.assertIn('links', response.json)
        self.assertIn('created_at', response.json['properties'])
        self.assertIn('updated_at', response.json['properties'])

    def test_get_servers_schema(self):
        response = self.get('schemas/servers')
        self.assertIn('description', response.json)
        self.assertIn('id', response.json)
        self.assertIn('title', response.json)
        self.assertIn('additionalProperties', response.json)
        self.assertIn('properties', response.json)

    def test_create_server(self):
        # Create a server
        # In a base somewhere, we create the default / 0 server fixture
        # automatically, so this would trigger a duplicate otherwise.
        fixture = self.get_server_fixture(1)

        response = self.post('servers', data=fixture)

        self.assertIn('id', response.json)
        self.assertIn('name', response.json)
        self.assertEqual(response.json['name'], fixture['name'])

    def test_create_server_junk(self):
        # Create a server
        fixture = self.get_server_fixture(0)

        # Add a junk property
        fixture['junk'] = 'Junk Field'

        # Ensure it fails with a 400
        self.post('servers', data=fixture, status_code=400)

    def test_create_server_with_invalid_name(self):
        # Create a server
        fixture = self.get_server_fixture(0)

        # Add an invalid name
        fixture['name'] = '$#$%^^'

        # Ensure it fails with a 400
        self.post('servers', data=fixture, status_code=400)

    def test_create_server_name_missing(self):
        fixture = self.get_server_fixture(0)
        del fixture['name']
        self.post('servers', data=fixture, status_code=400)

    def test_create_server_name_too_long(self):
        fixture = self.get_server_fixture(0)
        fixture['name'] = 'a' * 255 + '.example.org.'
        self.post('servers', data=fixture, status_code=400)

    @patch.object(central_service.Service, 'update_pool',
                  side_effect=messaging.MessagingTimeout())
    def test_create_server_timeout(self, _):
        # Create a server
        fixture = self.get_server_fixture(0)

        self.post('servers', data=fixture, status_code=504)

    @patch.object(central_service.Service, 'update_pool',
                  side_effect=exceptions.DuplicateServer())
    def test_create_server_duplicate(self, _):
        # Create a server
        fixture = self.get_server_fixture(0)

        self.post('servers', data=fixture, status_code=409)

    def test_get_servers(self):
        # Fetch the default pool
        pool = self.storage.get_pool(self.admin_context, default_pool_id)

        # Fetch the list of servers
        response = self.get('servers')

        self.assertIn('servers', response.json)
        self.assertEqual(len(pool.ns_records), len(response.json['servers']))

        # Add a new NS record to the pool
        pool.ns_records.append(
            objects.PoolNsRecord(priority=1, hostname='new-ns1.example.org.'))

        # Save the pool to add a new nameserver
        self.storage.update_pool(self.admin_context, pool)

        # Fetch the list of servers
        response = self.get('servers')

        self.assertIn('servers', response.json)
        self.assertEqual(len(pool.ns_records), len(response.json['servers']))

        # Add a new NS record to the pool
        pool.ns_records.append(
            objects.PoolNsRecord(priority=1, hostname='new-ns2.example.org.'))

        # Save the pool to add a new nameserver
        self.storage.update_pool(self.admin_context, pool)

        response = self.get('servers')

        self.assertIn('servers', response.json)
        self.assertEqual(len(pool.ns_records), len(response.json['servers']))

    @patch.object(central_service.Service, 'get_pool',
                  side_effect=messaging.MessagingTimeout())
    def test_get_servers_timeout(self, _):
        self.get('servers', status_code=504)

    def test_get_server(self):
        # Fetch the default pool
        pool = self.storage.get_pool(self.admin_context, default_pool_id)

        # Fetch the Server from the pool
        response = self.get('servers/%s' % pool.ns_records[0].id)

        self.assertIn('id', response.json)
        self.assertEqual(response.json['id'], pool.ns_records[0]['id'])

    @patch.object(central_service.Service, 'get_pool',
                  side_effect=messaging.MessagingTimeout())
    def test_get_server_timeout(self, _):
        # Fetch the default pool
        pool = self.storage.get_pool(self.admin_context, default_pool_id)

        self.get('servers/%s' % pool.ns_records[0].id, status_code=504)

    def test_get_server_with_invalid_id(self):
        self.get('servers/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff98GH',
                 status_code=404)

    def test_get_server_missing(self):
        self.get('servers/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980',
                 status_code=404)

    def test_update_server(self):
        # Fetch the default pool
        pool = self.storage.get_pool(self.admin_context, default_pool_id)

        data = {'name': 'new-ns1.example.org.'}

        response = self.put('servers/%s' % pool.ns_records[0].id,
                            data=data)

        self.assertIn('id', response.json)
        self.assertEqual(response.json['id'], pool.ns_records[0].id)

        self.assertIn('name', response.json)
        self.assertEqual(response.json['name'], 'new-ns1.example.org.')

    def test_update_server_missing(self):
        data = {'name': 'test.example.org.'}
        self.put('servers/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980', data=data,
                 status_code=404)

    def test_update_server_junk(self):
        # Fetch the default pool
        pool = self.storage.get_pool(self.admin_context, default_pool_id)

        data = {'name': 'test.example.org.', 'junk': 'Junk Field'}

        self.put('servers/%s' % pool.ns_records[0].id, data=data,
                 status_code=400)

    def test_delete_server(self):
        # Fetch the default pool
        pool = self.storage.get_pool(self.admin_context, default_pool_id)

        # Create a second server so that we can delete the first
        # because the last remaining server is not allowed to be deleted
        # Add a new NS record to the pool
        pool.ns_records.append(
            objects.PoolNsRecord(priority=1, hostname='new-ns2.example.org.'))

        # Save the pool to add a new nameserver
        self.storage.update_pool(self.admin_context, pool)

        # Now delete the server
        self.delete('servers/%s' % pool.ns_records[1].id)

        # Ensure we can no longer fetch the deleted server
        self.get('servers/%s' % pool.ns_records[1].id, status_code=404)

        # Also, verify we cannot delete last remaining server
        self.delete('servers/%s' % pool.ns_records[0].id, status_code=400)

    def test_delete_server_with_invalid_id(self):
        self.delete('servers/9fdadfb1-cf96-4259-ac6b-bb7b6d2ff98GH',
                    status_code=404)

    def test_delete_server_missing(self):
            self.delete('servers/9fdadfb1-cf96-4259-ac6b-bb7b6d2ff980',
                    status_code=404)
