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
from unittest import mock

import fixtures
from oslo_config import cfg
from oslo_config import fixture as cfg_fixture
from oslo_log import log as logging
from oslo_utils import timeutils
from oslo_utils import uuidutils
import oslotest.base

from designate.central import rpcapi as central_api
import designate.conf
from designate import context
from designate.producer import tasks
from designate import rpc
from designate.tests import base_fixtures
from designate.tests.unit import RoObject
from designate.tests.unit import RwObject
from designate.worker import rpcapi as worker_api


DUMMY_TASK_GROUP = cfg.OptGroup(
    name='producer_task:dummy',
    title='Configuration for Producer Task: Dummy Task'
)
DUMMY_TASK_OPTS = [
    cfg.IntOpt('per_page', default=100,
               help='Default amount of results returned per page'),
]

CONF = designate.conf.CONF
CONF.register_group(DUMMY_TASK_GROUP)
CONF.register_opts(DUMMY_TASK_OPTS, group=DUMMY_TASK_GROUP)
LOG = logging.getLogger(__name__)


class DummyTask(tasks.PeriodicTask):
    """Dummy task used to test helper functions"""
    __plugin_name__ = 'dummy'


class PeriodicTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

        self.task = DummyTask()
        self.task.my_partitions = range(0, 10)

    @mock.patch.object(central_api.CentralAPI, 'get_instance')
    def test_iter_zones_no_items(self, get_central):
        # Test that the iteration code is working properly.
        central = mock.Mock()
        get_central.return_value = central

        ctxt = mock.Mock()
        iterer = self.task._iter_zones(ctxt)

        central.find_zones.return_value = []

        self.assertRaises(StopIteration, next, iterer)

    @mock.patch.object(central_api.CentralAPI, 'get_instance')
    def test_iter_zones(self, get_central):
        # Test that the iteration code is working properly.
        central = mock.Mock()
        get_central.return_value = central

        ctxt = mock.Mock()
        iterer = self.task._iter_zones(ctxt)

        items = [RoObject(id=uuidutils.generate_uuid()) for i in range(0, 5)]
        central.find_zones.return_value = items

        # Iterate through the items causing the "paging" to be done.
        list(map(lambda i: next(iterer), items))
        central.find_zones.assert_called_once_with(
            ctxt, {"shard": "BETWEEN 0,9"}, limit=100)

        central.find_zones.reset_mock()

        # Call next on the iterator and see it trying to load a new page.
        # Also this will raise a StopIteration since there are no more items.
        central.find_zones.return_value = []
        self.assertRaises(StopIteration, next, iterer)

        central.find_zones.assert_called_once_with(
            ctxt,
            {"shard": "BETWEEN 0,9"},
            marker=items[-1].id,
            limit=100
        )

    def test_my_range(self):
        self.assertEqual((0, 9), self.task._my_range())


class PeriodicExistsTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

        CONF.set_override('interval', 5, 'producer_task:periodic_exists')

        # Mock a ctxt...
        self.ctxt = mock.Mock()
        self.useFixture(fixtures.MockPatchObject(
            context.DesignateContext, 'get_admin_context',
            return_value=self.ctxt
        ))

        # Patch get_notifier so that it returns a mock..
        self.mock_notifier = mock.Mock()
        self.useFixture(fixtures.MockPatchObject(
            rpc, 'get_notifier',
            return_value=self.mock_notifier
        ))

        self.task = tasks.PeriodicExistsTask()
        self.task.my_partitions = range(0, 10)

        # Install our own period results to verify that the end / start is
        # correct below
        self.period = tasks.PeriodicExistsTask._get_period(2)
        self.period_data = {
            "audit_period_beginning": self.period[0],
            "audit_period_ending": self.period[1]
        }
        self.useFixture(fixtures.MockPatchObject(
            tasks.PeriodicExistsTask, '_get_period',
            return_value=self.period
        ))

    def test_emit_exists(self):
        zone = RoObject(id=uuidutils.generate_uuid())

        with mock.patch.object(self.task, '_iter_zones') as iter_:
            iter_.return_value = [zone]
            self.task()

        data = dict(zone)
        data.update(self.period_data)

        # Ensure both the old (domain) and new (zone) events are fired
        # until the old is fully deprecated.
        self.mock_notifier.info.assert_any_call(
            self.ctxt, "dns.domain.exists", data)

        self.mock_notifier.info.assert_any_call(
            self.ctxt, "dns.zone.exists", data)

    def test_emit_exists_no_zones(self):
        with mock.patch.object(self.task, '_iter_zones') as iter_:
            iter_.return_value = []
            self.task()

        self.assertFalse(self.mock_notifier.info.called)

    def test_emit_exists_multiple_zones(self):
        zones = [RoObject()] * 10
        with mock.patch.object(self.task, '_iter_zones') as iter_:
            iter_.return_value = zones
            self.task()

        for zone in zones:
            data = dict(zone)
            data.update(self.period_data)

            # Ensure both the old (domain) and new (zone) events are fired
            # until the old is fully deprecated.
            self.mock_notifier.info.assert_any_call(
                self.ctxt, "dns.domain.exists", data)

            self.mock_notifier.info.assert_any_call(
                self.ctxt, "dns.zone.exists", data)


class PeriodicSecondaryRefreshTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

        # Mock a ctxt...
        self.ctxt = mock.Mock()
        self.useFixture(fixtures.MockPatchObject(
            context.DesignateContext, 'get_admin_context',
            return_value=self.ctxt
        ))

        # Mock a central...
        self.central = mock.Mock()
        self.useFixture(fixtures.MockPatchObject(
            central_api.CentralAPI, 'get_instance',
            return_value=self.central
        ))

        self.task = tasks.PeriodicSecondaryRefreshTask()
        self.task.my_partitions = 0, 9

    def test_refresh_no_zone(self):
        with mock.patch.object(self.task, '_iter') as _iter:
            _iter.return_value = []
            self.task()

        self.assertFalse(self.central.xfr_zone.called)

    def test_transferred_at_is_none(self):
        zone = RoObject(
            id=uuidutils.generate_uuid(),
            transferred_at=None,
            refresh=3600
        )

        with mock.patch.object(self.task, '_iter') as _iter:
            _iter.return_value = [zone]
            self.task()

        self.assertFalse(self.central.xfr_zone.called)

    def test_refresh_zone(self):
        transferred = timeutils.utcnow(True) - datetime.timedelta(minutes=62)
        zone = RoObject(
            id=uuidutils.generate_uuid(),
            transferred_at=transferred,
            refresh=3600
        )

        with mock.patch.object(self.task, '_iter') as _iter:
            _iter.return_value = [zone]
            self.task()

        self.central.xfr_zone.assert_called_once_with(self.ctxt, zone.id)

    def test_refresh_zone_not_expired(self):
        # Dummy zone object
        transferred = timeutils.utcnow(True) - datetime.timedelta(minutes=50)
        zone = RoObject(
            id=uuidutils.generate_uuid(),
            transferred_at=transferred,
            refresh=3600
        )

        with mock.patch.object(self.task, '_iter') as _iter:
            _iter.return_value = [zone]
            self.task()

        self.assertFalse(self.central.xfr_zone.called)


class PeriodicIncrementSerialTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

        self.central_api = mock.Mock()
        self.context = mock.Mock()
        self.worker_api = mock.Mock()
        mock.patch.object(worker_api.WorkerAPI, 'get_instance',
                          return_value=self.worker_api).start()
        mock.patch.object(central_api.CentralAPI, 'get_instance',
                          return_value=self.central_api).start()
        mock.patch.object(context.DesignateContext, 'get_admin_context',
                          return_value=self.context).start()
        self.central_api.increment_zone_serial.return_value = 123
        self.task = tasks.PeriodicIncrementSerialTask()
        self.task.my_partitions = 0, 9

    def test_increment_zone(self):
        zone = RoObject(
            id=uuidutils.generate_uuid(),
            action='CREATE',
            increment_serial=True,
            delayed_notify=False,
        )
        self.central_api.find_zones.return_value = [zone]

        self.task()

        self.central_api.increment_zone_serial.assert_called()
        self.worker_api.update_zone.assert_called()

    def test_increment_zone_with_action_none(self):
        zone = RwObject(
            id=uuidutils.generate_uuid(),
            action='NONE',
            status='ACTIVE',
            increment_serial=True,
            delayed_notify=False,
        )
        self.central_api.find_zones.return_value = [zone]

        self.task()

        self.central_api.increment_zone_serial.assert_called()
        self.worker_api.update_zone.assert_called()

        self.assertEqual('UPDATE', zone.action)
        self.assertEqual('PENDING', zone.status)

    def test_increment_zone_with_delayed_notify(self):
        zone = RoObject(
            id=uuidutils.generate_uuid(),
            action='CREATE',
            increment_serial=True,
            delayed_notify=True,
        )
        self.central_api.find_zones.return_value = [zone]

        self.task()

        self.central_api.increment_zone_serial.assert_called()
        self.worker_api.update_zone.assert_not_called()

    def test_increment_zone_skip_deleted(self):
        zone = RoObject(
            id=uuidutils.generate_uuid(),
            action='DELETE',
            increment_serial=True,
            delayed_notify=False,
        )
        self.central_api.find_zones.return_value = [zone]

        self.task()

        self.central_api.increment_zone_serial.assert_not_called()
        self.worker_api.update_zone.assert_not_called()


class PeriodicGenerateDelayedNotifyTaskTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))
        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(self.stdlog)

        self.central_api = mock.Mock()
        self.context = mock.Mock()
        self.worker_api = mock.Mock()
        mock.patch.object(worker_api.WorkerAPI, 'get_instance',
                          return_value=self.worker_api).start()
        mock.patch.object(central_api.CentralAPI, 'get_instance',
                          return_value=self.central_api).start()
        mock.patch.object(context.DesignateContext, 'get_admin_context',
                          return_value=self.context).start()
        self.task = tasks.PeriodicGenerateDelayedNotifyTask()
        self.task.my_partitions = 0, 9

    def test_zone_action_none(self):
        zone = RwObject(
            id='a6c7dcc6-8070-481b-8d5a-310100f5fc31',
            action='NONE',
            status='ACTIVE',
            increment_serial=False,
            delayed_notify=True,
        )
        self.central_api.find_zones.return_value = [zone]

        self.task()

        self.assertEqual('UPDATE', zone.action)
        self.assertEqual('PENDING', zone.status)

    def test_skip_deleted_zone(self):
        zone = RoObject(
            id='a6c7dcc6-8070-481b-8d5a-310100f5fc31',
            action='DELETE',
            increment_serial=False,
            delayed_notify=True,
        )
        self.central_api.find_zones.return_value = [zone]

        self.task()

        self.assertIn(
            'Skipping delayed NOTIFY for a6c7dcc6-8070-481b-8d5a-310100f5fc31 '
            'being DELETED',
            self.stdlog.logger.output
        )
