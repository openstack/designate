# Copyright 2021 Cloudification GmbH
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

from designate import objects

LOG = logging.getLogger(__name__)


class RRDataCERTTest(oslotest.base.BaseTestCase):
    def test_cert_record(self):
        recordset = objects.RecordSet(
            name='example.org.', type='CERT',
            records=objects.RecordList(objects=[
                objects.Record(
                    data=(
                        '1 1 255 KR1L0GbocaIOOim1+qdHtOSrDcOsGiI2NCcxuX2/Tqc='
                    )
                ),
            ])
        )

        recordset.validate()

        self.assertEqual('example.org.', recordset.name)
        self.assertEqual(
            '1 1 255 KR1L0GbocaIOOim1+qdHtOSrDcOsGiI2NCcxuX2/Tqc=',
            recordset.records[0].data
        )
        self.assertEqual('CERT', recordset.type)

    def test_parse_cert(self):
        cert_record = objects.CERT()
        cert_record.from_string(
            'DPKIX 1 RSASHA256 KR1L0GbocaIOOim1+qdHtOSrDcOsGiI2NCcxuX2/Tqc='
        )

        self.assertEqual('DPKIX', cert_record.cert_type)
        self.assertEqual(1, cert_record.key_tag)
        self.assertEqual('RSASHA256', cert_record.cert_algo)
        self.assertEqual(
            'KR1L0GbocaIOOim1+qdHtOSrDcOsGiI2NCcxuX2/Tqc=',
            cert_record.certificate
        )

    def test_parse_invalid_cert_type_value(self):
        cert_record = objects.CERT()
        self.assertRaisesRegex(
            ValueError,
            'Cert type value should be between 0 and 65535',
            cert_record.from_string,
            '99999 1 RSASHA256 KR1L0GbocaIOOim1+qdHtOSrDcOsGiI2NCcxuX2/Tqc='
        )

    def test_parse_invalid_cert_type_mnemonic(self):
        cert_record = objects.CERT()
        self.assertRaisesRegex(
            ValueError,
            'Cert type is not valid Mnemonic.',
            cert_record.from_string,
            'FAKETYPE 1 RSASHA256 KR1L0GbocaIOOim1+qdHtOSrDcOsGiI2NCcxuX2/Tqc='
        )

    def test_parse_invalid_cert_algo_value(self):
        cert_record = objects.CERT()
        self.assertRaisesRegex(
            ValueError,
            'Cert algorithm value should be between 0 and 255',
            cert_record.from_string,
            'DPKIX 1 256 KR1L0GbocaIOOim1+qdHtOSrDcOsGiI2NCcxuX2/Tqc='
        )

    def test_parse_invalid_cert_algo_mnemonic(self):
        cert_record = objects.CERT()
        self.assertRaisesRegex(
            ValueError,
            'Cert algorithm is not valid Mnemonic.',
            cert_record.from_string,
            'DPKIX 1 FAKESHA256 KR1L0GbocaIOOim1+qdHtOSrDcOsGiI2NCcxuX2/Tqc='
        )

    def test_parse_invalid_cert_certificate(self):
        cert_record = objects.CERT()
        self.assertRaisesRegex(
            ValueError,
            'Cert certificate is not valid.',
            cert_record.from_string,
            'DPKIX 1 RSASHA256 KR1L0GbocaIOOim1+qdHtOSrDcOsGiI2NCcxuX2/Tqc'
        )
