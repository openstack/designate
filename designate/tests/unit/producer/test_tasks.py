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
from designate.common import constants
import designate.conf
from designate import context
from designate import exceptions
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

    def __call__(self):
        pass


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


class PeriodicCheckServiceStatusTaskTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))
        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(self.stdlog)

        self.central_api = mock.Mock()
        self.context = mock.Mock()
        mock.patch.object(central_api.CentralAPI, 'get_instance',
                          return_value=self.central_api).start()
        mock.patch.object(context.DesignateContext, 'get_admin_context',
                          return_value=self.context).start()
        self.task = tasks.PeriodicCheckServiceStatusTask()
        self.task.my_partitions = 0, 9

    def test_mark_down_when_heartbeat_exceeds_threshold(self):
        old_time = (timeutils.utcnow() -
                    datetime.timedelta(seconds=700000))
        service_status = RwObject(
            id=uuidutils.generate_uuid(),
            status=constants.SERVICE_UP,
            heartbeated_at=old_time,
        )
        self.central_api.find_service_statuses.side_effect = [
            [service_status], []]

        self.task()

        self.assertEqual(constants.SERVICE_DOWN, service_status.status)
        self.central_api.update_service_status.assert_called_once_with(
            self.context, service_status)

    def test_no_change_when_heartbeat_within_threshold(self):
        recent_time = (timeutils.utcnow() -
                       datetime.timedelta(seconds=60))
        service_status = RwObject(
            id=uuidutils.generate_uuid(),
            status=constants.SERVICE_UP,
            heartbeated_at=recent_time,
        )
        self.central_api.find_service_statuses.side_effect = [
            [service_status], []]

        self.task()

        self.assertEqual(constants.SERVICE_UP, service_status.status)
        self.central_api.update_service_status.assert_not_called()

    def test_skip_when_no_heartbeat(self):
        service_status = RwObject(
            id=uuidutils.generate_uuid(),
            status=constants.SERVICE_UP,
            heartbeated_at=None,
        )
        self.central_api.find_service_statuses.side_effect = [
            [service_status], []]

        self.task()

        self.central_api.update_service_status.assert_not_called()


class PeriodicCleanupStoppedServiceStatusTaskTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

        self.central_api = mock.Mock()
        self.context = mock.Mock()
        mock.patch.object(central_api.CentralAPI, 'get_instance',
                          return_value=self.central_api).start()
        mock.patch.object(context.DesignateContext, 'get_admin_context',
                          return_value=self.context).start()
        self.task = tasks.PeriodicCleanupStoppedServiceStatusTask()
        self.task.my_partitions = 0, 9

    def test_delete_stopped_service_status(self):
        service_status = RoObject(
            id=uuidutils.generate_uuid(),
            status=constants.SERVICE_STOPPED,
        )
        self.central_api.find_service_statuses.side_effect = [
            [service_status], [],  # STOPPED iteration
            [],                    # DOWN iteration
        ]

        self.task()

        self.central_api.delete_service_status.assert_called_once_with(
            self.context, service_status)

    def test_no_stopped_entries(self):
        self.central_api.find_service_statuses.return_value = []

        self.task()

        self.central_api.delete_service_status.assert_not_called()

    def test_marker_not_found_is_ignored(self):
        service_status = RoObject(
            id=uuidutils.generate_uuid(),
            status=constants.SERVICE_STOPPED,
        )
        self.central_api.find_service_statuses.side_effect = [
            [service_status], exceptions.MarkerNotFound(),
            [],  # DOWN iteration
        ]

        self.task()

        self.central_api.delete_service_status.assert_called_once_with(
            self.context, service_status)

    def test_delete_stale_down_service_status(self):
        old_time = (timeutils.utcnow() -
                    datetime.timedelta(days=10))
        service_status = RoObject(
            id=uuidutils.generate_uuid(),
            status=constants.SERVICE_DOWN,
            heartbeated_at=old_time,
        )
        self.central_api.find_service_statuses.side_effect = [
            [],                        # STOPPED iteration
            [service_status], [],      # DOWN iteration
        ]

        self.task()

        self.central_api.delete_service_status.assert_called_once_with(
            self.context, service_status)

    def test_recent_down_service_not_deleted(self):
        recent_time = (timeutils.utcnow() -
                       datetime.timedelta(hours=1))
        service_status = RoObject(
            id=uuidutils.generate_uuid(),
            status=constants.SERVICE_DOWN,
            heartbeated_at=recent_time,
        )
        self.central_api.find_service_statuses.side_effect = [
            [],                        # STOPPED iteration
            [service_status], [],      # DOWN iteration
        ]

        self.task()

        self.central_api.delete_service_status.assert_not_called()

    def test_down_cleanup_skips_no_heartbeat(self):
        service_status = RoObject(
            id=uuidutils.generate_uuid(),
            status=constants.SERVICE_DOWN,
            heartbeated_at=None,
        )
        self.central_api.find_service_statuses.side_effect = [
            [],                        # STOPPED iteration
            [service_status], [],      # DOWN iteration
        ]

        self.task()

        self.central_api.delete_service_status.assert_not_called()

    def test_down_cleanup_disabled_when_threshold_zero(self):
        CONF.set_override(
            'time_threshold', 0,
            'producer_task:periodic_cleanup_stopped_service_status')
        self.central_api.find_service_statuses.side_effect = [
            [],  # STOPPED iteration (no DOWN iteration expected)
        ]

        self.task()

        self.central_api.delete_service_status.assert_not_called()


class PeriodicStalePtrRecordsRemovalTaskTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))
        CONF.set_override('region_name', 'RegionOne', 'neutron')

        # Mock a ctxt
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

        self.task = tasks.PeriodicStalePtrRecordsRemovalTask()
        self.task.my_partitions = range(0, 10)

    @mock.patch.object(central_api.CentralAPI, 'get_instance')
    def test_get_existing_floating_ip_ids_success(self, mock_get_instance):
        """Test successful retrieval of floating IP IDs."""
        fip1_id = uuidutils.generate_uuid()
        fip2_id = uuidutils.generate_uuid()
        floating_ips = [
            {'id': fip1_id, 'floating_ip_address': '192.168.1.1'},
            {'id': fip2_id, 'floating_ip_address': '192.168.1.2'}
        ]

        mock_central_api = mock.Mock()
        mock_central_api.get_floating_ips.return_value = floating_ips
        mock_get_instance.return_value = mock_central_api

        result = self.task._get_existing_floating_ip_ids(self.ctxt)

        self.assertEqual({fip1_id, fip2_id}, result)
        mock_central_api.get_floating_ips.assert_called_once_with(
            self.ctxt, region='RegionOne')

    @mock.patch.object(central_api.CentralAPI, 'get_instance')
    def test_get_existing_floating_ip_ids_failure(self, mock_get_instance):
        """Test handling of exceptions when retrieving floating IPs."""
        mock_central_api = mock.Mock()
        mock_central_api.get_floating_ips.side_effect = Exception(
            "Network error")
        mock_get_instance.return_value = mock_central_api

        result = self.task._get_existing_floating_ip_ids(self.ctxt)

        self.assertIsNone(result)
        mock_central_api.get_floating_ips.assert_called_once_with(
            self.ctxt, region='RegionOne')

    def test_identify_stale_ptr_records_no_stale(self):
        """Test identifying PTR records when none are stale."""
        fip1_id = uuidutils.generate_uuid()
        fip2_id = uuidutils.generate_uuid()

        ptr_records = [
            mock.Mock(id=uuidutils.generate_uuid(),
                     managed_resource_id=fip1_id,
                     managed_resource_region='RegionOne'),
            mock.Mock(id=uuidutils.generate_uuid(),
                     managed_resource_id=fip2_id,
                     managed_resource_region='RegionOne')
        ]
        existing_fip_ids = {fip1_id, fip2_id}

        result = self.task._identify_stale_ptr_records(
            ptr_records, existing_fip_ids)

        self.assertEqual([], result)

    def test_identify_stale_ptr_records_with_stale(self):
        """Test identifying PTR records when some are stale."""
        fip1_id = uuidutils.generate_uuid()
        fip2_id = uuidutils.generate_uuid()  # This will be missing
        fip3_id = uuidutils.generate_uuid()

        ptr_records = [
            mock.Mock(id=uuidutils.generate_uuid(),
                     managed_resource_id=fip1_id,
                     managed_resource_region='RegionOne'),
            mock.Mock(id=uuidutils.generate_uuid(),
                     managed_resource_id=fip2_id,
                     managed_resource_region='RegionOne'),
            mock.Mock(id=uuidutils.generate_uuid(),
                     managed_resource_id=fip3_id,
                     managed_resource_region='RegionOne')
        ]
        existing_fip_ids = {fip1_id, fip3_id}  # fip2_id missing

        result = self.task._identify_stale_ptr_records(
            ptr_records, existing_fip_ids)

        self.assertEqual(1, len(result))
        self.assertEqual(fip2_id, result[0].managed_resource_id)

    def test_delete_ptr_record_success(self):
        """Test successful deletion of a PTR record via the central
        service's delete_managed_records(), which keeps the zone serial
        and backend notification in sync.
        """
        mock_context = mock.Mock()
        ptr_record = mock.Mock(
            id=uuidutils.generate_uuid(),
            zone_id=uuidutils.generate_uuid(),
            managed_resource_id=uuidutils.generate_uuid()
        )

        result = self.task._delete_ptr_record(mock_context, ptr_record)

        self.assertTrue(result)
        self.central.delete_managed_records.assert_called_once_with(
            mock_context, zone_id=ptr_record.zone_id,
            criterion={'id': ptr_record.id})

    def test_delete_ptr_record_already_deleted(self):
        """delete_managed_records() is a no-op if another worker already
        deleted the record, so this should still report success.
        """
        mock_context = mock.Mock()
        ptr_record = mock.Mock(
            id=uuidutils.generate_uuid(),
            zone_id=uuidutils.generate_uuid(),
            managed_resource_id=uuidutils.generate_uuid()
        )
        self.central.delete_managed_records.return_value = None

        result = self.task._delete_ptr_record(mock_context, ptr_record)

        self.assertTrue(result)

    def test_delete_ptr_record_failure(self):
        """Test handling of unexpected errors during PTR record deletion."""
        mock_context = mock.Mock()
        ptr_record = mock.Mock(
            id=uuidutils.generate_uuid(),
            zone_id=uuidutils.generate_uuid(),
            managed_resource_id=uuidutils.generate_uuid()
        )
        self.central.delete_managed_records.side_effect = Exception(
            "Unexpected error")

        result = self.task._delete_ptr_record(mock_context, ptr_record)

        self.assertFalse(result)

    def test_process_stale_records(self):
        """Test that stale records are deleted and the elevated context
        used to delete them is built with the expected permissions.
        """
        mock_elevated_context = mock.Mock()
        self.ctxt.elevated.return_value = mock_elevated_context

        stale_ptr_records = [
            mock.Mock(id=uuidutils.generate_uuid()),
            mock.Mock(id=uuidutils.generate_uuid()),
        ]

        with mock.patch.object(
                self.task, '_delete_ptr_record',
                return_value=True) as mock_delete:
            result = self.task._process_stale_records(
                self.ctxt, stale_ptr_records)

        self.assertEqual(2, result)
        self.ctxt.elevated.assert_called_once_with(
            all_tenants=True, edit_managed_records=True)
        mock_delete.assert_has_calls([
            mock.call(mock_elevated_context, stale_ptr_records[0]),
            mock.call(mock_elevated_context, stale_ptr_records[1]),
        ])

    def test_process_stale_records_partial_failure(self):
        """Test that the deleted count only reflects successful
        deletions.
        """
        stale_ptr_records = [
            mock.Mock(id=uuidutils.generate_uuid()),
            mock.Mock(id=uuidutils.generate_uuid()),
        ]

        with mock.patch.object(
                self.task, '_delete_ptr_record',
                side_effect=[True, False]):
            result = self.task._process_stale_records(
                self.ctxt, stale_ptr_records)

        self.assertEqual(1, result)

    def test_call_no_ptr_records(self):
        """Test that the task returns early when there are no PTR
        records to process.
        """
        self.central.get_ptr_records.return_value = []

        with mock.patch.object(
                self.task, '_get_existing_floating_ip_ids') as mock_get_fips:
            self.task()

        self.central.get_ptr_records.assert_called_once_with(
            self.ctxt, {'zone_shard': 'BETWEEN 0,9',
                        'managed_resource_region': 'RegionOne'}, limit=100)
        mock_get_fips.assert_not_called()

    def test_call_no_region(self):
        CONF.set_override('region_name', None, 'neutron')

        self.task()

        self.central.get_ptr_records.assert_not_called()
        self.central.get_floating_ips.assert_not_called()
        self.central.delete_managed_records.assert_not_called()

    def test_call_preserves_other_regions(self):
        records = [
            mock.Mock(id='stale', zone_id='zone',
                      managed_resource_id='stale-fip',
                      managed_resource_region='RegionOne'),
            mock.Mock(id='live', managed_resource_id='live-fip',
                      managed_resource_region='RegionOne'),
            mock.Mock(id='other', managed_resource_id='other-fip',
                      managed_resource_region='RegionTwo'),
            mock.Mock(id='unknown', managed_resource_id='unknown-fip',
                      managed_resource_region=None),
        ]
        # Include other regions even though the query filters them out,
        # to verify that deletion also checks the record's own region.
        self.central.get_ptr_records.side_effect = [records, []]
        self.central.get_floating_ips.return_value = [{'id': 'live-fip'}]

        self.task()

        self.central.get_floating_ips.assert_called_once_with(
            self.ctxt, region='RegionOne')
        self.central.get_ptr_records.assert_has_calls([
            mock.call(self.ctxt, {'zone_shard': 'BETWEEN 0,9',
                                 'managed_resource_region': 'RegionOne'},
                      limit=100),
            mock.call(self.ctxt, {'zone_shard': 'BETWEEN 0,9',
                                 'managed_resource_region': 'RegionOne'},
                      limit=100, marker='unknown'),
        ])
        self.central.delete_managed_records.assert_called_once_with(
            self.ctxt.elevated.return_value,
            zone_id='zone', criterion={'id': 'stale'})

    def test_call_region_mismatch(self):
        self.central.get_ptr_records.side_effect = [[mock.Mock()], []]
        self.central.get_floating_ips.side_effect = (
            exceptions.ConfigurationError('Neutron region mismatch'))

        self.task()

        self.central.delete_managed_records.assert_not_called()

    def test_call_existing_fip_ids_none(self):
        """Test that the task returns early when the existing floating
        IP IDs could not be fetched.
        """
        self.central.get_ptr_records.side_effect = [[mock.Mock()], []]

        with (
            mock.patch.object(
                self.task, '_get_existing_floating_ip_ids',
                return_value=None),
            mock.patch.object(
                self.task, '_identify_stale_ptr_records') as mock_id,
        ):
            self.task()

        mock_id.assert_not_called()

    def test_call_existing_fip_ids_empty(self):
        """Test that the task returns early, without deleting anything,
        when neutron reports zero floating IPs. Treating an empty result
        the same as a fetch failure guards against wiping out every PTR
        record in the shard if the floating IP lookup is silently wrong.
        """
        self.central.get_ptr_records.side_effect = [[mock.Mock()], []]

        with (
            mock.patch.object(
                self.task, '_get_existing_floating_ip_ids',
                return_value=set()),
            mock.patch.object(
                self.task, '_identify_stale_ptr_records') as mock_id,
        ):
            self.task()

        mock_id.assert_not_called()

    def test_call_no_stale_records(self):
        """Test that no deletion is attempted when there are no stale
        PTR records.
        """
        self.central.get_ptr_records.side_effect = [[mock.Mock()], []]

        with (
            mock.patch.object(
                self.task, '_get_existing_floating_ip_ids',
                return_value={uuidutils.generate_uuid()}),
            mock.patch.object(
                self.task, '_identify_stale_ptr_records',
                return_value=[]),
            mock.patch.object(
                self.task, '_process_stale_records') as mock_process,
        ):
            self.task()

        mock_process.assert_not_called()

    def test_call_deletes_stale_records(self):
        """Test the happy path: stale PTR records are identified and
        handed off for deletion.
        """
        ptr_records = [mock.Mock()]
        stale_ptr_records = [mock.Mock()]
        existing_fip_ids = {uuidutils.generate_uuid()}
        self.central.get_ptr_records.side_effect = [ptr_records, []]

        with (
            mock.patch.object(
                self.task, '_get_existing_floating_ip_ids',
                return_value=existing_fip_ids),
            mock.patch.object(
                self.task, '_identify_stale_ptr_records',
                return_value=stale_ptr_records) as mock_identify,
            mock.patch.object(
                self.task, '_process_stale_records') as mock_process,
        ):
            self.task()

        mock_identify.assert_called_once_with(
            ptr_records, existing_fip_ids)
        mock_process.assert_called_once_with(self.ctxt, stale_ptr_records)

    def test_call_handles_exceptions(self):
        """Test that unexpected errors are caught and logged rather
        than propagated.
        """
        self.central.get_ptr_records.side_effect = Exception(
            "Unexpected error")

        # Should not raise.
        self.task()

        self.central.get_ptr_records.assert_called_once_with(
            self.ctxt, {'zone_shard': 'BETWEEN 0,9',
                        'managed_resource_region': 'RegionOne'}, limit=100)
