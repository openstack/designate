# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hpe.com>
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
import socket
from unittest import mock

import dns
import dns.exception
import dns.message
import dns.name
import dns.rcode
import dns.rdatatype
import dns.zone
import eventlet
from oslo_config import fixture as cfg_fixture
import oslotest.base

import designate.conf
from designate import dnsutils
from designate import exceptions


CONF = designate.conf.CONF


class TestDNSUtils(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

    def test_dnspyrecords_to_recordsetlist(self):
        node = dns.node.Node()
        node.rdatasets.append(
            dns.rdataset.from_text('in', 'a', 0, '192.0.2.1')
        )
        dnspython_records = {
            dns.name.Name(labels=[b'ipv4', b'example', b'org', b'']): node
        }
        recorset = dnsutils.dnspyrecords_to_recordsetlist(dnspython_records)
        self.assertEqual(1, len(recorset))
        self.assertEqual('ipv4.example.org.', recorset[0].name)
        self.assertIsNone(recorset[0].ttl)

    @mock.patch('socket.getaddrinfo')
    def test_get_ip_address(self, mock_getaddrinfo):
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 0, '', ('192.0.2.1', 0))
        ]
        self.assertEqual('192.0.2.1', dnsutils.get_ip_address('test'))

    @mock.patch('socket.getaddrinfo')
    def test_get_ip_address_none(self, mock_getaddrinfo):
        mock_getaddrinfo.return_value = []
        self.assertIsNone(dnsutils.get_ip_address('test'))

    @mock.patch.object(dns.query, 'udp')
    def test_send_udp_dns_message(self, mock_udp):
        CONF.set_override('all_tcp', False, 'service:worker')
        dnsutils.send_dns_message('msg', '192.0.2.1', 1234, 1)
        mock_udp.assert_called_with(
            'msg', '192.0.2.1', port=1234, timeout=1
        )

    @mock.patch.object(dns.query, 'tcp')
    def test_send_tcp_dns_message(self, mock_tcp):
        CONF.set_override('all_tcp', True, 'service:worker')
        dnsutils.send_dns_message('msg', '192.0.2.1', 1234, 1)
        mock_tcp.assert_called_with(
            'msg', '192.0.2.1', port=1234, timeout=1
        )

    def test_all_tcp_default(self):
        self.assertEqual(False, dnsutils.use_all_tcp())

    def test_all_tcp_using_worker(self):
        CONF.set_override('all_tcp', True, 'service:worker')
        self.assertEqual(True, dnsutils.use_all_tcp())

    def test_xfr_default(self):
        self.assertEqual(10, dnsutils.xfr_timeout())

    def test_xfr_timeout_set_using_worker(self):
        CONF.set_override('xfr_timeout', 40, 'service:worker')
        self.assertEqual(40, dnsutils.xfr_timeout())


class TestDoAfxr(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

    @mock.patch.object(dns.query, 'xfr')
    @mock.patch.object(dns.zone, 'from_xfr')
    def test_do_afxr(self, mock_from_xfr_impl, mock_xfr):
        mock_from_xfr = mock.MagicMock()
        mock_from_xfr_impl.return_value = mock_from_xfr

        mock_from_xfr.origin.to_text.return_value = 'raw_zone'
        mock_from_xfr.return_value = 'raw_zone'

        masters = [
            {'host': '192.0.2.1', 'port': 53},
            {'host': '192.0.2.2', 'port': 53},
        ]

        self.assertEqual(
            mock_from_xfr,
            dnsutils.do_axfr('example.com', masters)
        )

        self.assertTrue(mock_xfr.called)
        self.assertTrue(mock_from_xfr_impl.called)

    def test_do_afxr_no_masters(self):
        masters = [
        ]

        self.assertRaisesRegex(
            exceptions.XFRFailure,
            r'XFR failed for example.com. No servers in \[\] was reached.',
            dnsutils.do_axfr, 'example.com', masters,
        )

    @mock.patch.object(dns.query, 'xfr')
    @mock.patch.object(dns.zone, 'from_xfr')
    @mock.patch.object(eventlet.Timeout, 'cancel')
    def test_do_afxr_fails_with_timeout(self, mock_cancel, mock_from_xfr,
                                        mock_xfr):
        mock_from_xfr.side_effect = eventlet.Timeout()

        masters = [
            {'host': '192.0.2.1', 'port': 53},
            {'host': '192.0.2.2', 'port': 53},
            {'host': '192.0.2.3', 'port': 53},
            {'host': '192.0.2.4', 'port': 53},
        ]

        self.assertRaises(
            exceptions.XFRFailure,
            dnsutils.do_axfr, 'example.com.', masters,
        )

        self.assertTrue(mock_xfr.called)
        self.assertTrue(mock_from_xfr.called)
        self.assertTrue(mock_cancel.called)

    @mock.patch.object(dns.query, 'xfr')
    @mock.patch.object(dns.zone, 'from_xfr')
    def test_do_afxr_fails_with_form_error(self, mock_from_xfr, mock_xfr):
        mock_from_xfr.side_effect = dns.exception.FormError()

        masters = [
            {'host': '192.0.2.1', 'port': 53},
        ]

        self.assertRaises(
            exceptions.XFRFailure,
            dnsutils.do_axfr, 'example.com.', masters,
        )

        self.assertTrue(mock_xfr.called)
        self.assertTrue(mock_from_xfr.called)

    @mock.patch.object(dns.query, 'xfr')
    @mock.patch.object(dns.zone, 'from_xfr')
    def test_do_afxr_fails_with_socket_error(self, mock_from_xfr, mock_xfr):
        mock_from_xfr.side_effect = socket.error()

        masters = [
            {'host': '192.0.2.1', 'port': 53},
        ]

        self.assertRaises(
            exceptions.XFRFailure,
            dnsutils.do_axfr, 'example.com.', masters,
        )

        self.assertTrue(mock_xfr.called)
        self.assertTrue(mock_from_xfr.called)

    @mock.patch.object(dns.query, 'xfr')
    @mock.patch.object(dns.zone, 'from_xfr')
    def test_do_afxr_fails_with_exception(self, mock_from_xfr, mock_xfr):
        mock_from_xfr.side_effect = Exception()

        masters = [
            {'host': '192.0.2.1', 'port': 53},
        ]

        self.assertRaises(
            exceptions.XFRFailure,
            dnsutils.do_axfr, 'example.com.', masters,
        )

        self.assertTrue(mock_xfr.called)
        self.assertTrue(mock_from_xfr.called)


class TestDNSMessages(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

    @mock.patch.object(dnsutils, 'send_dns_message')
    def test_notify(self, mock_send_dns_message):
        dnsutils.notify('notify.test.', '203.0.113.1', port=54)

        mock_send_dns_message.assert_called_with(
            mock.ANY, '203.0.113.1', port=54, timeout=10
        )

        query = mock_send_dns_message.call_args[0][0]
        txt = query.to_text().split('\n')[1:]
        self.assertEqual([
            'opcode NOTIFY',
            'rcode NOERROR',
            'flags RD',
            ';QUESTION',
            'notify.test. IN SOA',
            ';ANSWER',
            ';AUTHORITY',
            ';ADDITIONAL'
        ], txt)

    @mock.patch.object(dnsutils, 'send_dns_message')
    def test_soa(self, mock_send_dns_message):
        dnsutils.soa_query('soa.test.', '203.0.113.1', port=54)

        mock_send_dns_message.assert_called_with(
            mock.ANY, '203.0.113.1', port=54, timeout=10
        )

        query = mock_send_dns_message.call_args[0][0]
        txt = query.to_text().split('\n')[1:]
        self.assertEqual([
            'opcode QUERY',
            'rcode NOERROR',
            'flags RD',
            ';QUESTION',
            'soa.test. IN SOA',
            ';ANSWER',
            ';AUTHORITY',
            ';ADDITIONAL'
        ], txt)

    @mock.patch.object(dnsutils, 'send_dns_message')
    def test_get_serial(self, mock_send_dns_message):
        mock_rdataset = mock.Mock(serial=5)
        mock_answer = mock.Mock()
        mock_answer.to_rdataset.return_value = [mock_rdataset]

        mock_result = mock.Mock()
        mock_result.answer = [mock_answer]
        mock_send_dns_message.return_value = mock_result

        self.assertEqual(
            5, dnsutils.get_serial('serial.test.', '203.0.113.1', port=54)
        )

        query = mock_send_dns_message.call_args[0][0]
        txt = query.to_text().split('\n')[1:]
        self.assertEqual([
            'opcode QUERY',
            'rcode NOERROR',
            'flags RD',
            ';QUESTION',
            'serial.test. IN SOA',
            ';ANSWER',
            ';AUTHORITY',
            ';ADDITIONAL'
        ], txt)

    @mock.patch.object(dnsutils, 'send_dns_message')
    def test_get_serial_no_answer(self, mock_send_dns_message):
        mock_result = mock.Mock()
        mock_result.answer = []
        mock_send_dns_message.return_value = mock_result

        self.assertFalse(
            dnsutils.get_serial('serial.test.', '203.0.113.1', port=54)
        )

    @mock.patch.object(dnsutils, 'send_dns_message')
    def test_get_serial_no_rdataset(self, mock_send_dns_message):
        mock_answer = mock.Mock()
        mock_answer.to_rdataset.return_value = []

        mock_result = mock.Mock()
        mock_result.answer = [mock_answer]
        mock_send_dns_message.return_value = mock_result

        self.assertFalse(
            dnsutils.get_serial('serial.test.', '203.0.113.1', port=54)
        )
