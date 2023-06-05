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

from designate import exceptions
from designate import objects

LOG = logging.getLogger(__name__)


class RRDataAAAATest(oslotest.base.BaseTestCase):
    def test_valid_aaaa_record(self):
        recordset = objects.RecordSet(
            name='www.example.test.', type='AAAA',
            records=objects.RecordList(objects=[
                objects.Record(data='2001:db8:0:1::1'),
            ])
        )
        recordset.validate()

    def test_reject_a_record(self):
        recordset = objects.RecordSet(
            name='www.example.test.', type='AAAA',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.1'),
            ])
        )
        self.assertRaisesRegex(
            exceptions.InvalidObject,
            'Provided object does not match schema',
            recordset.validate
        )

    def test_reject_invalid_data(self):
        recordset = objects.RecordSet(
            name='www.example.test.', type='AAAA',
            records=objects.RecordList(objects=[
                objects.Record(data='TXT'),
            ])
        )
        self.assertRaisesRegex(
            exceptions.InvalidObject,
            'Provided object does not match schema',
            recordset.validate
        )
