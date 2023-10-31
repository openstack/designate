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

from designate.common.decorators import lock
from designate import objects


class TestExtractZoneId(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_extract_zone_id_empty(self):
        self.assertIsNone(lock.extract_zone_id([], {}))

    def test_extract_zone_id_no_valid_objects(self):
        self.assertIsNone(
            lock.extract_zone_id([], {
                'ptr': objects.PTRList(), 'a': objects.AList()})
        )

    def test_extract_zone_id_kwargs(self):
        self.assertEqual(
            'test',
            lock.extract_zone_id([], {'zone_id': 'test'})
        )
        self.assertEqual(
            'test',
            lock.extract_zone_id([], {'zone': mock.Mock(id='test')})
        )
        self.assertEqual(
            'test',
            lock.extract_zone_id([], {'recordset': mock.Mock(zone_id='test')})
        )
        self.assertEqual(
            'test',
            lock.extract_zone_id([], {'record': mock.Mock(zone_id='test')})
        )

    def test_extract_zone_id_from_zone(self):
        self.assertEqual(
            '123',
            lock.extract_zone_id(['a', 'b', 'c'], {'x': objects.Zone(id=123)})
        )
        self.assertEqual(
            '123',
            lock.extract_zone_id([objects.Zone(id=123)], {})
        )

    def test_extract_zone_id_from_recordset(self):
        self.assertEqual(
            '123',
            lock.extract_zone_id([], {'x': objects.RecordSet(zone_id=123)})
        )
        self.assertEqual(
            '123',
            lock.extract_zone_id([objects.RecordSet(zone_id=123)], {})
        )

    def test_extract_zone_id_from_record(self):
        self.assertEqual(
            '123',
            lock.extract_zone_id([], {'x': objects.Record(zone_id=123)})
        )
        self.assertEqual(
            '123',
            lock.extract_zone_id([objects.Record(zone_id=123)], {})
        )

    def test_extract_zone_id_from_zone_transfer_request(self):
        self.assertEqual(
            '123',
            lock.extract_zone_id(
                [], {'x': objects.ZoneTransferRequest(zone_id=123)})
        )
        self.assertEqual(
            '123',
            lock.extract_zone_id(
                [objects.ZoneTransferRequest(zone_id=123)], {})
        )

    def test_extract_zone_id_from_zone_transfer_accept(self):
        self.assertEqual(
            '123',
            lock.extract_zone_id(
                [], {'x': objects.ZoneTransferAccept(zone_id=123)})
        )
        self.assertEqual(
            '123',
            lock.extract_zone_id([objects.ZoneTransferAccept(zone_id=123)], {})
        )

    def test_extract_zone_id_from_second_argument(self):
        self.assertEqual('456', lock.extract_zone_id(['123', '456'], {}))

    def test_extract_zone_id_when_second_argument_is_a_zone(self):
        self.assertEqual(
            '456', lock.extract_zone_id(['123', objects.Zone(id=456)], {})
        )
