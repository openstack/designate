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
import dns.rdataclass
import dns.rdatatype
import dns.resolver
import dns.rrset
import mock
from oslo.config import cfg

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
        expected_response = ("271189050001000000000000076578616d706c6503636f6d"
                             "0000010001")

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': self.addr, 'context': self.context}
        response = self.handler(request).next().to_wire()

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
        response = self.handler(request).next().to_wire()

        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def _get_secondary_domain(self, values=None, attributes=None):
        attributes = attributes or []
        fixture = self.get_domain_fixture("SECONDARY", values=values)
        fixture['email'] = cfg.CONF['service:central'].managed_resource_email

        domain = objects.Domain(**fixture)
        domain.attributes = objects.DomainAttributeList()
        return domain

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
        domain = self._get_secondary_domain({"serial": 123})
        domain.attributes.append(objects.DomainAttribute(
            **{"key": "master", "value": master}))

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
        expected_response = ("c380a5000001000000000000076578616d706c6503636f6d"
                             "0000060001")

        # The SOA serial should be different from the one in thedomain and
        # will trigger a AXFR
        func.return_value = self._get_soa_answer(123123)

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {
            'addr': (master, 53),
            'context': self.context
        }

        with mock.patch.object(self.handler.storage, 'find_domain',
                               return_value=domain):
            response = self.handler(request).next().to_wire()

        self.mock_tg.add_thread.assert_called_with(
            self.handler.domain_sync, self.context, domain, [master])
        self.assertEqual(expected_response, binascii.b2a_hex(response))

    @mock.patch.object(dns.resolver.Resolver, 'query')
    def test_dispatch_opcode_notify_same_serial(self, func):
        # DNS packet with NOTIFY opcode
        payload = "c38021000001000000000000076578616d706c6503636f6d0000060001"

        master = "10.0.0.1"
        domain = self._get_secondary_domain({"serial": 123})
        domain.attributes.append(objects.DomainAttribute(
            **{"key": "master", "value": master}))

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
        expected_response = ("c380a5000001000000000000076578616d706c6503636f6d"
                             "0000060001")

        # The SOA serial should be different from the one in thedomain and
        # will trigger a AXFR
        func.return_value = self._get_soa_answer(domain.serial)

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {
            'addr': (master, 53),
            'context': self.context
        }

        with mock.patch.object(self.handler.storage, 'find_domain',
                               return_value=domain):
            response = self.handler(request).next().to_wire()

        assert not self.mock_tg.add_thread.called
        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_dispatch_opcode_notify_invalid_master(self):
        # DNS packet with NOTIFY opcode
        payload = "c38021000001000000000000076578616d706c6503636f6d0000060001"

        # Have a domain with different master then the one where the notify
        # comes from causing it to be "ignored" as in not transferred and
        # logged
        master = "10.0.0.1"
        domain = self._get_secondary_domain({"serial": 123})
        domain.attributes.append(objects.DomainAttribute(
            **{"key": "master", "value": master}))

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
        expected_response = ("c380a1050001000000000000076578616d706c6503636f6d"
                             "0000060001")

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {
            'addr': ("10.0.0.2", 53),
            'context': self.context
        }

        with mock.patch.object(self.handler.storage, 'find_domain',
                               return_value=domain):
            response = self.handler(request).next().to_wire()

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
        expected_response = ("f163a0010000000000000000")

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {
            'addr': ("10.0.0.2", 53),
            'context': self.context
        }

        response = self.handler(request).next().to_wire()

        assert not self.mock_tg.add_thread.called
        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_dispatch_opcode_notify_invalid_domain(self):
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
        expected_response = ("c380a1090001000000000000076578616d706c6503636f6"
                             "d0000060001")

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {
            'addr': ("10.0.0.2", 53),
            'context': self.context
        }

        response = self.handler(request).next().to_wire()

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
        expected_response = ("2714a9050001000000000000076578616d706c6503636f6d"
                             "0000010001")

        request = dns.message.from_wire(binascii.a2b_hex(payload))
        request.environ = {'addr': self.addr, 'context': self.context}
        response = self.handler(request).next().to_wire()

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
        response = self.handler(request).next().to_wire()

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
        response = self.handler(request).next().to_wire()

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
        response = self.handler(request).next().to_wire()

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
            ("49c384000001000400000000076578616d706c6503636f6d0000fc0001c00c00"
             "06000100000e10002f036e7331076578616d706c65036f726700076578616d70"
             "6c65c00c551c063900000e10000002580001518000000e10c00c000200010000"
             "0e100002c029046d61696cc00c0001000100000e100004c0000201c00c000600"
             "0100000e100018c029c03a551c063900000e10000002580001518000000e10")

        domain = objects.Domain.from_dict({
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

        with mock.patch.object(self.storage, 'find_domain',
                               return_value=domain):
            with mock.patch.object(self.storage, 'find_recordsets_axfr',
                                   side_effect=_find_recordsets_axfr):
                request = dns.message.from_wire(binascii.a2b_hex(payload))
                request.environ = {'addr': self.addr, 'context': self.context}

                response = self.handler(request).next().get_wire()

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
            ("49c384000001000300000000076578616d706c6503636f6d0000fc0001c00c00"
             "06000100000e10002f036e7331076578616d706c65036f726700076578616d70"
             "6c65c00c551c063900000e10000002580001518000000e10c00c000200010000"
             "0e100002c029046d61696cc00c0001000100000e100004c0000201"),

            ("49c384000001000100000000076578616d706c6503636f6d0000fc0001c00c00"
             "06000100000e10002f036e7331076578616d706c65036f726700076578616d70"
             "6c65c00c551c063900000e10000002580001518000000e10"),
        ]

        # Set the max-message-size to 128
        self.config(max_message_size=128, group='service:mdns')

        domain = objects.Domain.from_dict({
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

        with mock.patch.object(self.storage, 'find_domain',
                               return_value=domain):
            with mock.patch.object(self.storage, 'find_recordsets_axfr',
                                   side_effect=_find_recordsets_axfr):
                request = dns.message.from_wire(binascii.a2b_hex(payload))
                request.environ = {'addr': self.addr, 'context': self.context}

                response_generator = self.handler(request)

                # Validate the first response
                response_one = response_generator.next().get_wire()
                self.assertEqual(
                    expected_response[0], binascii.b2a_hex(response_one))

                # Validate the second response
                response_two = response_generator.next().get_wire()
                self.assertEqual(
                    expected_response[1], binascii.b2a_hex(response_two))

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
        response = self.handler(request).next().to_wire()

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
        response = self.handler(request).next().to_wire()

        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_dispatch_opcode_query_tsig_scope_pool(self):
        # Create a domain/recordset/record to query
        domain = self.create_domain(name='example.com.')
        recordset = self.create_recordset(
            domain, name='example.com.', type='A')
        self.create_record(
            domain, recordset, data='192.0.2.5')

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
        expected_response = ("c28985000001000100000001076578616d706c6503636f6d"
                             "0000010001c00c0001000100000e100004c0000205000029"
                             "2000000000000000")

        response = self.handler(request).next().to_wire()

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
        expected_response = ("c28981050001000000000001076578616d706c6503636f6d"
                             "00000100010000292000000000000000")

        response = self.handler(request).next().to_wire()
        self.assertEqual(expected_response, binascii.b2a_hex(response))

    def test_dispatch_opcode_query_tsig_scope_zone(self):
        # Create a domain/recordset/record to query
        domain = self.create_domain(name='example.com.')
        recordset = self.create_recordset(
            domain, name='example.com.', type='A')
        self.create_record(
            domain, recordset, data='192.0.2.5')

        # Create a TSIG Key Matching the zone
        tsigkey_zone_known = self.create_tsigkey(
            name='known-zone',
            scope='ZONE',
            resource_id=domain.id)

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
        expected_response = ("c28985000001000100000001076578616d706c6503636f6d"
                             "0000010001c00c0001000100000e100004c0000205000029"
                             "2000000000000000")

        response = self.handler(request).next().to_wire()

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
        expected_response = ("c28981050001000000000001076578616d706c6503636f6d"
                             "00000100010000292000000000000000")

        response = self.handler(request).next().to_wire()
        self.assertEqual(expected_response, binascii.b2a_hex(response))
