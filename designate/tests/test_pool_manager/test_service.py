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
from oslo import messaging
from oslo.config import cfg
from mock import call
from mock import patch

from designate import exceptions
from designate import objects
from designate.backend import impl_fake
from designate.central import rpcapi as central_rpcapi
from designate.mdns import rpcapi as mdns_rpcapi
from designate.tests.test_pool_manager import PoolManagerTestCase


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
    def _build_domain(name, action, status):
        values = {
            'id': '75ea1626-eea7-46b5-acb7-41e5897c2d40',
            'name': name,
            'pool_id': '794ccc2c-d751-44fe-b57f-8894c9f5c842',
            'action': action,
            'serial': 1422062497,
            'status': status
        }
        return objects.Domain.from_dict(values)

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

        # Ensure notify_zone_changed and poll_for_serial_number
        # was called for each nameserver.
        self.assertEqual(2, mock_notify_zone_changed.call_count)
        self.assertEqual(
            [call(self.admin_context, domain,
                  self.service.pool.nameservers[0], 30, 2, 3, 0),
             call(self.admin_context, domain,
                  self.service.pool.nameservers[1], 30, 2, 3, 0)],
            mock_notify_zone_changed.call_args_list)
        self.assertEqual(2, mock_poll_for_serial_number.call_count)
        self.assertEqual(
            [call(self.admin_context, domain,
                  self.service.pool.nameservers[0], 30, 2, 3, 1),
             call(self.admin_context, domain,
                  self.service.pool.nameservers[1], 30, 2, 3, 1)],
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

        # Ensure notify_zone_changed and poll_for_serial_number
        # was called for each nameserver.
        self.assertEqual(2, mock_notify_zone_changed.call_count)
        self.assertEqual(
            [call(self.admin_context, domain,
                  self.service.pool.nameservers[0], 30, 2, 3, 0),
             call(self.admin_context, domain,
                  self.service.pool.nameservers[1], 30, 2, 3, 0)],
            mock_notify_zone_changed.call_args_list)
        self.assertEqual(2, mock_poll_for_serial_number.call_count)
        self.assertEqual(
            [call(self.admin_context, domain,
                  self.service.pool.nameservers[0], 30, 2, 3, 1),
             call(self.admin_context, domain,
                  self.service.pool.nameservers[1], 30, 2, 3, 1)],
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
