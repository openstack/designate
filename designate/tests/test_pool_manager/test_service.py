# Copyright 2014 eBay Inc.
#
# Author: Ron Rickard <rrickard@ebaysf.com>
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
from oslo_log import log
import oslo_messaging as messaging
from mock import call
from mock import Mock
from mock import patch

from designate import exceptions
from designate import objects
from designate.utils import generate_uuid
from designate.backend import impl_fake
from designate.central import rpcapi as central_rpcapi
from designate.mdns import rpcapi as mdns_rpcapi
from designate.storage.impl_sqlalchemy import tables
from designate.tests.test_pool_manager import PoolManagerTestCase
from designate.tests.test_pool_manager import POOL_DICT
import designate.pool_manager.service as pm_module

LOG = log.getLogger(__name__)


class PoolManagerServiceNoopTest(PoolManagerTestCase):

    def setUp(self):
        super(PoolManagerServiceNoopTest, self).setUp()

        self.config(
            threshold_percentage=100,
            enable_recovery_timer=False,
            enable_sync_timer=False,
            poll_retry_interval=1,
            poll_max_retries=1,
            cache_driver='noop',
            group='service:pool_manager')

        # TODO(kiall): Rework all this pool config etc into a fixture..
        # Configure the Pool ID
        self.config(
            pool_id='794ccc2c-d751-44fe-b57f-8894c9f5c842',
            group='service:pool_manager')

        # Start the Service
        with patch.object(
                        central_rpcapi.CentralAPI,
                        'get_pool',
                        return_value=objects.Pool.from_dict(POOL_DICT)):
            self.service = self.start_service('pool_manager')
            self.cache = self.service.cache

    @staticmethod
    def _build_zone(name, action, status, id=None):
        zid = id or '75ea1626-eea7-46b5-acb7-41e5897c2d40'
        values = {
            'id': zid,
            'name': name,
            'pool_id': '794ccc2c-d751-44fe-b57f-8894c9f5c842',
            'action': action,
            'serial': 1422062497,
            'status': status
        }
        return objects.Zone.from_dict(values)

    def _build_zones(self, n, action, status):
        return [
            self._build_zone("zone%02X.example." % cnt, action,
                             status, id=generate_uuid())
            for cnt in range(n)
        ]

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(mdns_rpcapi.MdnsAPI, 'poll_for_serial_number')
    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_create_zone(
            self, mock_update_status, mock_notify_zone_changed,
            mock_poll_for_serial_number, _):

        zone = self._build_zone('example.org.', 'CREATE', 'PENDING')

        self.service.create_zone(self.admin_context, zone)

        create_statuses = self.service._retrieve_statuses(
            self.admin_context, zone, 'CREATE')
        # Even though _retrieve_statuses tries to get from mdns, mdns does
        # not return any status
        self.assertEqual(0, len(create_statuses))

        # Ensure poll_for_serial_number was called for each nameserver.
        self.assertEqual(2, mock_poll_for_serial_number.call_count)
        self.assertEqual(
            [call(self.admin_context, zone,
                  self.service.pool.nameservers[0], 30, 1, 1, 5),
             call(self.admin_context, zone,
                  self.service.pool.nameservers[1], 30, 1, 1, 5)],
            mock_poll_for_serial_number.call_args_list)

        # Pool manager needs to call into mdns to calculate consensus as
        # there is no cache. So update_status is never called.
        self.assertFalse(mock_update_status.called)

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(impl_fake.FakeBackend, 'create_zone')
    @patch.object(mdns_rpcapi.MdnsAPI, 'poll_for_serial_number')
    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_create_zone_target_both_failure(
            self, mock_update_status, mock_notify_zone_changed,
            mock_poll_for_serial_number, mock_create_zone, _):

        zone = self._build_zone('example.org.', 'CREATE', 'PENDING')

        mock_create_zone.side_effect = exceptions.Backend

        self.service.create_zone(self.admin_context, zone)

        create_statuses = self.service._retrieve_statuses(
            self.admin_context, zone, 'CREATE')
        self.assertEqual(0, len(create_statuses))

        # Ensure notify_zone_changed and poll_for_serial_number
        # were never called.
        self.assertFalse(mock_notify_zone_changed.called)
        self.assertFalse(mock_poll_for_serial_number.called)

        # Since consensus is not reached this early, we immediately call
        # central's update_status.
        self.assertTrue(mock_update_status.called)

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(impl_fake.FakeBackend, 'create_zone')
    @patch.object(mdns_rpcapi.MdnsAPI, 'poll_for_serial_number')
    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_create_zone_target_one_failure(
            self, mock_update_status, mock_notify_zone_changed,
            mock_poll_for_serial_number, mock_create_zone, _):

        zone = self._build_zone('example.org.', 'CREATE', 'PENDING')

        mock_create_zone.side_effect = [None, exceptions.Backend]

        self.service.create_zone(self.admin_context, zone)

        create_statuses = self.service._retrieve_statuses(
            self.admin_context, zone, 'CREATE')
        self.assertEqual(0, len(create_statuses))

        # Since consensus is not reached this early, we immediately call
        # central's update_status.
        self.assertTrue(mock_update_status.called)

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(impl_fake.FakeBackend, 'create_zone')
    @patch.object(mdns_rpcapi.MdnsAPI, 'poll_for_serial_number')
    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_create_zone_target_one_failure_consensus(
            self, mock_update_status, mock_notify_zone_changed,
            mock_poll_for_serial_number, mock_create_zone, _):

        self.service.stop()
        self.config(
            threshold_percentage=50,
            group='service:pool_manager')
        with patch.object(
                        central_rpcapi.CentralAPI,
                        'get_pool',
                        return_value=objects.Pool.from_dict(POOL_DICT)):
            self.service = self.start_service('pool_manager')

        zone = self._build_zone('example.org.', 'CREATE', 'PENDING')

        mock_create_zone.side_effect = [None, exceptions.Backend]

        self.service.create_zone(self.admin_context, zone)

        create_statuses = self.service._retrieve_statuses(
            self.admin_context, zone, 'CREATE')
        self.assertEqual(0, len(create_statuses))

        # Ensure poll_for_serial_number was called for each nameserver.
        self.assertEqual(
            [call(self.admin_context, zone,
                  self.service.pool.nameservers[0], 30, 1, 1, 5),
             call(self.admin_context, zone,
                  self.service.pool.nameservers[1], 30, 1, 1, 5)],
            mock_poll_for_serial_number.call_args_list)

        self.assertFalse(mock_update_status.called)

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_update_status(self, mock_update_status, _):

        zone = self._build_zone('example.org.', 'UPDATE', 'PENDING')

        self.service.update_status(self.admin_context, zone,
                                   self.service.pool.nameservers[0],
                                   'SUCCESS', zone.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, zone, 'UPDATE')
        self.assertEqual(0, len(update_statuses))

        # Ensure update_status was not called.
        self.assertFalse(mock_update_status.called)

        self.service.update_status(self.admin_context, zone,
                                   self.service.pool.nameservers[1],
                                   'SUCCESS', zone.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, zone, 'UPDATE')
        self.assertEqual(0, len(update_statuses))

        # Ensure update_status was not called.
        self.assertFalse(mock_update_status.called)

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_update_status_both_failure(self, mock_update_status, _):
        zone = self._build_zone('example.org.', 'UPDATE', 'PENDING')

        self.service.update_status(self.admin_context, zone,
                                   self.service.pool.nameservers[0],
                                   'ERROR', zone.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, zone, 'UPDATE')
        self.assertEqual(0, len(update_statuses))

        mock_update_status.assert_called_once_with(
            self.admin_context, zone.id, 'ERROR', 0)

        # Reset the mock call attributes.
        mock_update_status.reset_mock()

        self.service.update_status(self.admin_context, zone,
                                   self.service.pool.nameservers[1],
                                   'ERROR', zone.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, zone, 'UPDATE')
        self.assertEqual(0, len(update_statuses))

        mock_update_status.assert_called_once_with(
            self.admin_context, zone.id, 'ERROR', 0)

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_update_status_one_failure(self, mock_update_status, _):
        zone = self._build_zone('example.org.', 'UPDATE', 'PENDING')

        self.service.update_status(self.admin_context, zone,
                                   self.service.pool.nameservers[0],
                                   'SUCCESS', zone.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, zone, 'UPDATE')
        self.assertEqual(0, len(update_statuses))

        # Ensure update_status was not called.
        self.assertFalse(mock_update_status.called)

        self.service.update_status(self.admin_context, zone,
                                   self.service.pool.nameservers[1],
                                   'ERROR', zone.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, zone, 'UPDATE')
        self.assertEqual(0, len(update_statuses))

        mock_update_status.assert_called_once_with(
            self.admin_context, zone.id, 'ERROR', 0)

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_update_status_one_failure_consensus(self, mock_update_status, _):

        self.service.stop()
        self.config(
            threshold_percentage=50,
            group='service:pool_manager')
        with patch.object(
                        central_rpcapi.CentralAPI,
                        'get_pool',
                        return_value=objects.Pool.from_dict(POOL_DICT)):
            self.service = self.start_service('pool_manager')

        zone = self._build_zone('example.org.', 'UPDATE', 'PENDING')

        self.service.update_status(self.admin_context, zone,
                                   self.service.pool.nameservers[0],
                                   'SUCCESS', zone.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, zone, 'UPDATE')
        self.assertEqual(0, len(update_statuses))

        # Ensure update_status was not called.
        self.assertFalse(mock_update_status.called)

        # Reset the mock call attributes.
        mock_update_status.reset_mock()

        self.service.update_status(self.admin_context, zone,
                                   self.service.pool.nameservers[1],
                                   'ERROR', zone.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, zone, 'UPDATE')
        self.assertEqual(0, len(update_statuses))

        mock_update_status.assert_called_once_with(
            self.admin_context, zone.id, 'ERROR', 0)

    @patch.object(central_rpcapi.CentralAPI, 'find_zones')
    def test_periodic_sync_not_leader(self, mock_find_zones):
        self.service._update_zone_on_target = Mock(return_value=False)
        self.service._pool_election = Mock()
        self.service._pool_election.is_leader = False
        self.service.update_zone = Mock()

        self.service.periodic_sync()
        self.assertFalse(mock_find_zones.called)

    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_update_zone_no_consensus(self, mock_cent_update_status):
        zone = self._build_zone('example.org.', 'UPDATE', 'PENDING')
        self.service._update_zone_on_target = Mock(return_value=True)
        self.service._exceed_or_meet_threshold = Mock(return_value=False)

        ret = self.service.update_zone(self.admin_context, zone)
        self.assertFalse(ret)

        self.assertEqual(2, self.service._update_zone_on_target.call_count)
        self.assertEqual(1, mock_cent_update_status.call_count)

    @patch.object(mdns_rpcapi.MdnsAPI, 'poll_for_serial_number')
    def test_update_zone(self, mock_mdns_poll):
        zone = self._build_zone('example.org.', 'UPDATE', 'PENDING')
        self.service._update_zone_on_target = Mock(return_value=True)
        self.service._update_zone_on_also_notify = Mock()
        self.service.pool.also_notifies = ['bogus']
        self.service._exceed_or_meet_threshold = Mock(return_value=True)

        # cache.retrieve will throw exceptions.PoolManagerStatusNotFound
        # mdns_api.poll_for_serial_number will be called twice
        ret = self.service.update_zone(self.admin_context, zone)
        self.assertTrue(ret)

        self.assertEqual(2, self.service._update_zone_on_target.call_count)
        self.assertEqual(1, self.service._update_zone_on_also_notify.call_count)  # noqa
        self.assertEqual(2, mock_mdns_poll.call_count)

    # Periodic sync

    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    @patch.object(central_rpcapi.CentralAPI, 'find_zones')
    def test_periodic_sync(self, mock_find_zones,
                           mock_cent_update_status, *a):
        self.service.update_zone = Mock()
        mock_find_zones.return_value = self._build_zones(2, 'UPDATE',
                                                         'PENDING')
        self.service.periodic_sync()

        self.assertEqual(1, mock_find_zones.call_count)
        criterion = mock_find_zones.call_args_list[0][0][1]
        self.assertEqual('!ERROR', criterion['status'])
        self.assertEqual(2, self.service.update_zone.call_count)
        self.assertEqual(0, mock_cent_update_status.call_count)

    @patch.object(pm_module.time, 'sleep')
    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    @patch.object(central_rpcapi.CentralAPI, 'find_zones')
    def test_periodic_sync_with_failing_update(
            self, mock_find_zones, mock_cent_update_status, *mocks):
        self.service.update_zone = Mock(return_value=False)  # fail update
        mock_find_zones.return_value = self._build_zones(3, 'UPDATE',
                                                         'PENDING')
        self.service.periodic_sync()

        self.assertEqual(1, mock_find_zones.call_count)
        criterion = mock_find_zones.call_args_list[0][0][1]
        self.assertEqual('!ERROR', criterion['status'])

        # 3 zones, all failing, with 3 attempts: 9 calls
        self.assertEqual(9, self.service.update_zone.call_count)

        # the zones have been put in ERROR status
        self.assertEqual(3, mock_cent_update_status.call_count)

    @patch.object(pm_module.time, 'sleep')
    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    @patch.object(central_rpcapi.CentralAPI, 'find_zones')
    def test_periodic_sync_with_failing_update_with_exception(
            self, mock_find_zones, mock_cent_update_status, *mocks):
        self.service.update_zone = Mock(side_effect=Exception)
        mock_find_zones.return_value = self._build_zones(3, 'UPDATE',
                                                         'PENDING')
        self.service.periodic_sync()

        self.assertEqual(1, mock_find_zones.call_count)
        criterion = mock_find_zones.call_args_list[0][0][1]
        self.assertEqual('!ERROR', criterion['status'])

        # 3 zones, all failing, with 3 attempts: 9 calls
        self.assertEqual(9, self.service.update_zone.call_count)

        # the zones have been put in ERROR status
        self.assertEqual(3, mock_cent_update_status.call_count)


class PoolManagerServiceEndToEndTest(PoolManagerServiceNoopTest):

    def setUp(self):
        super(PoolManagerServiceEndToEndTest, self).setUp()

    def _fetch_all_zones(self):
        """Fetch all zones including deleted ones
        """
        query = tables.zones.select()
        return self.storage.session.execute(query).fetchall()

    def _log_all_zones(self, zones, msg=None):
        """Log out a summary of zones
        """
        if msg:
            LOG.debug("--- %s ---" % msg)
        cols = ('name', 'status', 'action', 'deleted', 'deleted_at',
                'parent_zone_id')
        tpl = "%-35s | %-11s | %-11s | %-32s | %-20s | %s"
        LOG.debug(tpl % cols)
        for z in zones:
            LOG.debug(tpl % tuple(z[k] for k in cols))

    def _assert_count_all_zones(self, n):
        """Assert count ALL zones including deleted ones
        """
        zones = self._fetch_all_zones()
        if len(zones) == n:
            return

        msg = "failed: %d zones expected, %d found" % (n, len(zones))
        self._log_all_zones(zones, msg=msg)
        raise Exception("Unexpected number of zones")

    def _assert_num_failed_zones(self, action, n):
        zones = self.service._get_failed_zones(
            self.admin_context, action)
        if len(zones) != n:
            LOG.error("Expected %d failed zones, got %d", n, len(zones))
            self._log_all_zones(zones, msg='listing zones')
            self.assertEqual(n, len(zones))

    def _assert_num_healthy_zones(self, action, n):
        criterion = {
            'action': action,
            'pool_id': pm_module.CONF['service:pool_manager'].pool_id,
            'status': '!%s' % pm_module.ERROR_STATUS
        }
        zones = self.service.central_api.find_zones(self.admin_context,
                                                    criterion)
        if len(zones) != n:
            LOG.error("Expected %d healthy zones, got %d", n, len(zones))
            self._log_all_zones(zones, msg='listing zones')
            self.assertEqual(n, len(zones))
