# Copyright 2025 Cloudification GmbH
#
# Author: cloudification <contact@cloudification.io>
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
from oslo_log import log as logging
import oslotest.base

from designate.exceptions import InvalidObject
from designate import objects

LOG = logging.getLogger(__name__)


class HTTPSTest(oslotest.base.BaseTestCase):

    def test_https_record(self):
        recordset = objects.RecordSet(
            name='example.org.', type='HTTPS',
            records=objects.RecordList(objects=[
                objects.Record(data='1 sample.example.org.'
                                    ' alpn=http/1.1,h2'),
            ])
        )

        recordset.validate()

    def test_parse_https(self):
        https_record = objects.HTTPS()
        ipv61 = '2001:db8:3333:4444:5555:6666:7777:8888'
        ipv6hint = f"{ipv61},2001:db8:3333:4444:cccc:dddd:eeee:ffff"
        ipv4hint = "1.2.3.4,9.8.7.6"
        alpn = "h3,h2,http/1.1"
        port = "888"
        target = 'sample.example.org.'
        https_record.from_string(f'1 {target}'
                                 f' alpn={alpn}'
                                 f' ipv4hint={ipv4hint}'
                                 f' ipv6hint={ipv6hint}'
                                 f' port={port}'
                                 )
        self.assertEqual(1, https_record.priority)
        self.assertEqual(target, https_record.target)
        self.assertEqual(f"alpn={alpn}", https_record.alpn)
        self.assertEqual(f"ipv6hint={ipv6hint}", https_record.ipv6hint)
        self.assertEqual(f"ipv4hint={ipv4hint}", https_record.ipv4hint)
        self.assertEqual(f"port={port}", https_record.port)

    def test_no_valid_alpn(self):
        recordset = objects.RecordSet(
            name='example.org.', type='HTTPS',
            records=objects.RecordList(objects=[
                objects.Record(data='1 sample.example.org. alpn=foo'),
            ])
        )

        self.assertRaises(InvalidObject, recordset.validate)

    def test_non_valid_port(self):
        recordset = objects.RecordSet(
            name='example.org.', type='HTTPS',
            records=objects.RecordList(objects=[
                objects.Record(data='1 sample.example.org.'
                                    ' port=foo'),
            ])
        )

        self.assertRaises(InvalidObject, recordset.validate)

    def test_non_valid_ech(self):
        recordset = objects.RecordSet(
            name='example.org.', type='HTTPS',
            records=objects.RecordList(objects=[
                objects.Record(data='1 sample.example.org.'
                                    ' ech=foo//'),
            ])
        )

        self.assertRaises(InvalidObject, recordset.validate)

    def test_non_valid_ipv4hint(self):
        recordset = objects.RecordSet(
            name='example.org.', type='HTTPS',
            records=objects.RecordList(objects=[
                objects.Record(data='1 sample.example.org.'
                                    ' ipv4hint=foo,192.168.1.2'),
            ])
        )

        self.assertRaises(InvalidObject, recordset.validate)

    def test_non_valid_ipv6hint(self):
        recordset = objects.RecordSet(
            name='example.org.', type='HTTPS',
            records=objects.RecordList(objects=[
                objects.Record(data='1 sample.example.org.'
                                    ' ipv6hint=foo'),
            ])
        )

        self.assertRaises(InvalidObject, recordset.validate)

    def test_no_default_alpn(self):
        recordset = objects.RecordSet(
            name='example.org.', type='HTTPS',
            records=objects.RecordList(objects=[
                objects.Record(data='1 sample.example.org. '
                                    'alpn=http/1.1 '
                                    'no-default-alpn port=8000'),
            ])
        )

        recordset.validate()

    def test_no_default_alpn_no_alpn_param(self):
        recordset = objects.RecordSet(
            name='example.org.', type='HTTPS',
            records=objects.RecordList(objects=[
                objects.Record(data='1 sample.example.org. '
                                    'no-default-alpn port=8000'),
            ])
        )

        self.assertRaises(InvalidObject, recordset.validate)

    def test_dohpath_invalid(self):
        query = "/dns-query{?dns}"
        data = f'1 doh.example. alpn=h2 dohpath={query}'
        recordset = objects.RecordSet(
            name='example.org.', type='HTTPS',
            records=objects.RecordList(objects=[
                objects.Record(data=data),
            ])
        )

        self.assertRaises(InvalidObject, recordset.validate)

    def test_mandatory(self):
        ipv6 = "2001:db8:3333:4444:5555:6666:7777:8888"
        recordset = objects.RecordSet(
            name='example.org.', type='HTTPS',
            records=objects.RecordList(objects=[
                objects.Record(
                    data='1 sample.example.org.'
                         ' ipv4hint=192.168.1.2'
                         f' ipv6hint={ipv6}'
                         ' alpn=h2'
                         ' mandatory=alpn,ipv4hint'),
            ])
        )

        recordset.validate()

    def test_mandatory_negative(self):
        ipv6hint = "2001:db8:3333:4444:5555:6666:7777:8888"
        recordset = objects.RecordSet(
            name='example.org.', type='HTTPS',
            records=objects.RecordList(objects=[
                objects.Record(
                    data=f'1 sample.example.org.'
                         f' ipv6hint={ipv6hint}'
                         f' mandatory=alpn,ipv4hint'),
            ])
        )

        self.assertRaises(InvalidObject, recordset.validate)
