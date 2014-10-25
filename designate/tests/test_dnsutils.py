# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hp.com>
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
from dns import zone as dnszone

from designate import dnsutils
from designate.tests import TestCase

SAMPLES = {
    ("cname.example.com.", "CNAME"): {
        "records": ["example.com."],
    },
    ("_http._tcp.example.com.", "SRV"): {
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
        "records": ["ns1.example.com."]
    },
    ("ipv6.example.com.", "AAAA"): {
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
        "records": [
            "5 192.0.0.2.example.com.",
            '10 192.0.0.3.example.com.'
        ]
    },
    ("example.com.", "TXT"): {
        "records": ['"abc" "def"']
    },
    ("example.com.", "SPF"): {
        "records": ['"v=spf1 mx a"']
    },
    ("example.com.", "NS"): {
        "records": [
            'ns1.example.com.',
            'ns2.example.com.'
        ]
    }
}


class TestUtils(TestCase):
    def test_parse_zone(self):
        zone_file = self.get_zonefile_fixture()

        dnspython_zone = dnszone.from_text(
            zone_file,
            # Don't relativize, otherwise we end up with '@' record names.
            relativize=False,
            # Dont check origin, we allow missing NS records (missing SOA
            # records are taken care of in _create_zone).
            check_origin=False)

        zone = dnsutils.from_dnspython_zone(dnspython_zone)

        for rrset in zone.recordsets:
            k = (rrset.name, rrset.type)
            self.assertIn(k, SAMPLES)

            sample_ttl = SAMPLES[k].get('ttl', None)
            if rrset.obj_attr_is_set('ttl') or sample_ttl is not None:
                self.assertEqual(rrset.ttl, sample_ttl)

            self.assertEqual(len(SAMPLES[k]['records']), len(rrset.records))

            for r in rrset.records:
                self.assertIn(r.data, SAMPLES[k]['records'])

        self.assertEqual(len(SAMPLES), len(zone.recordsets))
        self.assertEqual('example.com.', zone.name)
