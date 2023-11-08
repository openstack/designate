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
from unittest import mock

import oslotest.base

from designate.objects import fields


class EnumTest(oslotest.base.BaseTestCase):
    def test_get_schema(self):
        result = fields.Enum('valid').get_schema()
        self.assertEqual('valid', result['enum'])
        self.assertEqual('any', result['type'])


class DomainFieldTest(oslotest.base.BaseTestCase):
    def test_not_valid_domain_field(self):
        sub_domain = 'a' * 64
        self.assertRaisesRegex(
            ValueError,
            f'Host {sub_domain} is too long',
            fields.DomainField().coerce, mock.Mock(), mock.Mock(),
            f'{sub_domain}.example.org.'
        )


class EmailFieldTest(oslotest.base.BaseTestCase):
    def test_not_valid_email_field(self):
        self.assertRaisesRegex(
            ValueError,
            '- is not an email',
            fields.EmailField().coerce, mock.Mock(), mock.Mock(),
            '-'
        )
        self.assertRaisesRegex(
            ValueError,
            'Email @ is invalid',
            fields.EmailField().coerce, mock.Mock(), mock.Mock(),
            '@'
        )


class HostFieldTest(oslotest.base.BaseTestCase):
    def test_is_none(self):
        self.assertIsNone(
            fields.HostField(nullable=True).coerce(
                mock.Mock(), mock.Mock(), None
            )
        )

    def test_not_valid_host_field(self):
        sub_domain = 'a' * 64
        self.assertRaisesRegex(
            ValueError,
            f'Host {sub_domain} is too long',
            fields.HostField().coerce, mock.Mock(), mock.Mock(),
            f'{sub_domain}.example.org.'
        )
        self.assertRaisesRegex(
            ValueError,
            'Host name example.org does not end with a dot',
            fields.HostField().coerce, mock.Mock(), mock.Mock(),
            'example.org'
        )


class SRVFieldTest(oslotest.base.BaseTestCase):
    def test_is_none(self):
        self.assertIsNone(
            fields.SRVField(nullable=True).coerce(
                mock.Mock(), mock.Mock(), None
            )
        )

    def test_not_valid_srv_field(self):
        sub_domain = 'a' * 64
        self.assertRaisesRegex(
            ValueError,
            f'Host {sub_domain} is too long',
            fields.SRVField().coerce, mock.Mock(), mock.Mock(),
            f'{sub_domain}.example.org.'
        )
        self.assertRaisesRegex(
            ValueError,
            'Host name example.org does not end with a dot',
            fields.SRVField().coerce, mock.Mock(), mock.Mock(),
            'example.org'
        )


class TxtFieldTest(oslotest.base.BaseTestCase):
    def test_not_valid_txt(self):
        self.assertRaisesRegex(
            ValueError,
            r"Do NOT put '\\' into end of TXT record",
            fields.TxtField().coerce, mock.Mock(), mock.Mock(),
            " \\"
        )


class SshfpTest(oslotest.base.BaseTestCase):
    def test_not_valid_sshfp(self):
        self.assertRaisesRegex(
            ValueError,
            'Host name  is not a SSHFP record',
            fields.Sshfp().coerce, mock.Mock(), mock.Mock(),
            ''
        )


class NaptrFlagsFieldTest(oslotest.base.BaseTestCase):
    def test_not_valid_naptr_flags(self):
        record = 'A' * 256
        self.assertRaisesRegex(
            ValueError,
            f'NAPTR record {record} flags field cannot be longer than 255 '
            'characters',
            fields.NaptrFlagsField().coerce, mock.Mock(), mock.Mock(),
            record
        )
        self.assertRaisesRegex(
            ValueError,
            'NAPTR record record flags can be S, A, U and P',
            fields.NaptrFlagsField().coerce, mock.Mock(), mock.Mock(),
            'record'
        )


class NaptrServiceFieldTest(oslotest.base.BaseTestCase):
    def test_not_valid_naptr_service(self):
        record = 'A' * 256
        self.assertRaisesRegex(
            ValueError,
            f'NAPTR record {record} service field cannot be longer than 255 '
            'characters',
            fields.NaptrServiceField().coerce, mock.Mock(), mock.Mock(),
            record
        )
        self.assertRaisesRegex(
            ValueError,
            '_ NAPTR record service is invalid',
            fields.NaptrServiceField().coerce, mock.Mock(), mock.Mock(),
            '_'
        )


class NaptrRegexpFieldTest(oslotest.base.BaseTestCase):
    def test_not_valid_naptr_regexp(self):
        record = 'A' * 256
        self.assertRaisesRegex(
            ValueError,
            f'NAPTR record {record} regexp field cannot be longer than 255 '
            'characters',
            fields.NaptrRegexpField().coerce, mock.Mock(), mock.Mock(),
            record
        )
        self.assertRaisesRegex(
            ValueError,
            '_ NAPTR record is invalid',
            fields.NaptrRegexpField().coerce, mock.Mock(), mock.Mock(),
            '_'
        )


class CertTypeFieldTest(oslotest.base.BaseTestCase):
    def test_not_valid_cert_type(self):
        self.assertRaisesRegex(
            ValueError,
            'Cert type _ is not a valid Mnemonic or value',
            fields.CertTypeField().coerce, mock.Mock(), mock.Mock(),
            '_'
        )


class CertAlgoFieldTest(oslotest.base.BaseTestCase):
    def test_not_valid_cert_algo(self):
        self.assertRaisesRegex(
            ValueError,
            'Cert Algo _ is not a valid Mnemonic or value',
            fields.CertAlgoField().coerce, mock.Mock(), mock.Mock(),
            '_'
        )


class IPOrHostTest(oslotest.base.BaseTestCase):
    def test_valid(self):
        self.assertEqual(
            'example.org.',
            fields.IPOrHost().coerce(mock.Mock(), mock.Mock(), 'example.org.')
        )
        self.assertEqual(
            '192.0.2.1',
            fields.IPOrHost().coerce(mock.Mock(), mock.Mock(), '192.0.2.1')
        )

    def test_not_valid_ip_or_host(self):
        self.assertRaisesRegex(
            ValueError,
            'example.org is not IP address or host name',
            fields.IPOrHost().coerce, mock.Mock(), mock.Mock(), 'example.org'
        )
