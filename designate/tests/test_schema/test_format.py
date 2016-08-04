# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from oslo_log import log as logging

from designate.tests import TestCase
from designate.schema import format


LOG = logging.getLogger(__name__)


class SchemaFormatTest(TestCase):
    def test_is_ipv4(self):
        valid_ipaddresses = [
            '0.0.0.1',
            '127.0.0.1',
            '10.0.0.1',
            '192.0.2.2',
        ]

        invalid_ipaddresses = [
            '0.0.0.0',
            '0.0.0.256',
            '0.0.256.0',
            '0.256.0.0',
            '256.0.0.0',
            '127.0.0',
            '127.0.0.999',
            '127.0.0.256',
            '127.0..1',
            '-1.0.0.1',
            '1.0.-0.1',
            '1.0.0.-1',
            'ABCDEF',
            'ABC/DEF',
            'ABC\\DEF',
            # Trailing newline - Bug 1471158
            "127.0.0.1\n",
        ]

        for ipaddress in valid_ipaddresses:
            self.assertTrue(format.is_ipv4(ipaddress))

        for ipaddress in invalid_ipaddresses:
            self.assertFalse(format.is_ipv4(ipaddress))

    def test_is_ipv6(self):
        valid_ipaddresses = [
            '2001:db8::0',
            '2001:0db8:85a3:0000:0000:8a2e:0370:7334',
            '2001:db8:85a3:0000:0000:8a2e:0370:7334',
            '2001:db8:85a3::8a2e:0370:7334',
        ]

        invalid_ipaddresses = [
            # Invalid characters
            'hhhh:hhhh:hhhh:hhhh:hhhh:hhhh:hhhh:hhhh'
            # Trailing newline - Bug 1471158
            "2001:db8::0\n",
        ]

        for ipaddress in valid_ipaddresses:
            self.assertTrue(format.is_ipv6(ipaddress),
                            'Expected Valid: %s' % ipaddress)

        for ipaddress in invalid_ipaddresses:
            self.assertFalse(format.is_ipv6(ipaddress),
                             'Expected Invalid: %s' % ipaddress)

    def test_is_hostname(self):
        valid_hostnames = [
            'example.com.',
            'www.example.com.',
            '*.example.com.',
            '12345.example.com.',
            '192-0-2-1.example.com.',
            'ip192-0-2-1.example.com.',
            'www.ip192-0-2-1.example.com.',
            'ip192-0-2-1.www.example.com.',
            'abc-123.example.com.',
            '_tcp.example.com.',
            '_service._tcp.example.com.',
            ('1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.8.b.d.0.1.0.0.2'
             '.ip6.arpa.'),
            '1.1.1.1.in-addr.arpa.',
            'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.',
            ('abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghi.'),
        ]

        invalid_hostnames = [
            '**.example.com.',
            '*.*.example.org.',
            'a.*.example.org.',
            # Exceeds single lable length limit
            ('abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijkL'
             '.'),
            ('abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijkL'
             '.'),
            # Exceeds total length limit
            ('abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopq.'),
            # Empty label part
            'abc..def.',
            '..',
            # Invalid character
            'abc$.def.',
            'abc.def$.',
            # Labels must not start with a -
            '-abc.',
            'abc.-def.',
            'abc.-def.ghi.',
            # Labels must not end with a -
            'abc-.',
            'abc.def-.',
            'abc.def-.ghi.',
            # Labels must not start or end with a -
            '-abc-.',
            'abc.-def-.',
            'abc.-def-.ghi.',
            # Trailing newline - Bug 1471158
            "www.example.com.\n",
        ]

        for hostname in valid_hostnames:
            self.assertTrue(format.is_hostname(hostname))

        for hostname in invalid_hostnames:
            self.assertFalse(format.is_hostname(hostname))

    def test_is_ns_hostname(self):
        valid_ns_hostnames = [
            'example.com.',
            'www.example.com.',
            '12345.example.com.',
            '192-0-2-1.example.com.',
            'ip192-0-2-1.example.com.',
            'www.ip192-0-2-1.example.com.',
            'ip192-0-2-1.www.example.com.',
            'abc-123.example.com.',
            '_tcp.example.com.',
            '_service._tcp.example.com.',
            ('1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.8.b.d.0.1.0.0.2'
             '.ip6.arpa.'),
            '1.1.1.1.in-addr.arpa.',
            'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.',
            ('abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghi.'),
        ]

        invalid_ns_hostnames = [
            # Wildcard NS hostname, bug #1533299
            '*.example.com.',
            '**.example.com.',
            '*.*.example.org.',
            'a.*.example.org.',
            # Exceeds single lable length limit
            ('abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijkL'
             '.'),
            ('abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijkL'
             '.'),
            # Exceeds total length limit
            ('abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopq.'),
            # Empty label part
            'abc..def.',
            '..',
            # Invalid character
            'abc$.def.',
            'abc.def$.',
            # Labels must not start with a -
            '-abc.',
            'abc.-def.',
            'abc.-def.ghi.',
            # Labels must not end with a -
            'abc-.',
            'abc.def-.',
            'abc.def-.ghi.',
            # Labels must not start or end with a -
            '-abc-.',
            'abc.-def-.',
            'abc.-def-.ghi.',
            # Trailing newline - Bug 1471158
            "www.example.com.\n",
        ]

        for hostname in valid_ns_hostnames:
            self.assertTrue(format.is_ns_hostname(hostname))

        for hostname in invalid_ns_hostnames:
            self.assertFalse(format.is_ns_hostname(hostname))

    def test_is_zonename(self):
        valid_zonenames = [
            'example.com.',
            'www.example.com.',
            '12345.example.com.',
            '192-0-2-1.example.com.',
            'ip192-0-2-1.example.com.',
            'www.ip192-0-2-1.example.com.',
            'ip192-0-2-1.www.example.com.',
            'abc-123.example.com.',
            '_tcp.example.com.',
            '_service._tcp.example.com.',
            ('1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.8.b.d.0.1.0.0.2'
             '.ip6.arpa.'),
            '1.1.1.1.in-addr.arpa.',
            'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.',
            ('abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghi.'),
        ]

        invalid_zonenames = [
            '*.example.com.',
            '**.example.com.',
            '*.*.example.org.',
            'a.*.example.org.',
            # Exceeds single lable length limit
            ('abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijkL'
             '.'),
            ('abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijkL'
             '.'),
            ('abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijkL'
             '.'),
            # Exceeds total length limit
            ('abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopq.'),
            # Empty label part
            'abc..def.',
            '..',
            # Invalid character
            'abc$.def.',
            'abc.def$.',
            # Labels must not start with a -
            '-abc.',
            'abc.-def.',
            'abc.-def.ghi.',
            # Labels must not end with a -
            'abc-.',
            'abc.def-.',
            'abc.def-.ghi.',
            # Labels must not start or end with a -
            '-abc-.',
            'abc.-def-.',
            'abc.-def-.ghi.',
            # Trailing newline - Bug 1471158
            "example.com.\n",
        ]

        for zonename in valid_zonenames:
            self.assertTrue(format.is_zonename(zonename), zonename)

        for zonename in invalid_zonenames:
            self.assertFalse(format.is_zonename(zonename), zonename)

    def test_is_srv_hostname(self):
        valid_hostnames = [
            '_sip._tcp.example.com.',
            '_sip._udp.example.com.',
        ]

        invalid_hostnames = [
            # Invalid Formats
            '_tcp.example.com.',
            'sip._udp.example.com.',
            '_sip.udp.example.com.',
            'sip.udp.example.com.',
            # Trailing newline - Bug 1471158
            "_sip._tcp.example.com.\n",
        ]

        for hostname in valid_hostnames:
            self.assertTrue(format.is_srv_hostname(hostname),
                            'Expected Valid: %s' % hostname)

        for hostname in invalid_hostnames:
            self.assertFalse(format.is_srv_hostname(hostname),
                             'Expected Invalid: %s' % hostname)

    def test_is_tldname(self):
        valid_tldnames = [
            'com',
            'net',
            'org',
            'co.uk',
        ]

        invalid_tldnames = [
            # Invalid Formats
            'com.',
            '.com',
            # Trailing newline - Bug 1471158
            "com\n",
        ]

        for tldname in valid_tldnames:
            self.assertTrue(format.is_tldname(tldname),
                            'Expected Valid: %s' % tldname)

        for tldname in invalid_tldnames:
            self.assertFalse(format.is_tldname(tldname),
                             'Expected Invalid: %s' % tldname)

    def test_is_email(self):
        valid_emails = [
            'user@example.com',
            'user@emea.example.com',
            'user@example.com',
            'first.last@example.com',
        ]

        invalid_emails = [
            # We use the email addr for the SOA RNAME field, this means the
            # entire address, excluding the @ must be chacracters valid
            # as a DNS name. i.e. + and % addressing is invalid.
            'user+plus@example.com',
            'user%example.org@example.com',
            'example.org',
            '@example.org',
            'user@*.example.org',
            'user',
            'user@',
            'user+plus',
            'user+plus@',
            'user%example.org',
            'user%example.org@',
            'user@example.org.',
            # Exceeds total length limit
            ('user@fghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijk.'
             'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopq.'),
            # Exceeds single lable length limit
            ('user@abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefg'
             'hijkL.'),
            ('user@abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefg'
             'hijk.abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefg'
             'hijkL.'),
            # Exceeds single lable length limit in username part
            ('abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijkL'
             '@example.com.'),
        ]

        for email in valid_emails:
            LOG.debug('Expecting success for: %s' % email)
            self.assertTrue(format.is_email(email))

        for email in invalid_emails:
            LOG.debug('Expecting failure for: %s' % email)
            self.assertFalse(format.is_email(email))

    def test_is_sshfp(self):
        valid_sshfps = [
            '72d30d211ce8c464de2811e534de23b9be9b4dc4',
            '7f3f61e323a7d75de08a2a6069b333e925cae260f4902017194002f226db8658',
        ]

        invalid_sshfps = [
            # Invalid Formats
            'P2d30d211ce8c464de2811e534de23b9be9b4dc4',  # "P" !IN [A-F]
            '72d30d211',
            # Trailing newline - Bug 1471158
            "72d30d211ce8c464de2811e534de23b9be9b4dc4\n",
        ]

        for sshfp in valid_sshfps:
            self.assertTrue(format.is_sshfp_fingerprint(sshfp),
                            'Expected Valid: %s' % sshfp)

        for sshfp in invalid_sshfps:
            self.assertFalse(format.is_sshfp_fingerprint(sshfp),
                             'Expected Invalid: %s' % sshfp)

    def test_is_uuid(self):
        valid_uuids = [
            'd3693ef8-2188-11e5-bf77-676ff9eb39dd',
        ]

        invalid_uuids = [
            # Invalid Formats
            'p3693ef8-2188-11e5-bf77-676ff9eb39dd',  # "p" !IN [A-F]
            'd3693ef8218811e5bf77676ff9eb39dd',
            # Trailing newline - Bug 1471158
            "d3693ef8-2188-11e5-bf77-676ff9eb39dd\n",
        ]

        for uuid in valid_uuids:
            self.assertTrue(format.is_uuid(uuid),
                            'Expected Valid: %s' % uuid)

        for uuid in invalid_uuids:
            self.assertFalse(format.is_uuid(uuid),
                             'Expected Invalid: %s' % uuid)

    def test_is_fip_id(self):
        valid_fip_ids = [
            'region-a:d3693ef8-2188-11e5-bf77-676ff9eb39dd',
        ]

        invalid_fip_ids = [
            # Invalid Formats
            'region-a:p3693ef8-2188-11e5-bf77-676ff9eb39dd',  # "p" !IN [A-F]
            # Trailing newline - Bug 1471158
            "region-a:d3693ef8-2188-11e5-bf77-676ff9eb39dd\n",
        ]

        for fip_id in valid_fip_ids:
            self.assertTrue(format.is_floating_ip_id(fip_id),
                            'Expected Valid: %s' % fip_id)

        for fip_id in invalid_fip_ids:
            self.assertFalse(format.is_floating_ip_id(fip_id),
                             'Expected Invalid: %s' % fip_id)

    def test_is_ip_and_port(self):
        valid_ip_and_ports = [
            '192.0.2.1:80',
            '192.0.2.1:1',
            '192.0.2.1:65535',
        ]

        invalid_ip_and_ports = [
            '192.0.2.1:65536',
            # Trailing newline - Bug 1471158
            "192.0.2.1:80\n",
        ]

        for ip_and_port in valid_ip_and_ports:
            self.assertTrue(format.is_ip_and_port(ip_and_port),
                            'Expected Valid: %s' % ip_and_port)

        for ip_and_port in invalid_ip_and_ports:
            self.assertFalse(format.is_ip_and_port(ip_and_port),
                             'Expected Invalid: %s' % ip_and_port)
