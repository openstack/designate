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


class RRDataPTRTest(oslotest.base.BaseTestCase):
    def test_ptr_record(self):
        recordset = objects.RecordSet(
            name='ptr.example.org.', type='PTR',
            records=objects.RecordList(objects=[
                objects.Record(data='1.2.0.192.in-addr.arpa.'),
            ])
        )

        recordset.validate()

        self.assertEqual('ptr.example.org.', recordset.name)
        self.assertEqual('1.2.0.192.in-addr.arpa.',
                         recordset.records[0].data)
        self.assertEqual('PTR', recordset.type)

    def test_ptr_invalid_data(self):
        recordset = objects.RecordSet(
            name='ptr.example.org.', type='PTR',
            records=objects.RecordList(objects=[
                objects.Record(data='invalid_data'),
            ])
        )

        self.assertRaisesRegex(
            exceptions.InvalidObject,
            'Provided object does not match schema',
            recordset.validate
        )
