# Copyright 2016 Rackspace
#
# Author: Rahman Syed <rahman.syed@gmail.com>
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


class RRDataMXTest(oslotest.base.BaseTestCase):
    def test_parse_mx(self):
        mx_record = objects.MX()
        mx_record.from_string('0 mail.example.org.')

        self.assertEqual(0, mx_record.priority)
        self.assertEqual('mail.example.org.', mx_record.exchange)

    def test_validate_mx_signed_zero(self):
        record_set = objects.RecordSet(
            name='www.example.org.', type='MX',
            records=objects.RecordList(objects=[
                objects.Record(data='-0 mail.example.test.',
                               status='ACTIVE'),
            ])
        )

        self.assertRaises(InvalidObject, record_set.validate)

    def test_validate_mx_not_fqdn(self):
        record_set = objects.RecordSet(
            name='www.example.org.', type='MX',
            records=objects.RecordList(objects=[
                objects.Record(data='10 mail.example.test',
                               status='ACTIVE'),
            ])
        )

        self.assertRaises(InvalidObject, record_set.validate)
