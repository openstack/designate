# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
import jsonschema
from datetime import datetime
from moniker.openstack.common import log as logging
from moniker.tests import TestCase
from moniker import schema

LOG = logging.getLogger(__name__)


class TestSchemaValidator(TestCase):
    def test_validate_format_ipaddress(self):
        test_schema = {
            "properties": {
                "ipaddress": {
                    "type": "string",
                    "format": "ip-address",
                    "required": True
                },
            }
        }

        validator = schema.SchemaValidator(test_schema)

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
        ]

        for ipaddress in valid_ipaddresses:
            LOG.debug('Expecting success for: %s' % ipaddress)
            validator.validate({'ipaddress': ipaddress})

        for ipaddress in invalid_ipaddresses:
            with self.assertRaises(jsonschema.ValidationError):
                LOG.debug('Expecting failure for: %s' % ipaddress)
                validator.validate({'ipaddress': ipaddress})

    def test_validate_format_hostname(self):
        test_schema = {
            "properties": {
                "hostname": {
                    "type": "string",
                    "format": "host-name",
                    "required": True
                },
            }
        }

        validator = schema.SchemaValidator(test_schema)

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
        ]

        for hostname in valid_hostnames:
            LOG.debug('Expecting success for: %s' % hostname)
            validator.validate({'hostname': hostname})

        for hostname in invalid_hostnames:
            with self.assertRaises(jsonschema.ValidationError):
                LOG.debug('Expecting failure for: %s' % hostname)
                validator.validate({'hostname': hostname})

    def test_validate_format_domainname(self):
        test_schema = {
            "properties": {
                "domainname": {
                    "type": "string",
                    "format": "domain-name",
                    "required": True
                },
            }
        }

        validator = schema.SchemaValidator(test_schema)

        valid_domainnames = [
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

        invalid_domainnames = [
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
        ]

        for domainname in valid_domainnames:
            LOG.debug('Expecting success for: %s' % domainname)
            validator.validate({'domainname': domainname})

        for domainname in invalid_domainnames:
            with self.assertRaises(jsonschema.ValidationError):
                LOG.debug('Expecting failure for: %s' % domainname)
                validator.validate({'domainname': domainname})

    def test_validate_format_email(self):
        test_schema = {
            "properties": {
                "email": {
                    "type": "string",
                    "format": "email",
                    "required": True
                },
            }
        }

        validator = schema.SchemaValidator(test_schema)

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
            validator.validate({'email': email})

        for email in invalid_emails:
            with self.assertRaises(jsonschema.ValidationError):
                LOG.debug('Expecting failure for: %s' % email)
                validator.validate({'email': email})

    def test_validate_format_datetime(self):
        test_schema = {
            "properties": {
                "date_time": {
                    "type": "string",
                    "format": "date-time",
                    "required": True
                },
            }
        }

        validator = schema.SchemaValidator(test_schema)

        valid_datetimes = [
            datetime(2013, 1, 1)
        ]

        for dt in valid_datetimes:
            validator.validate({'date_time': dt})


class TestSchema(TestCase):
    def test_constructor(self):
        domain = schema.Schema('v1', 'domain')

        self.assertIsInstance(domain, schema.Schema)
