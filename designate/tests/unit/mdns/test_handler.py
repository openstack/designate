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


from unittest import mock

import dns
from oslo_config import fixture as cfg_fixture
import oslotest.base

import designate.conf
from designate import exceptions
from designate.mdns import handler
from designate import objects
from designate import rpc
from designate.tests import base_fixtures
from designate.worker import rpcapi as worker_rpcapi


CONF = designate.conf.CONF


class MdnsHandleTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(self.stdlog)
        self.useFixture(cfg_fixture.Config(CONF))

        self.context = mock.Mock()
        self.storage = mock.Mock()
        self.tg = mock.Mock()

        self.handler = handler.RequestHandler(self.storage, self.tg)

    @mock.patch.object(rpc, 'get_client', mock.Mock())
    def test_worker_api(self):
        self.assertIsNone(self.handler._worker_api)
        self.assertIsInstance(self.handler.worker_api,
                              worker_rpcapi.WorkerAPI)
        self.assertIsNotNone(self.handler._worker_api)
        self.assertIsInstance(self.handler.worker_api,
                              worker_rpcapi.WorkerAPI)

    @mock.patch.object(dns.resolver.BaseResolver, "read_registry", mock.Mock())
    @mock.patch.object(dns.resolver.BaseResolver, "read_resolv_conf",
                       mock.Mock())
    @mock.patch.object(rpc, 'get_client', mock.Mock())
    @mock.patch.object(dns.resolver.Resolver, 'resolve')
    def test_notify(self, mock_query):
        self.storage.find_zone.return_value = objects.Zone(
            id='e2bed4dc-9d01-11e4-89d3-123b93f75cba',
            serial=2,
            masters=objects.ZoneMasterList.from_list([
                {'host': '192.0.2.1', 'port': 53},
            ])
        )
        mock_query.return_value = [
            mock.Mock(serial=1)
        ]

        request = dns.message.make_query(
            'www.example.org.', dns.rdatatype.SOA
        )
        request.environ = dict(addr=['192.0.2.1'], context=self.context)

        response = self.handler._handle_notify(request)

        self.assertEqual(dns.rcode.NOERROR, tuple(response)[0].rcode())

        self.assertIn(
            'Scheduling AXFR for e2bed4dc-9d01-11e4-89d3-123b93f75cba '
            'from 192.0.2.1:53',
            self.stdlog.logger.output
        )

    @mock.patch.object(dns.resolver.BaseResolver, "read_registry", mock.Mock())
    @mock.patch.object(dns.resolver.BaseResolver, "read_resolv_conf",
                       mock.Mock())
    @mock.patch.object(dns.resolver.Resolver, 'resolve')
    def test_notify_same_serial(self, mock_query):
        self.storage.find_zone.return_value = objects.Zone(
            id='e2bed4dc-9d01-11e4-89d3-123b93f75cba',
            serial=1,
            masters=objects.ZoneMasterList.from_list([
                {'host': '192.0.2.1', 'port': 53},
            ])
        )
        mock_query.return_value = [
            mock.Mock(serial=1)
        ]

        request = dns.message.make_query(
            'www.example.org.', dns.rdatatype.SOA
        )
        request.environ = dict(addr=['192.0.2.1'], context=self.context)

        response = self.handler._handle_notify(request)

        self.assertEqual(dns.rcode.NOERROR, tuple(response)[0].rcode())

        self.assertIn(
            'Serial 1 is the same for master and us for '
            'e2bed4dc-9d01-11e4-89d3-123b93f75cba',
            self.stdlog.logger.output
        )

    def test_notify_no_questions(self):
        request = dns.message.make_query(
            'www.example.org.', dns.rdatatype.SOA
        )
        request.environ = dict(context=self.context)
        request.question = []

        response = self.handler._handle_notify(request)

        self.assertEqual(dns.rcode.FORMERR, tuple(response)[0].rcode())

    def test_notify_zone_not_found(self):
        self.storage.find_zone.side_effect = exceptions.ZoneNotFound

        request = dns.message.make_query(
            'www.example.org.', dns.rdatatype.SOA
        )
        request.environ = dict(context=self.context)

        response = self.handler._handle_notify(request)

        self.assertEqual(dns.rcode.NOTAUTH, tuple(response)[0].rcode())

    def test_notify_no_master_addr(self):
        self.storage.find_zone.return_value = objects.Zone(
            masters=objects.ZoneMasterList.from_list([
                {'host': '192.0.2.1', 'port': 53},
            ])
        )

        request = dns.message.make_query(
            'www.example.org.', dns.rdatatype.SOA
        )
        request.environ = dict(addr=['203.0.113.1', 53], context=self.context)

        response = self.handler._handle_notify(request)

        self.assertEqual(dns.rcode.REFUSED, tuple(response)[0].rcode())

        self.assertIn(
            'NOTIFY for None from non-master server 203.0.113.1, refusing.',
            self.stdlog.logger.output
        )

    def test_axfr_zone_not_found(self):
        self.storage.find_zone.side_effect = exceptions.ZoneNotFound

        request = dns.message.make_query(
            'www.example.org.', dns.rdatatype.AXFR
        )
        request.environ = dict(context=self.context)

        response = tuple(self.handler._handle_axfr(request))

        self.assertEqual(dns.rcode.REFUSED, response[0].rcode())

        self.assertIn(
            'ZoneNotFound while handling axfr request. '
            'Question was www.example.org. IN AXFR',
            self.stdlog.logger.output
        )

    def test_axfr_forbidden(self):
        self.storage.find_zone.side_effect = exceptions.Forbidden

        request = dns.message.make_query(
            'www.example.org.', dns.rdatatype.AXFR
        )
        request.environ = dict(context=self.context)

        response = tuple(self.handler._handle_axfr(request))

        self.assertEqual(dns.rcode.REFUSED, response[0].rcode())

        self.assertIn(
            'Forbidden while handling axfr request. '
            'Question was www.example.org. IN AXFR',
            self.stdlog.logger.output
        )

    def test_get_max_message_size(self):
        CONF.set_override('max_message_size', 32768, 'service:mdns')

        self.assertEqual(
            32768, self.handler._get_max_message_size(had_tsig=False)
        )

    def test_get_max_message_size_larger_than_allowed(self):
        CONF.set_override('max_message_size', 65535 * 2, 'service:mdns')

        self.assertEqual(
            65535, self.handler._get_max_message_size(had_tsig=False)
        )

        self.assertIn(
            'MDNS max message size must not be greater than 65535',
            self.stdlog.logger.output
        )

    def test_get_max_message_with_tsig(self):
        CONF.set_override('max_message_size', 65535, 'service:mdns')

        self.assertEqual(
            65300, self.handler._get_max_message_size(had_tsig=True)
        )

    def test_zone_criterion_from_request_unknown_scope(self):
        mock_tsigkey = mock.Mock()
        mock_tsigkey.scope = 'UNKNOWN'

        request = dns.message.make_query(
            'www.example.org.', dns.rdatatype.AXFR
        )
        request.environ = dict(context=self.context, tsigkey=mock_tsigkey)

        self.assertRaisesRegex(
            NotImplementedError,
            'Support for UNKNOWN scoped TSIG Keys is not implemented',
            self.handler._zone_criterion_from_request, request
        )

    def test_zone_criterion_from_request_enforce_tsig(self):
        CONF.set_override('query_enforce_tsig', True, 'service:mdns')

        request = dns.message.make_query(
            'www.example.org.', dns.rdatatype.AXFR
        )
        request.environ = dict(context=self.context, tsigkey=None)

        self.assertRaisesRegex(
            exceptions.Forbidden,
            'Request is not TSIG signed',
            self.handler._zone_criterion_from_request, request
        )


class TestRequestHandlerCall(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.handler = handler.RequestHandler(mock.Mock(), mock.Mock())

        # Use a simple handlers that doesn't require a real request
        self.handler._handle_query_error = mock.Mock(return_value='Error')
        self.handler._handle_axfr = mock.Mock(return_value=['AXFR'])
        self.handler._handle_record_query = mock.Mock(
            return_value=['Record Query'])
        self.handler._handle_notify = mock.Mock(return_value=['Notify'])

    def test__call___unhandled_opcodes(self):
        unhandled_codes = [
            dns.opcode.STATUS,
            dns.opcode.IQUERY,
            dns.opcode.UPDATE,
        ]

        request = mock.Mock()
        for code in unhandled_codes:
            request.opcode.return_value = code  # return an error

            self.assertEqual(['Error'], list(self.handler(request)))
            self.handler._handle_query_error.assert_called_with(
                request, dns.rcode.REFUSED
            )

    def test__call__query_error_with_more_than_one_question(self):
        request = mock.Mock()
        request.opcode.return_value = dns.opcode.QUERY
        request.question = [mock.Mock(), mock.Mock()]

        self.assertEqual(['Error'], list(self.handler(request)))
        self.handler._handle_query_error.assert_called_with(
            request, dns.rcode.REFUSED
        )

    def test__call__query_error_with_data_claas_not_in(self):
        request = mock.Mock()
        request.opcode.return_value = dns.opcode.QUERY
        request.question = [mock.Mock(rdclass=dns.rdataclass.ANY)]

        self.assertEqual(['Error'], list(self.handler(request)))
        self.handler._handle_query_error.assert_called_with(
            request, dns.rcode.REFUSED
        )

    def test__call__axfr(self):
        request = mock.Mock()
        request.opcode.return_value = dns.opcode.QUERY
        request.question = [
            mock.Mock(rdclass=dns.rdataclass.IN, rdtype=dns.rdatatype.AXFR)
        ]

        self.assertEqual(['AXFR'], list(self.handler(request)))

    def test__call__ixfr(self):
        request = mock.Mock()
        request.opcode.return_value = dns.opcode.QUERY
        request.question = [
            mock.Mock(rdclass=dns.rdataclass.IN, rdtype=dns.rdatatype.IXFR)
        ]

        self.assertEqual(['AXFR'], list(self.handler(request)))

    def test__call__record_query(self):
        request = mock.Mock()
        request.opcode.return_value = dns.opcode.QUERY
        request.question = [
            mock.Mock(rdclass=dns.rdataclass.IN, rdtype=dns.rdatatype.A)
        ]

        self.assertEqual(['Record Query'], list(self.handler(request)))

    def test__call__notify(self):
        request = mock.Mock()
        request.opcode.return_value = dns.opcode.NOTIFY

        self.assertEqual(['Notify'], list(self.handler(request)))

    def test_convert_to_rrset_no_records(self):
        zone = objects.Zone.from_dict({'ttl': 1234})
        recordset = objects.RecordSet(
            name='www.example.org.',
            type='A',
            records=objects.RecordList(objects=[
            ])
        )

        r_rrset = self.handler._convert_to_rrset(zone, recordset)

        self.assertIsNone(r_rrset)

    def test_convert_to_rrset(self):
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


class HandleRecordQueryTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.context = mock.Mock()
        self.storage = mock.Mock()
        self.handler = handler.RequestHandler(self.storage, mock.Mock())

    def test_handle_record_query_empty_recordlist(self):
        # bug #1550441
        self.storage.find_recordset.return_value = objects.RecordSet(
            name='www.example.org.',
            type='A',
            records=objects.RecordList(objects=[
            ])
        )

        request = dns.message.make_query('www.example.org.', dns.rdatatype.A)
        request.environ = dict(context=self.context)
        response_gen = self.handler._handle_record_query(request)
        for response in response_gen:
            # This was raising an exception due to bug #1550441
            out = response.to_wire(max_size=65535)

            self.assertEqual(33, len(out))

    def test_handle_record_query_zone_not_found(self):
        self.storage.find_recordset.return_value = objects.RecordSet(
            name='www.example.org.',
            type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.2'),
            ])
        )
        self.storage.find_zone.side_effect = exceptions.ZoneNotFound

        request = dns.message.make_query('www.example.org.', dns.rdatatype.A)
        request.environ = dict(context=self.context)
        response = tuple(self.handler._handle_record_query(request))

        self.assertEqual(1, len(response))
        self.assertEqual(dns.rcode.REFUSED, response[0].rcode())

    def test_handle_record_query_forbidden(self):
        self.storage.find_recordset.return_value = objects.RecordSet(
            name='www.example.org.',
            type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.2'),
            ])
        )
        self.storage.find_zone.side_effect = exceptions.Forbidden

        request = dns.message.make_query('www.example.org.', dns.rdatatype.A)
        request.environ = dict(context=self.context)
        response = tuple(self.handler._handle_record_query(request))

        self.assertEqual(1, len(response))
        self.assertEqual(dns.rcode.REFUSED, response[0].rcode())

    def test_handle_record_query_find_recordsed_forbidden(self):
        self.storage.find_recordset.side_effect = exceptions.Forbidden

        request = dns.message.make_query('www.example.org.', dns.rdatatype.A)
        request.environ = dict(context=self.context)
        response = tuple(self.handler._handle_record_query(request))

        self.assertEqual(1, len(response))
        self.assertEqual(dns.rcode.REFUSED, response[0].rcode())

    def test_handle_record_query_find_recordsed_not_found(self):
        self.storage.find_recordset.side_effect = exceptions.NotFound

        request = dns.message.make_query('www.example.org.', dns.rdatatype.A)
        request.environ = dict(context=self.context)
        response = tuple(self.handler._handle_record_query(request))

        self.assertEqual(1, len(response))
        self.assertEqual(dns.rcode.REFUSED, response[0].rcode())
