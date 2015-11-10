# Copyright 2014 Rackspace Inc.
#
# Author: Tim Simmons <tim.simmons@rackspace.com>
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

import dns
import dns.resolver
import mock

import designate
from designate.agent import handler
from designate.tests.test_agent import AgentTestCase


class AgentRequestHandlerTest(AgentTestCase):
    def setUp(self):
        super(AgentRequestHandlerTest, self).setUp()
        self.config(allow_notify=["0.0.0.0"],
                    backend_driver="fake",
                    transfer_source="1.2.3.4",
                    group='service:agent')
        self.handler = handler.RequestHandler()
        self.addr = ["0.0.0.0", 5558]

    @mock.patch.object(dns.resolver.Resolver, 'query')
    @mock.patch('designate.dnsutils.do_axfr')
    def test_receive_notify(self, doaxfr, query):
        """
        Get a NOTIFY and ensure the response is right,
        and an AXFR is triggered
        """
        payload = ("1a7220000001000000000000076578616d706c6503636f6d000006"
                  "0001")
        # expected response is NOERROR, other fields are
        # opcode NOTIFY
        # rcode NOERROR
        # flags QR AA
        # ;QUESTION
        # example.com. IN SOA
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = (b"1a72a4000001000000000000076578616d706c6503"
                            b"636f6d0000060001")
        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': ["0.0.0.0", 1234]}
        response = next(self.handler(request)).to_wire()
        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_receive_notify_bad_notifier(self):
        """
        Get a NOTIFY from a bad master and refuse it
        """
        payload = "243520000001000000000000076578616d706c6503636f6d0000060001"
        # expected response is REFUSED, other fields are
        # opcode NOTIFY
        # rcode REFUSED
        # flags QR
        # ;QUESTION
        # example.com. IN SOA
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = (b"2435a0050001000000000000076578616d706c6503636f"
                            b"6d0000060001")
        request = dns.message.from_wire(binascii.a2b_hex(payload))
        # Bad 'requester'
        request.environ = {'addr': ["6.6.6.6", 1234]}
        response = next(self.handler(request)).to_wire()

        self.assertEqual(expected_response, binascii.b2a_hex(response))

    @mock.patch.object(dns.resolver.Resolver, 'query')
    @mock.patch('designate.dnsutils.do_axfr')
    def test_receive_create(self, doaxfr, query):
        """
        Get a CREATE and ensure the response is right,
        and an AXFR is triggered, and the proper backend
        call is made
        """
        payload = "735d70000001000000000000076578616d706c6503636f6d00ff02ff00"
        # Expected NOERROR other fields are
        # opcode 14
        # rcode NOERROR
        # flags QR AA
        # ;QUESTION
        # example.com. CLASS65280 TYPE65282
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = (b"735df4000001000000000000076578616d706c6503636f"
                             b"6d00ff02ff00")
        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': ["0.0.0.0", 1234]}
        with mock.patch.object(
            designate.backend.agent_backend.impl_fake.FakeBackend,
                'find_zone_serial', return_value=None):

            response = next(self.handler(request)).to_wire()
            self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_receive_create_bad_notifier(self):
        """
        Get a NOTIFY from a bad master and refuse it
        """
        payload = "8dfd70000001000000000000076578616d706c6503636f6d00ff02ff00"
        # expected response is REFUSED, other fields are
        # opcode 14
        # rcode REFUSED
        # flags QR
        # ;QUESTION
        # example.com. CLASS65280 TYPE65282
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = (b"8dfdf0050001000000000000076578616d706c6503636f"
                             b"6d00ff02ff00")
        request = dns.message.from_wire(binascii.a2b_hex(payload))
        # Bad 'requester'
        request.environ = {'addr': ["6.6.6.6", 1234]}
        response = next(self.handler(request)).to_wire()

        self.assertEqual(expected_response, binascii.b2a_hex(response))

    @mock.patch('designate.utils.execute')
    def test_receive_delete(self, func):
        """
        Get a DELETE and ensure the response is right,
        and that the proper backend call is made
        """
        payload = "3b9970000001000000000000076578616d706c6503636f6d00ff03ff00"
        # Expected NOERROR other fields are
        # opcode 14
        # rcode NOERROR
        # flags QR AA
        # ;QUESTION
        # example.com. CLASS65280 TYPE65283
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = (b"3b99f4000001000000000000076578616d706c6503636f"
                             b"6d00ff03ff00")
        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': ["0.0.0.0", 1234]}
        response = next(self.handler(request)).to_wire()

        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_receive_delete_bad_notifier(self):
        """
        Get a message with an unsupported OPCODE and make
        sure that it is refused
        """
        payload = "e6da70000001000000000000076578616d706c6503636f6d00ff03ff00"
        # expected response is REFUSED, other fields are
        # opcode 14
        # rcode REFUSED
        # flags QR
        # ;QUESTION
        # example.com. CLASS65280 TYPE65283
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = (b"e6daf0050001000000000000076578616d706c6503636f"
                             b"6d00ff03ff00")
        request = dns.message.from_wire(binascii.a2b_hex(payload))
        # Bad 'requester'
        request.environ = {'addr': ["6.6.6.6", 1234]}
        response = next(self.handler(request)).to_wire()

        self.assertEqual(expected_response, binascii.b2a_hex(response))

    @mock.patch.object(dns.resolver.Resolver, 'query')
    @mock.patch.object(designate.dnsutils, 'do_axfr')
    def test_transfer_source(self, doaxfr, query):
        """
        Get a CREATE and ensure the response is right,
        and an AXFR is triggered with the right source IP
        """
        payload = "735d70000001000000000000076578616d706c6503636f6d00ff02ff00"
        # Expected NOERROR other fields are
        # opcode 14
        # rcode NOERROR
        # flags QR AA
        # ;QUESTION
        # example.com. CLASS65280 TYPE65282
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = (b"735df4000001000000000000076578616d706c6503636f"
                             b"6d00ff02ff00")
        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': ["0.0.0.0", 1234]}
        with mock.patch.object(
            designate.backend.agent_backend.impl_fake.FakeBackend,
                'find_zone_serial', return_value=None):
            response = next(self.handler(request)).to_wire()
            doaxfr.assert_called_with('example.com.', [], source="1.2.3.4")
            self.assertEqual(expected_response, binascii.b2a_hex(response))
