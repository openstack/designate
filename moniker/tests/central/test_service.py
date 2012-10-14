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

    def create_domain(self, **kwargs):
        context = kwargs.pop('context', self.get_admin_context())
        service = kwargs.pop('service', self.get_central_service())

        values = dict(
            name='example.com',
            email='info@example.com',
        )

        values.update(kwargs)

        return service.create_domain(context, values=values)

    def create_record(self, domain_id, **kwargs):
        context = kwargs.pop('context', self.get_admin_context())
        service = kwargs.pop('service', self.get_central_service())

        values = dict(
            name='www.example.com',
            type='A',
            data='127.0.0.1'
        )

        values.update(kwargs)

        return service.create_record(context, domain_id, values=values)

    # Server Tests
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
            service.get_server(context, server['id'])

    # Domain Tests
    def test_create_domain(self):
        context = self.get_admin_context()
        service = self.get_central_service()

        values = dict(
            name='example.com',
            email='info@example.com'
        )

        # Create a domain
        domain = service.create_domain(context, values=values)

        # Ensure all values have been set correctly
        self.assertIsNotNone(domain['id'])
        self.assertEqual(domain['name'], values['name'])
        self.assertEqual(domain['email'], values['email'])

    def test_get_domains(self):
        context = self.get_admin_context()
        service = self.get_central_service()

        # Ensure we have no domains to start with.
        domains = service.get_domains(context)
        self.assertEqual(len(domains), 0)

        # Create a single domain (using default values)
        self.create_domain()

        # Ensure we can retrieve the newly created domain
        domains = service.get_domains(context)
        self.assertEqual(len(domains), 1)
        self.assertEqual(domains[0]['name'], 'example.com')

        # Create a second domain
        self.create_domain(name='example.net')

        # Ensure we can retrieve both domain
        domains = service.get_domains(context)
        self.assertEqual(len(domains), 2)
        self.assertEqual(domains[0]['name'], 'example.com')
        self.assertEqual(domains[1]['name'], 'example.net')

    def test_get_domain(self):
        context = self.get_admin_context()
        service = self.get_central_service()

        # Create a domain
        domain_name = '%d.example.com' % random.randint(10, 1000)
        expected_domain = self.create_domain(name=domain_name)

        # Retrieve it, and ensure it's the same
        domain = service.get_domain(context, expected_domain['id'])
        self.assertEqual(domain['id'], expected_domain['id'])
        self.assertEqual(domain['name'], expected_domain['name'])
        self.assertEqual(domain['email'], expected_domain['email'])

    def test_update_domain(self):
        context = self.get_admin_context()
        service = self.get_central_service()

        # Create a domain
        expected_domain = self.create_domain()

        # Update the domain
        values = dict(email='new@example.com')
        service.update_domain(context, expected_domain['id'], values=values)

        # Fetch the domain again
        domain = service.get_domain(context, expected_domain['id'])

        # Ensure the domain was updated correctly
        self.assertEqual(domain['email'], 'new@example.com')

    def test_delete_domain(self):
        context = self.get_admin_context()
        service = self.get_central_service()

        # Create a domain
        domain = self.create_domain()

        # Delete the domain
        service.delete_domain(context, domain['id'])

        # Fetch the domain again, ensuring an exception is raised
        with self.assertRaises(exceptions.DomainNotFound):
            service.get_domain(context, domain['id'])

    # Record Tests
    def test_create_record(self):
        context = self.get_admin_context()
        service = self.get_central_service()
        domain = self.create_domain()

        values = dict(
            name='www.example.com',
            type='A',
            data='127.0.0.1'
        )

        # Create a record
        record = service.create_record(context, domain['id'], values=values)

        # Ensure all values have been set correctly
        self.assertIsNotNone(record['id'])
        self.assertIsNotNone(record['ttl'])
        self.assertEqual(record['name'], values['name'])
        self.assertEqual(record['type'], values['type'])
        self.assertEqual(record['data'], values['data'])

    def test_get_records(self):
        context = self.get_admin_context()
        service = self.get_central_service()
        domain = self.create_domain()

        # Ensure we have no records to start with.
        records = service.get_records(context, domain['id'])
        self.assertEqual(len(records), 0)

        # Create a single record (using default values)
        self.create_record(domain['id'])

        # Ensure we can retrieve the newly created record
        records = service.get_records(context, domain['id'])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['name'], 'www.example.com')

        # Create a second record
        self.create_record(domain['id'], name='mail.example.com')

        # Ensure we can retrieve both records
        records = service.get_records(context, domain['id'])
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]['name'], 'www.example.com')
        self.assertEqual(records[1]['name'], 'mail.example.com')

    def test_get_record(self):
        context = self.get_admin_context()
        service = self.get_central_service()
        domain = self.create_domain()

        # Create a record
        record_name = '%d.example.com' % random.randint(10, 1000)
        expected_record = self.create_record(domain['id'], name=record_name)

        # Retrieve it, and ensure it's the same
        record = service.get_record(context, domain['id'],
                                    expected_record['id'])
        self.assertEqual(record['id'], expected_record['id'])
        self.assertEqual(record['name'], expected_record['name'])

    def test_update_record(self):
        context = self.get_admin_context()
        service = self.get_central_service()
        domain = self.create_domain()

        # Create a record
        expected_record = self.create_record(domain['id'])

        # Update the server
        values = dict(data='127.0.0.2')
        service.update_record(context, domain['id'], expected_record['id'],
                              values=values)

        # Fetch the record again
        record = service.get_record(context, domain['id'],
                                    expected_record['id'])

        # Ensure the record was updated correctly
        self.assertEqual(record['data'], '127.0.0.2')

    def test_delete_record(self):
        context = self.get_admin_context()
        service = self.get_central_service()
        domain = self.create_domain()

        # Create a record
        record = self.create_record(domain['id'])

        # Delete the record
        service.delete_record(context, domain['id'], record['id'])

        # Fetch the record again, ensuring an exception is raised
        with self.assertRaises(exceptions.RecordNotFound):
            service.get_record(context, domain['id'], record['id'])
