# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hpe.com>
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

import datetime

from oslo_log import log as logging
from oslo_utils import timeutils

from designate.storage.impl_sqlalchemy import tables
from designate.tests import TestCase
from designate.tests import fixtures
from designate.producer import tasks


LOG = logging.getLogger(__name__)


class TaskTest(TestCase):
    def setUp(self):
        super(TaskTest, self).setUp()

    def _enable_tasks(self, tasks):
        self.config(
            enabled_tasks=tasks,
            group="service:producer")


class DeletedzonePurgeTest(TaskTest):
    def setUp(self):
        super(DeletedzonePurgeTest, self).setUp()

        self.config(
            interval=3600,
            time_threshold=604800,
            batch_size=100,
            group="producer_task:zone_purge"
        )

        self.purge_task_fixture = self.useFixture(
            fixtures.ZoneManagerTaskFixture(tasks.DeletedZonePurgeTask)
        )

    def _create_deleted_zone(self, name, mock_deletion_time):
        # Create a zone and set it as deleted
        zone = self.create_zone(name=name)
        self._delete_zone(zone, mock_deletion_time)
        return zone

    def _fetch_all_zones(self):
        # Fetch all zones including deleted ones
        query = tables.zones.select()
        return self.central_service.storage.session.execute(query).fetchall()

    def _delete_zone(self, zone, mock_deletion_time):
        # Set a zone as deleted
        zid = zone.id.replace('-', '')
        query = tables.zones.update().\
            where(tables.zones.c.id == zid).\
            values(
                action='NONE',
                deleted=zid,
                deleted_at=mock_deletion_time,
                status='DELETED',
        )

        pxy = self.central_service.storage.session.execute(query)
        self.assertEqual(1, pxy.rowcount)
        return zone

    def _create_deleted_zones(self):
        # Create a number of deleted zones in the past days
        zones = []
        now = timeutils.utcnow()
        for age in range(18):
            age *= (24 * 60 * 60)  # seconds
            delta = datetime.timedelta(seconds=age)
            deletion_time = now - delta
            name = "example%d.org." % len(zones)
            z = self._create_deleted_zone(name, deletion_time)
            zones.append(z)

        return zones

    def test_purge_zones(self):
        # Create 18 zones, run producer, check if 7 zones are remaining
        self.config(quota_zones=1000)
        self._create_deleted_zones()

        self.purge_task_fixture.task()

        zones = self._fetch_all_zones()
        LOG.info("Number of zones: %d", len(zones))
        self.assertEqual(7, len(zones))


class PeriodicGenerateDelayedNotifyTaskTest(TaskTest):

    def setUp(self):
        super(PeriodicGenerateDelayedNotifyTaskTest, self).setUp()

        self.config(
            interval=5,
            batch_size=100,
            group="producer_task:delayed_notify"
        )

        self.generate_delayed_notify_task_fixture = self.useFixture(
            fixtures.ZoneManagerTaskFixture(
                tasks.PeriodicGenerateDelayedNotifyTask
            )
        )

    def _fetch_zones(self, query=None):
        # Fetch zones including deleted ones
        if query is None:
            query = tables.zones.select()
        return self.central_service.storage.session.execute(query).fetchall()

    def _create_zones(self):
        # Create a number of zones; half of them with delayed_notify set
        for age in range(20):
            name = "example%d.org." % age
            delayed_notify = (age % 2 == 0)
            self.create_zone(
                name=name,
                delayed_notify=delayed_notify,
            )

    def test_generate_delayed_notify_zones(self):
        # Create zones and set some of them as pending update.
        self.generate_delayed_notify_task_fixture.task()
        self.config(quota_zones=1000)
        self.config(
            interval=1,
            batch_size=5,
            group="producer_task:delayed_notify"
        )
        self._create_zones()
        zones = self._fetch_zones(tables.zones.select().where(
            tables.zones.c.delayed_notify == True))  # nopep8
        self.assertEqual(10, len(zones))

        self.generate_delayed_notify_task_fixture.task()

        zones = self._fetch_zones(tables.zones.select().where(
            tables.zones.c.delayed_notify == True))  # nopep8
        self.assertEqual(5, len(zones))

        # Run the task and check if it reset the delayed_notify flag
        self.generate_delayed_notify_task_fixture.task()

        zones = self._fetch_zones(tables.zones.select().where(
            tables.zones.c.delayed_notify == True))  # nopep8
        self.assertEqual(0, len(zones))
