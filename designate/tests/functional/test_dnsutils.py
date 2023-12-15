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


import dns
import dns.query
import dns.tsigkeyring

import designate.conf
from designate import dnsutils
from designate import exceptions
from designate import objects
from designate import storage
import designate.tests.functional


CONF = designate.conf.CONF
SAMPLES = {
    ("cname.example.com.", "CNAME"): {
        "ttl": 10800,
        "records": ["example.com."],
    },
    ("_http._tcp.example.com.", "SRV"): {
        "ttl": 10800,
        "records": [
            "10 0 80 192.0.2.4.example.com.",
            "10 5 80 192.0.2.5.example.com."
        ],
    },
    ("ipv4.example.com.", "A"): {
        "ttl": 300,
        "records": ["192.0.2.1"]
    },
    ("delegation.example.com.", "NS"): {
        "ttl": 10800,
        "records": ["ns1.example.com."]
    },
    ("ipv6.example.com.", "AAAA"): {
        "ttl": 10800,
        "records": ["2001:db8::"],
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
            "5 192.0.2.2.example.com.",
            '10 192.0.2.3.example.com.'
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


class TestTsigUtils(designate.tests.functional.TestCase):
    def setUp(self):
        super().setUp()
        self.storage = storage.get_storage()
        self.tsig_keyring = dnsutils.TsigKeyring(self.storage)

    def test_tsig_keyring(self):
        expected_result = b'J\x89\x9e:WRy\xca\xde\xb4\xa7\xb2'

        self.create_tsigkey(fixture=0)

        query = dns.message.make_query(
            'example.com.', dns.rdatatype.SOA,
        )
        query.use_tsig(dns.tsigkeyring.from_text(
            {'test-key-one': 'SomeOldSecretKey'})
        )

        self.assertEqual(expected_result, self.tsig_keyring.get(query.keyname))
        self.assertEqual(expected_result, self.tsig_keyring[query.keyname])

    def test_tsig_keyring_not_found(self):
        query = dns.message.make_query(
            'example.com.', dns.rdatatype.SOA,
        )
        query.use_tsig(dns.tsigkeyring.from_text(
            {'test-key-one': 'SomeOldSecretKey'})
        )

        self.assertIsNone(self.tsig_keyring.get(query.keyname))


class TestUtils(designate.tests.functional.TestCase):
    def setUp(self):
        super().setUp()

    def test_from_dnspython_zone(self):
        zone_file = self.get_zonefile_fixture()

        dnspython_zone = dns.zone.from_text(
            zone_file,
            relativize=False,
            check_origin=False
        )

        zone = dnsutils.from_dnspython_zone(dnspython_zone)

        self.assertIsInstance(zone, objects.zone.Zone)

    def test_from_dnspython_zone_zero_soa(self):
        CONF.set_override('min_ttl', 1234, 'service:central')

        zone_file = self.get_zonefile_fixture(variant='zerosoa')

        dnspython_zone = dns.zone.from_text(
            zone_file,
            relativize=False,
            check_origin=False
        )

        zone = dnsutils.from_dnspython_zone(dnspython_zone)

        self.assertIsInstance(zone, objects.zone.Zone)
        self.assertEqual(1234, zone.ttl)

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
