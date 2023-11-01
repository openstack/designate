# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Federico Ceratto <federico.ceratto@hpe.com>
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
import dns.rdataclass
import dns.rdatatype
from oslo_config import fixture as cfg_fixture
import oslotest.base

import designate.conf
from designate import dnsutils
from designate.tests.unit import RoObject
from designate.worker.tasks import zone as worker_zone


CONF = designate.conf.CONF


class WorkerNotifyTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))
        self.zone = RoObject(name='zn', serial=314)
        self.notify = worker_zone.GetZoneSerial(
            mock.Mock(), mock.Mock(), self.zone, '203.0.113.1', 1234
        )

    @mock.patch('time.sleep', mock.Mock())
    def test_get_serial_number_nxdomain(self):
        CONF.set_override('serial_timeout', 0.1, 'service:worker')

        # The zone is not found but it was supposed to be there
        response = RoObject(
            answer=[RoObject(
                rdclass=dns.rdataclass.IN,
                rdtype=dns.rdatatype.SOA
            )],
            rcode=mock.Mock(return_value=dns.rcode.NXDOMAIN)
        )
        zone = RoObject(name='zn', serial=314)
        notify = worker_zone.GetZoneSerial(mock.Mock(), mock.Mock(),
                                           zone, '203.0.113.1',
                                           1234)
        notify._make_and_send_soa_message = mock.Mock(
            return_value=response
        )

        self.assertEqual(('NO_ZONE', None), notify())

    @mock.patch('time.sleep', mock.Mock())
    def test_get_serial_number_nxdomain_deleted_zone(self):
        # The zone is not found and it's not was supposed be there
        response = RoObject(
            answer=[RoObject(
                rdclass=dns.rdataclass.IN,
                rdtype=dns.rdatatype.SOA
            )],
            rcode=mock.Mock(return_value=dns.rcode.NXDOMAIN)
        )
        zone = RoObject(name='zn', serial=0, action='DELETE')
        notify = worker_zone.GetZoneSerial(mock.Mock(), mock.Mock(),
                                           zone, '203.0.113.1',
                                           1234)
        notify._make_and_send_soa_message = mock.Mock(
            return_value=response
        )
        self.assertEqual(('NO_ZONE', 0), notify())

    @mock.patch('time.sleep', mock.Mock())
    def test_get_serial_number_ok(self):
        zone = RoObject(name='zn', serial=314)
        ds = RoObject(items=[zone])
        response = RoObject(
            answer=[RoObject(
                name='zn',
                rdclass=dns.rdataclass.IN,
                rdtype=dns.rdatatype.SOA,
                to_rdataset=mock.Mock(return_value=ds)
            )],
            rcode=mock.Mock(return_value=dns.rcode.NOERROR),
            flags=dns.flags.AA,
            ednsflags=dns.rcode.NOERROR,
        )
        notify = worker_zone.GetZoneSerial(mock.Mock(), mock.Mock(),
                                           zone, '203.0.113.1',
                                           1234)
        notify._make_and_send_soa_message = mock.Mock(
            return_value=response
        )
        self.assertEqual(('SUCCESS', 314), notify())

    @mock.patch('time.sleep', mock.Mock())
    @mock.patch.object(dnsutils, 'send_dns_message')
    def test_make_and_send_dns_message_error_flags(self,
                                                   mock_send_dns_message):
        response = RoObject(
            rcode=mock.Mock(return_value=dns.rcode.NOERROR),
            # rcode is NOERROR but flags are not NOERROR
            flags=123,
            ednsflags=321,
            answer=['answer'],
        )
        mock_send_dns_message.return_value = response

        notify = worker_zone.GetZoneSerial(mock.Mock(), mock.Mock(),
                                           self.zone, '203.0.113.1',
                                           1234)

        self.assertEqual(('ERROR', None), notify())

    @mock.patch('time.sleep', mock.Mock())
    @mock.patch.object(dnsutils, 'send_dns_message')
    def test_make_and_send_dns_message_missing_AA_flags(self,
                                                        mock_send_dns_message):
        response = RoObject(
            rcode=mock.Mock(return_value=dns.rcode.NOERROR),
            # rcode is NOERROR but (flags & dns.flags.AA) gives 0
            flags=0,
            answer=['answer'],
        )
        mock_send_dns_message.return_value = response

        notify = worker_zone.GetZoneSerial(mock.Mock(), mock.Mock(),
                                           self.zone, '203.0.113.1',
                                           1234)

        self.assertEqual(('ERROR', None), notify())

    @mock.patch.object(dnsutils, 'send_dns_message')
    def test_make_and_send_dns_message_timeout(self, mock_send_dns_message):
        mock_send_dns_message.side_effect = dns.exception.Timeout

        out = self.notify._make_and_send_soa_message(
            self.zone.name, 'host', 123
        )

        self.assertIsNone(out)

    @mock.patch.object(dnsutils, 'send_dns_message')
    def test_make_and_send_dns_message_bad_response(self,
                                                    mock_send_dns_message):
        self.notify._make_dns_message = mock.Mock(return_value='')
        mock_send_dns_message.side_effect = dns.query.BadResponse

        out = self.notify._make_and_send_soa_message(
            self.zone.name, 'host', 123
        )

        self.assertIsNone(out)

    @mock.patch.object(dnsutils, 'send_dns_message')
    def test_make_and_send_dns_message_eagain(self, mock_send_dns_message):
        # bug #1558096
        socket_error = socket.error()
        socket_error.errno = socket.errno.EAGAIN
        mock_send_dns_message.side_effect = socket_error

        out = self.notify._make_and_send_soa_message(
            self.zone.name, 'host', 123
        )

        self.assertIsNone(out)

    @mock.patch.object(dnsutils, 'send_dns_message')
    def test_make_and_send_dns_message_econnrefused(self,
                                                    mock_send_dns_message):
        # bug #1558096
        socket_error = socket.error()
        socket_error.errno = socket.errno.ECONNREFUSED
        # socket errors other than EAGAIN should raise
        mock_send_dns_message.side_effect = socket_error

        self.assertRaises(
            socket.error,
            self.notify._make_and_send_soa_message,
            self.zone.name, 'host', 123
        )

    @mock.patch.object(dnsutils, 'send_dns_message')
    def test_make_and_send_dns_message_nxdomain(self, mock_send_dns_message):
        response = RoObject(
            rcode=mock.Mock(return_value=dns.rcode.NXDOMAIN),
            flags=dns.flags.AA,
            ednsflags=dns.rcode.NXDOMAIN
        )
        mock_send_dns_message.return_value = response

        out = self.notify._make_and_send_soa_message(
            self.zone.name, 'host', 123
        )

        self.assertEqual(response, out)
