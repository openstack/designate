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
import testtools
from oslo.config import cfg
from mock import call
from mock import patch

from designate import exceptions
from designate.backend import impl_fake
from designate.central import rpcapi as central_rpcapi
from designate.mdns import rpcapi as mdns_rpcapi
from designate.tests.test_pool_manager import PoolManagerTestCase


class PoolManagerServiceTest(PoolManagerTestCase):

    def setUp(self):
        super(PoolManagerServiceTest, self).setUp()

        self.config(
            backends=['fake'],
            threshold_percentage=100,
            enable_recovery_timer=False,
            enable_sync_timer=False,
            group='service:pool_manager')

        self.config(
            server_ids=['f278782a-07dc-4502-9177-b5d85c5f7c7e',
                        'a38703f2-b71e-4e5b-ab22-30caaed61dfd'],
            group='backend:fake')

        section_name = 'backend:fake:f278782a-07dc-4502-9177-b5d85c5f7c7e'
        server_opts = [
            cfg.StrOpt('host', default='10.0.0.2'),
            cfg.IntOpt('port', default=53),
            cfg.StrOpt('tsig_key')
        ]
        cfg.CONF.register_group(cfg.OptGroup(name=section_name))
        cfg.CONF.register_opts(server_opts, group=section_name)

        section_name = 'backend:fake:a38703f2-b71e-4e5b-ab22-30caaed61dfd'
        server_opts = [
            cfg.StrOpt('host', default='10.0.0.3'),
            cfg.IntOpt('port', default=53),
            cfg.StrOpt('tsig_key')
        ]
        cfg.CONF.register_group(cfg.OptGroup(name=section_name))
        cfg.CONF.register_opts(server_opts, group=section_name)

        self.service = self.start_service('pool_manager')
        self.cache = self.service.cache

    def test_stop(self):
        # NOTE: Start is already done by the fixture in start_service()
        self.service.stop()

    def test_pool_instance_topic(self):
        self.assertEqual(
            'pool_manager.%s' % cfg.CONF['service:pool_manager'].pool_id,
            self.service.topic)

    def test_no_pool_servers_configured(self):
        self.service.stop()
        self.config(
            server_ids=[],
            group='backend:fake'
        )

        with testtools.ExpectedException(exceptions.NoPoolServersConfigured):
            self.start_service('pool_manager')

    @patch.object(mdns_rpcapi.MdnsAPI, 'poll_for_serial_number')
    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    def test_create_domain(self, mock_notify_zone_changed,
                           mock_poll_for_serial_number):
        domain = self.create_domain(name='example.org.')

        # Reset the mock call attributes.
        mock_notify_zone_changed.reset_mock()
        mock_poll_for_serial_number.reset_mock()

        self.service.create_domain(self.admin_context, domain)

        create_statuses = self._find_pool_manager_statuses(
            self.admin_context, 'CREATE', domain)
        self.assertEqual(0, len(create_statuses))

        # Ensure notify_zone_changed and poll_for_serial_number
        # was called for each backend server.
        self.assertEqual(2, mock_notify_zone_changed.call_count)
        self.assertEqual(
            [call(self.admin_context, domain,
                  self.service.server_backends[0]['server'], 30, 2, 3, 0),
             call(self.admin_context, domain,
                  self.service.server_backends[1]['server'], 30, 2, 3, 0)],
            mock_notify_zone_changed.call_args_list)
        self.assertEqual(2, mock_poll_for_serial_number.call_count)
        self.assertEqual(
            [call(self.admin_context, domain,
                  self.service.server_backends[0]['server'], 30, 2, 3, 1),
             call(self.admin_context, domain,
                  self.service.server_backends[1]['server'], 30, 2, 3, 1)],
            mock_poll_for_serial_number.call_args_list)

    @patch.object(impl_fake.FakeBackend, 'create_domain')
    @patch.object(mdns_rpcapi.MdnsAPI, 'poll_for_serial_number')
    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    def test_create_domain_backend_both_failure(self, mock_notify_zone_changed,
                                                mock_poll_for_serial_number,
                                                mock_create_domain):
        domain = self.create_domain(name='example.org.')

        # Reset the mock call attributes.
        mock_notify_zone_changed.reset_mock()
        mock_poll_for_serial_number.reset_mock()
        mock_create_domain.side_effect = exceptions.Backend

        self.service.create_domain(self.admin_context, domain)

        create_statuses = self._find_pool_manager_statuses(
            self.admin_context, 'CREATE', domain)
        self.assertEqual(2, len(create_statuses))
        self.assertEqual('ERROR', create_statuses[0].status)
        self.assertEqual('ERROR', create_statuses[1].status)

        update_statuses = self._find_pool_manager_statuses(
            self.admin_context, 'UPDATE', domain)
        self.assertEqual(0, len(update_statuses))

        # Ensure notify_zone_changed and poll_for_serial_number
        # were never called.
        self.assertEqual(False, mock_notify_zone_changed.called)
        self.assertEqual(False, mock_poll_for_serial_number.called)

    @patch.object(impl_fake.FakeBackend, 'create_domain')
    @patch.object(mdns_rpcapi.MdnsAPI, 'poll_for_serial_number')
    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    def test_create_domain_backend_one_failure(self, mock_notify_zone_changed,
                                               mock_poll_for_serial_number,
                                               mock_create_domain):
        domain = self.create_domain(name='example.org.')

        # Reset the mock call attributes.
        mock_notify_zone_changed.reset_mock()
        mock_poll_for_serial_number.reset_mock()
        mock_create_domain.side_effect = [None, exceptions.Backend]

        self.service.create_domain(self.admin_context, domain)

        create_statuses = self._find_pool_manager_statuses(
            self.admin_context, 'CREATE', domain)
        self.assertEqual(2, len(create_statuses))
        self.assertEqual('SUCCESS', create_statuses[0].status)
        self.assertEqual('ERROR', create_statuses[1].status)

        mock_notify_zone_changed.assert_called_once_with(
            self.admin_context, domain,
            self.service.server_backends[0]['server'], 30, 2, 3, 0)
        mock_poll_for_serial_number.assert_called_once_with(
            self.admin_context, domain,
            self.service.server_backends[0]['server'], 30, 2, 3, 1)

    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_delete_domain(self, mock_update_status):
        domain = self.create_domain(name='example.org.')

        self.service.create_domain(self.admin_context, domain)

        create_statuses = self._find_pool_manager_statuses(
            self.admin_context, 'CREATE', domain)
        self.assertEqual(0, len(create_statuses))

        self.service.delete_domain(self.admin_context, domain)

        delete_statuses = self._find_pool_manager_statuses(
            self.admin_context, 'DELETE', domain)
        self.assertEqual(0, len(delete_statuses))

        mock_update_status.assert_called_once_with(
            self.admin_context, domain.id, 'SUCCESS', domain.serial)

    @patch.object(impl_fake.FakeBackend, 'delete_domain')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_delete_domain_backend_both_failure(self, mock_update_status,
                                                mock_delete_domain):
        domain = self.create_domain(name='example.org.')

        self.service.create_domain(self.admin_context, domain)

        create_statuses = self._find_pool_manager_statuses(
            self.admin_context, 'CREATE', domain)
        self.assertEqual(0, len(create_statuses))

        mock_delete_domain.side_effect = exceptions.Backend

        self.service.delete_domain(self.admin_context, domain)

        delete_statuses = self._find_pool_manager_statuses(
            self.admin_context, 'DELETE', domain)
        self.assertEqual(2, len(delete_statuses))
        self.assertEqual('ERROR', delete_statuses[0].status)
        self.assertEqual('ERROR', delete_statuses[1].status)

        mock_update_status.assert_called_once_with(
            self.admin_context, domain.id, 'ERROR', domain.serial)

    @patch.object(impl_fake.FakeBackend, 'delete_domain')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_delete_domain_backend_one_failure(self, mock_update_status,
                                               mock_delete_domain):
        domain = self.create_domain(name='example.org.')

        self.service.create_domain(self.admin_context, domain)

        create_statuses = self._find_pool_manager_statuses(
            self.admin_context, 'CREATE', domain)
        self.assertEqual(0, len(create_statuses))

        mock_delete_domain.side_effect = [None, exceptions.Backend]

        self.service.delete_domain(self.admin_context, domain)

        delete_statuses = self._find_pool_manager_statuses(
            self.admin_context, 'DELETE', domain)
        self.assertEqual(2, len(delete_statuses))
        self.assertEqual('SUCCESS', delete_statuses[0].status)
        self.assertEqual('ERROR', delete_statuses[1].status)

        mock_update_status.assert_called_once_with(
            self.admin_context, domain.id, 'ERROR', domain.serial)

    @patch.object(impl_fake.FakeBackend, 'delete_domain')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_delete_domain_backend_one_failure_success(
            self, mock_update_status, mock_delete_domain):

        self.service.stop()
        self.config(
            threshold_percentage=50,
            group='service:pool_manager')
        self.service = self.start_service('pool_manager')

        domain = self.create_domain(name='example.org.')

        self.service.create_domain(self.admin_context, domain)

        create_statuses = self._find_pool_manager_statuses(
            self.admin_context, 'CREATE', domain)
        self.assertEqual(0, len(create_statuses))

        mock_delete_domain.side_effect = [None, exceptions.Backend]

        self.service.delete_domain(self.admin_context, domain)

        delete_statuses = self._find_pool_manager_statuses(
            self.admin_context, 'DELETE', domain)
        self.assertEqual(2, len(delete_statuses))
        self.assertEqual('SUCCESS', delete_statuses[0].status)
        self.assertEqual('ERROR', delete_statuses[1].status)

        mock_update_status.assert_called_once_with(
            self.admin_context, domain.id, 'SUCCESS', domain.serial)

    @patch.object(mdns_rpcapi.MdnsAPI, 'poll_for_serial_number')
    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    def test_update_domain(self, mock_notify_zone_changed,
                           mock_poll_for_serial_number):
        domain = self.create_domain(name='example.org.')

        self.service.create_domain(self.admin_context, domain)

        create_statuses = self._find_pool_manager_statuses(
            self.admin_context, 'CREATE', domain)
        self.assertEqual(0, len(create_statuses))

        # Reset the mock call attributes.
        mock_notify_zone_changed.reset_mock()
        mock_poll_for_serial_number.reset_mock()

        self.service.update_domain(self.admin_context, domain)

        # Ensure notify_zone_changed and poll_for_serial_number
        # was called for each backend server.
        self.assertEqual(2, mock_notify_zone_changed.call_count)
        self.assertEqual(
            [call(self.admin_context, domain,
                  self.service.server_backends[0]['server'], 30, 2, 3, 0),
             call(self.admin_context, domain,
                  self.service.server_backends[1]['server'], 30, 2, 3, 0)],
            mock_notify_zone_changed.call_args_list)
        self.assertEqual(2, mock_poll_for_serial_number.call_count)
        self.assertEqual(
            [call(self.admin_context, domain,
                  self.service.server_backends[0]['server'], 30, 2, 3, 1),
             call(self.admin_context, domain,
                  self.service.server_backends[1]['server'], 30, 2, 3, 1)],
            mock_poll_for_serial_number.call_args_list)

    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_update_status(self, mock_update_status):
        domain = self.create_domain(name='example.org.')

        self.service.create_domain(self.admin_context, domain)

        create_statuses = self._find_pool_manager_statuses(
            self.admin_context, 'CREATE', domain)
        self.assertEqual(0, len(create_statuses))

        self.service.update_status(self.admin_context, domain,
                                   self.service.server_backends[0]['server'],
                                   'SUCCESS', domain.serial)

        update_statuses = self._find_pool_manager_statuses(
            self.admin_context, 'UPDATE', domain)
        self.assertEqual(1, len(update_statuses))
        self.assertEqual('SUCCESS', update_statuses[0].status)
        self.assertEqual(domain.serial, update_statuses[0].serial_number)

        # Ensure update_status was not called.
        self.assertEqual(False, mock_update_status.called)

        self.service.update_status(self.admin_context, domain,
                                   self.service.server_backends[1]['server'],
                                   'SUCCESS', domain.serial)

        update_statuses = self._find_pool_manager_statuses(
            self.admin_context, 'UPDATE', domain)
        self.assertEqual(0, len(update_statuses))

        mock_update_status.assert_called_once_with(
            self.admin_context, domain.id, 'SUCCESS', domain.serial)

    def _find_pool_manager_statuses(self, context, action,
                                    domain=None, status=None):
        criterion = {
            'action': action
        }
        if domain:
            criterion['domain_id'] = domain.id
        if status:
            criterion['status'] = status

        return self.cache.find_pool_manager_statuses(
            context, criterion=criterion)
