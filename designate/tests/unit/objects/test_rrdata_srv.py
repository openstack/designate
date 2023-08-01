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


class RRDataSRVTest(oslotest.base.BaseTestCase):
    def test_srv_record(self):
        recordset = objects.RecordSet(
            name='_sip._tcp.example.org.', type='SRV',
            records=objects.RecordList(objects=[
                objects.Record(data='10 0 5060 server1.example.org.'),
            ])
        )

        recordset.validate()

        self.assertEqual('_sip._tcp.example.org.', recordset.name)
        self.assertEqual('SRV', recordset.type)

    def test_srv_invalid_data(self):
        recordset = objects.RecordSet(
            name='_sip._tcp.example.org.', type='SRV',
            records=objects.RecordList(objects=[
                objects.Record(data='10 0'),
            ])
        )

        self.assertRaisesRegex(
            exceptions.InvalidObject,
            'Provided object does not match schema',
            recordset.validate
        )

    def test_srv_invalid_srv_name(self):
        recordset = objects.RecordSet(
            name='_sip.tcp.example.org.', type='SRV',
            records=objects.RecordList(objects=[
                objects.Record(data='10 0'),
            ])
        )

        self.assertRaisesRegex(
            exceptions.InvalidObject,
            'name is invalid',
            recordset.validate
        )
