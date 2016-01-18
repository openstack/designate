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
import logging
import uuid

import oslo_messaging as messaging
from oslo_config import cfg
from mock import call
from mock import Mock
from mock import patch

from designate import exceptions
from designate import objects
from designate.backend import impl_fake
from designate.storage.impl_sqlalchemy import tables
from designate.central import rpcapi as central_rpcapi
from designate.mdns import rpcapi as mdns_rpcapi
from designate.tests.test_pool_manager import PoolManagerTestCase
import designate.pool_manager.service as pm_module

LOG = logging.getLogger(__name__)


class PoolManagerServiceNoopTest(PoolManagerTestCase):

    def setUp(self):
        super(PoolManagerServiceNoopTest, self).setUp()

        self.config(
            threshold_percentage=100,
            enable_recovery_timer=False,
            enable_sync_timer=False,
            cache_driver='noop',
            group='service:pool_manager')

        # TODO(kiall): Rework all this pool config etc into a fixture..
        # Configure the Pool ID
        self.config(
            pool_id='794ccc2c-d751-44fe-b57f-8894c9f5c842',
            group='service:pool_manager')

        # Configure the Pool
        section_name = 'pool:794ccc2c-d751-44fe-b57f-8894c9f5c842'
        section_opts = [
            cfg.ListOpt('targets', default=[
                'f278782a-07dc-4502-9177-b5d85c5f7c7e',
                'a38703f2-b71e-4e5b-ab22-30caaed61dfd',
            ]),
            cfg.ListOpt('nameservers', default=[
                'c5d64303-4cba-425a-9f3c-5d708584dde4',
                'c67cdc95-9a9e-4d2a-98ed-dc78cbd85234',
            ]),
            cfg.ListOpt('also_notifies', default=[]),
        ]
        cfg.CONF.register_group(cfg.OptGroup(name=section_name))
        cfg.CONF.register_opts(section_opts, group=section_name)

        # Configure the Pool Targets
        section_name = 'pool_target:f278782a-07dc-4502-9177-b5d85c5f7c7e'
        section_opts = [
            cfg.StrOpt('type', default='fake'),
            cfg.ListOpt('masters', default=['127.0.0.1:5354']),
            cfg.DictOpt('options', default={})
        ]
        cfg.CONF.register_group(cfg.OptGroup(name=section_name))
        cfg.CONF.register_opts(section_opts, group=section_name)

        section_name = 'pool_target:a38703f2-b71e-4e5b-ab22-30caaed61dfd'
        section_opts = [
            cfg.StrOpt('type', default='fake'),
            cfg.ListOpt('masters', default=['127.0.0.1:5354']),
            cfg.DictOpt('options', default={})
        ]
        cfg.CONF.register_group(cfg.OptGroup(name=section_name))
        cfg.CONF.register_opts(section_opts, group=section_name)

        # Configure the Pool Nameservers
        section_name = 'pool_nameserver:c5d64303-4cba-425a-9f3c-5d708584dde4'
        section_opts = [
            cfg.StrOpt('host', default='127.0.0.1'),
            cfg.StrOpt('port', default=5355),
        ]
        cfg.CONF.register_group(cfg.OptGroup(name=section_name))
        cfg.CONF.register_opts(section_opts, group=section_name)

        section_name = 'pool_nameserver:c67cdc95-9a9e-4d2a-98ed-dc78cbd85234'
        section_opts = [
            cfg.StrOpt('host', default='127.0.0.1'),
            cfg.StrOpt('port', default=5356),
        ]
        cfg.CONF.register_group(cfg.OptGroup(name=section_name))
        cfg.CONF.register_opts(section_opts, group=section_name)

        # Start the Service
        self.service = self.start_service('pool_manager')
        self.cache = self.service.cache

    @staticmethod
    def _build_domain(name, action, status, id=None):
        zid = id or '75ea1626-eea7-46b5-acb7-41e5897c2d40'
        values = {
            'id': zid,
            'name': name,
            'pool_id': '794ccc2c-d751-44fe-b57f-8894c9f5c842',
            'action': action,
            'serial': 1422062497,
            'status': status
        }
        return objects.Domain.from_dict(values)

    def _build_domains(self, n, action, status):
        return [
            self._build_domain("zone%02X.example" % cnt, action,
                               status, id=str(uuid.uuid4()))
            for cnt in range(n)
        ]

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(mdns_rpcapi.MdnsAPI, 'poll_for_serial_number')
    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_create_domain(
            self, mock_update_status, mock_notify_zone_changed,
            mock_poll_for_serial_number, _):

        domain = self._build_domain('example.org.', 'CREATE', 'PENDING')

        self.service.create_domain(self.admin_context, domain)

        create_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'CREATE')
        # Even though _retrieve_statuses tries to get from mdns, mdns does
        # not return any status
        self.assertEqual(0, len(create_statuses))

        # Ensure poll_for_serial_number was called for each nameserver.
        self.assertEqual(2, mock_poll_for_serial_number.call_count)
        self.assertEqual(
            [call(self.admin_context, domain,
                  self.service.pool.nameservers[0], 30, 15, 10, 5),
             call(self.admin_context, domain,
                  self.service.pool.nameservers[1], 30, 15, 10, 5)],
            mock_poll_for_serial_number.call_args_list)

        # Pool manager needs to call into mdns to calculate consensus as
        # there is no cache. So update_status is never called.
        self.assertEqual(False, mock_update_status.called)

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(impl_fake.FakeBackend, 'create_domain')
    @patch.object(mdns_rpcapi.MdnsAPI, 'poll_for_serial_number')
    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_create_domain_target_both_failure(
            self, mock_update_status, mock_notify_zone_changed,
            mock_poll_for_serial_number, mock_create_domain, _):

        domain = self._build_domain('example.org.', 'CREATE', 'PENDING')

        mock_create_domain.side_effect = exceptions.Backend

        self.service.create_domain(self.admin_context, domain)

        create_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'CREATE')
        self.assertEqual(0, len(create_statuses))

        # Ensure notify_zone_changed and poll_for_serial_number
        # were never called.
        self.assertEqual(False, mock_notify_zone_changed.called)
        self.assertEqual(False, mock_poll_for_serial_number.called)

        # Since consensus is not reached this early, we immediatly call
        # central's update_status.
        self.assertEqual(True, mock_update_status.called)

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(impl_fake.FakeBackend, 'create_domain')
    @patch.object(mdns_rpcapi.MdnsAPI, 'poll_for_serial_number')
    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_create_domain_target_one_failure(
            self, mock_update_status, mock_notify_zone_changed,
            mock_poll_for_serial_number, mock_create_domain, _):

        domain = self._build_domain('example.org.', 'CREATE', 'PENDING')

        mock_create_domain.side_effect = [None, exceptions.Backend]

        self.service.create_domain(self.admin_context, domain)

        create_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'CREATE')
        self.assertEqual(0, len(create_statuses))

        # Since consensus is not reached this early, we immediatly call
        # central's update_status.
        self.assertEqual(True, mock_update_status.called)

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(impl_fake.FakeBackend, 'create_domain')
    @patch.object(mdns_rpcapi.MdnsAPI, 'poll_for_serial_number')
    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_create_domain_target_one_failure_consensus(
            self, mock_update_status, mock_notify_zone_changed,
            mock_poll_for_serial_number, mock_create_domain, _):

        self.service.stop()
        self.config(
            threshold_percentage=50,
            group='service:pool_manager')
        self.service = self.start_service('pool_manager')

        domain = self._build_domain('example.org.', 'CREATE', 'PENDING')

        mock_create_domain.side_effect = [None, exceptions.Backend]

        self.service.create_domain(self.admin_context, domain)

        create_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'CREATE')
        self.assertEqual(0, len(create_statuses))

        # Ensure poll_for_serial_number was called for each nameserver.
        self.assertEqual(
            [call(self.admin_context, domain,
                  self.service.pool.nameservers[0], 30, 15, 10, 5),
             call(self.admin_context, domain,
                  self.service.pool.nameservers[1], 30, 15, 10, 5)],
            mock_poll_for_serial_number.call_args_list)

        self.assertEqual(False, mock_update_status.called)

    @patch.object(impl_fake.FakeBackend, 'delete_domain',
                  side_effect=exceptions.Backend)
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_delete_domain(self, mock_update_status, _):
        domain = self._build_domain('example.org.', 'DELETE', 'PENDING')

        self.service.delete_domain(self.admin_context, domain)

        mock_update_status.assert_called_once_with(
            self.admin_context, domain.id, 'ERROR', domain.serial)

    @patch.object(impl_fake.FakeBackend, 'delete_domain')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_delete_domain_target_both_failure(
            self, mock_update_status, mock_delete_domain):

        domain = self._build_domain('example.org.', 'DELETE', 'PENDING')

        mock_delete_domain.side_effect = exceptions.Backend

        self.service.delete_domain(self.admin_context, domain)

        mock_update_status.assert_called_once_with(
            self.admin_context, domain.id, 'ERROR', domain.serial)

    @patch.object(impl_fake.FakeBackend, 'delete_domain')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_delete_domain_target_one_failure(
            self, mock_update_status, mock_delete_domain):

        domain = self._build_domain('example.org.', 'DELETE', 'PENDING')

        mock_delete_domain.side_effect = [None, exceptions.Backend]

        self.service.delete_domain(self.admin_context, domain)

        mock_update_status.assert_called_once_with(
            self.admin_context, domain.id, 'ERROR', domain.serial)

    @patch.object(impl_fake.FakeBackend, 'delete_domain')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_delete_domain_target_one_failure_consensus(
            self, mock_update_status, mock_delete_domain):

        self.service.stop()
        self.config(
            threshold_percentage=50,
            group='service:pool_manager')
        self.service = self.start_service('pool_manager')

        domain = self._build_domain('example.org.', 'DELETE', 'PENDING')

        mock_delete_domain.side_effect = [None, exceptions.Backend]

        self.service.delete_domain(self.admin_context, domain)

        mock_update_status.assert_called_once_with(
            self.admin_context, domain.id, 'ERROR', domain.serial)

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_update_status(self, mock_update_status, _):

        domain = self._build_domain('example.org.', 'UPDATE', 'PENDING')

        self.service.update_status(self.admin_context, domain,
                                   self.service.pool.nameservers[0],
                                   'SUCCESS', domain.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'UPDATE')
        self.assertEqual(0, len(update_statuses))

        # Ensure update_status was not called.
        self.assertEqual(False, mock_update_status.called)

        self.service.update_status(self.admin_context, domain,
                                   self.service.pool.nameservers[1],
                                   'SUCCESS', domain.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'UPDATE')
        self.assertEqual(0, len(update_statuses))

        # Ensure update_status was not called.
        self.assertEqual(False, mock_update_status.called)

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_update_status_both_failure(self, mock_update_status, _):
        domain = self._build_domain('example.org.', 'UPDATE', 'PENDING')

        self.service.update_status(self.admin_context, domain,
                                   self.service.pool.nameservers[0],
                                   'ERROR', domain.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'UPDATE')
        self.assertEqual(0, len(update_statuses))

        mock_update_status.assert_called_once_with(
            self.admin_context, domain.id, 'ERROR', 0)

        # Reset the mock call attributes.
        mock_update_status.reset_mock()

        self.service.update_status(self.admin_context, domain,
                                   self.service.pool.nameservers[1],
                                   'ERROR', domain.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'UPDATE')
        self.assertEqual(0, len(update_statuses))

        mock_update_status.assert_called_once_with(
            self.admin_context, domain.id, 'ERROR', 0)

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_update_status_one_failure(self, mock_update_status, _):
        domain = self._build_domain('example.org.', 'UPDATE', 'PENDING')

        self.service.update_status(self.admin_context, domain,
                                   self.service.pool.nameservers[0],
                                   'SUCCESS', domain.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'UPDATE')
        self.assertEqual(0, len(update_statuses))

        # Ensure update_status was not called.
        self.assertEqual(False, mock_update_status.called)

        self.service.update_status(self.admin_context, domain,
                                   self.service.pool.nameservers[1],
                                   'ERROR', domain.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'UPDATE')
        self.assertEqual(0, len(update_statuses))

        mock_update_status.assert_called_once_with(
            self.admin_context, domain.id, 'ERROR', 0)

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_update_status_one_failure_consensus(self, mock_update_status, _):

        self.service.stop()
        self.config(
            threshold_percentage=50,
            group='service:pool_manager')
        self.service = self.start_service('pool_manager')

        domain = self._build_domain('example.org.', 'UPDATE', 'PENDING')

        self.service.update_status(self.admin_context, domain,
                                   self.service.pool.nameservers[0],
                                   'SUCCESS', domain.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'UPDATE')
        self.assertEqual(0, len(update_statuses))

        # Ensure update_status was not called.
        self.assertEqual(False, mock_update_status.called)

        # Reset the mock call attributes.
        mock_update_status.reset_mock()

        self.service.update_status(self.admin_context, domain,
                                   self.service.pool.nameservers[1],
                                   'ERROR', domain.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'UPDATE')
        self.assertEqual(0, len(update_statuses))

        mock_update_status.assert_called_once_with(
            self.admin_context, domain.id, 'ERROR', 0)

    @patch.object(central_rpcapi.CentralAPI, 'find_domains')
    def test_periodic_sync_not_leader(self, mock_find_domains):
        self.service._update_domain_on_target = Mock(return_value=False)
        self.service._pool_election = Mock()
        self.service._pool_election.is_leader = False
        self.service.update_domain = Mock()

        self.service.periodic_sync()
        self.assertFalse(mock_find_domains.called)

    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_update_domain_no_consensus(self, mock_cent_update_status):
        zone = self._build_domain('example.org.', 'UPDATE', 'PENDING')
        self.service._update_domain_on_target = Mock(return_value=True)
        self.service._exceed_or_meet_threshold = Mock(return_value=False)

        ret = self.service.update_domain(self.admin_context, zone)
        self.assertFalse(ret)

        self.assertEqual(2, self.service._update_domain_on_target.call_count)
        self.assertEqual(1, mock_cent_update_status.call_count)

    @patch.object(mdns_rpcapi.MdnsAPI, 'poll_for_serial_number')
    def test_update_domain(self, mock_mdns_poll):
        zone = self._build_domain('example.org.', 'UPDATE', 'PENDING')
        self.service._update_domain_on_target = Mock(return_value=True)
        self.service._update_domain_on_also_notify = Mock()
        self.service.pool.also_notifies = ['bogus']
        self.service._exceed_or_meet_threshold = Mock(return_value=True)

        # cache.retrieve will throw exceptions.PoolManagerStatusNotFound
        # mdns_api.poll_for_serial_number will be called twice
        ret = self.service.update_domain(self.admin_context, zone)
        self.assertTrue(ret)

        self.assertEqual(2, self.service._update_domain_on_target.call_count)
        self.assertEqual(1, self.service._update_domain_on_also_notify.call_count)  # noqa
        self.assertEqual(2, mock_mdns_poll.call_count)

    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    @patch.object(central_rpcapi.CentralAPI, 'find_domains')
    def test_periodic_sync(self, mock_find_domains,
                           mock_cent_update_status, *a):
        self.service.update_domain = Mock()
        mock_find_domains.return_value = self._build_domains(2, 'UPDATE',
                                                             'PENDING')
        self.service.periodic_sync()

        self.assertEqual(1, mock_find_domains.call_count)
        criterion = mock_find_domains.call_args_list[0][0][1]
        self.assertEqual('!ERROR', criterion['status'])
        self.assertEqual(2, self.service.update_domain.call_count)
        self.assertEqual(0, mock_cent_update_status.call_count)

    @patch.object(pm_module.time, 'sleep')
    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    @patch.object(central_rpcapi.CentralAPI, 'find_domains')
    def test_periodic_sync_with_failing_update(
            self, mock_find_domains, mock_cent_update_status, *mocks):
        self.service.update_domain = Mock(return_value=False)  # fail update
        mock_find_domains.return_value = self._build_domains(3, 'UPDATE',
                                                             'PENDING')
        self.service.periodic_sync()

        self.assertEqual(1, mock_find_domains.call_count)
        criterion = mock_find_domains.call_args_list[0][0][1]
        self.assertEqual('!ERROR', criterion['status'])

        # 3 zones, all failing, with 3 attempts: 9 calls
        self.assertEqual(9, self.service.update_domain.call_count)

        # the zones have been put in ERROR status
        self.assertEqual(3, mock_cent_update_status.call_count)

    @patch.object(pm_module.time, 'sleep')
    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    @patch.object(central_rpcapi.CentralAPI, 'find_domains')
    def test_periodic_sync_with_failing_update_with_exception(
            self, mock_find_domains, mock_cent_update_status, *mocks):
        self.service.update_domain = Mock(side_effect=Exception)
        mock_find_domains.return_value = self._build_domains(3, 'UPDATE',
                                                             'PENDING')
        self.service.periodic_sync()

        self.assertEqual(1, mock_find_domains.call_count)
        criterion = mock_find_domains.call_args_list[0][0][1]
        self.assertEqual('!ERROR', criterion['status'])

        # 3 zones, all failing, with 3 attempts: 9 calls
        self.assertEqual(9, self.service.update_domain.call_count)

        # the zones have been put in ERROR status
        self.assertEqual(3, mock_cent_update_status.call_count)

    # Periodic recovery

    @patch.object(pm_module.time, 'sleep')
    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_periodic_recovery(self, mock_find_domains,
                               mock_cent_update_status, *mocks):

        def mock_get_failed_domains(ctx, action):
            if action == pm_module.DELETE_ACTION:
                return self._build_domains(3, 'DELETE', 'ERROR')
            if action == pm_module.CREATE_ACTION:
                return self._build_domains(4, 'CREATE', 'ERROR')
            if action == pm_module.UPDATE_ACTION:
                return self._build_domains(5, 'UPDATE', 'ERROR')

        self.service._get_failed_domains = mock_get_failed_domains
        self.service.delete_domain = Mock()
        self.service.create_domain = Mock()
        self.service.update_domain = Mock()

        self.service.periodic_recovery()

        self.assertEqual(3, self.service.delete_domain.call_count)
        self.assertEqual(4, self.service.create_domain.call_count)
        self.assertEqual(5, self.service.update_domain.call_count)


class PoolManagerServiceEndToEndTest(PoolManagerServiceNoopTest):

    def setUp(self):
        super(PoolManagerServiceEndToEndTest, self).setUp()

    def _fetch_all_domains(self):
        """Fetch all zones including deleted ones
        """
        query = tables.zones.select()
        return self.storage.session.execute(query).fetchall()

    def _log_all_domains(self, zones, msg=None):
        """Log out a summary of zones
        """
        if msg:
            LOG.debug("--- %s ---" % msg)
        cols = ('name', 'status', 'action', 'deleted', 'deleted_at',
                'parent_domain_id')
        tpl = "%-35s | %-11s | %-11s | %-32s | %-20s | %s"
        LOG.debug(tpl % cols)
        for z in zones:
            LOG.debug(tpl % tuple(z[k] for k in cols))

    def _assert_count_all_domains(self, n):
        """Assert count ALL zones including deleted ones
        """
        zones = self._fetch_all_domains()
        if len(zones) == n:
            return

        msg = "failed: %d zones expected, %d found" % (n, len(zones))
        self._log_all_domains(zones, msg=msg)
        raise Exception("Unexpected number of zones")

    def _assert_num_failed_domains(self, action, n):
        zones = self.service._get_failed_domains(
            self.admin_context, action)
        if len(zones) != n:
            LOG.error("Expected %d failed zones, got %d", n, len(zones))
            self._log_all_domains(zones, msg='listing zones')
            self.assertEqual(n, len(zones))

    def _assert_num_healthy_domains(self, action, n):
        criterion = {
            'action': action,
            'pool_id': pm_module.CONF['service:pool_manager'].pool_id,
            'status': '!%s' % pm_module.ERROR_STATUS
        }
        zones = self.service.central_api.find_domains(self.admin_context,
                                                      criterion)
        if len(zones) != n:
            LOG.error("Expected %d healthy zones, got %d", n, len(zones))
            self._log_all_domains(zones, msg='listing zones')
            self.assertEqual(n, len(zones))

    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    def test_periodic_sync_and_recovery(
            self, mock_cent_update_status, *a):
        # Periodic sync + recovery
        self.service._periodic_sync_retry_interval = 0

        # Create healthy zones, run a periodic sync that will fail
        self.create_domain(name='created.example.com.')
        self._assert_num_healthy_domains(pm_module.CREATE_ACTION, 1)

        z = self.create_domain(name='updated.example.net.')
        z.email = 'info@example.net'
        self.service.central_api.update_domain(self.admin_context, z)
        self._assert_num_healthy_domains(pm_module.UPDATE_ACTION, 1)

        with patch.object(self.service, '_update_domain_on_target',
                          return_value=False):
            self.service.periodic_sync()

        zones = self.service._fetch_healthy_zones(self.admin_context)
        self.assertEqual(0, len(zones))
        self._assert_num_failed_domains(pm_module.CREATE_ACTION, 1)
        self._assert_num_failed_domains(pm_module.UPDATE_ACTION, 1)

        # Now run a periodic_recovery that will fix the zones

        backends = self.service.target_backends
        for tid in self.service.target_backends:
            backends[tid].create_domain = Mock()
            backends[tid].update_domain = Mock()
            backends[tid].delete_domain = Mock()

        self.service.periodic_recovery()

        # There are 2 pool targets in use
        for backend in self.service.target_backends.itervalues():
            self.assertEqual(1, backend.create_domain.call_count)
            self.assertEqual(1, backend.update_domain.call_count)
