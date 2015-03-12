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


class PoolManagerServiceMemcacheTest(PoolManagerTestCase):

    def setUp(self):
        super(PoolManagerServiceMemcacheTest, self).setUp()

        self.config(
            backends=['fake'],
            threshold_percentage=100,
            enable_recovery_timer=False,
            enable_sync_timer=False,
            cache_driver='memcache',
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
        self.assertEqual(2, len(create_statuses))
        self.assertEqual(None, create_statuses[0].status)
        self.assertEqual(None, create_statuses[1].status)

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

        self.assertEqual(False, mock_update_status.called)

    @patch.object(impl_fake.FakeBackend, 'create_domain')
    @patch.object(mdns_rpcapi.MdnsAPI, 'poll_for_serial_number')
    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_create_domain_backend_both_failure(
            self, mock_update_status, mock_notify_zone_changed,
            mock_poll_for_serial_number, mock_create_domain):

        domain = self._build_domain('example.org.', 'CREATE', 'PENDING')

        mock_create_domain.side_effect = exceptions.Backend

        self.service.create_domain(self.admin_context, domain)

        create_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'CREATE')
        self.assertEqual(2, len(create_statuses))
        self.assertEqual('ERROR', create_statuses[0].status)
        self.assertEqual('ERROR', create_statuses[1].status)

        # Ensure notify_zone_changed and poll_for_serial_number
        # were never called.
        self.assertEqual(False, mock_notify_zone_changed.called)
        self.assertEqual(False, mock_poll_for_serial_number.called)

        mock_update_status.assert_called_once_with(
            self.admin_context, domain.id, 'ERROR', domain.serial)

    @patch.object(impl_fake.FakeBackend, 'create_domain')
    @patch.object(mdns_rpcapi.MdnsAPI, 'poll_for_serial_number')
    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_create_domain_backend_one_failure(
            self, mock_update_status, mock_notify_zone_changed,
            mock_poll_for_serial_number, mock_create_domain):

        domain = self._build_domain('example.org.', 'CREATE', 'PENDING')

        mock_create_domain.side_effect = [None, exceptions.Backend]

        self.service.create_domain(self.admin_context, domain)

        create_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'CREATE')
        self.assertEqual(2, len(create_statuses))
        self.assertEqual(None, create_statuses[0].status)
        self.assertEqual('ERROR', create_statuses[1].status)

        mock_notify_zone_changed.assert_called_once_with(
            self.admin_context, domain,
            self.service.server_backends[0]['server'], 30, 2, 3, 0)
        mock_poll_for_serial_number.assert_called_once_with(
            self.admin_context, domain,
            self.service.server_backends[0]['server'], 30, 2, 3, 1)

        self.assertEqual(False, mock_update_status.called)

    @patch.object(impl_fake.FakeBackend, 'create_domain')
    @patch.object(mdns_rpcapi.MdnsAPI, 'poll_for_serial_number')
    @patch.object(mdns_rpcapi.MdnsAPI, 'notify_zone_changed')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_create_domain_backend_one_failure_consensus(
            self, mock_update_status, mock_notify_zone_changed,
            mock_poll_for_serial_number, mock_create_domain):

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
        self.assertEqual(2, len(create_statuses))
        self.assertEqual(None, create_statuses[0].status)
        self.assertEqual('ERROR', create_statuses[1].status)

        mock_notify_zone_changed.assert_called_once_with(
            self.admin_context, domain,
            self.service.server_backends[0]['server'], 30, 2, 3, 0)
        mock_poll_for_serial_number.assert_called_once_with(
            self.admin_context, domain,
            self.service.server_backends[0]['server'], 30, 2, 3, 1)

        mock_update_status.assert_called_once_with(
            self.admin_context, domain.id, 'ERROR', domain.serial)

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_delete_domain(self, mock_update_status, _):

        domain = self._build_domain('example.org.', 'DELETE', 'PENDING')

        self.service.delete_domain(self.admin_context, domain)

        delete_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'DELETE')
        self.assertEqual(0, len(delete_statuses))

        mock_update_status.assert_called_once_with(
            self.admin_context, domain.id, 'SUCCESS', domain.serial)

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(impl_fake.FakeBackend, 'delete_domain')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_delete_domain_backend_both_failure(
            self, mock_update_status, mock_delete_domain, _):

        domain = self._build_domain('example.org.', 'DELETE', 'PENDING')

        mock_delete_domain.side_effect = exceptions.Backend

        self.service.delete_domain(self.admin_context, domain)

        delete_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'DELETE')
        self.assertEqual(2, len(delete_statuses))
        self.assertEqual('ERROR', delete_statuses[0].status)
        self.assertEqual('ERROR', delete_statuses[1].status)

        mock_update_status.assert_called_once_with(
            self.admin_context, domain.id, 'ERROR', domain.serial)

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(impl_fake.FakeBackend, 'delete_domain')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_delete_domain_backend_one_failure(
            self, mock_update_status, mock_delete_domain, _):

        domain = self._build_domain('example.org.', 'DELETE', 'PENDING')

        mock_delete_domain.side_effect = [None, exceptions.Backend]

        self.service.delete_domain(self.admin_context, domain)

        delete_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'DELETE')
        self.assertEqual(2, len(delete_statuses))
        self.assertEqual('SUCCESS', delete_statuses[0].status)
        self.assertEqual('ERROR', delete_statuses[1].status)

        mock_update_status.assert_called_once_with(
            self.admin_context, domain.id, 'ERROR', domain.serial)

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(impl_fake.FakeBackend, 'delete_domain')
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_delete_domain_backend_one_failure_consensus(
            self, mock_update_status, mock_delete_domain, _):

        self.service.stop()
        self.config(
            threshold_percentage=50,
            group='service:pool_manager')
        self.service = self.start_service('pool_manager')

        domain = self._build_domain('example.org.', 'DELETE', 'PENDING')

        mock_delete_domain.side_effect = [None, exceptions.Backend]

        self.service.delete_domain(self.admin_context, domain)

        delete_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'DELETE')
        self.assertEqual(2, len(delete_statuses))
        self.assertEqual('SUCCESS', delete_statuses[0].status)
        self.assertEqual('ERROR', delete_statuses[1].status)

        mock_update_status.assert_called_once_with(
            self.admin_context, domain.id, 'SUCCESS', domain.serial)

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_update_status(self, mock_update_status, _):

        domain = self._build_domain('example.org.', 'UPDATE', 'PENDING')

        self.service.update_status(self.admin_context, domain,
                                   self.service.server_backends[0]['server'],
                                   'SUCCESS', domain.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'UPDATE')
        self.assertEqual(1, len(update_statuses))
        self.assertEqual('SUCCESS', update_statuses[0].status)
        self.assertEqual(domain.serial, update_statuses[0].serial_number)

        # Ensure update_status was not called.
        self.assertEqual(False, mock_update_status.called)

        self.service.update_status(self.admin_context, domain,
                                   self.service.server_backends[1]['server'],
                                   'SUCCESS', domain.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'UPDATE')
        self.assertEqual(0, len(update_statuses))

        mock_update_status.assert_called_once_with(
            self.admin_context, domain.id, 'SUCCESS', domain.serial)

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_update_status_both_failure(self, mock_update_status, _):

        domain = self._build_domain('example.org.', 'UPDATE', 'PENDING')

        self.service.update_status(self.admin_context, domain,
                                   self.service.server_backends[0]['server'],
                                   'ERROR', domain.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'UPDATE')
        self.assertEqual(1, len(update_statuses))
        self.assertEqual('ERROR', update_statuses[0].status)
        self.assertEqual(domain.serial, update_statuses[0].serial_number)

        mock_update_status.assert_called_once_with(
            self.admin_context, domain.id, 'ERROR', 0)

        # Reset the mock call attributes.
        mock_update_status.reset_mock()

        self.service.update_status(self.admin_context, domain,
                                   self.service.server_backends[1]['server'],
                                   'ERROR', domain.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'UPDATE')
        self.assertEqual(2, len(update_statuses))
        self.assertEqual('ERROR', update_statuses[0].status)
        self.assertEqual(domain.serial, update_statuses[0].serial_number)
        self.assertEqual('ERROR', update_statuses[1].status)
        self.assertEqual(domain.serial, update_statuses[1].serial_number)

        self.assertEqual(2, mock_update_status.call_count)
        self.assertEqual(
            [call(self.admin_context, domain.id, 'SUCCESS', domain.serial),
             call(self.admin_context, domain.id, 'ERROR', 0)],
            mock_update_status.call_args_list)

    @patch.object(mdns_rpcapi.MdnsAPI, 'get_serial_number',
                  side_effect=messaging.MessagingException)
    @patch.object(central_rpcapi.CentralAPI, 'update_status')
    def test_update_status_one_failure(self, mock_update_status, _):

        domain = self._build_domain('example.org.', 'UPDATE', 'PENDING')

        self.service.update_status(self.admin_context, domain,
                                   self.service.server_backends[0]['server'],
                                   'SUCCESS', domain.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'UPDATE')
        self.assertEqual(1, len(update_statuses))
        self.assertEqual('SUCCESS', update_statuses[0].status)
        self.assertEqual(domain.serial, update_statuses[0].serial_number)

        # Ensure update_status was not called.
        self.assertEqual(False, mock_update_status.called)

        self.service.update_status(self.admin_context, domain,
                                   self.service.server_backends[1]['server'],
                                   'ERROR', domain.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'UPDATE')
        self.assertEqual(2, len(update_statuses))
        self.assertEqual('SUCCESS', update_statuses[0].status)
        self.assertEqual(domain.serial, update_statuses[0].serial_number)
        self.assertEqual('ERROR', update_statuses[1].status)
        self.assertEqual(domain.serial, update_statuses[1].serial_number)

        self.assertEqual(2, mock_update_status.call_count)
        self.assertEqual(
            [call(self.admin_context, domain.id, 'SUCCESS', domain.serial),
             call(self.admin_context, domain.id, 'ERROR', 0)],
            mock_update_status.call_args_list)

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
                                   self.service.server_backends[0]['server'],
                                   'SUCCESS', domain.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'UPDATE')
        self.assertEqual(1, len(update_statuses))
        self.assertEqual('SUCCESS', update_statuses[0].status)
        self.assertEqual(domain.serial, update_statuses[0].serial_number)

        mock_update_status.assert_called_once_with(
            self.admin_context, domain.id, 'SUCCESS', domain.serial)

        # Reset the mock call attributes.
        mock_update_status.reset_mock()

        self.service.update_status(self.admin_context, domain,
                                   self.service.server_backends[1]['server'],
                                   'ERROR', domain.serial)

        update_statuses = self.service._retrieve_statuses(
            self.admin_context, domain, 'UPDATE')
        self.assertEqual(2, len(update_statuses))
        self.assertEqual('SUCCESS', update_statuses[0].status)
        self.assertEqual(domain.serial, update_statuses[0].serial_number)
        self.assertEqual('ERROR', update_statuses[1].status)
        self.assertEqual(domain.serial, update_statuses[1].serial_number)

        self.assertEqual(2, mock_update_status.call_count)
        self.assertEqual(
            [call(self.admin_context, domain.id, 'SUCCESS', domain.serial),
             call(self.admin_context, domain.id, 'ERROR', 0)],
            mock_update_status.call_args_list)
