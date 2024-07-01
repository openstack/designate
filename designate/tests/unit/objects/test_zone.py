# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Federico Ceratto <federico.ceratto@hpe.com>
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
import unittest

from oslo_log import log as logging
from oslo_utils import uuidutils
import oslotest.base

from designate import exceptions
from designate import objects

LOG = logging.getLogger(__name__)


def create_test_zone():
    return objects.Zone(
        id=uuidutils.generate_uuid(),
        name='www.example.org.',
        email='foo@example.com',
    )


class ZoneTest(oslotest.base.BaseTestCase):
    def test_init(self):
        zone = create_test_zone()
        self.assertEqual('www.example.org.', zone.name)

    def test_masters_none(self):
        zone = objects.Zone()
        self.assertRaisesRegex(
            exceptions.RelationNotLoaded,
            'masters is not loaded on Zone',
            lambda: zone.masters
        )

    def test_masters(self):
        zone = objects.Zone(
            masters=objects.ZoneMasterList.from_list([
                {'host': '192.0.2.1', 'port': 53}
            ])
        )
        self.assertEqual(
            [{'host': '192.0.2.1', 'port': 53}], zone.masters.to_list())

    def test_masters_2(self):
        zone = objects.Zone(
            masters=objects.ZoneMasterList.from_list([
                {'host': '192.0.2.1'},
                {'host': '192.0.2.2'}
            ])
        )
        self.assertEqual(2, len(zone.masters))

    def test_get_master_by_ip(self):
        zone = objects.Zone(
            masters=objects.ZoneMasterList.from_list([
                {'host': '192.0.2.1', 'port': 53},
                {'host': '192.0.2.2', 'port': 53}
            ])
        )
        m = zone.get_master_by_ip('192.0.2.2').to_data()

        self.assertEqual('192.0.2.2:53', m)

    @unittest.expectedFailure  # bug: zone.masters is not iterable
    def test_get_master_by_ip_none(self):
        zone = objects.Zone()
        master = zone.get_master_by_ip('192.0.2.2')
        self.assertFalse(master)

    def test_validate(self):
        zone = create_test_zone()
        zone.validate()

    def test_validate_invalid_secondary(self):
        zone = objects.Zone(
            type='SECONDARY',
        )
        self.assertRaisesRegex(
            exceptions.InvalidObject,
            'Provided object does not match schema',
            zone.validate
        )

    def test_validate_primary_with_masters(self):
        masters = objects.ZoneMasterList()
        masters.append(objects.ZoneMaster.from_data("192.0.2.1:53"))
        zone = objects.Zone(
            name='example.com.',
            type='PRIMARY',
            email="foo@example.com",
            masters=masters
        )
        self.assertRaisesRegex(
            exceptions.InvalidObject,
            'Provided object does not match schema',
            zone.validate
        )

    def test_validate_primary_no_email(self):
        zone = objects.Zone(
            name='example.com.',
            type='PRIMARY',
        )
        self.assertRaisesRegex(
            exceptions.InvalidObject,
            'Provided object does not match schema',
            zone.validate
        )

    def test_validate_secondary_with_email(self):
        masters = objects.ZoneMasterList()
        masters.append(objects.ZoneMaster.from_data("192.0.2.1:53"))
        zone = objects.Zone(
            name='example.com.',
            type='SECONDARY',
            email="foo@example.com",
            masters=masters
        )
        self.assertRaisesRegex(
            exceptions.InvalidObject,
            'Provided object does not match schema',
            zone.validate
        )

    def test_validate_secondary_with_ttl(self):
        masters = objects.ZoneMasterList()
        masters.append(objects.ZoneMaster.from_data("192.0.2.1:53"))
        zone = objects.Zone(
            name='example.com.',
            type='SECONDARY',
            ttl=600,
            masters=masters
        )
        self.assertRaisesRegex(
            exceptions.InvalidObject,
            'Provided object does not match schema',
            zone.validate
        )

    def test_validate_secondary_with_masters_empty_list(self):
        masters = objects.ZoneMasterList()
        zone = objects.Zone(
            name='example.com.',
            type='SECONDARY',
            masters=masters
        )
        self.assertRaisesRegex(
            exceptions.InvalidObject,
            'Provided object does not match schema',
            zone.validate
        )

    def test_validate_secondary_with_masters_none(self):
        zone = objects.Zone(
            name='example.com.',
            type='SECONDARY',
            masters=None
        )

        self.assertRaisesRegex(
            exceptions.InvalidObject,
            'Provided object does not match schema',
            zone.validate
        )

    def test_include_shard_id_in_string_representation(self):
        zone = objects.Zone(
            name='example.org.',
            type='PRIMARY',
            email='foo@example.com',
            shard=4095
        )
        zone.validate()

        self.assertIn("shard:'4095'", str(zone))
