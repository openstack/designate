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

import mock
import oslotest.base

from designate import utils
from designate.tests import fixtures


class TestSocket(oslotest.base.BaseTestCase):
    def setUp(self):
        super(TestSocket, self).setUp()
        self.stdlog = fixtures.StandardLogging()
        self.useFixture(self.stdlog)

    @mock.patch('socket.socket')
    def test_bind_tcp(self, mock_sock_impl):
        mock_sock = mock.MagicMock()
        mock_sock_impl.return_value = mock_sock

        utils.bind_tcp('127.0.0.1', 53, 100, 1)

        mock_sock.setblocking.assert_called_once_with(True)

        mock_sock.bind.assert_called_once_with(('127.0.0.1', 53))

        mock_sock.listen.assert_called_once_with(100)

        self.assertIn(
            'Opening TCP Listening Socket on 127.0.0.1:53',
            self.stdlog.logger.output
        )

    @mock.patch('socket.socket')
    def test_bind_tcp_without_port(self, mock_sock_impl):
        random_port = random.randint(1024, 65535)
        mock_sock = mock.MagicMock()
        mock_sock_impl.return_value = mock_sock

        mock_sock.getsockname.return_value = ('127.0.0.1', random_port)

        utils.bind_tcp('127.0.0.1', 0, 100, 1)

        self.assertIn(
            'Listening on TCP port %(port)d' % {'port': random_port},
            self.stdlog.logger.output
        )

    @mock.patch('socket.socket')
    def test_bind_udp(self, mock_sock_impl):
        mock_sock = mock.MagicMock()
        mock_sock_impl.return_value = mock_sock

        utils.bind_udp('127.0.0.1', 53)

        mock_sock.setblocking.assert_called_once_with(True)

        mock_sock.bind.assert_called_once_with(('127.0.0.1', 53))

        self.assertIn(
            'Opening UDP Listening Socket on 127.0.0.1:53',
            self.stdlog.logger.output
        )

    @mock.patch('socket.socket')
    def test_bind_udp_without_port(self, mock_sock_impl):
        random_port = random.randint(1024, 65535)
        mock_sock = mock.MagicMock()
        mock_sock_impl.return_value = mock_sock

        mock_sock.getsockname.return_value = ('127.0.0.1', random_port)

        utils.bind_udp('127.0.0.1', 0)

        self.assertIn(
            'Listening on UDP port %(port)d' % {'port': random_port},
            self.stdlog.logger.output
        )
