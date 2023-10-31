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
from unittest import mock

import eventlet
import oslotest.base

from designate.backend import impl_nsd4
from designate import context
from designate import exceptions
from designate import objects


class NSD4BackendTestCase(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()

        self.context = mock.Mock()
        self.admin_context = mock.Mock()
        mock.patch.object(
            context.DesignateContext, 'get_admin_context',
            return_value=self.admin_context).start()

        keyfile = mock.sentinel.key
        certfile = mock.sentinel.cert

        self.zone = objects.Zone(
            id='e2bed4dc-9d01-11e4-89d3-123b93f75cba',
            name='example.com.',
            email='example@example.com',
        )
        self.port = 6969
        self.target = {
            'id': '4588652b-50e7-46b9-b688-a9bad40a873e',
            'type': 'nsd4',
            'masters': [
                {'host': '192.0.2.1', 'port': 53},
                {'host': '192.0.2.2', 'port': 35},
            ],
            'options': [
                {'key': 'keyfile', 'value': keyfile.name},
                {'key': 'certfile', 'value': certfile.name},
                {'key': 'pattern', 'value': 'test-pattern'},
                {'key': 'port', 'value': str(self.port)},
            ],
        }

        self.backend = impl_nsd4.NSD4Backend(
            objects.PoolTarget.from_dict(self.target)
        )

    @mock.patch.object(eventlet, 'connect')
    @mock.patch.object(eventlet, 'wrap_ssl')
    def _test_command(self, mock_ssl, mock_connect, command_context):
        sock = mock.MagicMock()
        stream = mock.MagicMock()
        mock_connect.return_value = mock.sentinel.client
        mock_ssl.return_value = sock
        sock.makefile.return_value = stream
        if command_context == 'create_fail':
            stream.read.return_value = 'goat'
        else:
            stream.read.return_value = 'ok'

        if command_context == 'create':
            self.backend.create_zone(self.context, self.zone)
            command = 'NSDCT1 addzone %s test-pattern\n' % self.zone.name
        elif command_context == 'delete':
            self.backend.delete_zone(self.context, self.zone)
            command = 'NSDCT1 delzone %s\n' % self.zone.name
        elif command_context == 'create_fail':
            self.assertRaises(exceptions.Backend,
                              self.backend.create_zone,
                              self.context, self.zone)
            command = 'NSDCT1 addzone %s test-pattern\n' % self.zone.name

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
        self.assertRaises(exceptions.Backend,
                          self.backend.create_zone,
                          self.context, self.zone)

    def test_socket_error(self):
        self.backend._command = mock.MagicMock(side_effect=socket.error)
        self.assertRaises(exceptions.Backend,
                          self.backend.create_zone,
                          self.context, self.zone)
