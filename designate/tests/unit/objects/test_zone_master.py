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


import oslotest.base

from designate import objects


class ZoneMasterTest(oslotest.base.BaseTestCase):
    def test_zone_master_from_data(self):
        zone_master = objects.ZoneMaster.from_data('192.0.2.2:5354')
        self.assertEqual('192.0.2.2', zone_master.host)
        self.assertEqual(5354, zone_master.port)

    def test_zone_master_to_data(self):
        zone_master = objects.ZoneMaster.from_data('192.0.2.2:5354')

        self.assertEqual('192.0.2.2:5354', zone_master.to_data())

    def test_zone_masters_from_list(self):
        zone_masters = objects.ZoneMasterList.from_list([
            {'host': '192.0.2.1', 'port': 5354, },
            {'host': '192.0.2.2', 'port': 5354, },
            {'host': '192.0.2.100', 'port': 5354, },
        ])

        self.assertEqual(3, len(zone_masters))

        for zone_master in zone_masters:
            self.assertIn('192.0.2.', zone_master.host)
            self.assertEqual(5354, zone_master.port)

    def test_zone_masters_to_list(self):
        zone_masters_payload = [
            {'host': '192.0.2.1', 'port': 53, },
            {'host': '192.0.2.100', 'port': 5354, },
        ]

        zone_masters = objects.ZoneMasterList.from_list(zone_masters_payload)

        self.assertEqual(2, len(zone_masters))

        for zone_master in zone_masters.to_list():
            self.assertIn(zone_master, zone_masters_payload)

    def test_zone_masters_to_data(self):
        expected_results = [
            '192.0.2.1:53',
            '192.0.2.2:5354'
        ]

        zone_masters = [
            {'host': '192.0.2.1', 'port': 53, },
            {'host': '192.0.2.2', 'port': 5354, },
        ]

        zone_masters = objects.ZoneMasterList.from_list(zone_masters)

        self.assertEqual(2, len(zone_masters))

        for zone_master in zone_masters.to_data():
            self.assertIn(zone_master, expected_results)
