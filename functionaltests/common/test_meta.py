"""
Copyright 2015 Rackspace

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from functionaltests.api.v2.models.recordset_model import RecordsetModel
from functionaltests.common.models import ZoneFile
from functionaltests.common.models import ZoneFileRecord

import tempest_lib.base


class MetaTest(tempest_lib.base.BaseTestCase):

    def test_zone_file_model_meta_test(self):
        zone_file = ZoneFile.from_text(
            """
            $ORIGIN mydomain.com.
            $TTL 1234

            mydomain.com.  IN NS ns1.example.com.
            mydomain.com.  IN SOA ns1.example.com. mail.mydomain.com. 1 2 3 4 5
            """)
        self.assertEqual('mydomain.com.', zone_file.origin)
        self.assertEqual(1234, zone_file.ttl)

        ns_record = ZoneFileRecord(
            name='mydomain.com.', type='NS', data='ns1.example.com.')
        soa_record = ZoneFileRecord(
            name='mydomain.com.', type='SOA',
            data='ns1.example.com. mail.mydomain.com. 1 2 3 4 5')

        self.assertEqual(zone_file.records[0], ns_record)
        self.assertEqual(zone_file.records[1], soa_record)

    def test_zone_file_record_model_meta_test(self):
        record = ZoneFileRecord(name='one.com.', type='A', data='1.2.3.4')
        wrong_name = ZoneFileRecord(name='two.com.', type='A', data='1.2.3.4')
        wrong_type = ZoneFileRecord(name='one.com.', type='MX', data='1.2.3.4')
        wrong_data = ZoneFileRecord(name='one.com.', type='A', data='1.2.3.5')

        self.assertEqual(record, record)
        self.assertNotEqual(record, wrong_name)
        self.assertNotEqual(record, wrong_type)
        self.assertNotEqual(record, wrong_data)

    def test_zone_file_records_from_recordset(self):
        # we don't need all of the recordset's fields here
        recordset = RecordsetModel.from_dict({
            "type": "NS",
            "name": "mydomain.com.",
            "records": ["ns1.a.com.", "ns2.a.com.", "ns3.a.com."],
        })

        records = ZoneFileRecord.records_from_recordset(recordset)
        expected = [
            ZoneFileRecord(name="mydomain.com.", type="NS", data="ns1.a.com."),
            ZoneFileRecord(name="mydomain.com.", type="NS", data="ns2.a.com."),
            ZoneFileRecord(name="mydomain.com.", type="NS", data="ns3.a.com."),
        ]
        self.assertEqual(expected, records)
