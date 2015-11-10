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

import os
import socket
import ssl

import eventlet
import fixtures
from mock import MagicMock

from designate import exceptions
from designate import objects
from designate.tests.test_backend import BackendTestCase
from designate.tests import resources
from designate.backend import impl_nsd4


class NSD4ServerStub(object):
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
        self.server = NSD4ServerStub()
        self.server.start()

        self.addCleanup(self.tearDown)

    def tearDown(self):
        self.server.stop()


# NOTE: We'll only test the specifics to the nsd4 backend here.
# Rest is handled via scenarios
class NSD4BackendTestCase(BackendTestCase):
    def setUp(self):
        super(NSD4BackendTestCase, self).setUp()

        self.server_fixture = NSD4Fixture()
        self.useFixture(self.server_fixture)

        keyfile = os.path.join(resources.path, 'ssl', 'nsd_control.key')
        certfile = os.path.join(resources.path, 'ssl', 'nsd_control.pem')

        self.target = objects.PoolTarget.from_dict({
            'id': '4588652b-50e7-46b9-b688-a9bad40a873e',
            'type': 'nsd4',
            'masters': [{'host': '192.0.2.1', 'port': 53},
                        {'host': '192.0.2.2', 'port': 35}],
            'options': [
                {'key': 'keyfile', 'value': keyfile},
                {'key': 'certfile', 'value': certfile},
                {'key': 'pattern', 'value': 'test-pattern'},
                {'key': 'port', 'value': self.server_fixture.server.port}
            ],
        })

        self.backend = impl_nsd4.NSD4Backend(self.target)

    def test_create_zone(self):
        context = self.get_context()
        zone = self.get_zone_fixture()
        self.backend.create_zone(context, zone)
        command = 'NSDCT1 addzone %s test-pattern\n' % zone['name']
        self.assertEqual(command, self.server_fixture.server.recved_command)

    def test_delete_zone(self):
        context = self.get_context()
        zone = self.get_zone_fixture()
        self.backend.delete_zone(context, zone)
        command = 'NSDCT1 delzone %s\n' % zone['name']
        self.assertEqual(command, self.server_fixture.server.recved_command)

    def test_server_not_ok(self):
        self.server_fixture.server.response = 'goat'
        context = self.get_context()
        zone = self.get_zone_fixture()
        self.assertRaises(exceptions.Backend,
                          self.backend.create_zone,
                          context, zone)

    def test_ssl_error(self):
        self.backend._command = MagicMock(side_effect=ssl.SSLError)
        context = self.get_context()
        zone = self.get_zone_fixture()
        self.assertRaises(exceptions.Backend,
                          self.backend.create_zone,
                          context, zone)

    def test_socket_error(self):
        self.backend._command = MagicMock(side_effect=socket.error)
        context = self.get_context()
        zone = self.get_zone_fixture()
        self.assertRaises(exceptions.Backend,
                          self.backend.create_zone,
                          context, zone)
