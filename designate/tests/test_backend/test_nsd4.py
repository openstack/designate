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

import socket
import ssl

import eventlet
import mock

from designate import exceptions
from designate import objects
from designate.tests.test_backend import BackendTestCase
from designate.backend import impl_nsd4


# NOTE: We'll only test the specifics to the nsd4 backend here.
# Rest is handled via scenarios
class NSD4BackendTestCase(BackendTestCase):
    def setUp(self):
        super(NSD4BackendTestCase, self).setUp()

        # NOTE(hieulq): we mock out NSD4 back-end with random port

        keyfile = mock.sentinel.key
        certfile = mock.sentinel.cert
        self.port = 6969
        self.target = objects.PoolTarget.from_dict({
            'id': '4588652b-50e7-46b9-b688-a9bad40a873e',
            'type': 'nsd4',
            'masters': [{'host': '192.0.2.1', 'port': 53},
                        {'host': '192.0.2.2', 'port': 35}],
            'options': [
                {'key': 'keyfile', 'value': keyfile.name},
                {'key': 'certfile', 'value': certfile.name},
                {'key': 'pattern', 'value': 'test-pattern'},
                {'key': 'port', 'value': str(self.port)}
            ],
        })
        self.backend = impl_nsd4.NSD4Backend(self.target)

    @mock.patch.object(eventlet, 'connect')
    @mock.patch.object(eventlet, 'wrap_ssl')
    def _test_command(self, mock_ssl, mock_connect, command_context):
        sock = mock.MagicMock()
        stream = mock.MagicMock()
        mock_connect.return_value = mock.sentinel.client
        mock_ssl.return_value = sock
        sock.makefile.return_value = stream
        if command_context is 'create_fail':
            stream.read.return_value = 'goat'
        else:
            stream.read.return_value = 'ok'

        context = self.get_context()
        zone = self.get_zone_fixture()

        if command_context is 'create':
            self.backend.create_zone(context, zone)
            command = 'NSDCT1 addzone %s test-pattern\n' % zone['name']
        elif command_context is 'delete':
            self.backend.delete_zone(context, zone)
            command = 'NSDCT1 delzone %s\n' % zone['name']
        elif command_context is 'create_fail':
            self.assertRaises(exceptions.Backend,
                              self.backend.create_zone,
                              context, zone)
            command = 'NSDCT1 addzone %s test-pattern\n' % zone['name']

        stream.write.assert_called_once_with(command)
        mock_ssl.assert_called_once_with(mock.sentinel.client,
                                         certfile=mock.sentinel.cert.name,
                                         keyfile=mock.sentinel.key.name)
        mock_connect.assert_called_once_with(('127.0.0.1', self.port))
        sock.makefile.assert_called_once_with()
        sock.close.assert_called_once_with()
        stream.close.assert_called_once_with()
        stream.flush.assert_called_once_with()
        stream.read.assert_called_once_with()

    def test_create_zone(self):
        self._test_command(command_context='create')

    def test_delete_zone(self):
        self._test_command(command_context='delete')

    def test_server_not_ok(self):
        self._test_command(command_context='create_fail')

    def test_ssl_error(self):
        self.backend._command = mock.MagicMock(side_effect=ssl.SSLError)
        context = self.get_context()
        zone = self.get_zone_fixture()
        self.assertRaises(exceptions.Backend,
                          self.backend.create_zone,
                          context, zone)

    def test_socket_error(self):
        self.backend._command = mock.MagicMock(side_effect=socket.error)
        context = self.get_context()
        zone = self.get_zone_fixture()
        self.assertRaises(exceptions.Backend,
                          self.backend.create_zone,
                          context, zone)
