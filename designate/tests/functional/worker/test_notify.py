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
from unittest import mock
from unittest.mock import patch

import dns
import dns.exception
import dns.message
import dns.query

from designate import objects
import designate.tests.functional
from designate.worker.tasks import zone


class WorkerNotifyTest(designate.tests.functional.TestCase):
    test_zone = {
        'name': 'example.com.',
        'email': 'example@example.com',
        'serial': 100,
    }

    def setUp(self):
        super().setUp()
        self.nameserver = objects.PoolNameserver.from_dict({
            'id': 'f278782a-07dc-4502-9177-b5d85c5f7c7e',
            'host': '192.0.2.1',
            'port': 65255
        })
        self.mock_tg = mock.Mock()

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
        with patch.object(dns.query, 'udp', return_value=dns.message.from_wire(
                binascii.a2b_hex(poll_response))):
            get_zone_serial = zone.GetZoneSerial(
                self.mock_tg, 'context',
                objects.Zone.from_dict(self.test_zone),
                self.nameserver.host, self.nameserver.port,
            )
            result = get_zone_serial()
            self.assertEqual(result[0], 'SUCCESS')
            self.assertEqual(result[1], self.test_zone['serial'])

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
        with patch.object(dns.query, 'udp', return_value=dns.message.from_wire(
                binascii.a2b_hex(poll_response))):
            get_zone_serial = zone.GetZoneSerial(
                self.mock_tg, 'context',
                objects.Zone.from_dict(self.test_zone),
                self.nameserver.host, self.nameserver.port,
            )
            result = get_zone_serial()
            self.assertEqual(result[0], 'SUCCESS')
            self.assertEqual(result[1], 99)

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
        with patch.object(dns.query, 'udp', return_value=dns.message.from_wire(
                binascii.a2b_hex(poll_response))):
            get_zone_serial = zone.GetZoneSerial(
                self.mock_tg, 'context',
                objects.Zone.from_dict(self.test_zone),
                self.nameserver.host, self.nameserver.port,
            )
            result = get_zone_serial()
            self.assertEqual(result[0], 'SUCCESS')
            self.assertEqual(result[1], 101)

    @patch.object(dns.query, 'udp', side_effect=dns.exception.Timeout)
    def test_poll_for_serial_number_timeout(self, _):
        self.CONF.set_override('serial_timeout', 1, 'service:worker')
        get_zone_serial = zone.GetZoneSerial(
            self.mock_tg, 'context',
            objects.Zone.from_dict(self.test_zone),
            self.nameserver.host, self.nameserver.port,
        )
        result = get_zone_serial()
        self.assertEqual(result[0], 'ERROR')
        self.assertIsNone(result[1])
