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

import eventlet
import fixtures
from mock import MagicMock
import os
import socket
import ssl
from oslo.config import cfg

from designate import exceptions
from designate import tests
from designate.tests.test_backend import BackendTestMixin
from designate.tests import resources

# impl_nsd4slave needs to register its options before being instanciated.
# Import it and pretend to use it to avoid flake8 unused import errors.
from designate.backend import impl_nsd4slave
impl_nsd4slave


class NSD4ServerStub:
    recved_command = None
    response = 'ok'
    keyfile = os.path.join(resources.path, 'ssl', 'nsd_server.key')
    certfile = os.path.join(resources.path, 'ssl', 'nsd_server.pem')

    def handle(self, client_sock, client_addr):
        stream = client_sock.makefile()
        self.recved_command = stream.readline()
        stream.write(self.response)
        stream.flush()

    def start(self):
        self.port = 1025
        while True:
            try:
                eventlet.spawn_n(eventlet.serve,
                                 eventlet.wrap_ssl(
                                     eventlet.listen(('127.0.0.1', self.port)),
                                     keyfile=self.keyfile,
                                     certfile=self.certfile,
                                     server_side=True),
                                 self.handle)
                break
            except socket.error:
                self.port = self.port + 1

    def stop(self):
        eventlet.StopServe()


class NSD4Fixture(fixtures.Fixture):
    def setUp(self):
        super(NSD4Fixture, self).setUp()
        self.servers = [NSD4ServerStub(), NSD4ServerStub()]
        [server.start() for server in self.servers]
        impl_nsd4slave.DEFAULT_PORT = self.servers[0].port
        cfg.CONF.set_override('backend_driver', 'nsd4slave', 'service:agent')
        cfg.CONF.set_override(
            'servers', ['127.0.0.1', '127.0.0.1:%d' % self.servers[1].port],
            'backend:nsd4slave')
        keyfile = os.path.join(resources.path, 'ssl', 'nsd_control.key')
        certfile = os.path.join(resources.path, 'ssl', 'nsd_control.pem')
        cfg.CONF.set_override('keyfile', keyfile, 'backend:nsd4slave')
        cfg.CONF.set_override('certfile', certfile, 'backend:nsd4slave')
        cfg.CONF.set_override('pattern', 'test-pattern', 'backend:nsd4slave')
        self.addCleanup(self.tearDown)

    def tearDown(self):
        [server.stop() for server in self.servers]


# NOTE: We'll only test the specifics to the nsd4 backend here.
# Rest is handled via scenarios
class NSD4SlaveBackendTestCase(tests.TestCase, BackendTestMixin):
    def setUp(self):
        super(NSD4SlaveBackendTestCase, self).setUp()

        self.server_fixture = NSD4Fixture()
        self.useFixture(self.server_fixture)

        self.backend = self.get_backend_driver()

    def test_create_domain(self):
        context = self.get_context()
        domain = self.get_domain_fixture()
        self.backend.create_domain(context, domain)
        command = 'NSDCT1 addzone %s test-pattern\n' % domain['name']
        [self.assertEqual(server.recved_command, command)
         for server in self.server_fixture.servers]

    def test_delete_domain(self):
        context = self.get_context()
        domain = self.get_domain_fixture()
        self.backend.delete_domain(context, domain)
        command = 'NSDCT1 delzone %s\n' % domain['name']
        [self.assertEqual(server.recved_command, command)
         for server in self.server_fixture.servers]

    def test_server_not_ok(self):
        self.server_fixture.servers[0].response = 'goat'
        context = self.get_context()
        domain = self.get_domain_fixture()
        self.assertRaises(exceptions.NSD4SlaveBackendError,
                          self.backend.create_domain,
                          context, domain)

    def test_ssl_error(self):
        self.backend._command = MagicMock(side_effet=ssl.SSLError)
        context = self.get_context()
        domain = self.get_domain_fixture()
        self.assertRaises(exceptions.NSD4SlaveBackendError,
                          self.backend.create_domain,
                          context, domain)

    def test_socket_error(self):
        self.backend._command = MagicMock(side_effet=socket.error)
        context = self.get_context()
        domain = self.get_domain_fixture()
        self.assertRaises(exceptions.NSD4SlaveBackendError,
                          self.backend.create_domain,
                          context, domain)
