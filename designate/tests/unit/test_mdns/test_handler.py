# Copyright 2014 Rackspace Inc.
#
# Author: Eric Larson <eric.larson@rackspace.com>
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

import unittest

from mock import Mock
from oslo_log import log as logging
import dns

from designate import exceptions
from designate import objects
from designate.mdns import handler

LOG = logging.getLogger(__name__)


class TestRequestHandlerCall(unittest.TestCase):
    """
    Unit test to assert the dispatching based on the request
    operation.
    """

    def setUp(self):
        self.storage = Mock()
        self.tg = Mock()
        self.handler = handler.RequestHandler(self.storage, self.tg)

        # Use a simple handlers that doesn't require a real request
        self.handler._handle_query_error = Mock(return_value='Error')
        self.handler._handle_axfr = Mock(return_value=['AXFR'])
        self.handler._handle_record_query = Mock(return_value=['Record Query'])
        self.handler._handle_notify = Mock(return_value=['Notify'])

    def assert_error(self, request, error_type):
        self.handler._handle_query_error.assert_called_with(
            request, error_type
        )

    def test_central_api_property(self):
        self.handler._central_api = 'foo'
        assert self.handler.central_api == 'foo'

    def test___call___unhandled_opcodes(self):
        unhandled_codes = [
            dns.opcode.STATUS,
            dns.opcode.IQUERY,
            dns.opcode.UPDATE,
        ]

        request = Mock()
        for code in unhandled_codes:
            request.opcode.return_value = code  # return an error
            assert list(self.handler(request)) == ['Error']
            self.assert_error(request, dns.rcode.REFUSED)

    def test___call__query_error_with_more_than_one_question(self):
        request = Mock()
        request.opcode.return_value = dns.opcode.QUERY
        request.question = [Mock(), Mock()]

        assert list(self.handler(request)) == ['Error']
        self.assert_error(request, dns.rcode.REFUSED)

    def test___call__query_error_with_data_claas_not_in(self):
        request = Mock()
        request.opcode.return_value = dns.opcode.QUERY
        request.question = [Mock(rdclass=dns.rdataclass.ANY)]
        assert list(self.handler(request)) == ['Error']
        self.assert_error(request, dns.rcode.REFUSED)

    def test___call__axfr(self):
        request = Mock()
        request.opcode.return_value = dns.opcode.QUERY
        request.question = [
            Mock(rdclass=dns.rdataclass.IN, rdtype=dns.rdatatype.AXFR)
        ]
        assert list(self.handler(request)) == ['AXFR']

    def test___call__ixfr(self):
        request = Mock()
        request.opcode.return_value = dns.opcode.QUERY
        request.question = [
            Mock(rdclass=dns.rdataclass.IN, rdtype=dns.rdatatype.IXFR)
        ]
        assert list(self.handler(request)) == ['AXFR']

    def test___call__record_query(self):
        request = Mock()
        request.opcode.return_value = dns.opcode.QUERY
        request.question = [
            Mock(rdclass=dns.rdataclass.IN, rdtype=dns.rdatatype.A)
        ]
        assert list(self.handler(request)) == ['Record Query']

    def test___call__notify(self):
        request = Mock()
        request.opcode.return_value = dns.opcode.NOTIFY
        assert list(self.handler(request)) == ['Notify']

    def test__convert_to_rrset_no_records(self):
        zone = objects.Zone.from_dict({'ttl': 1234})
        recordset = objects.RecordSet(
            name='www.example.org.',
            type='A',
            records=objects.RecordList(objects=[
            ])
        )

        r_rrset = self.handler._convert_to_rrset(zone, recordset)
        self.assertIsNone(r_rrset)

    def test__convert_to_rrset(self):
        zone = objects.Zone.from_dict({'ttl': 1234})
        recordset = objects.RecordSet(
            name='www.example.org.',
            type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.1'),
                objects.Record(data='192.0.2.2'),
            ])
        )

        r_rrset = self.handler._convert_to_rrset(zone, recordset)
        self.assertEqual(2, len(r_rrset))


class HandleRecordQueryTest(unittest.TestCase):

    def setUp(self):
        self.storage = Mock()
        self.tg = Mock()
        self.handler = handler.RequestHandler(self.storage, self.tg)

    def test__handle_record_query_empty_recordlist(self):
        # bug #1550441
        self.storage.find_recordset.return_value = objects.RecordSet(
            name='www.example.org.',
            type='A',
            records=objects.RecordList(objects=[
            ])
        )
        request = dns.message.make_query('www.example.org.', dns.rdatatype.A)
        request.environ = dict(context='ctx')
        response_gen = self.handler._handle_record_query(request)
        for r in response_gen:
            # This was raising an exception due to bug #1550441
            out = r.to_wire(max_size=65535)
            self.assertEqual(33, len(out))

    def test__handle_record_query_zone_not_found(self):
        self.storage.find_recordset.return_value = objects.RecordSet(
            name='www.example.org.',
            type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.2'),
            ])
        )
        self.storage.find_zone.side_effect = exceptions.ZoneNotFound
        request = dns.message.make_query('www.example.org.', dns.rdatatype.A)
        request.environ = dict(context='ctx')
        response = tuple(self.handler._handle_record_query(request))
        self.assertEqual(1, len(response))
        self.assertEqual(dns.rcode.REFUSED, response[0].rcode())

    def test__handle_record_query_forbidden(self):
        self.storage.find_recordset.return_value = objects.RecordSet(
            name='www.example.org.',
            type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.2'),
            ])
        )
        self.storage.find_zone.side_effect = exceptions.Forbidden
        request = dns.message.make_query('www.example.org.', dns.rdatatype.A)
        request.environ = dict(context='ctx')
        response = tuple(self.handler._handle_record_query(request))
        self.assertEqual(1, len(response))
        self.assertEqual(dns.rcode.REFUSED, response[0].rcode())

    def test__handle_record_query_find_recordsed_forbidden(self):
        self.storage.find_recordset.side_effect = exceptions.Forbidden
        request = dns.message.make_query('www.example.org.', dns.rdatatype.A)
        request.environ = dict(context='ctx')
        response = tuple(self.handler._handle_record_query(request))
        self.assertEqual(1, len(response))
        self.assertEqual(dns.rcode.REFUSED, response[0].rcode())

    def test__handle_record_query_find_recordsed_not_found(self):
        self.storage.find_recordset.side_effect = exceptions.NotFound
        request = dns.message.make_query('www.example.org.', dns.rdatatype.A)
        request.environ = dict(context='ctx')
        response = tuple(self.handler._handle_record_query(request))
        self.assertEqual(1, len(response))
        self.assertEqual(dns.rcode.REFUSED, response[0].rcode())
