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
from moniker.tests import TestCase
from moniker import storage
from moniker import exceptions

LOG = logging.getLogger(__name__)


class StorageTestCase(TestCase):
    __test__ = False

    def get_storage_driver(self):
        connection = storage.get_connection()
        return connection


class StorageDriverTestCase(StorageTestCase):
    __test__ = False

    def setUp(self):
        super(StorageDriverTestCase, self).setUp()
        self.storage_conn = self.get_storage_driver()

    def create_server(self, fixture=0, values={}):
        fixture = self.get_server_fixture(fixture, values)
        return fixture, self.storage_conn.create_server(
            self.admin_context,
            fixture)

    def create_domain(self, fixture=0, values={}):
        fixture = self.get_domain_fixture(fixture, values)
        return fixture, self.storage_conn.create_domain(
            self.admin_context,
            fixture)

    def create_record(self, domain, fixture=0, values={}):
        fixture = self.get_record_fixture(domain['name'], fixture, values)
        return fixture, self.storage_conn.create_record(
            self.admin_context,
            domain['id'],
            fixture)

    def test_init(self):
        self.get_storage_driver()

    def test_create_server(self):
        values = {
            'name': 'ns1.example.org.',
            'ipv4': '192.0.2.1',
            'ipv6': '2001:db8::1',
        }

        result = self.storage_conn.create_server(
            self.admin_context, values=values)

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['name'], values['name'])
        self.assertEqual(result['ipv4'], values['ipv4'])
        self.assertEqual(result['ipv6'], values['ipv6'])

    def test_create_server_ipv4_only(self):
        values = [{
            'name': 'ns1.example.org.',
            'ipv4': '192.0.2.1',
            'ipv6': None,
        }, {
            'name': 'ns2.example.org.',
            'ipv4': '192.0.2.2'
        }]

        for value in values:
            result = self.storage_conn.create_server(
                self.admin_context, values=value)

            self.assertIsNotNone(result['id'])
            self.assertIsNotNone(result['created_at'])
            self.assertIsNone(result['updated_at'])

            self.assertEqual(result['name'], value['name'])
            self.assertEqual(result['ipv4'], value['ipv4'])
            self.assertIsNone(result['ipv6'])

    def test_create_server_duplicate(self):
        # Create the Initial Server
        self.create_server()

        values = [{
            # No Changes/Identical
        }, {
            'ipv4': '127.0.0.1',
        }, {
            'ipv4': '127.0.0.1',
            'ipv6': '::1',
        }, {
            'ipv6': '::1',
        }, {
            'name': 'localhost.',
        }, {
            'name': 'localhost.',
            'ipv4': '127.0.0.1',
        }, {
            'name': 'localhost.',
            'ipv6': '::1',
        }]

        for value in values:
            with self.assertRaises(exceptions.DuplicateServer):
                self.create_server(values=value)

    def test_get_servers(self):
        actual = self.storage_conn.get_servers(self.admin_context)
        self.assertEqual(actual, [])

        # Create a single server
        server_one = self.create_server()[1]

        actual = self.storage_conn.get_servers(self.admin_context)
        self.assertEqual(len(actual), 1)

        self.assertEqual(str(actual[0]['name']), str(server_one['name']))
        self.assertEqual(str(actual[0]['ipv4']), str(server_one['ipv4']))
        self.assertEqual(str(actual[0]['ipv6']), str(server_one['ipv6']))

        # Create a second server
        server_two = self.create_server(fixture=1)[1]

        actual = self.storage_conn.get_servers(self.admin_context)
        self.assertEqual(len(actual), 2)

        self.assertEqual(str(actual[1]['name']), str(server_two['name']))
        self.assertEqual(str(actual[1]['ipv4']), str(server_two['ipv4']))
        self.assertEqual(str(actual[1]['ipv6']), str(server_two['ipv6']))

    def test_get_servers_criterion(self):
        server_one = self.create_server(0)[1]
        server_two = self.create_server(1)[1]

        criterion = dict(
            name=server_one['name']
        )

        results = self.storage_conn.get_servers(self.admin_context,
                                                criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], server_one['name'])

        criterion = dict(
            name=server_two['name']
        )

        results = self.storage_conn.get_servers(self.admin_context,
                                                criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], server_two['name'])

    def test_get_server(self):
        # Create a server
        expected = self.create_server()[1]
        actual = self.storage_conn.get_server(
            self.admin_context, expected['id'])

        self.assertEqual(str(actual['name']), str(expected['name']))
        self.assertEqual(str(actual['ipv4']), str(expected['ipv4']))
        self.assertEqual(str(actual['ipv6']), str(expected['ipv6']))

    def test_get_server_missing(self):
        with self.assertRaises(exceptions.ServerNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage_conn.get_server(self.admin_context, uuid)

    def test_update_server(self):
        # Create a server
        fixture, server = self.create_server()

        updated = self.storage_conn.update_server(
            self.admin_context, server['id'], fixture)

        self.assertEqual(str(updated['name']), str(fixture['name']))
        self.assertEqual(str(updated['ipv4']), str(fixture['ipv4']))
        self.assertEqual(str(updated['ipv6']), str(fixture['ipv6']))

    def test_update_server_duplicate(self):
        # Create two servers
        self.create_server(fixture=0)
        server = self.create_server(fixture=1)[1]

        values = self.server_fixtures[0]

        with self.assertRaises(exceptions.DuplicateServer):
            self.storage_conn.update_server(
                self.admin_context, server['id'], values)

    def test_update_server_missing(self):
        with self.assertRaises(exceptions.ServerNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage_conn.update_server(self.admin_context, uuid, {})

    def test_delete_server(self):
        server_fixture, server = self.create_server()

        self.storage_conn.delete_server(self.admin_context, server['id'])

        with self.assertRaises(exceptions.ServerNotFound):
            self.storage_conn.get_server(self.admin_context, server['id'])

    def test_delete_server_missing(self):
        with self.assertRaises(exceptions.ServerNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage_conn.delete_server(self.admin_context, uuid)

    def test_create_domain(self):
        values = {
            'name': 'example.net.',
            'email': 'example@example.net'
        }

        result = self.storage_conn.create_domain(self.admin_context,
                                                 values=values)

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['name'], values['name'])
        self.assertEqual(result['email'], values['email'])

    def test_create_domain_duplicate(self):
        # Create the Initial Domain
        self.create_domain()

        with self.assertRaises(exceptions.DuplicateDomain):
            self.create_domain()

    def test_get_domains(self):
        actual = self.storage_conn.get_domains(self.admin_context)
        self.assertEqual(actual, [])

        # Create a single domain
        fixture_one, domain_one = self.create_domain()

        actual = self.storage_conn.get_domains(self.admin_context)
        self.assertEqual(len(actual), 1)

        self.assertEqual(actual[0]['name'], domain_one['name'])
        self.assertEqual(actual[0]['email'], domain_one['email'])

        # Create a second domain
        self.create_domain(fixture=1)

        actual = self.storage_conn.get_domains(self.admin_context)
        self.assertEqual(len(actual), 2)

    def test_get_domains_criterion(self):
        domain_one = self.create_domain(0)[1]
        domain_two = self.create_domain(1)[1]

        criterion = dict(
            name=domain_one['name']
        )

        results = self.storage_conn.get_domains(self.admin_context,
                                                criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], domain_one['name'])
        self.assertEqual(results[0]['email'], domain_one['email'])

        criterion = dict(
            name=domain_two['name']
        )

        results = self.storage_conn.get_domains(self.admin_context,
                                                criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], domain_two['name'])
        self.assertEqual(results[0]['email'], domain_two['email'])

    def test_get_domain(self):
        # Create a domain
        fixture, expected = self.create_domain()
        actual = self.storage_conn.get_domain(self.admin_context,
                                              expected['id'])

        self.assertEqual(actual['name'], expected['name'])
        self.assertEqual(actual['email'], expected['email'])

    def test_get_domain_missing(self):
        with self.assertRaises(exceptions.DomainNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage_conn.get_domain(self.admin_context, uuid)

    def test_update_domain(self):
        # Create a domain
        fixture, domain = self.create_domain()

        updated = self.storage_conn.update_domain(self.admin_context,
                                                  domain['id'], fixture)

        self.assertEqual(updated['name'], fixture['name'])
        self.assertEqual(updated['email'], fixture['email'])

    def test_update_domain_duplicate(self):
        # Create two domains
        fixture_one, domain_one = self.create_domain(fixture=0)
        domain_two = self.create_domain(fixture=1)[1]

        with self.assertRaises(exceptions.DuplicateDomain):
            self.storage_conn.update_domain(
                self.admin_context,
                domain_two['id'],
                fixture_one)

    def test_update_domain_missing(self):
        with self.assertRaises(exceptions.DomainNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage_conn.update_domain(self.admin_context, uuid, {})

    def test_delete_domain(self):
        domain_fixture, domain = self.create_domain()

        self.storage_conn.delete_domain(self.admin_context, domain['id'])

        with self.assertRaises(exceptions.DomainNotFound):
            self.storage_conn.get_domain(self.admin_context, domain['id'])

    def test_delete_domain_missing(self):
        with self.assertRaises(exceptions.DomainNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage_conn.delete_domain(self.admin_context, uuid)

    def test_create_record(self):
        domain_fixture, domain = self.create_domain()

        values = {
            'name': 'www.%s' % domain['name'],
            'type': 'A',
            'data': '192.0.2.1',
        }

        result = self.storage_conn.create_record(self.admin_context,
                                                 domain['id'], values=values)

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['name'], values['name'])
        self.assertEqual(result['type'], values['type'])
        self.assertEqual(result['data'], values['data'])

    def test_get_records(self):
        domain = self.create_domain()[1]
        actual = self.storage_conn.get_records(self.admin_context,
                                               domain['id'])
        self.assertEqual(actual, [])

        # Create a single record
        record_one = self.create_record(domain, fixture=0)[1]

        actual = self.storage_conn.get_records(self.admin_context,
                                               domain['id'])
        self.assertEqual(len(actual), 1)

        self.assertEqual(actual[0]['name'], record_one['name'])
        self.assertEqual(actual[0]['type'], record_one['type'])
        self.assertEqual(actual[0]['data'], record_one['data'])

        # Create a second record
        record_two = self.create_record(domain, fixture=1)[1]

        actual = self.storage_conn.get_records(self.admin_context,
                                               domain['id'])
        self.assertEqual(len(actual), 2)

        self.assertEqual(actual[1]['name'], record_two['name'])
        self.assertEqual(actual[1]['type'], record_two['type'])
        self.assertEqual(actual[1]['data'], record_two['data'])

    def test_get_records_criterion(self):
        domain = self.create_domain()[1]

        record_one = self.create_record(domain, fixture=0)[1]
        self.create_record(domain, fixture=1)

        criterion = dict(
            data=record_one['data']
        )

        results = self.storage_conn.get_records(self.admin_context,
                                                domain['id'],
                                                criterion)

        self.assertEqual(len(results), 1)

        criterion = dict(
            type='A'
        )

        results = self.storage_conn.get_records(self.admin_context,
                                                domain['id'],
                                                criterion)

        self.assertEqual(len(results), 2)

    def test_get_record(self):
        domain = self.create_domain()[1]

        expected = self.create_record(domain)[1]

        actual = self.storage_conn.get_record(self.admin_context,
                                              expected['id'])

        self.assertEqual(actual['name'], expected['name'])
        self.assertEqual(actual['type'], expected['type'])
        self.assertEqual(actual['data'], expected['data'])

    def test_get_record_missing(self):
        with self.assertRaises(exceptions.RecordNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage_conn.get_record(self.admin_context, uuid)

    def test_update_record(self):
        domain_fixture, domain = self.create_domain()

        # Create a record
        record_fixture, record = self.create_record(domain)

        updated = self.storage_conn.update_record(self.admin_context,
                                                  record['id'], record_fixture)

        self.assertEqual(updated['name'], record_fixture['name'])
        self.assertEqual(updated['type'], record_fixture['type'])
        self.assertEqual(updated['data'], record_fixture['data'])

    def test_update_record_missing(self):
        with self.assertRaises(exceptions.RecordNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage_conn.update_record(self.admin_context, uuid, {})

    def test_delete_record(self):
        domain = self.create_domain()[1]

        # Create a record
        record = self.create_record(domain)[1]

        self.storage_conn.delete_record(self.admin_context, record['id'])

        with self.assertRaises(exceptions.RecordNotFound):
            self.storage_conn.get_record(self.admin_context, record['id'])

    def test_delete_record_missing(self):
        with self.assertRaises(exceptions.RecordNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage_conn.delete_record(self.admin_context, uuid)

    def test_ping(self):
        pong = self.storage_conn.ping(self.admin_context)

        self.assertEqual(pong['status'], True)
        self.assertIsNotNone(pong['rtt'])
