# Copyright (c) 2014 Rackspace Hosting
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import binascii

import dns
import dns.message
import dns.query
import dns.exception
import mock
from mock import patch

from designate.tests.test_mdns import MdnsTestCase
from designate.mdns import notify
from designate import objects


class MdnsNotifyTest(MdnsTestCase):

    test_domain = {
        'name': 'example.com.',
        'email': 'example@example.com',
        'serial': 100,
    }

    def setUp(self):
        super(MdnsNotifyTest, self).setUp()
        self.nameserver = objects.PoolNameserver.from_dict({
            'id': 'f278782a-07dc-4502-9177-b5d85c5f7c7e',
            'host': '127.0.0.1',
            'port': 65255
        })
        self.mock_tg = mock.Mock()
        self.notify = notify.NotifyEndpoint(self.mock_tg)

    def test_send_notify_message(self):
        # id 10001
        # opcode NOTIFY
        # rcode NOERROR
        # flags QR AA
        # ;QUESTION
        # example.com. IN SOA
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        expected_notify_response = ("2711a4000001000000000000076578616d706c650"
                                    "3636f6d0000060001")
        context = self.get_context()
        with patch.object(dns.query, 'udp', return_value=dns.message.from_wire(
                binascii.a2b_hex(expected_notify_response))):
            response, retry = self.notify.notify_zone_changed(
                context, objects.Domain.from_dict(self.test_domain),
                self.nameserver, 0, 0, 2, 0)
            self.assertEqual(response, dns.message.from_wire(
                binascii.a2b_hex(expected_notify_response)))
            self.assertEqual(retry, 1)

    def test_send_notify_message_non_auth(self):
        # id 10001
        # opcode NOTIFY
        # rcode NOTAUTH
        # flags QR
        # ;QUESTION
        # example.com. IN SOA
        # ;ANSWER
        # ;AUTHORITY
        # ;ADDITIONAL
        non_auth_notify_response = ("2711a4090001000000000000076578616d706c650"
                                    "3636f6d0000060001")
        context = self.get_context()
        with patch.object(dns.query, 'udp', return_value=dns.message.from_wire(
                binascii.a2b_hex(non_auth_notify_response))):
            response, retry = self.notify.notify_zone_changed(
                context, objects.Domain.from_dict(self.test_domain),
                self.nameserver, 0, 0, 2, 0)
            self.assertEqual(response, None)
            self.assertEqual(retry, 1)

    @patch.object(dns.query, 'udp', side_effect=dns.exception.Timeout)
    def test_send_notify_message_timeout(self, _):
        context = self.get_context()
        response, retry = self.notify.notify_zone_changed(
            context, objects.Domain.from_dict(self.test_domain),
            self.nameserver, 0, 0, 2, 0)
        self.assertEqual(response, None)
        self.assertEqual(retry, 2)

    @patch.object(dns.query, 'udp', side_effect=dns.query.BadResponse)
    def test_send_notify_message_bad_response(self, _):
        context = self.get_context()
        response, retry = self.notify.notify_zone_changed(
            context, objects.Domain.from_dict(self.test_domain),
            self.nameserver, 0, 0, 2, 0)
        self.assertEqual(response, None)
        self.assertEqual(retry, 1)

    def test_poll_for_serial_number(self):
        # id 10001
        # opcode QUERY
        # rcode NOERROR
        # flags QR AA
        # ;QUESTION
        # example.com. IN SOA
        # ;ANSWER
        # example.com. 3600 IN SOA example-ns.com. admin.example.com. 100 3600
        #  600 86400 3600
        # ;AUTHORITY
        # ;ADDITIONAL
        poll_response = ("271184000001000100000000076578616d706c6503636f6d0000"
                         "060001c00c0006000100000e1000290a6578616d706c652d6e73"
                         "c0140561646d696ec00c0000006400000e100000025800015180"
                         "00000e10")
        context = self.get_context()
        with patch.object(dns.query, 'udp', return_value=dns.message.from_wire(
                binascii.a2b_hex(poll_response))):
            status, serial, retries = self.notify.get_serial_number(
                context, objects.Domain.from_dict(self.test_domain),
                self.nameserver, 0, 0, 2, 0)
            self.assertEqual(status, 'SUCCESS')
            self.assertEqual(serial, self.test_domain['serial'])
            self.assertEqual(retries, 2)

    def test_poll_for_serial_number_lower_serial(self):
        # id 10001
        # opcode QUERY
        # rcode NOERROR
        # flags QR AA
        # ;QUESTION
        # example.com. IN SOA
        # ;ANSWER
        # example.com. 3600 IN SOA example-ns.com. admin.example.com. 99 3600
        #  600 86400 3600
        # ;AUTHORITY
        # ;ADDITIONAL
        poll_response = ("271184000001000100000000076578616d706c6503636f6d0000"
                         "060001c00c0006000100000e1000290a6578616d706c652d6e73"
                         "c0140561646d696ec00c0000006300000e100000025800015180"
                         "00000e10")
        context = self.get_context()
        with patch.object(dns.query, 'udp', return_value=dns.message.from_wire(
                binascii.a2b_hex(poll_response))):
            status, serial, retries = self.notify.get_serial_number(
                context, objects.Domain.from_dict(self.test_domain),
                self.nameserver, 0, 0, 2, 0)
            self.assertEqual(status, 'ERROR')
            self.assertEqual(serial, 99)
            self.assertEqual(retries, 0)

    def test_poll_for_serial_number_higher_serial(self):
        # id 10001
        # opcode QUERY
        # rcode NOERROR
        # flags QR AA
        # ;QUESTION
        # example.com. IN SOA
        # ;ANSWER
        # example.com. 3600 IN SOA example-ns.com. admin.example.com. 101 3600
        #  600 86400 3600
        # ;AUTHORITY
        # ;ADDITIONAL
        poll_response = ("271184000001000100000000076578616d706c6503636f6d0000"
                         "060001c00c0006000100000e1000290a6578616d706c652d6e73"
                         "c0140561646d696ec00c0000006500000e100000025800015180"
                         "00000e10")
        context = self.get_context()
        with patch.object(dns.query, 'udp', return_value=dns.message.from_wire(
                binascii.a2b_hex(poll_response))):
            status, serial, retries = self.notify.get_serial_number(
                context, objects.Domain.from_dict(self.test_domain),
                self.nameserver, 0, 0, 2, 0)
            self.assertEqual(status, 'SUCCESS')
            self.assertEqual(serial, 101)
            self.assertEqual(retries, 2)

    @patch.object(dns.query, 'udp', side_effect=dns.exception.Timeout)
    def test_poll_for_serial_number_timeout(self, _):
        context = self.get_context()
        status, serial, retries = self.notify.get_serial_number(
            context, objects.Domain.from_dict(self.test_domain),
            self.nameserver, 0, 0, 2, 0)
        self.assertEqual(status, 'ERROR')
        self.assertEqual(serial, None)
        self.assertEqual(retries, 0)

    @patch('dns.query.udp', side_effect=dns.exception.Timeout)
    @patch('dns.query.tcp', side_effect=dns.exception.Timeout)
    def test_send_dns_message_all_tcp(self, tcp, udp):
        self.config(
            all_tcp=True,
            group='service:mdns'
        )
        context = self.get_context()
        test_domain = objects.Domain.from_dict(self.test_domain)
        status, serial, retries = self.notify.get_serial_number(
            context, test_domain, self.nameserver, 0, 0, 2, 0)
        response, retry = self.notify.notify_zone_changed(
            context, test_domain, self.nameserver, 0, 0, 2, 0)
        assert not udp.called
        assert tcp.called
