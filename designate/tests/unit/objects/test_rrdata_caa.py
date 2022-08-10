# Copyright 2018 Canonical Ltd.
#
# Author: Tytus Kurek <tytus.kurek@canonical.com>
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
from oslo_log import log as logging
import oslotest.base

from designate import objects

LOG = logging.getLogger(__name__)


class RRDataCAATest(oslotest.base.BaseTestCase):
    def test_parse_caa_issue(self):
        caa_record = objects.CAA()
        caa_record.from_string('0 issue ca.example.net')

        self.assertEqual(0, caa_record.flags)
        self.assertEqual('issue ca.example.net', caa_record.prpt)

    def test_parse_caa_issuewild(self):
        caa_record = objects.CAA()
        caa_record.from_string('1 issuewild ca.example.net; policy=ev')

        self.assertEqual(1, caa_record.flags)
        self.assertEqual('issuewild ca.example.net; policy=ev',
                         caa_record.prpt)

    def test_parse_caa_iodef(self):
        caa_record = objects.CAA()
        caa_record.from_string('0 iodef https://example.net/')

        self.assertEqual(0, caa_record.flags)
        self.assertEqual('iodef https://example.net/', caa_record.prpt)

        caa_record = objects.CAA()
        caa_record.from_string('0 iodef mailto:security@example.net')

        self.assertEqual(0, caa_record.flags)
        self.assertEqual('iodef mailto:security@example.net', caa_record.prpt)

        caa_record = objects.CAA()
        caa_record.from_string('0 iodef mailto:security+caa@example.net')

        self.assertEqual(0, caa_record.flags)
        self.assertEqual('iodef mailto:security+caa@example.net',
                         caa_record.prpt)

    def test_parse_caa_invalid(self):
        caa_record = objects.CAA()
        self.assertRaisesRegex(
            ValueError,
            "Property tag 1 2 must be 'issue', 'issuewild' or 'iodef'",
            caa_record.from_string, '0 1 2'
        )

    def test_parse_caa_issue_host_too_long(self):
        hostname = 'a' * 64
        caa_record = objects.CAA()
        self.assertRaisesRegex(
            ValueError,
            'Host aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
            'aaaaaaaaaa is too long',
            caa_record.from_string, '0 issue %s.net' % hostname
        )

    def test_parse_caa_issue_domain_not_valid(self):
        caa_record = objects.CAA()
        self.assertRaisesRegex(
            ValueError,
            'Domain abc. is invalid',
            caa_record.from_string, '0 issue abc.'
        )

    def test_parse_caa_issue_key_value_not_valid(self):
        caa_record = objects.CAA()
        self.assertRaisesRegex(
            ValueError,
            'def is not a valid key-value pair',
            caa_record.from_string, '0 issue abc;def'
        )

    def test_parse_caa_iodef_mail_host_too_long(self):
        hostname = 'a' * 64
        caa_record = objects.CAA()
        self.assertRaisesRegex(
            ValueError,
            'Host aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
            'aaaaaaaaaa is too long',
            caa_record.from_string, '0 iodef mailto:me@%s.net' % hostname
        )

    def test_parse_caa_iodef_mail_domain_not_valid(self):
        caa_record = objects.CAA()
        self.assertRaisesRegex(
            ValueError,
            'Domain example.net. is invalid',
            caa_record.from_string, '0 iodef mailto:me@example.net.'
        )

    def test_parse_caa_iodef_http_host_too_long(self):
        hostname = 'a' * 64
        caa_record = objects.CAA()
        self.assertRaisesRegex(
            ValueError,
            'Host aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
            'aaaaaaaaaa is too long',
            caa_record.from_string, '0 iodef https://%s.net/' % hostname
        )

    def test_parse_caa_iodef_http_domain_not_valid(self):
        caa_record = objects.CAA()
        self.assertRaisesRegex(
            ValueError,
            'Domain example.net. is invalid',
            caa_record.from_string, '0 iodef https://example.net./'
        )

    def test_parse_caa_iodef_not_valid_url(self):
        caa_record = objects.CAA()
        self.assertRaisesRegex(
            ValueError,
            'https:// is not a valid URL',
            caa_record.from_string, '0 iodef https://'
        )
