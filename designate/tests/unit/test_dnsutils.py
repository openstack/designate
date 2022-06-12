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
import dns.rcode
import dns.rdatatype
import dns.zone
import eventlet
from oslo_config import cfg
from oslo_config import fixture as cfg_fixture
import oslotest.base

from designate import dnsutils
from designate import exceptions
from designate import objects
import designate.tests

CONF = cfg.CONF

SAMPLES = {
    ("cname.example.com.", "CNAME"): {
        "ttl": 10800,
        "records": ["example.com."],
    },
    ("_http._tcp.example.com.", "SRV"): {
        "ttl": 10800,
        "records": [
            "10 0 80 192.0.0.4.example.com.",
            "10 5 80 192.0.0.5.example.com."
        ],
    },
    ("ipv4.example.com.", "A"): {
        "ttl": 300,
        "records": ["192.0.0.1"]
    },
    ("delegation.example.com.", "NS"): {
        "ttl": 10800,
        "records": ["ns1.example.com."]
    },
    ("ipv6.example.com.", "AAAA"): {
        "ttl": 10800,
        "records": ["fd00::1"],
    },
    ("example.com.", "SOA"): {
        "records": [
            "ns1.example.com. nsadmin.example.com."
            " 2013091101 7200 3600 2419200 10800"
        ],
        "ttl": 600
    },
    ("example.com.", "MX"): {
        "ttl": 10800,
        "records": [
            "5 192.0.0.2.example.com.",
            '10 192.0.0.3.example.com.'
        ]
    },
    ("example.com.", "TXT"): {
        "ttl": 10800,
        "records": ['"abc" "def"']
    },
    ("example.com.", "SPF"): {
        "ttl": 10800,
        "records": ['"v=spf1 mx a"']
    },
    ("example.com.", "NS"): {
        "ttl": 10800,
        "records": [
            'ns1.example.com.',
            'ns2.example.com.'
        ]
    }
}


class TestUtils(designate.tests.TestCase):
    def setUp(self):
        super(TestUtils, self).setUp()

    def test_from_dnspython_zone(self):
        zone_file = self.get_zonefile_fixture()

        dnspython_zone = dns.zone.from_text(
            zone_file,
            relativize=False,
            check_origin=False
        )

        zone = dnsutils.from_dnspython_zone(dnspython_zone)

        self.assertIsInstance(zone, objects.zone.Zone)

    def test_from_dnspython_zone_no_soa(self):
        zone_file = self.get_zonefile_fixture(variant='nosoa')

        dnspython_zone = dns.zone.from_text(
            zone_file,
            relativize=False,
            check_origin=False
        )

        self.assertRaisesRegex(
            exceptions.BadRequest,
            'An SOA record is required',
            dnsutils.from_dnspython_zone, dnspython_zone,
        )

    def test_parse_zone(self):
        zone_file = self.get_zonefile_fixture()

        dnspython_zone = dns.zone.from_text(
            zone_file,
            # Don't relativize, otherwise we end up with '@' record names.
            relativize=False,
            # Dont check origin, we allow missing NS records (missing SOA
            # records are taken care of in _create_zone).
            check_origin=False
        )

        zone = dnsutils.from_dnspython_zone(dnspython_zone)

        for rrset in zone.recordsets:
            k = (rrset.name, rrset.type)
            self.assertIn(k, SAMPLES)

            sample_ttl = SAMPLES[k].get('ttl', None)
            if rrset.obj_attr_is_set('ttl') or sample_ttl is not None:
                self.assertEqual(sample_ttl, rrset.ttl)

            self.assertEqual(len(rrset.records), len(SAMPLES[k]['records']))

            for record in rrset.records:
                self.assertIn(record.data, SAMPLES[k]['records'])

        self.assertEqual(len(SAMPLES), len(zone.recordsets))
        self.assertEqual('example.com.', zone.name)

    def test_zone_lock(self):
        # Initialize a ZoneLock
        lock = dnsutils.ZoneLock(0.1)

        # Ensure there's no lock for different zones
        for zone_name in ['foo.com.', 'bar.com.', 'example.com.']:
            self.assertTrue(lock.acquire(zone_name))

        # Ensure a lock for successive calls for the same zone
        self.assertTrue(lock.acquire('example2.com.'))
        self.assertFalse(lock.acquire('example2.com.'))

        # Acquire, release, and reacquire
        self.assertTrue(lock.acquire('example3.com.'))
        lock.release('example3.com.')
        self.assertTrue(lock.acquire('example3.com.'))

    def test_limit_notify_middleware(self):
        self.CONF.set_override('notify_delay', 0.1, 'service:agent')

        # Initialize the middlware
        placeholder_app = None
        middleware = dnsutils.LimitNotifyMiddleware(placeholder_app)

        # Prepare a NOTIFY
        zone_name = 'example.com.'
        notify = dns.message.make_query(zone_name, dns.rdatatype.SOA)
        notify.flags = 0
        notify.set_opcode(dns.opcode.NOTIFY)
        notify.flags |= dns.flags.AA

        # Send the NOTIFY through the middleware
        # No problem, middleware should return None to pass it on
        self.assertIsNone(middleware.process_request(notify))

    @mock.patch('designate.dnsutils.ZoneLock.acquire', return_value=False)
    def test_limit_notify_middleware_no_acquire(self, mock_acquire):
        self.CONF.set_override('notify_delay', 0.1, 'service:agent')

        # Initialize the middlware
        placeholder_app = None
        middleware = dnsutils.LimitNotifyMiddleware(placeholder_app)

        # Prepare a NOTIFY
        zone_name = 'example.com.'
        notify = dns.message.make_query(zone_name, dns.rdatatype.SOA)
        notify.flags = 0
        notify.set_opcode(dns.opcode.NOTIFY)
        notify.flags |= dns.flags.AA

        # Make a response object to match the middleware's return
        response = dns.message.make_response(notify)
        # Provide an authoritative answer
        response.flags |= dns.flags.AA

        # Send the NOTIFY through the middleware
        # Lock can't be acquired, a NOTIFY is already being worked on
        # so just return what would have come back for a successful NOTIFY
        # This needs to be a one item tuple for the serialization middleware
        self.assertEqual(middleware.process_request(notify), (response,))

    def test_all_tcp_default(self):
        self.assertEqual(False, dnsutils.use_all_tcp())

    def test_all_tcp_using_mdns(self):
        CONF.set_override('all_tcp', True, 'service:mdns')
        self.assertEqual(True, dnsutils.use_all_tcp())

    def test_all_tcp_using_worker(self):
        CONF.set_override('all_tcp', True, 'service:worker')
        self.assertEqual(True, dnsutils.use_all_tcp())

    @mock.patch.object(dns.query, 'udp')
    def test_send_soa_message(self, mock_udp):
        dnsutils.soa('zone_name', '192.0.2.1', 1234, 1)
        msg = mock_udp.call_args[0][0]
        mock_udp.assert_called_with(
            mock.ANY, '192.0.2.1', port=1234, timeout=1
        )
        txt = msg.to_text().split('\n')[1:]
        self.assertEqual([
            'opcode QUERY',
            'rcode NOERROR',
            'flags RD',
            ';QUESTION',
            'zone_name. IN SOA',
            ';ANSWER',
            ';AUTHORITY',
            ';ADDITIONAL'
        ], txt)


class TestDoAfxr(oslotest.base.BaseTestCase):
    def setUp(self):
        super(TestDoAfxr, self).setUp()
        self.useFixture(cfg_fixture.Config(CONF))

    def test_xfr_default(self):
        self.assertEqual(10, dnsutils.xfr_timeout())

    def test_xfr_timeout_set_using_mdns(self):
        CONF.set_override('xfr_timeout', 30, 'service:mdns')
        self.assertEqual(30, dnsutils.xfr_timeout())

    def test_xfr_timeout_set_using_worker(self):
        CONF.set_override('xfr_timeout', 40, 'service:worker')
        self.assertEqual(40, dnsutils.xfr_timeout())

    @mock.patch.object(dns.query, 'xfr')
    @mock.patch.object(dns.zone, 'from_xfr')
    def test_do_afxr(self, mock_from_xfr_impl, mock_xfr):
        mock_from_xfr = mock.MagicMock()
        mock_from_xfr_impl.return_value = mock_from_xfr

        mock_from_xfr.origin.to_text.return_value = 'raw_zone'
        mock_from_xfr.return_value = 'raw_zone'

        masters = [
            {'host': '192.168.0.1', 'port': 53},
            {'host': '192.168.0.2', 'port': 53},
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
            {'host': '192.168.0.1', 'port': 53},
            {'host': '192.168.0.2', 'port': 53},
            {'host': '192.168.0.3', 'port': 53},
            {'host': '192.168.0.4', 'port': 53},
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
            {'host': '192.168.0.1', 'port': 53},
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
            {'host': '192.168.0.1', 'port': 53},
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
            {'host': '192.168.0.1', 'port': 53},
        ]

        self.assertRaises(
            exceptions.XFRFailure,
            dnsutils.do_axfr, 'example.com.', masters,
        )

        self.assertTrue(mock_xfr.called)
        self.assertTrue(mock_from_xfr.called)

    @mock.patch.object(dns.query, 'udp')
    def test_send_udp_dns_message(self, mock_udp):
        CONF.set_override('all_tcp', False, 'service:mdns')
        dnsutils.send_dns_message('msg', '192.0.2.1', 1234, 1)
        mock_udp.assert_called_with(
            'msg', '192.0.2.1', port=1234, timeout=1
        )

    @mock.patch.object(dns.query, 'tcp')
    def test_send_tcp_dns_message(self, mock_tcp):
        CONF.set_override('all_tcp', True, 'service:mdns')
        dnsutils.send_dns_message('msg', '192.0.2.1', 1234, 1)
        mock_tcp.assert_called_with(
            'msg', '192.0.2.1', port=1234, timeout=1
        )
