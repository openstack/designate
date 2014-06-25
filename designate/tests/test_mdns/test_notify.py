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
from mock import patch

from designate.tests.test_mdns import MdnsTestCase
from designate.mdns import notify


class MdnsNotifyTest(MdnsTestCase):
    def setUp(self):
        super(MdnsNotifyTest, self).setUp()

        # Ensure that notify options are set
        self.config(slave_nameserver_ips_and_ports=['127.0.0.1:65255'],
                    group='service:mdns')
        self.notify = notify.NotifyEndpoint()

    @patch.object(notify.NotifyEndpoint, '_send_notify_message')
    def test_notify_opcode(self, mock):
        context = self.get_context()
        self.notify.notify_zone_changed(context, 'example.com')
        self.assertTrue(mock.called)

    def test_get_notify_message(self):
        context = self.get_context()
        # DNS message with NOTIFY opcode
        ref_message = \
            "4d2824000001000000000000076578616d706c6503636f6d0000060001"
        msg = self.notify._get_notify_message(context, 'example.com')
        # The first 11 characters of the on wire message change on every run.
        msg_tail = binascii.b2a_hex(msg.to_wire())[11:]
        self.assertEqual(ref_message[11:], msg_tail)

    @patch.object(dns.query, 'udp', side_effect=dns.exception.Timeout())
    def test_send_notify_message_timeout(self, _):
        context = self.get_context()
        # DNS message with NOTIFY opcode
        notify_message = dns.message.from_wire(binascii.a2b_hex(
            "4d2824000001000000000000076578616d706c6503636f6d0000060001"))

        msg = self.notify._send_notify_message(
            context, 'example.com', notify_message, '127.0.0.1', 65255, 1)
        self.assertIsInstance(msg, dns.exception.Timeout)

    @patch.object(dns.query, 'udp', side_effect=dns.query.BadResponse)
    def test_send_notify_message_badresponse(self, _):
        context = self.get_context()
        # DNS message with NOTIFY opcode
        notify_message = dns.message.from_wire(binascii.a2b_hex(
            "4d2824000001000000000000076578616d706c6503636f6d0000060001"))

        msg = self.notify._send_notify_message(
            context, 'example.com', notify_message, '127.0.0.1', 65255, 1)
        self.assertIsInstance(msg, dns.query.BadResponse)
