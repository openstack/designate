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

from oslo_concurrency import lockutils
from oslo_log import log as logging
from oslo_utils import uuidutils
import oslotest.base

from designate.common.decorators import lock
from designate import exceptions
from designate.objects import record
from designate.objects import zone

LOG = logging.getLogger(__name__)


class FakeCoordination:
    def get_lock(self, name):
        return lockutils.lock(name)


class FakeService:
    def __init__(self):
        self.zone_lock_local = lock.ZoneLockLocal()
        self.coordination = FakeCoordination()


class CentralDecoratorTests(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.context = mock.Mock()
        self.service = FakeService()

    def test_synchronized_zone_exception_raised(self):
        @lock.synchronized_zone()
        def mock_get_zone(cls, current_index, zone_obj):
            self.assertEqual(
                {f'zone-{zone_obj.id}'.encode('ascii')},
                cls.zone_lock_local._held
            )
            if current_index % 3 == 0:
                raise exceptions.ZoneNotFound()

        for index in range(9):
            try:
                mock_get_zone(
                    self.service, index,
                    zone.Zone(id=uuidutils.generate_uuid())
                )
            except exceptions.ZoneNotFound:
                pass

    def test_synchronized_new_zone_with_recursion(self):
        @lock.synchronized_zone(new_zone=True)
        def mock_create_zone(cls, context):
            self.assertEqual({b'create-new-zone'}, cls.zone_lock_local._held)
            mock_create_record(
                cls, context, zone.Zone(id=uuidutils.generate_uuid())
            )

        @lock.synchronized_zone()
        def mock_create_record(cls, context, zone_obj):
            self.assertIn(
                f'zone-{zone_obj.id}'.encode('ascii'),
                cls.zone_lock_local._held
            )
            self.assertIn(b'create-new-zone', cls.zone_lock_local._held)

        mock_create_zone(
            self.service, self.context
        )

    def test_synchronized_zone_recursive_decorator_call(self):
        @lock.synchronized_zone()
        def mock_create_record(cls, context, record_obj):
            self.assertEqual(
                {f'zone-{record_obj.zone_id}'.encode('ascii')},
                cls.zone_lock_local._held
            )
            mock_get_zone(cls, context, zone.Zone(id=record_obj.zone_id))

        @lock.synchronized_zone()
        def mock_get_zone(cls, context, zone_obj):
            self.assertEqual(
                {f'zone-{zone_obj.id}'.encode('ascii')},
                cls.zone_lock_local._held
            )

        mock_create_record(
            self.service, self.context,
            record_obj=record.Record(zone_id=uuidutils.generate_uuid())
        )
        mock_get_zone(
            self.service, self.context,
            zone_obj=zone.Zone(id=uuidutils.generate_uuid())
        )

    def test_synchronized_zone_raises_exception_when_no_zone_provided(self):
        @lock.synchronized_zone(new_zone=False)
        def mock_not_creating_new_zone(cls, context, record_obj):
            pass

        self.assertRaisesRegex(
            Exception,
            'Failed to determine zone id for synchronized operation',
            mock_not_creating_new_zone, self.service, mock.Mock(), None
        )
