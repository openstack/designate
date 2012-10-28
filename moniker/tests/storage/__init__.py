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
import copy
from nose import SkipTest
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging
from moniker.tests import TestCase
from moniker import storage
from moniker import exceptions

LOG = logging.getLogger(__name__)


class StorageTestCase(TestCase):
    __test__ = False

    def get_storage_driver(self, conf=cfg.CONF):
        engine = storage.get_engine(conf)
        connection = engine.get_connection(conf)
        return connection


class StorageDriverTestCase(StorageTestCase):
    __test__ = False

    server_fixtures = [{
        'name': 'ns1.example.org',
        'ipv4': '192.0.2.1',
        'ipv6': '2001:db8::1',
    }, {
        'name': 'ns2.example.org',
        'ipv4': '192.0.2.2',
        'ipv6': '2001:db8::2',
    }, {
        'name': 'ns2.example.org',
        'ipv4': '192.0.2.2',
        'ipv6': '2001:db8::2',
    }]

    def setUp(self):
        super(StorageDriverTestCase, self).setUp()
        self.storage_conn = self.get_storage_driver()
        self.admin_context = self.get_admin_context()

    def create_server_fixture(self, fixture=0, values={}):
        _values = copy.copy(self.server_fixtures[fixture])
        _values.update(values)

        return self.storage_conn.create_server(self.admin_context, _values)

    def test_init(self):
        self.get_storage_driver()

    def test_create_server(self):
        values = {
            'name': 'ns1.example.org',
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
            'name': 'ns1.example.org',
            'ipv4': '192.0.2.1',
            'ipv6': None,
        }, {
            'name': 'ns2.example.org',
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
        self.create_server_fixture()

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
            'name': 'localhost',
        }, {
            'name': 'localhost',
            'ipv4': '127.0.0.1',
        }, {
            'name': 'localhost',
            'ipv6': '::1',
        }]

        for value in values:
            with self.assertRaises(exceptions.DuplicateServer):
                self.create_server_fixture(values=value)

    def test_get_servers(self):
        actual = self.storage_conn.get_servers(self.admin_context)
        self.assertEqual(actual, [])

        # Create a single server
        server_one = self.create_server_fixture()

        actual = self.storage_conn.get_servers(self.admin_context)
        self.assertEqual(len(actual), 1)

        self.assertEqual(str(actual[0]['name']), str(server_one['name']))
        self.assertEqual(str(actual[0]['ipv4']), str(server_one['ipv4']))
        self.assertEqual(str(actual[0]['ipv6']), str(server_one['ipv6']))

        # Create a second server
        self.create_server_fixture(fixture=1)

        actual = self.storage_conn.get_servers(self.admin_context)
        self.assertEqual(len(actual), 2)

    def test_get_server(self):
        # Create a server
        expected = self.create_server_fixture()
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
        server = self.create_server_fixture()

        values = self.server_fixtures[1]
        updated = self.storage_conn.update_server(
            self.admin_context, server['id'], values)

        self.assertEqual(str(updated['name']), str(values['name']))
        self.assertEqual(str(updated['ipv4']), str(values['ipv4']))
        self.assertEqual(str(updated['ipv6']), str(values['ipv6']))

    def test_update_server_duplicate(self):
        # Create two servers
        self.create_server_fixture(fixture=0)
        server = self.create_server_fixture(fixture=1)

        values = self.server_fixtures[0]

        with self.assertRaises(exceptions.DuplicateServer):
            self.storage_conn.update_server(
                self.admin_context, server['id'], values)

    def test_update_server_missing(self):
        with self.assertRaises(exceptions.ServerNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage_conn.update_server(self.admin_context, uuid, {})

    def test_delete_server(self):
        server = self.create_server_fixture(fixture=0)

        self.storage_conn.delete_server(self.admin_context, server['id'])

        with self.assertRaises(exceptions.ServerNotFound):
            self.storage_conn.get_server(self.admin_context, server['id'])

    def test_delete_server_missing(self):
        with self.assertRaises(exceptions.ServerNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage_conn.delete_server(self.admin_context, uuid)

    def test_create_domain(self):
        raise SkipTest()

    def test_create_domain_duplicate(self):
        raise SkipTest()

    def test_create_domain_missing(self):
        raise SkipTest()

    def test_get_domains(self):
        raise SkipTest()

    def test_get_domain(self):
        raise SkipTest()

    def test_get_domain_missing(self):
        raise SkipTest()

    def test_update_domain(self):
        raise SkipTest()

    def test_update_domain_duplicate(self):
        raise SkipTest()

    def test_update_domain_missing(self):
        raise SkipTest()

    def test_delete_domain(self):
        raise SkipTest()

    def test_delete_domain_missing(self):
        raise SkipTest()

    def test_create_record(self):
        raise SkipTest()

    def test_get_records(self):
        raise SkipTest()

    def test_get_record(self):
        raise SkipTest()

    def test_get_record_missing(self):
        raise SkipTest()

    def test_update_record(self):
        raise SkipTest()

    def test_update_record_missing(self):
        raise SkipTest()

    def test_delete_record(self):
        raise SkipTest()

    def test_delete_record_missing(self):
        raise SkipTest()
