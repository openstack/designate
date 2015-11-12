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

import dns
from mock import Mock

from designate.mdns import handler


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
        return True

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
