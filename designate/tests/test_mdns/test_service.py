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
import socket

import dns
import dns.message
import mock
from oslo_log import log as logging

from designate.tests.test_mdns import MdnsTestCase

LOG = logging.getLogger(__name__)


def hex_wire(response):
    return binascii.b2a_hex(response.to_wire())


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

        sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.service._dns_handle(self.addr, binascii.a2b_hex(payload),
                                 sock_udp=sock_udp)
        sendto_mock.assert_called_once_with(
            binascii.a2b_hex(expected_response), self.addr)

    def _send_request_to_mdns(self, req):
        """Send request to localhost"""
        self.assertTrue(len(self.service._dns_socks_udp))
        port = self.service._dns_socks_udp[0].getsockname()[1]
        response = dns.query.udp(req, '127.0.0.1', port=port, timeout=1)
        LOG.info("\n-- RESPONSE --\n%s\n--------------\n" % response.to_text())
        return response

    def _query_mdns(self, qname, rdtype, rdclass=dns.rdataclass.IN):
        """Send query to localhost"""
        req = dns.message.make_query(qname, rdtype, rdclass=rdclass)
        req.id = 123
        return self._send_request_to_mdns(req)

    def test_query(self):
        zone = self.create_zone()

        # Reply query for NS
        response = self._query_mdns(zone.name, dns.rdatatype.NS)
        self.assertEqual(dns.rcode.NOERROR, response.rcode())
        self.assertEqual(1, len(response.answer))
        ans = response.answer[0]
        self.assertEqual(dns.rdatatype.NS, ans.rdtype)
        self.assertEqual(zone.name, ans.name.to_text())
        self.assertEqual(zone.ttl, ans.ttl)

        # Reply query for SOA
        response = self._query_mdns(zone.name, dns.rdatatype.SOA)
        self.assertEqual(dns.rcode.NOERROR, response.rcode())
        self.assertEqual(1, len(response.answer))
        ans = response.answer[0]
        self.assertEqual(dns.rdatatype.SOA, ans.rdtype)
        self.assertEqual(zone.name, ans.name.to_text())
        self.assertEqual(zone.ttl, ans.ttl)

        # Refuse query for incorrect rdclass
        response = self._query_mdns(zone.name, dns.rdatatype.SOA,
                                    rdclass=dns.rdataclass.RESERVED0)
        self.assertEqual(dns.rcode.REFUSED, response.rcode())
        expected = b'007b81050001000000000000076578616d706c6503636f6d0000060000'  # noqa
        self.assertEqual(expected, hex_wire(response))

        # Refuse query for ANY
        response = self._query_mdns("www.%s" % zone.name, dns.rdatatype.ANY)
        self.assertEqual(dns.rcode.REFUSED, response.rcode())
        expected = b'007b8105000100000000000003777777076578616d706c6503636f6d0000ff0001'  # noqa
        self.assertEqual(expected, hex_wire(response))

        # Reply query for A against inexistent record
        response = self._query_mdns("nope.%s" % zone.name, dns.rdatatype.A)
        self.assertEqual(dns.rcode.REFUSED, response.rcode())
        expected = b'007b81050001000000000000046e6f7065076578616d706c6503636f6d0000010001'  # noqa
        self.assertEqual(expected, hex_wire(response))

        # Reply query for A
        recordset = self.create_recordset(zone)
        self.create_record(zone, recordset)
        response = self._query_mdns(recordset.name, dns.rdatatype.A)
        self.assertEqual(dns.rcode.NOERROR, response.rcode())
        self.assertEqual(1, len(response.answer))
        ans = response.answer[0]
        self.assertEqual(dns.rdatatype.A, ans.rdtype)
        self.assertEqual(recordset.name, ans.name.to_text())
        self.assertEqual(zone.ttl, ans.ttl)
        self.assertEqual('3600 IN A 192.0.2.1', str(ans.to_rdataset()))
        expected = b'007b85000001000100000000046d61696c076578616d706c6503636f6d0000010001c00c0001000100000e100004c0000201'  # noqa
        self.assertEqual(expected, hex_wire(response))

    def test_query_axfr(self):
        zone = self.create_zone()

        # Query for AXFR
        response = self._query_mdns(zone.name, dns.rdatatype.AXFR)
        self.assertEqual(dns.rcode.NOERROR, response.rcode())
        self.assertEqual(2, len(response.answer))
        ans = response.answer[0]  # SOA
        self.assertEqual(dns.rdatatype.SOA, ans.rdtype)
        self.assertEqual(zone.name, ans.name.to_text())
        self.assertEqual(zone.ttl, ans.ttl)
        ans = response.answer[1]  # NS
        self.assertEqual(dns.rdatatype.NS, ans.rdtype)
        self.assertEqual(zone.name, ans.name.to_text())
        self.assertEqual(zone.ttl, ans.ttl)

    def test_notify_notauth_primary_zone(self):
        zone = self.create_zone()

        # Send NOTIFY to mdns: NOTAUTH for primary zone
        notify = dns.message.make_query(zone.name, dns.rdatatype.SOA)
        notify.id = 123
        notify.flags = 0
        notify.set_opcode(dns.opcode.NOTIFY)
        notify.flags |= dns.flags.AA
        response = self._send_request_to_mdns(notify)
        self.assertEqual(dns.rcode.NOTAUTH, response.rcode())
        expected = b'007ba0090001000000000000076578616d706c6503636f6d0000060001'  # noqa
        self.assertEqual(expected, hex_wire(response))

    def test_notify_non_master(self):
        zone = self.create_zone(type='SECONDARY', email='test@example.com')

        # Send NOTIFY to mdns: refuse from non-master
        notify = dns.message.make_query(zone.name, dns.rdatatype.SOA)
        notify.id = 123
        notify.flags = 0
        notify.set_opcode(dns.opcode.NOTIFY)
        notify.flags |= dns.flags.AA
        response = self._send_request_to_mdns(notify)
        self.assertEqual(dns.rcode.REFUSED, response.rcode())
        expected = b'007ba0050001000000000000076578616d706c6503636f6d0000060001'  # noqa
        self.assertEqual(expected, hex_wire(response))
