# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Author: Artom Lifshitz <artom.lifshitz@enovance.com>
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

from mock import call
from mock import MagicMock
from designate import exceptions
from designate import tests
from designate.tests.test_backend import BackendTestMixin


class MultiBackendTestCase(tests.TestCase, BackendTestMixin):
    """
    Test the master/slave ordering as defined in MultiBackend.

    Test that create for tsigkeys, servers and domains is done on the master
    first, then on the slave. At the same time, test that if the slave raises
    an exception, delete is called on the master to cleanup.

    Test that delete for tsigkeys, servers and domains is done on the slave
    first, then on the master. At the same time, test that if the master raises
    an exception, create is called on the slave to cleanup.

    Test that updates and all operations on records are done on the master
    only.
    """

    def setUp(self):
        super(MultiBackendTestCase, self).setUp()
        self.config(backend_driver='multi', group='service:agent')
        self.backend = self.get_backend_driver()

        self.backends = MagicMock()
        self.backend.master = MagicMock()
        self.backend.slave = MagicMock()
        self.backends.master = self.backend.master
        self.backends.slave = self.backend.slave

    def test_create_tsigkey(self):
        context = self.get_context()
        tsigkey = self.get_tsigkey_fixture()
        self.backend.slave.create_tsigkey = MagicMock(
            side_effect=exceptions.Backend)
        self.assertRaises(exceptions.Backend, self.backend.create_tsigkey,
                          context, tsigkey)
        self.assertEqual(self.backends.mock_calls,
                         [call.master.create_tsigkey(context, tsigkey),
                          call.slave.create_tsigkey(context, tsigkey),
                          call.master.delete_tsigkey(context, tsigkey)])

    def test_update_tsigkey(self):
        context = self.get_context()
        tsigkey = self.get_tsigkey_fixture()
        self.backend.update_tsigkey(context, tsigkey)
        self.assertEqual(self.backends.mock_calls,
                         [call.master.update_tsigkey(context, tsigkey)])

    def test_delete_tsigkey(self):
        context = self.get_context()
        tsigkey = self.get_tsigkey_fixture()
        self.backend.master.delete_tsigkey = MagicMock(
            side_effect=exceptions.Backend)
        self.assertRaises(exceptions.Backend, self.backend.delete_tsigkey,
                          context, tsigkey)
        self.assertEqual(self.backends.mock_calls,
                         [call.slave.delete_tsigkey(context, tsigkey),
                          call.master.delete_tsigkey(context, tsigkey),
                          call.slave.create_tsigkey(context, tsigkey)])

    def test_create_domain(self):
        context = self.get_context()
        domain = self.get_domain_fixture()
        self.backend.slave.create_domain = MagicMock(
            side_effect=exceptions.Backend)
        self.assertRaises(exceptions.Backend, self.backend.create_domain,
                          context, domain)
        self.assertEqual(self.backends.mock_calls,
                         [call.master.create_domain(context, domain),
                          call.slave.create_domain(context, domain),
                          call.master.delete_domain(context, domain)])

    def test_update_domain(self):
        context = self.get_context()
        domain = self.get_domain_fixture()
        self.backend.update_domain(context, domain)
        self.assertEqual(self.backends.mock_calls,
                         [call.master.update_domain(context, domain)])

    def test_delete_domain(self):
        context = self.get_context()
        domain = self.get_domain_fixture()
        # Since multi's delete fetches the domain from central to be able to
        # recreate it if something goes wrong, create the domain first
        self.backend.central_service.create_server(
            self.get_admin_context(), self.get_server_fixture())
        self.backend.central_service.create_domain(context, domain)
        self.backend.master.delete_domain = MagicMock(
            side_effect=exceptions.Backend)
        self.assertRaises(exceptions.Backend, self.backend.delete_domain,
                          context, domain)
        self.assertEqual(self.backends.mock_calls,
                         [call.slave.delete_domain(context, domain),
                          call.master.delete_domain(context, domain),
                          call.slave.create_domain(context, domain)])

    def test_create_server(self):
        context = self.get_context()
        server = self.get_server_fixture()
        self.backend.slave.create_server = MagicMock(
            side_effect=exceptions.Backend)
        self.assertRaises(exceptions.Backend, self.backend.create_server,
                          context, server)
        self.assertEqual(self.backends.mock_calls,
                         [call.master.create_server(context, server),
                          call.slave.create_server(context, server),
                          call.master.delete_server(context, server)])

    def test_update_server(self):
        context = self.get_context()
        server = self.get_server_fixture()
        self.backend.update_server(context, server)
        self.assertEqual(self.backends.mock_calls,
                         [call.master.update_server(context, server)])

    def test_delete_server(self):
        context = self.get_context()
        server = self.get_server_fixture()
        self.backend.master.delete_server = MagicMock(
            side_effect=exceptions.Backend)
        self.assertRaises(exceptions.Backend, self.backend.delete_server,
                          context, server)
        self.assertEqual(self.backends.mock_calls,
                         [call.slave.delete_server(context, server),
                          call.master.delete_server(context, server),
                          call.slave.create_server(context, server)])

    def test_create_record(self):
        context = self.get_context()
        domain = self.get_domain_fixture()
        record = self.get_record_fixture(domain['name'])
        self.backend.create_record(context, domain, record)
        self.assertEqual(self.backends.mock_calls,
                         [call.master.create_record(context, domain, record)])

    def test_update_record(self):
        context = self.get_context()
        domain = self.get_domain_fixture()
        record = self.get_record_fixture(domain['name'])
        self.backend.update_record(context, domain, record)
        self.assertEqual(self.backends.mock_calls,
                         [call.master.update_record(context, domain, record)])

    def test_delete_record(self):
        context = self.get_context()
        domain = self.get_domain_fixture()
        record = self.get_record_fixture(domain['name'])
        self.backend.delete_record(context, domain, record)
        self.assertEqual(self.backends.mock_calls,
                         [call.master.delete_record(context, domain, record)])

    def test_ping(self):
        context = self.get_context()
        self.backend.ping(context)
        self.assertEqual(self.backends.mock_calls,
                         [call.master.ping(context),
                          call.slave.ping(context)])

    def test_start(self):
        self.backend.start()
        self.assertEqual(self.backends.mock_calls,
                         [call.master.start(), call.slave.start()])

    def test_stop(self):
        self.backend.stop()
        self.assertEqual(self.backends.mock_calls,
                         [call.slave.stop(), call.master.stop()])
