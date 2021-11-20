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

from designate.central import service
from designate import exceptions
from designate.objects import record
from designate.objects import zone
from designate.tests.test_central import CentralTestCase
from designate import utils

LOG = logging.getLogger(__name__)


class FakeCoordination(object):
    def get_lock(self, name):
        return lockutils.lock(name)


class CentralDecoratorTests(CentralTestCase):
    def test_synchronized_zone_exception_raised(self):
        @service.synchronized_zone()
        def mock_get_zone(cls, index, zone):
            self.assertEqual(service.ZONE_LOCKS.held, {zone.id})
            if index % 3 == 0:
                raise exceptions.ZoneNotFound()

        for index in range(9):
            try:
                mock_get_zone(mock.Mock(coordination=FakeCoordination()),
                              index,
                              zone.Zone(id=utils.generate_uuid()))
            except exceptions.ZoneNotFound:
                pass

    def test_synchronized_zone_recursive_decorator_call(self):
        @service.synchronized_zone()
        def mock_create_record(cls, context, record):
            self.assertEqual(service.ZONE_LOCKS.held, {record.zone_id})
            mock_get_zone(cls, context, zone.Zone(id=record.zone_id))

        @service.synchronized_zone()
        def mock_get_zone(cls, context, zone):
            self.assertEqual(service.ZONE_LOCKS.held, {zone.id})

        mock_create_record(mock.Mock(coordination=FakeCoordination()),
                           self.get_context(),
                           record=record.Record(zone_id=utils.generate_uuid()))
        mock_get_zone(mock.Mock(coordination=FakeCoordination()),
                      self.get_context(),
                      zone=zone.Zone(id=utils.generate_uuid()))

    def test_synchronized_zone_raises_exception_when_no_zone_provided(self):
        @service.synchronized_zone(new_zone=False)
        def mock_not_creating_new_zone(cls, context, record):
            pass

        self.assertRaisesRegex(
            Exception,
            'Failed to determine zone id for '
            'synchronized operation',
            mock_not_creating_new_zone, self.get_context(), None
        )
