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

import base64

from oslo_log import log as logging
import oslotest.base

from designate.exceptions import InvalidObject
from designate import objects

LOG = logging.getLogger(__name__)


class SVCBTest(oslotest.base.BaseTestCase):

    def test_svcb_record(self):
        recordset = objects.RecordSet(
            name='example.org.', type='SVCB',
            records=objects.RecordList(objects=[
                objects.Record(
                    data='1 sample.example.org.'
                         ' alpn=http/1.1,h2 dohpath=/dns-query{?dns}'
                ),
            ])
        )

        recordset.validate()

    def test_alpn_without_dohpath(self):
        recordset = objects.RecordSet(
            name='example.org.', type='SVCB',
            records=objects.RecordList(objects=[
                objects.Record(
                    data='1 sample.example.org.'
                         ' alpn=http/1.1,h2'
                ),
            ])
        )

        recordset.validate()

    def test_parse_svcb(self):
        svcb_record = objects.SVCB()
        ipv61 = '2001:db8:3333:4444:5555:6666:7777:8888'
        ipv6hint = f'{ipv61},2001:db8:3333:4444:cccc:dddd:eeee:ffff'
        ipv4hint = "1.2.3.4,9.8.7.6"
        alpn = "h3,h2,http/1.1"
        port = "888"
        target = "sample.example.org."
        dohpath = '/dns-query{?dns}'
        svcb_record.from_string(f'1 {target} alpn={alpn}'
                                f' ipv4hint={ipv4hint} '
                                f'ipv6hint={ipv6hint} port={port}'
                                f' dohpath={dohpath}'
                                )

        self.assertEqual(1, svcb_record.priority)
        self.assertEqual(target, svcb_record.target)
        self.assertEqual(f"alpn={alpn}", svcb_record.alpn)
        self.assertEqual(f"ipv6hint={ipv6hint}", svcb_record.ipv6hint)
        self.assertEqual(f"ipv4hint={ipv4hint}", svcb_record.ipv4hint)
        self.assertEqual(f"port={port}", svcb_record.port)
        self.assertEqual(f"dohpath={dohpath}", svcb_record.dohpath)

    def test_no_valid_alpn(self):
        doh = "dohpath=/dns-query{?dns}"
        recordset = objects.RecordSet(
            name='example.org.', type='SVCB',
            records=objects.RecordList(objects=[
                objects.Record(data=f'1 sample.example.org. alpn=foo {doh}'),
            ])
        )

        self.assertRaises(InvalidObject, recordset.validate)

    def test_non_valid_port(self):
        recordset = objects.RecordSet(
            name='example.org.', type='SVCB',
            records=objects.RecordList(objects=[
                objects.Record(data='1 sample.example.org. port=foo'),
            ])
        )

        self.assertRaises(InvalidObject, recordset.validate)

    def test_ech(self):
        svcb_record = objects.SVCB()
        ipv4hint = "1.2.3.4"
        alpn = "h2"
        target = "sample.example.org."
        ech = base64.b64encode(target.encode()).decode()
        doh = '/dns-query{?dns}'
        svcb_record.from_string(f'1 {target} alpn={alpn}'
                                f' ipv4hint={ipv4hint}'
                                f' dohpath={doh}'
                                f' ech={ech}'
                                )

        self.assertEqual(1, svcb_record.priority)
        self.assertEqual(target, svcb_record.target)
        self.assertEqual(f"alpn={alpn}", svcb_record.alpn)
        self.assertEqual(f"ipv4hint={ipv4hint}", svcb_record.ipv4hint)
        self.assertEqual(f"ech={ech}", svcb_record.ech)

    def test_echconfig(self):
        alpn = "h3"
        target = "sample.example.org."
        ech = base64.b64encode(target.encode()).decode()

        recordset = objects.RecordSet(
            name='example.org.', type='SVCB',
            records=objects.RecordList(objects=[
                objects.Record(
                    data=f'1 sample.example.org.'
                         f' alpn={alpn} echconfig={ech}'),
            ])
        )
        self.assertRaises(InvalidObject, recordset.validate)

    def test_ech_validate(self):
        svcb_record = objects.SVCB()
        ipv4hint = "1.2.3.4"
        alpn = "h3"
        target = "sample.example.org."
        doh = '/dns-query{?dns}'
        ech = base64.b64encode(target.encode()).decode()
        svcb_record.from_string(f'1 {target} alpn={alpn}'
                                f' ipv4hint={ipv4hint}'
                                f' ech={ech}'
                                f' dohpath={doh}'
                                )

        self.assertEqual(1, svcb_record.priority)
        self.assertEqual(target, svcb_record.target)
        self.assertEqual(f"alpn={alpn}", svcb_record.alpn)
        self.assertEqual(f"ipv4hint={ipv4hint}", svcb_record.ipv4hint)
        self.assertEqual(f"ech={ech}", svcb_record.ech)

    def test_non_valid_ipv4hint(self):
        recordset = objects.RecordSet(
            name='example.org.', type='SVCB',
            records=objects.RecordList(objects=[
                objects.Record(
                    data='1 sample.example.org. ipv4hint=foo,192.168.1.2'
                ),
            ])
        )

        self.assertRaises(InvalidObject, recordset.validate)

    def test_escape_string_ech(self):
        recordset = objects.RecordSet(
            name='example.org.', type='SVCB',
            records=objects.RecordList(objects=[
                objects.Record(data='1 sample.example.org.'
                                    ' ech=foo//'),
            ])
        )

        self.assertRaises(InvalidObject, recordset.validate)

    def test_non_base64_ech(self):
        recordset = objects.RecordSet(
            name='example.org.', type='SVCB',
            records=objects.RecordList(objects=[
                objects.Record(data='1 sample.example.org.'
                                    ' ech=textstring'),
            ])
        )

        self.assertRaises(InvalidObject, recordset.validate)

    def test_non_valid_ipv6hint(self):
        recordset = objects.RecordSet(
            name='example.org.', type='SVCB',
            records=objects.RecordList(objects=[
                objects.Record(data='1 sample.example.org. ipv6hint=foo'),
            ])
        )

        self.assertRaises(InvalidObject, recordset.validate)

    def test_unsupported_param(self):
        recordset = objects.RecordSet(
            name='example.org.', type='SVCB',
            records=objects.RecordList(objects=[
                objects.Record(
                    data='1 sample.example.org. bazz=foo'
                ),
            ])
        )

        self.assertRaises(InvalidObject, recordset.validate)

    def test_doh(self):
        doh = '/dns-query{?dns}'
        recordset = objects.RecordSet(
            name='example.org.', type='SVCB',
            records=objects.RecordList(objects=[
                objects.Record(
                    data=f'1 sample.example.org. dohpath={doh}'
                ),
            ])
        )
        recordset.validate()

    def test_doh_not_relative(self):
        doh = 'dns-query{?dns}'
        recordset = objects.RecordSet(
            name='example.org.', type='SVCB',
            records=objects.RecordList(objects=[
                objects.Record(
                    data=f'1 sample.example.org. dohpath={doh}'
                ),
            ])
        )
        self.assertRaises(InvalidObject, recordset.validate)

    def test_doh_not_missed_dns(self):
        doh = '/dns-query{?test}'
        recordset = objects.RecordSet(
            name='example.org.', type='SVCB',
            records=objects.RecordList(objects=[
                objects.Record(
                    data=f'1 sample.example.org. dohpath={doh}'
                ),
            ])
        )
        self.assertRaises(InvalidObject, recordset.validate)

    def test_doh_short(self):
        doh = '/{dns}'
        recordset = objects.RecordSet(
            name='example.org.', type='SVCB',
            records=objects.RecordList(objects=[
                objects.Record(
                    data=f'1 sample.example.org. dohpath={doh}'
                ),
            ])
        )
        self.assertRaises(InvalidObject, recordset.validate)

    def test_no_doh_h3_alpn(self):
        recordset = objects.RecordSet(
            name='example.org.', type='SVCB',
            records=objects.RecordList(objects=[
                objects.Record(
                    data='1 sample.example.org. alpn=h3'
                ),
            ])
        )
        recordset.validate()

    def test_no_doh_h2_alpn(self):
        recordset = objects.RecordSet(
            name='example.org.', type='SVCB',
            records=objects.RecordList(objects=[
                objects.Record(
                    data='1 sample.example.org. alpn=h2'
                ),
            ])
        )
        recordset.validate()

    def test_no_doh_complex_alpn(self):
        recordset = objects.RecordSet(
            name='example.org.', type='SVCB',
            records=objects.RecordList(objects=[
                objects.Record(
                    data='1 sample.example.org. alpn=h3,h2,http/1.1'
                ),
            ])
        )
        recordset.validate()

    def test_escape_in_ech(self):
        recordset = objects.RecordSet(
            name='example.org.', type='HTTPS',
            records=objects.RecordList(objects=[
                objects.Record(
                    data='1 sample.example.org. port=8888 ech=foo//'
                ),
            ])
        )
        self.assertRaises(InvalidObject, recordset.validate)

    def test_dns_no_doh_h3_alpn(self):
        recordset = objects.RecordSet(
            name='_dns.example.org.', type='SVCB',
            records=objects.RecordList(objects=[
                objects.Record(
                    data='1 sample.example.org. alpn=h3'
                ),
            ])
        )
        self.assertRaises(InvalidObject, recordset.validate)

    def test_dns_no_doh_h2_alpn(self):
        recordset = objects.RecordSet(
            name='_dns.example.org.', type='SVCB',
            records=objects.RecordList(objects=[
                objects.Record(
                    data='1 sample.example.org. alpn=h2'
                ),
            ])
        )
        self.assertRaises(InvalidObject, recordset.validate)
