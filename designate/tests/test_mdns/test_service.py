# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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
import socket

import dns
import dns.message
import mock

from designate.tests.test_mdns import MdnsTestCase


class MdnsServiceTest(MdnsTestCase):
    def setUp(self):
        super(MdnsServiceTest, self).setUp()

        # Use a random port for MDNS
        self.config(port=0, group='service:mdns')

        self.service = self.start_service('mdns')
        self.addr = ['0.0.0.0', 5556]

    def test_stop(self):
        # NOTE: Start is already done by the fixture in start_service()
        self.service.stop()

    @mock.patch.object(dns.message, 'make_query')
    def test_handle_empty_payload(self, query_mock):
        self.service._dns_handle(self.addr, ' '.encode('utf-8'))
        query_mock.assert_called_once_with('unknown', dns.rdatatype.A)

    @mock.patch.object(socket.socket, 'sendto', new_callable=mock.MagicMock)
    def test_handle_udp_payload(self, sendto_mock):
        # DNS packet with IQUERY opcode
        payload = "271209000001000000000000076578616d706c6503636f6d0000010001"

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
        expected_response = (b"271289050001000000000000076578616d706c6503636f6"
                             b"d0000010001")

        self.service._dns_handle(self.addr, binascii.a2b_hex(payload))
        sendto_mock.assert_called_once_with(
            binascii.a2b_hex(expected_response), self.addr)
