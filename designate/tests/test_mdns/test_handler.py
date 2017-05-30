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

import dns
import dns.rdataclass
import dns.rdatatype
import dns.resolver
import dns.rrset
import mock
import testtools
from oslo_config import cfg

from designate import context
from designate import objects
from designate.tests.test_mdns import MdnsTestCase
from designate.mdns import handler

CONF = cfg.CONF
default_pool_id = CONF['service:central'].default_pool_id

ANSWER = [
    "id 1234",
    "opcode QUERY",
    "rcode NOERROR",
    "flags QR AA RD",
    ";QUESTION",
    "example.com. IN SOA",
    ";ANSWER",
    "example.com. 3600 IN SOA ns1.example.com. root.master.com. "
    "%(serial)s 3600 1800 604800 3600",
    ";AUTHORITY",
    "example.com. 3600 IN NS ns1.master.com.",
    ";ADDITIONAL"
]


class MdnsRequestHandlerTest(MdnsTestCase):
    def setUp(self):
        super(MdnsRequestHandlerTest, self).setUp()
        self.mock_tg = mock.Mock()
        self.handler = handler.RequestHandler(self.storage, self.mock_tg)
        self.addr = ["0.0.0.0", 5556]

        self.context = context.DesignateContext.get_admin_context(
            all_tenants=True)

        # Create a TSIG Key for the default pool, and another for some other
        # pool.
        self.tsigkey_pool_default = self.create_tsigkey(
            name='default-pool',
            scope='POOL',
            resource_id=default_pool_id)

        self.tsigkey_pool_unknown = self.create_tsigkey(
            name='unknown-pool',
            scope='POOL',
            resource_id='628e55a0-c724-4767-8c59-0a61c15d3444')

        self.tsigkey_zone_unknown = self.create_tsigkey(
            name='unknown-zone',
            scope='ZONE',
            resource_id='82fd08be-9eb7-4d94-8267-a26f8348671d')

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
        expected_response = (b"271189050001000000000000076578616d706c6503636f"
                             b"6d0000010001")

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': self.addr, 'context': self.context}
        response = next(self.handler(request)).to_wire()

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
        expected_response = (b"271291050001000000000000076578616d706c6503636f"
                             b"6d0000010001")

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': self.addr, 'context': self.context}
        response = next(self.handler(request)).to_wire()

        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def _get_secondary_zone(self, values=None, attributes=None,
                            masters=None):
        attributes = attributes or []
        masters = masters or [{"host": "10.0.0.1", "port": 53}]
        fixture = self.get_zone_fixture("SECONDARY", values=values)
        fixture['email'] = cfg.CONF['service:central'].managed_resource_email

        zone = objects.Zone(**fixture)
        zone.attributes = objects.ZoneAttributeList().from_list(attributes)
        zone.masters = objects.ZoneMasterList().from_list(masters)
        return zone

    def _get_soa_answer(self, serial):
        text = "\n".join(ANSWER) % {"serial": str(serial)}
        msg = dns.message.from_text(text)
        name = dns.name.from_text('example.com.')
        answer = dns.resolver.Answer(name, dns.rdatatype.SOA,
                                     dns.rdataclass.IN, msg)
        return answer

    @mock.patch.object(dns.resolver.Resolver, 'query')
    def test_dispatch_opcode_notify_different_serial(self, func):
        # DNS packet with NOTIFY opcode
        payload = "c38021000001000000000000076578616d706c6503636f6d0000060001"

        master = "10.0.0.1"
        zone = self._get_secondary_zone({"serial": 123})

        # expected response is an error code NOERROR.  The other fields are
        # id 50048
        # opcode NOTIFY
        # rcode NOERROR
        # flags QR AA RD
        # ;QUESTION
        # example.com. IN A
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = (b"c380a5000001000000000000076578616d706c6503636f"
                             b"6d0000060001")

        # The SOA serial should be different from the one in thezone and
        # will trigger a AXFR
        func.return_value = self._get_soa_answer(123123)

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {
            'addr': (master, 53),
            'context': self.context
        }

        with mock.patch.object(self.handler.storage, 'find_zone',
                               return_value=zone):
            response = next(self.handler(request)).to_wire()

        self.mock_tg.add_thread.assert_called_with(
            self.handler.zone_sync, self.context, zone,
            [zone.masters[0]])
        self.assertEqual(expected_response, binascii.b2a_hex(response))

    @mock.patch.object(dns.resolver.Resolver, 'query')
    def test_dispatch_opcode_notify_same_serial(self, func):
        # DNS packet with NOTIFY opcode
        payload = "c38021000001000000000000076578616d706c6503636f6d0000060001"

        master = "10.0.0.1"
        zone = self._get_secondary_zone({"serial": 123})

        # expected response is an error code NOERROR.  The other fields are
        # id 50048
        # opcode NOTIFY
        # rcode NOERROR
        # flags QR AA RD
        # ;QUESTION
        # example.com. IN SOA
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = (b"c380a5000001000000000000076578616d706c6503636f"
                             b"6d0000060001")

        # The SOA serial should be different from the one in thezone and
        # will trigger a AXFR
        func.return_value = self._get_soa_answer(zone.serial)

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {
            'addr': (master, 53),
            'context': self.context
        }

        with mock.patch.object(self.handler.storage, 'find_zone',
                               return_value=zone):
            response = next(self.handler(request)).to_wire()

        assert not self.mock_tg.add_thread.called
        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_dispatch_opcode_notify_invalid_master(self):
        # DNS packet with NOTIFY opcode
        payload = "c38021000001000000000000076578616d706c6503636f6d0000060001"

        # Have a zone with different master then the one where the notify
        # comes from causing it to be "ignored" as in not transferred and
        # logged

        zone = self._get_secondary_zone({"serial": 123})

        # expected response is an error code REFUSED.  The other fields are
        # id 50048
        # opcode NOTIFY
        # rcode REFUSED
        # flags QR AA RD
        # ;QUESTION
        # example.com. IN SOA
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = (b"c380a1050001000000000000076578616d706c6503636f"
                             b"6d0000060001")

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {
            'addr': ("10.0.0.2", 53),
            'context': self.context
        }

        with mock.patch.object(self.handler.storage, 'find_zone',
                               return_value=zone):
            response = next(self.handler(request)).to_wire()

        assert not self.mock_tg.add_thread.called
        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_dispatch_opcode_notify_no_question_formerr(self):
        # DNS packet with NOTIFY opcode and no question
        payload = "f16320000000000000000000"

        # expected response is an error code FORMERR.  The other fields are
        # id 61795
        # opcode NOTIFY
        # rcode FORMERR
        # flags QR RD
        # ;QUESTION
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = (b"f163a0010000000000000000")

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {
            'addr': ("10.0.0.2", 53),
            'context': self.context
        }

        response = next(self.handler(request)).to_wire()

        assert not self.mock_tg.add_thread.called
        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_dispatch_opcode_notify_invalid_zone(self):
        # DNS packet with NOTIFY opcode
        payload = "c38021000001000000000000076578616d706c6503636f6d0000060001"

        # expected response is an error code NOTAUTH.  The other fields are
        # id 50048
        # opcode NOTIFY
        # rcode NOTAUTH
        # flags QR RD
        # ;QUESTION
        # example.com. IN SOA
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = (b"c380a1090001000000000000076578616d706c6503636f"
                             b"6d0000060001")

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {
            'addr': ("10.0.0.2", 53),
            'context': self.context
        }

        response = next(self.handler(request)).to_wire()

        assert not self.mock_tg.add_thread.called
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
        expected_response = (b"2714a9050001000000000000076578616d706c6503636f"
                             b"6d0000010001")

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': self.addr, 'context': self.context}
        response = next(self.handler(request)).to_wire()

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
    #     response = self.handler(request).next().to_wire()

    #     # strip the id from the response and compare
    #     self.assertEqual(expected_response, binascii.b2a_hex(response)[5:])

    def test_dispatch_opcode_query_non_existent_zone(self):
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
        expected_response = (b"271581050001000000000001076578616d706c6503636f"
                             b"6d00000100010000292000000000000000")
        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': self.addr, 'context': self.context}
        response = next(self.handler(request)).to_wire()

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
        expected_response = (b"271685000001000100000000046d61696c076578616d70"
                             b"6c6503636f6d0000010001c00c0001000100000e100004"
                             b"c0000201")

        # This creates an A record for mail.example.com
        zone = self.create_zone()
        recordset = self.create_recordset(zone, 'A')
        self.create_record(zone, recordset)

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': self.addr, 'context': self.context}
        response = next(self.handler(request)).to_wire()

        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_dispatch_opcode_query_TXT(self):
        # query is for text.example.com. IN TXT
        payload = "d2f5012000010000000000010474657874076578616d706c6503636f6d00001000010000291000000000000000"  # noqa

        # expected_response is NOERROR.  The other fields are
        # id 54005
        # opcode QUERY
        # rcode NOERROR
        # flags QR AA RD
        # edns 0
        # payload 8192
        # ;QUESTION
        # text.example.com. IN TXT
        # ;ANSWER
        # text.example.com. 3600 IN TXT "footxtdata"
        # ;AUTHORITY
        # ;ADDITIONAL

        expected_response = b"d2f5850000010001000000010474657874076578616d706c6503636f6d0000100001c00c0010000100000e10000b0a666f6f747874646174610000292000000000000000"  # noqa

        # This creates an TXT record for mail.example.com
        zone = self.create_zone()
        recordset = self.create_recordset(zone, 'TXT')
        self.create_record(zone, recordset)

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': self.addr, 'context': self.context}
        response = next(self.handler(request)).to_wire()
        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_dispatch_opcode_query_TXT_quoted_strings(self):
        # query is for text.example.com. IN TXT
        payload = "d2f5012000010000000000010474657874076578616d706c6503636f6d00001000010000291000000000000000"  # noqa

        expected_response = b"d2f5850000010001000000010474657874076578616d706c6503636f6d0000100001c00c0010000100000e10000d03666f6f0362617204626c61680000292000000000000000"  # noqa
        # expected_response is NOERROR.  The other fields are
        # response: id 54005
        # opcode QUERY
        # rcode NOERROR
        # flags QR AA RD
        # edns 0
        # payload 8192
        # ;QUESTION
        # text.example.com. IN TXT
        # ;ANSWER
        # text.example.com. 3600 IN TXT "foo" "bar" "blah"
        # ;AUTHORITY
        # ;ADDITIONAL

        zone = self.create_zone()
        recordset = self.create_recordset(zone, type='TXT')
        values = {'data': '"foo" "bar" "blah"'}
        self.storage.create_record(
            self.admin_context, zone['id'], recordset['id'],
            objects.Record.from_dict(values))

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': self.addr, 'context': self.context}
        response = next(self.handler(request)).to_wire()
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
        expected_response = (b"271785000001000100000000046d61696c076578616d70"
                             b"6c6503636f6d00000f0001c00c000f000100000e100014"
                             b"0005046d61696c076578616d706c65036f726700")

        # This creates an MX record for mail.example.com
        zone = self.create_zone()
        recordset = self.create_recordset(zone, 'MX')
        self.create_record(zone, recordset)

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': self.addr, 'context': self.context}
        response = next(self.handler(request)).to_wire()

        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_dispatch_opcode_query_AXFR(self):
        # Query is for example.com. IN AXFR
        # id 18883
        # opcode QUERY
        # rcode NOERROR
        # flags AD
        # edns 0
        # payload 4096
        # ;QUESTION
        # example.com. IN AXFR
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        payload = ("49c300200001000000000001076578616d706c6503636f6d0000fc0001"
                   "0000291000000000000000")

        # id 18883
        # opcode QUERY
        # rcode NOERROR
        # flags QR AA
        # ;QUESTION
        # example.com. IN AXFR
        # ;ANSWER
        # example.com. 3600 IN SOA ns1.example.org. example.example.com.
        # -> 1427899961 3600 600 86400 3600
        # mail.example.com. 3600 IN A 192.0.2.1
        # example.com. 3600 IN NS ns1.example.org.
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = \
            (b"49c384000001000400000000076578616d706c6503636f6d0000fc0001c0"
             b"0c0006000100000e10002f036e7331076578616d706c65036f7267000765786"
             b"16d706c65c00c551c063900000e10000002580001518000000e10c00c000200"
             b"0100000e100002c029046d61696cc00c0001000100000e100004c0000201c00"
             b"c0006000100000e100018c029c03a551c063900000e10000002580001518000"
             b"000e10")

        zone = objects.Zone.from_dict({
            'name': 'example.com.',
            'ttl': 3600,
            'serial': 1427899961,
            'email': 'example@example.com',
        })

        def _find_recordsets_axfr(context, criterion):
            if criterion['type'] == 'SOA':
                return [['UUID1', 'SOA', '3600', 'example.com.',
                         'ns1.example.org. example.example.com. 1427899961 '
                         '3600 600 86400 3600', 'ACTION']]

            elif criterion['type'] == '!SOA':
                return [
                    ['UUID2', 'NS', '3600', 'example.com.', 'ns1.example.org.',
                     'ACTION'],
                    ['UUID3', 'A', '3600', 'mail.example.com.', '192.0.2.1',
                     'ACTION'],
                ]

        with mock.patch.object(self.storage, 'find_zone',
                               return_value=zone):
            with mock.patch.object(self.storage, 'find_recordsets_axfr',
                                   side_effect=_find_recordsets_axfr):
                request = dns.message.from_wire(binascii.a2b_hex(payload))
                request.environ = {'addr': self.addr, 'context': self.context}

                response = next(self.handler(request)).get_wire()

                self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_dispatch_opcode_query_AXFR_multiple_messages(self):
        # Query is for example.com. IN AXFR
        # id 18883
        # opcode QUERY
        # rcode NOERROR
        # flags AD
        # edns 0
        # payload 4096
        # ;QUESTION
        # example.com. IN AXFR
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        payload = ("49c300200001000000000001076578616d706c6503636f6d0000fc0001"
                   "0000291000000000000000")

        expected_response = [
            (b"49c384000001000300000000076578616d706c6503636f6d0000fc0001c00c"
             b"0006000100000e10002f036e7331076578616d706c65036f726700076578616"
             b"d706c65c00c551c063900000e10000002580001518000000e10c00c0002000"
             b"100000e100002c029046d61696cc00c0001000100000e100004c0000201"),

            (b"49c384000001000100000000076578616d706c6503636f6d0000fc0001c00c"
             b"0006000100000e10002f036e7331076578616d706c65036f72670007657861"
             b"6d706c65c00c551c063900000e10000002580001518000000e10"),
        ]

        # Set the max-message-size to 128
        self.config(max_message_size=128, group='service:mdns')

        zone = objects.Zone.from_dict({
            'name': 'example.com.',
            'ttl': 3600,
            'serial': 1427899961,
            'email': 'example@example.com',
        })

        def _find_recordsets_axfr(context, criterion):
            if criterion['type'] == 'SOA':
                return [['UUID1', 'SOA', '3600', 'example.com.',
                         'ns1.example.org. example.example.com. 1427899961 '
                         '3600 600 86400 3600', 'ACTION']]

            elif criterion['type'] == '!SOA':
                return [
                    ['UUID2', 'NS', '3600', 'example.com.', 'ns1.example.org.',
                     'ACTION'],
                    ['UUID3', 'A', '3600', 'mail.example.com.', '192.0.2.1',
                     'ACTION'],
                ]

        with mock.patch.object(self.storage, 'find_zone',
                               return_value=zone):
            with mock.patch.object(self.storage, 'find_recordsets_axfr',
                                   side_effect=_find_recordsets_axfr):
                request = dns.message.from_wire(binascii.a2b_hex(payload))
                request.environ = {'addr': self.addr, 'context': self.context}

                response_generator = self.handler(request)

                # Validate the first response
                response_one = next(response_generator).get_wire()
                self.assertEqual(
                    expected_response[0], binascii.b2a_hex(response_one))

                # Validate the second response
                response_two = next(response_generator).get_wire()
                self.assertEqual(
                    expected_response[1], binascii.b2a_hex(response_two))

    def test_dispatch_opcode_query_AXFR_rrset_over_max_size(self):
        # Query is for example.com. IN AXFR
        # id 18883
        # opcode QUERY
        # rcode NOERROR
        # flags AD
        # edns 0
        # payload 4096
        # ;QUESTION
        # example.com. IN AXFR
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        payload = ("49c300200001000000000001076578616d706c6503636f6d0000fc0001"
                   "0000291000000000000000")

        expected_response = [
            # Initial SOA
            (b"49c384000001000100000000076578616d706c6503636f6d0000fc0001c00c0"
             b"006000100000e10002f036e7331076578616d706c65036f726700076578616d"
             b"706c65c00c551c063900000e10000002580001518000000e10"),

            # First NS record
            (b"49c384000001000100000000076578616d706c6503636f6d0000fc0001c00c0"
             b"002000100000e1000413f616161616161616161616161616161616161616161"
             b"616161616161616161616161616161616161616161616161616161616161616"
             b"16161616161616161616100"),

            # Second NS Record and SOA trailer
            (b"49c384000001000200000000076578616d706c6503636f6d0000fc0001c00c0"
             b"002000100000e10000c0a6262626262626262626200c00c0006000100000e10"
             b"002f036e7331076578616d706c65036f726700076578616d706c65c00c551c0"
             b"63900000e10000002580001518000000e10"),
        ]

        # Set the max-message-size to 128
        self.config(max_message_size=128, group='service:mdns')

        zone = objects.Zone.from_dict({
            'name': 'example.com.',
            'ttl': 3600,
            'serial': 1427899961,
            'email': 'example@example.com',
        })

        def _find_recordsets_axfr(context, criterion):
            if criterion['type'] == 'SOA':
                return [['UUID1', 'SOA', '3600', 'example.com.',
                         'ns1.example.org. example.example.com. 1427899961 '
                         '3600 600 86400 3600', 'ACTION']]

            elif criterion['type'] == '!SOA':
                return [
                    ['UUID2', 'NS', '3600', 'example.com.', 'a' * 63 + '.',
                     'ACTION'],
                    ['UUID2', 'NS', '3600', 'example.com.', 'b' * 10 + '.',
                     'ACTION'],
                ]

        with mock.patch.object(self.storage, 'find_zone',
                               return_value=zone):
            with mock.patch.object(self.storage, 'find_recordsets_axfr',
                                   side_effect=_find_recordsets_axfr):
                request = dns.message.from_wire(binascii.a2b_hex(payload))
                request.environ = {'addr': self.addr, 'context': self.context}

                response_generator = self.handler(request)

                # Validate the first response
                response_one = next(response_generator).get_wire()
                self.assertEqual(
                    expected_response[0], binascii.b2a_hex(response_one))

                # Validate the second response
                response_two = next(response_generator).get_wire()
                self.assertEqual(
                    expected_response[1], binascii.b2a_hex(response_two))

                # Validate the third response
                response_three = next(response_generator).get_wire()
                self.assertEqual(
                    expected_response[2], binascii.b2a_hex(response_three))

                # Ensure a StopIteration is raised after the final response.
                with testtools.ExpectedException(StopIteration):
                    next(response_generator)

    def test_dispatch_opcode_query_AXFR_rr_over_max_size(self):
        # Query is for example.com. IN AXFR
        # id 18883
        # opcode QUERY
        # rcode NOERROR
        # flags AD
        # edns 0
        # payload 4096
        # ;QUESTION
        # example.com. IN AXFR
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        payload = ("49c300200001000000000001076578616d706c6503636f6d0000fc0001"
                   "0000291000000000000000")

        expected_response = [
            # Initial SOA
            (b"49c384000001000100000000076578616d706c6503636f6d0000fc0001c00c0"
             b"006000100000e10002f036e7331076578616d706c65036f726700076578616d"
             b"706c65c00c551c063900000e10000002580001518000000e10"),

            # SRVFAIL
            (""),
        ]

        # Set the max-message-size to 128
        self.config(max_message_size=128, group='service:mdns')

        zone = objects.Zone.from_dict({
            'name': 'example.com.',
            'ttl': 3600,
            'serial': 1427899961,
            'email': 'example@example.com',
        })

        def _find_recordsets_axfr(context, criterion):
            if criterion['type'] == 'SOA':
                return [['UUID1', 'SOA', '3600', 'example.com.',
                         'ns1.example.org. example.example.com. 1427899961 '
                         '3600 600 86400 3600', 'ACTION']]

            elif criterion['type'] == '!SOA':
                return [
                    ['UUID2', 'NS', '3600', 'example.com.',
                    'a' * 63 + '.' + 'a' * 63 + '.', 'ACTION'],
                ]

        with mock.patch.object(self.storage, 'find_zone',
                               return_value=zone):
            with mock.patch.object(self.storage, 'find_recordsets_axfr',
                                   side_effect=_find_recordsets_axfr):
                request = dns.message.from_wire(binascii.a2b_hex(payload))
                request.environ = {'addr': self.addr, 'context': self.context}

                response_generator = self.handler(request)

                # Validate the first response
                response_one = next(response_generator).get_wire()
                self.assertEqual(
                    expected_response[0], binascii.b2a_hex(response_one))

                # Validate the second response is a SERVFAIL
                response_two = next(response_generator)
                self.assertEqual(
                    dns.rcode.SERVFAIL, response_two.rcode())

                # Ensure a StopIteration is raised after the final response.
                with testtools.ExpectedException(StopIteration):
                    next(response_generator)

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
        expected_response = (b"271881050001000000000000046d61696c076578616d70"
                             b"6c6503636f6d0000050001")

        # This creates an MX record for mail.example.com
        # But we query for a CNAME record
        zone = self.create_zone()
        recordset = self.create_recordset(zone, 'MX')
        self.create_record(zone, recordset)

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': self.addr, 'context': self.context}
        response = next(self.handler(request)).to_wire()

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
        expected_response = (b"271981050001000000000000076578616d706c6503636f"
                             b"6d0000270001")

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': self.addr, 'context': self.context}
        response = next(self.handler(request)).to_wire()

        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_dispatch_opcode_query_tsig_scope_pool(self):
        # Create a zone/recordset/record to query
        zone = self.create_zone(name='example.com.')
        recordset = self.create_recordset(
            zone, name='example.com.', type='A')
        self.create_record(
            zone, recordset, data='192.0.2.5')

        # DNS packet with QUERY opcode for A example.com.
        payload = ("c28901200001000000000001076578616d706c6503636f6d0000010001"
                   "0000291000000000000000")

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {
            'addr': self.addr,
            'context': self.context,
            'tsigkey': self.tsigkey_pool_default,
        }

        # Ensure the Query, with the correct pool's TSIG, gives a NOERROR.
        # id 49801
        # opcode QUERY
        # rcode NOERROR
        # flags QR AA RD
        # edns 0
        # payload 8192
        # ;QUESTION
        # example.com. IN A
        # ;ANSWER
        # example.com. 3600 IN A 192.0.2.5
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = (b"c28985000001000100000001076578616d706c6503636f"
                             b"6d0000010001c00c0001000100000e100004c000020500"
                             b"00292000000000000000")

        response = next(self.handler(request)).to_wire()

        self.assertEqual(expected_response, binascii.b2a_hex(response))

        # Ensure the Query, with the incorrect pool's TSIG, gives a REFUSED
        request.environ['tsigkey'] = self.tsigkey_pool_unknown

        # id 49801
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
        expected_response = (b"c28981050001000000000001076578616d706c6503636f"
                             b"6d00000100010000292000000000000000")

        response = next(self.handler(request)).to_wire()
        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_dispatch_opcode_query_tsig_scope_zone(self):
        # Create a zone/recordset/record to query
        zone = self.create_zone(name='example.com.')
        recordset = self.create_recordset(
            zone, name='example.com.', type='A')
        self.create_record(
            zone, recordset, data='192.0.2.5')

        # Create a TSIG Key Matching the zone
        tsigkey_zone_known = self.create_tsigkey(
            name='known-zone',
            scope='ZONE',
            resource_id=zone.id)

        # DNS packet with QUERY opcode for A example.com.
        payload = ("c28901200001000000000001076578616d706c6503636f6d0000010001"
                   "0000291000000000000000")

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {
            'addr': self.addr,
            'context': self.context,
            'tsigkey': tsigkey_zone_known,
        }

        # Ensure the Query, with the correct zone's TSIG, gives a NOERROR.
        # id 49801
        # opcode QUERY
        # rcode NOERROR
        # flags QR AA RD
        # edns 0
        # payload 8192
        # ;QUESTION
        # example.com. IN A
        # ;ANSWER
        # example.com. 3600 IN A 192.0.2.5
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_response = (b"c28985000001000100000001076578616d706c6503636f"
                             b"6d0000010001c00c0001000100000e100004c000020500"
                             b"00292000000000000000")

        response = next(self.handler(request)).to_wire()

        self.assertEqual(expected_response, binascii.b2a_hex(response))

        # Ensure the Query, with the incorrect zone's TSIG, gives a REFUSED
        request.environ['tsigkey'] = self.tsigkey_zone_unknown

        # id 49801
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
        expected_response = (b"c28981050001000000000001076578616d706c6503636f"
                             b"6d00000100010000292000000000000000")

        response = next(self.handler(request)).to_wire()
        self.assertEqual(expected_response, binascii.b2a_hex(response))
