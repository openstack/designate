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

import dns

from designate import context
from designate.tests.test_mdns import MdnsTestCase
from designate.mdns import handler


class MdnsRequestHandlerTest(MdnsTestCase):
    def setUp(self):
        super(MdnsRequestHandlerTest, self).setUp()
        self.handler = handler.RequestHandler()
        self.addr = ["0.0.0.0", 5556]
        self.context = context.DesignateContext.get_admin_context(
            all_tenants=True)

    def test_dispatch_opcode_iquery(self):
        # DNS packet with IQUERY opcode
        payload = "271109000001000000000000076578616d706c6503636f6d0000010001"

        # expected response is an error code REFUSED.  The other fields are
        # id 10001
        # opcode IQUERY
        # rcode REFUSED
        # flags QR RD
        # ;QUESTION
        # example.com. IN A
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = ("271189050001000000000000076578616d706c6503636f6d"
                             "0000010001")

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': self.addr, 'context': self.context}
        response = self.handler(request).to_wire()

        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_dispatch_opcode_status(self):
        # DNS packet with STATUS opcode
        payload = "271211000001000000000000076578616d706c6503636f6d0000010001"

        # expected response is an error code REFUSED.  The other fields are
        # id 10002
        # opcode STATUS
        # rcode REFUSED
        # flags QR RD
        # ;QUESTION
        # example.com. IN A
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = ("271291050001000000000000076578616d706c6503636f6d"
                             "0000010001")

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': self.addr, 'context': self.context}
        response = self.handler(request).to_wire()

        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_dispatch_opcode_notify(self):
        # DNS packet with NOTIFY opcode
        payload = "271321000001000000000000076578616d706c6503636f6d0000010001"

        # expected response is an error code REFUSED.  The other fields are
        # id 10003
        # opcode NOTIFY
        # rcode REFUSED
        # flags QR RD
        # ;QUESTION
        # example.com. IN A
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = ("2713a1050001000000000000076578616d706c6503636f6d"
                             "0000010001")

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': self.addr, 'context': self.context}
        response = self.handler(request).to_wire()

        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_dispatch_opcode_update(self):
        # DNS packet with UPDATE opcode
        payload = "271429000001000000000000076578616d706c6503636f6d0000010001"

        # expected response is an error code REFUSED.  The other fields are
        # id 10004
        # opcode UPDATE
        # rcode REFUSED
        # flags QR RD
        # ;ZONE
        # example.com. IN A
        # ;PREREQ
        # ;UPDATE
        # ;ADDITIONAL
        expected_response = ("2714a9050001000000000000076578616d706c6503636f6d"
                             "0000010001")

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': self.addr, 'context': self.context}
        response = self.handler(request).to_wire()

        self.assertEqual(expected_response, binascii.b2a_hex(response))

    # def test_dispatch_opcode_query_invalid(self):
    #     # invalid query
    #     payload = "1234"

    #     # expected_response is FORMERR.  The other fields are
    #     # id <varies>
    #     # opcode QUERY
    #     # rcode FORMERR
    #     # flags QR RD
    #     # ;QUESTION
    #     # ;ANSWER
    #     # ;AUTHORITY
    #     # ;ADDITIONAL
    #     expected_response = "1010000000000000000"

    #     request = dns.message.from_wire(binascii.a2b_hex(payload))
    #     request.environ = {'addr': self.addr, 'context': self.context}
    #     response = self.handler(request).to_wire()

    #     # strip the id from the response and compare
    #     self.assertEqual(expected_response, binascii.b2a_hex(response)[5:])

    def test_dispatch_opcode_query_non_existent_domain(self):
        # DNS packet with QUERY opcode
        # query is for example.com. IN A
        payload = ("271501200001000000000001076578616d706c6503636f6d0000010001"
                   "0000291000000000000000")

        # expected_response is an error code REFUSED.  The other fields are
        # id 10005
        # opcode QUERY
        # rcode REFUSED
        # flags QR RD
        # edns 0
        # payload 8192
        # ;QUESTION
        # example.com. IN A
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = ("271581050001000000000001076578616d706c6503636f6d"
                             "00000100010000292000000000000000")
        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': self.addr, 'context': self.context}
        response = self.handler(request).to_wire()

        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_dispatch_opcode_query_A(self):
        # query is for mail.example.com. IN A
        payload = ("271601000001000000000000046d61696c076578616d706c6503636f6d"
                   "0000010001")

        # expected_response is NOERROR.  The other fields are
        # id 10006
        # opcode QUERY
        # rcode NOERROR
        # flags QR AA RD
        # ;QUESTION
        # mail.example.com. IN A
        # ;ANSWER
        # mail.example.com. 3600 IN A 192.0.2.1
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = ("271685000001000100000000046d61696c076578616d706c"
                             "6503636f6d0000010001c00c0001000100000e100004c000"
                             "0201")

        # This creates an A record for mail.example.com
        domain = self.create_domain()
        recordset = self.create_recordset(domain, 'A')
        self.create_record(domain, recordset)

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': self.addr, 'context': self.context}
        response = self.handler(request).to_wire()

        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_dispatch_opcode_query_MX(self):
        # query is for mail.example.com. IN MX
        payload = ("271701000001000000000000046d61696c076578616d706c6503636f6d"
                   "00000f0001")

        # expected_response is NOERROR.  The other fields are
        # id 10007
        # opcode QUERY
        # rcode NOERROR
        # flags QR AA RD
        # ;QUESTION
        # mail.example.com. IN MX
        # ;ANSWER
        # mail.example.com. 3600 IN MX 5 mail.example.org.
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = ("271785000001000100000000046d61696c076578616d706c"
                             "6503636f6d00000f0001c00c000f000100000e1000140005"
                             "046d61696c076578616d706c65036f726700")

        # This creates an MX record for mail.example.com
        domain = self.create_domain()
        recordset = self.create_recordset(domain, 'MX')
        self.create_record(domain, recordset)

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': self.addr, 'context': self.context}
        response = self.handler(request).to_wire()

        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_dispatch_opcode_query_nonexistent_recordtype(self):
        # query is for mail.example.com. IN CNAME
        payload = ("271801000001000000000000046d61696c076578616d706c6503636f6d"
                   "0000050001")

        # expected_response is REFUSED.  The other fields are
        # id 10008
        # opcode QUERY
        # rcode REFUSED
        # flags QR RD
        # ;QUESTION
        # mail.example.com. IN CNAME
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = ("271881050001000000000000046d61696c076578616d706c"
                             "6503636f6d0000050001")

        # This creates an MX record for mail.example.com
        # But we query for a CNAME record
        domain = self.create_domain()
        recordset = self.create_recordset(domain, 'MX')
        self.create_record(domain, recordset)

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': self.addr, 'context': self.context}
        response = self.handler(request).to_wire()

        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_dispatch_opcode_query_unsupported_recordtype(self):
        # query is for example.com. IN DNAME
        payload = "271901000001000000000000076578616d706c6503636f6d0000270001"

        # expected_response is REFUSED.  The other fields are
        # id 10009
        # opcode QUERY
        # rcode REFUSED
        # flags QR RD
        # ;QUESTION
        # example.com. IN DNAME
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = ("271981050001000000000000076578616d706c6503636f6d"
                             "0000270001")

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': self.addr, 'context': self.context}
        response = self.handler(request).to_wire()

        self.assertEqual(expected_response, binascii.b2a_hex(response))
