# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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

import binascii
import errno
import socket
import struct

import dns
import dns.message
import mock
from oslo_log import log as logging

from designate.tests.test_mdns import MdnsTestCase

LOG = logging.getLogger(__name__)


def hex_wire(response):
    return binascii.b2a_hex(response.to_wire())


class MdnsServiceTest(MdnsTestCase):

    # DNS packet with IQUERY opcode
    query_payload = binascii.a2b_hex(
        "271209000001000000000000076578616d706c6503636f6d0000010001"
    )
    expected_response = binascii.a2b_hex(
        b"271289050001000000000000076578616d706c6503636f6d0000010001"
    )
    # expected response is an error code REFUSED.  The other fields are
    # id 10002
    # opcode IQUERY
    # rcode REFUSED
    # flags QR RD
    # ;QUESTION
    # example.com. IN A
    # ;ANSWER
    # ;AUTHORITY
    # ;ADDITIONAL

    # Use self._print_dns_msg() to display the messages

    def setUp(self):
        super(MdnsServiceTest, self).setUp()

        # Use a random port for MDNS
        self.config(port=0, group='service:mdns')

        self.service = self.start_service('mdns')
        self.addr = ['0.0.0.0', 5556]

    @staticmethod
    def _print_dns_msg(desc, wire):
        """Print DNS message for debugging"""
        q = dns.message.from_wire(wire).to_text()
        print("%s:\n%s\n" % (desc, q))

    def test_stop(self):
        # NOTE: Start is already done by the fixture in start_service()
        self.service.stop()

    @mock.patch.object(dns.message, 'make_query')
    def test_handle_empty_payload(self, query_mock):
        mock_socket = mock.Mock()
        self.service._dns_handle_udp_query(mock_socket, self.addr,
                                           ' '.encode('utf-8'))
        query_mock.assert_called_once_with('unknown', dns.rdatatype.A)

    def test_handle_udp_payload(self):
        mock_socket = mock.Mock()
        self.service._dns_handle_udp_query(mock_socket, self.addr,
                                           self.query_payload)
        mock_socket.sendto.assert_called_once_with(self.expected_response,
                                                   self.addr)

    def test__dns_handle_tcp_conn_fail_unpack(self):
        # will call recv() only once
        mock_socket = mock.Mock()
        mock_socket.recv.side_effect = ['X', 'boo']  # X will fail unpack

        self.service._dns_handle_tcp_conn(('1.2.3.4', 42), mock_socket)
        self.assertEqual(1, mock_socket.recv.call_count)
        self.assertEqual(1, mock_socket.close.call_count)

    def test__dns_handle_tcp_conn_one_query(self):
        payload = self.query_payload
        mock_socket = mock.Mock()
        pay_len = struct.pack("!H", len(payload))
        mock_socket.recv.side_effect = [pay_len, payload, socket.timeout]

        self.service._dns_handle_tcp_conn(('1.2.3.4', 42), mock_socket)

        self.assertEqual(3, mock_socket.recv.call_count)
        self.assertEqual(1, mock_socket.sendall.call_count)
        self.assertEqual(1, mock_socket.close.call_count)
        wire = mock_socket.sendall.call_args[0][0]
        expected_length_raw = wire[:2]
        (expected_length, ) = struct.unpack('!H', expected_length_raw)
        self.assertEqual(len(wire), expected_length + 2)
        self.assertEqual(self.expected_response, wire[2:])

    def test__dns_handle_tcp_conn_multiple_queries(self):
        payload = self.query_payload
        mock_socket = mock.Mock()
        pay_len = struct.pack("!H", len(payload))
        # Process 5 queries, then receive a misaligned query and close the
        # connection there
        mock_socket.recv.side_effect = [
            pay_len, payload,
            pay_len, payload,
            pay_len, payload,
            pay_len, payload,
            pay_len, payload,
            'X', payload,
            pay_len, payload,
            pay_len, payload,
        ]
        self.service._dns_handle_tcp_conn(('1.2.3.4', 42), mock_socket)

        self.assertEqual(11, mock_socket.recv.call_count)
        self.assertEqual(5, mock_socket.sendall.call_count)
        self.assertEqual(1, mock_socket.close.call_count)

    def test__dns_handle_tcp_conn_multiple_queries_socket_error(self):
        payload = self.query_payload
        mock_socket = mock.Mock()
        pay_len = struct.pack("!H", len(payload))
        # Process 5 queries, then receive a socket error and close the
        # connection there
        mock_socket.recv.side_effect = [
            pay_len, payload,
            pay_len, payload,
            pay_len, payload,
            pay_len, payload,
            pay_len, payload,
            socket.error(errno.EAGAIN),
            pay_len, payload,
            pay_len, payload,
        ]
        self.service._dns_handle_tcp_conn(('1.2.3.4', 42), mock_socket)

        self.assertEqual(11, mock_socket.recv.call_count)
        self.assertEqual(5, mock_socket.sendall.call_count)
        self.assertEqual(1, mock_socket.close.call_count)

    def test__dns_handle_tcp_conn_multiple_queries_ignore_bad_query(self):
        payload = self.query_payload
        mock_socket = mock.Mock()
        pay_len = struct.pack("!H", len(payload))
        # Ignore a broken query and keep going as long as the query len
        # header was correct
        mock_socket.recv.side_effect = [
            pay_len, payload,
            pay_len, payload[:-5] + b'hello',
            pay_len, payload,
            pay_len, payload,
            pay_len, payload,
        ]
        self.service._dns_handle_tcp_conn(('1.2.3.4', 42), mock_socket)

        self.assertEqual(11, mock_socket.recv.call_count)
        self.assertEqual(4, mock_socket.sendall.call_count)
        self.assertEqual(1, mock_socket.close.call_count)
