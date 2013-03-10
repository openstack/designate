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

    def setUp(self):
        super(StorageTestCase, self).setUp()
        self.storage = storage.get_storage()

    def create_server(self, fixture=0, values={}):
        fixture = self.get_server_fixture(fixture, values)
        return fixture, self.storage.create_server(self.admin_context, fixture)

    def create_tsigkey(self, fixture=0, values={}):
        fixture = self.get_tsigkey_fixture(fixture, values)
        return fixture, self.storage.create_tsigkey(self.admin_context,
                                                    fixture)

    def create_domain(self, fixture=0, values={}):
        fixture = self.get_domain_fixture(fixture, values)
        return fixture, self.storage.create_domain(self.admin_context,
                                                   fixture)

    def create_record(self, domain, fixture=0, values={}):
        fixture = self.get_record_fixture(domain['name'], fixture, values)
        return fixture, self.storage.create_record(self.admin_context,
                                                   domain['id'],
                                                   fixture)

    # Server Tests
    def test_create_server(self):
        values = {
            'name': 'ns1.example.org.'
        }

        result = self.storage.create_server(self.admin_context, values=values)

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['name'], values['name'])

    def test_create_server_duplicate(self):
        # Create the Initial Server
        self.create_server()

        with self.assertRaises(exceptions.DuplicateServer):
            self.create_server()

    def test_get_servers(self):
        actual = self.storage.get_servers(self.admin_context)
        self.assertEqual(actual, [])

        # Create a single server
        _, server_one = self.create_server()

        actual = self.storage.get_servers(self.admin_context)
        self.assertEqual(len(actual), 1)

        self.assertEqual(str(actual[0]['name']), str(server_one['name']))

        # Create a second server
        _, server_two = self.create_server(fixture=1)

        actual = self.storage.get_servers(self.admin_context)
        self.assertEqual(len(actual), 2)

        self.assertEqual(str(actual[1]['name']), str(server_two['name']))

    def test_get_servers_criterion(self):
        _, server_one = self.create_server(0)
        _, server_two = self.create_server(1)

        criterion = dict(
            name=server_one['name']
        )

        results = self.storage.get_servers(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], server_one['name'])

        criterion = dict(
            name=server_two['name']
        )

        results = self.storage.get_servers(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], server_two['name'])

    def test_get_server(self):
        # Create a server
        _, expected = self.create_server()
        actual = self.storage.get_server(self.admin_context, expected['id'])

        self.assertEqual(str(actual['name']), str(expected['name']))

    def test_get_server_missing(self):
        with self.assertRaises(exceptions.ServerNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.get_server(self.admin_context, uuid)

    def test_update_server(self):
        # Create a server
        fixture, server = self.create_server()

        updated = self.storage.update_server(self.admin_context, server['id'],
                                             fixture)

        self.assertEqual(str(updated['name']), str(fixture['name']))

    def test_update_server_duplicate(self):
        # Create two servers
        self.create_server(fixture=0)
        _, server = self.create_server(fixture=1)

        values = self.server_fixtures[0]

        with self.assertRaises(exceptions.DuplicateServer):
            self.storage.update_server(self.admin_context, server['id'],
                                       values)

    def test_update_server_missing(self):
        with self.assertRaises(exceptions.ServerNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.update_server(self.admin_context, uuid, {})

    def test_delete_server(self):
        server_fixture, server = self.create_server()

        self.storage.delete_server(self.admin_context, server['id'])

        with self.assertRaises(exceptions.ServerNotFound):
            self.storage.get_server(self.admin_context, server['id'])

    def test_delete_server_missing(self):
        with self.assertRaises(exceptions.ServerNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.delete_server(self.admin_context, uuid)

    # TSIG Key Tests
    def test_create_tsigkey(self):
        values = self.get_tsigkey_fixture()

        result = self.storage.create_tsigkey(self.admin_context, values=values)

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['name'], values['name'])
        self.assertEqual(result['algorithm'], values['algorithm'])
        self.assertEqual(result['secret'], values['secret'])

    def test_create_tsigkey_duplicate(self):
        # Create the Initial TsigKey
        _, tsigkey_one = self.create_tsigkey()

        values = self.get_tsigkey_fixture(1)
        values['name'] = tsigkey_one['name']

        with self.assertRaises(exceptions.DuplicateTsigKey):
            self.create_tsigkey(values=values)

    def test_get_tsigkeys(self):
        actual = self.storage.get_tsigkeys(self.admin_context)
        self.assertEqual(actual, [])

        # Create a single tsigkey
        _, tsigkey_one = self.create_tsigkey()

        actual = self.storage.get_tsigkeys(self.admin_context)
        self.assertEqual(len(actual), 1)

        self.assertEqual(actual[0]['name'], tsigkey_one['name'])
        self.assertEqual(actual[0]['algorithm'], tsigkey_one['algorithm'])
        self.assertEqual(actual[0]['secret'], tsigkey_one['secret'])

        # Create a second tsigkey
        _, tsigkey_two = self.create_tsigkey(fixture=1)

        actual = self.storage.get_tsigkeys(self.admin_context)
        self.assertEqual(len(actual), 2)

        self.assertEqual(actual[1]['name'], tsigkey_two['name'])
        self.assertEqual(actual[1]['algorithm'], tsigkey_two['algorithm'])
        self.assertEqual(actual[1]['secret'], tsigkey_two['secret'])

    def test_get_tsigkeys_criterion(self):
        _, tsigkey_one = self.create_tsigkey(fixture=0)
        _, tsigkey_two = self.create_tsigkey(fixture=1)

        criterion = dict(
            name=tsigkey_one['name']
        )

        results = self.storage.get_tsigkeys(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], tsigkey_one['name'])

        criterion = dict(
            name=tsigkey_two['name']
        )

        results = self.storage.get_tsigkeys(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], tsigkey_two['name'])

    def test_get_tsigkey(self):
        # Create a tsigkey
        _, expected = self.create_tsigkey()

        actual = self.storage.get_tsigkey(self.admin_context, expected['id'])

        self.assertEqual(actual['name'], expected['name'])
        self.assertEqual(actual['algorithm'], expected['algorithm'])
        self.assertEqual(actual['secret'], expected['secret'])

    def test_get_tsigkey_missing(self):
        with self.assertRaises(exceptions.TsigKeyNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.get_tsigkey(self.admin_context, uuid)

    def test_update_tsigkey(self):
        # Create a tsigkey
        fixture, tsigkey = self.create_tsigkey()

        updated = self.storage.update_tsigkey(self.admin_context,
                                              tsigkey['id'],
                                              fixture)

        self.assertEqual(updated['name'], fixture['name'])
        self.assertEqual(updated['algorithm'], fixture['algorithm'])
        self.assertEqual(updated['secret'], fixture['secret'])

    def test_update_tsigkey_duplicate(self):
        # Create two tsigkeys
        self.create_tsigkey(fixture=0)
        _, tsigkey = self.create_tsigkey(fixture=1)

        values = self.tsigkey_fixtures[0]

        with self.assertRaises(exceptions.DuplicateTsigKey):
            self.storage.update_tsigkey(self.admin_context, tsigkey['id'],
                                        values)

    def test_update_tsigkey_missing(self):
        with self.assertRaises(exceptions.TsigKeyNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.update_tsigkey(self.admin_context, uuid, {})

    def test_delete_tsigkey(self):
        tsigkey_fixture, tsigkey = self.create_tsigkey()

        self.storage.delete_tsigkey(self.admin_context, tsigkey['id'])

        with self.assertRaises(exceptions.TsigKeyNotFound):
            self.storage.get_tsigkey(self.admin_context, tsigkey['id'])

    def test_delete_tsigkey_missing(self):
        with self.assertRaises(exceptions.TsigKeyNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.delete_tsigkey(self.admin_context, uuid)

    # Domain Tests
    def test_create_domain(self):
        values = {
            'name': 'example.net.',
            'email': 'example@example.net'
        }

        result = self.storage.create_domain(self.admin_context, values=values)

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
        actual = self.storage.get_domains(self.admin_context)
        self.assertEqual(actual, [])

        # Create a single domain
        fixture_one, domain_one = self.create_domain()

        actual = self.storage.get_domains(self.admin_context)
        self.assertEqual(len(actual), 1)

        self.assertEqual(actual[0]['name'], domain_one['name'])
        self.assertEqual(actual[0]['email'], domain_one['email'])

        # Create a second domain
        self.create_domain(fixture=1)

        actual = self.storage.get_domains(self.admin_context)
        self.assertEqual(len(actual), 2)

    def test_get_domains_criterion(self):
        _, domain_one = self.create_domain(0)
        _, domain_two = self.create_domain(1)

        criterion = dict(
            name=domain_one['name']
        )

        results = self.storage.get_domains(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], domain_one['name'])
        self.assertEqual(results[0]['email'], domain_one['email'])

        criterion = dict(
            name=domain_two['name']
        )

        results = self.storage.get_domains(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], domain_two['name'])
        self.assertEqual(results[0]['email'], domain_two['email'])

    def test_get_domain(self):
        # Create a domain
        fixture, expected = self.create_domain()
        actual = self.storage.get_domain(self.admin_context, expected['id'])

        self.assertEqual(actual['name'], expected['name'])
        self.assertEqual(actual['email'], expected['email'])

    def test_get_domain_missing(self):
        with self.assertRaises(exceptions.DomainNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.get_domain(self.admin_context, uuid)

    def test_find_domain_criterion(self):
        _, domain_one = self.create_domain(0)
        _, domain_two = self.create_domain(1)

        criterion = dict(
            name=domain_one['name']
        )

        result = self.storage.find_domain(self.admin_context, criterion)

        self.assertEqual(result['name'], domain_one['name'])
        self.assertEqual(result['email'], domain_one['email'])

        criterion = dict(
            name=domain_two['name']
        )

        result = self.storage.find_domain(self.admin_context, criterion)

        self.assertEqual(result['name'], domain_two['name'])
        self.assertEqual(result['email'], domain_two['email'])

    def test_find_domain_criterion_missing(self):
        _, expected = self.create_domain(0)

        criterion = dict(
            name=expected['name'] + "NOT FOUND"
        )

        with self.assertRaises(exceptions.DomainNotFound):
            self.storage.find_domain(self.admin_context, criterion)

    def test_update_domain(self):
        # Create a domain
        fixture, domain = self.create_domain()

        updated = self.storage.update_domain(self.admin_context, domain['id'],
                                             fixture)

        self.assertEqual(updated['name'], fixture['name'])
        self.assertEqual(updated['email'], fixture['email'])

    def test_update_domain_duplicate(self):
        # Create two domains
        fixture_one, domain_one = self.create_domain(fixture=0)
        _, domain_two = self.create_domain(fixture=1)

        with self.assertRaises(exceptions.DuplicateDomain):
            self.storage.update_domain(self.admin_context, domain_two['id'],
                                       fixture_one)

    def test_update_domain_missing(self):
        with self.assertRaises(exceptions.DomainNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.update_domain(self.admin_context, uuid, {})

    def test_delete_domain(self):
        domain_fixture, domain = self.create_domain()

        self.storage.delete_domain(self.admin_context, domain['id'])

        with self.assertRaises(exceptions.DomainNotFound):
            self.storage.get_domain(self.admin_context, domain['id'])

    def test_delete_domain_missing(self):
        with self.assertRaises(exceptions.DomainNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.delete_domain(self.admin_context, uuid)

    def test_create_record(self):
        domain_fixture, domain = self.create_domain()

        values = {
            'name': 'www.%s' % domain['name'],
            'type': 'A',
            'data': '192.0.2.1',
        }

        result = self.storage.create_record(self.admin_context, domain['id'],
                                            values=values)

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['name'], values['name'])
        self.assertEqual(result['type'], values['type'])
        self.assertEqual(result['data'], values['data'])

    def test_get_records(self):
        _, domain = self.create_domain()
        actual = self.storage.get_records(self.admin_context, domain['id'])
        self.assertEqual(actual, [])

        # Create a single record
        _, record_one = self.create_record(domain, fixture=0)

        actual = self.storage.get_records(self.admin_context, domain['id'])
        self.assertEqual(len(actual), 1)

        self.assertEqual(actual[0]['name'], record_one['name'])
        self.assertEqual(actual[0]['type'], record_one['type'])
        self.assertEqual(actual[0]['data'], record_one['data'])

        # Create a second record
        _, record_two = self.create_record(domain, fixture=1)

        actual = self.storage.get_records(self.admin_context, domain['id'])
        self.assertEqual(len(actual), 2)

        self.assertEqual(actual[1]['name'], record_two['name'])
        self.assertEqual(actual[1]['type'], record_two['type'])
        self.assertEqual(actual[1]['data'], record_two['data'])

    def test_get_records_criterion(self):
        _, domain = self.create_domain()

        _, record_one = self.create_record(domain, fixture=0)
        self.create_record(domain, fixture=1)

        criterion = dict(
            data=record_one['data']
        )

        results = self.storage.get_records(self.admin_context, domain['id'],
                                           criterion)

        self.assertEqual(len(results), 1)

        criterion = dict(
            type='A'
        )

        results = self.storage.get_records(self.admin_context, domain['id'],
                                           criterion)

        self.assertEqual(len(results), 2)

    def test_get_records_criterion_wildcard(self):
        _, domain = self.create_domain()

        values = {'name': 'one.%s' % domain['name']}

        self.create_record(domain, fixture=0, values=values)
        criterion = dict(
            name="%%%s" % domain['name']
        )

        results = self.storage.get_records(self.admin_context, domain['id'],
                                           criterion)

        self.assertEqual(len(results), 1)

    def test_get_record(self):
        _, domain = self.create_domain()

        _, expected = self.create_record(domain)

        actual = self.storage.get_record(self.admin_context, expected['id'])

        self.assertEqual(actual['name'], expected['name'])
        self.assertEqual(actual['type'], expected['type'])
        self.assertEqual(actual['data'], expected['data'])

    def test_get_record_missing(self):
        with self.assertRaises(exceptions.RecordNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.get_record(self.admin_context, uuid)

    def test_find_record_criterion(self):
        _, domain = self.create_domain(0)
        _, expected = self.create_record(domain)

        criterion = dict(
            name=expected['name']
        )

        actual = self.storage.find_record(self.admin_context, domain['id'],
                                          criterion)

        self.assertEqual(actual['name'], expected['name'])
        self.assertEqual(actual['type'], expected['type'])
        self.assertEqual(actual['data'], expected['data'])

    def test_find_record_criterion_missing(self):
        _, domain = self.create_domain(0)
        _, expected = self.create_record(domain)

        criterion = dict(
            name=expected['name'] + "NOT FOUND"
        )

        with self.assertRaises(exceptions.RecordNotFound):
            self.storage.find_record(self.admin_context, domain['id'],
                                     criterion)

    def test_update_record(self):
        domain_fixture, domain = self.create_domain()

        # Create a record
        record_fixture, record = self.create_record(domain)

        updated = self.storage.update_record(self.admin_context, record['id'],
                                             record_fixture)

        self.assertEqual(updated['name'], record_fixture['name'])
        self.assertEqual(updated['type'], record_fixture['type'])
        self.assertEqual(updated['data'], record_fixture['data'])

    def test_update_record_missing(self):
        with self.assertRaises(exceptions.RecordNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.update_record(self.admin_context, uuid, {})

    def test_delete_record(self):
        _, domain = self.create_domain()

        # Create a record
        _, record = self.create_record(domain)

        self.storage.delete_record(self.admin_context, record['id'])

        with self.assertRaises(exceptions.RecordNotFound):
            self.storage.get_record(self.admin_context, record['id'])

    def test_delete_record_missing(self):
        with self.assertRaises(exceptions.RecordNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.delete_record(self.admin_context, uuid)

    def test_ping(self):
        pong = self.storage.ping(self.admin_context)

        self.assertEqual(pong['status'], True)
        self.assertIsNotNone(pong['rtt'])
