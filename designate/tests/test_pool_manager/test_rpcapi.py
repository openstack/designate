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
import mock
from mock import patch
from oslo import messaging

from designate import objects
from designate.pool_manager.rpcapi import PoolManagerAPI
from designate.tests.test_pool_manager import PoolManagerTestCase


class PoolManagerAPITest(PoolManagerTestCase):

    @patch.object(messaging.RPCClient, 'prepare')
    def test_create_domain(self, mock_prepare):
        inner_mock = mock.Mock()
        inner_mock.cast = mock.Mock(return_value=None)
        mock_prepare.return_value = inner_mock

        values = {
            'name': 'example.org.',
            'pool_id': '794ccc2c-d751-44fe-b57f-8894c9f5c842'
        }
        domain = objects.Domain.from_dict(values)
        PoolManagerAPI.get_instance().create_domain(self.admin_context, domain)

        mock_prepare.assert_called_once_with(
            topic='pool_manager.%s' % domain.pool_id)
        mock_prepare.return_value.cast.assert_called_once_with(
            self.admin_context, 'create_domain', domain=domain)

    @patch.object(messaging.RPCClient, 'prepare')
    def test_delete_domain(self, mock_prepare):
        inner_mock = mock.Mock()
        inner_mock.cast = mock.Mock(return_value=None)
        mock_prepare.return_value = inner_mock

        values = {
            'name': 'example.org.',
            'pool_id': '794ccc2c-d751-44fe-b57f-8894c9f5c842'
        }
        domain = objects.Domain.from_dict(values)
        PoolManagerAPI.get_instance().delete_domain(self.admin_context, domain)

        mock_prepare.assert_called_once_with(
            topic='pool_manager.%s' % domain.pool_id)
        mock_prepare.return_value.cast.assert_called_once_with(
            self.admin_context, 'delete_domain', domain=domain)

    @patch.object(messaging.RPCClient, 'prepare')
    def test_update_domain(self, mock_prepare):
        inner_mock = mock.Mock()
        inner_mock.cast = mock.Mock(return_value=None)
        mock_prepare.return_value = inner_mock

        values = {
            'name': 'example.org.',
            'pool_id': '794ccc2c-d751-44fe-b57f-8894c9f5c842'
        }
        domain = objects.Domain.from_dict(values)
        PoolManagerAPI.get_instance().update_domain(self.admin_context, domain)

        mock_prepare.assert_called_once_with(
            topic='pool_manager.%s' % domain.pool_id)
        mock_prepare.return_value.cast.assert_called_once_with(
            self.admin_context, 'update_domain', domain=domain)

    @patch.object(messaging.RPCClient, 'prepare')
    def test_update_status(self, mock_prepare):
        inner_mock = mock.Mock()
        inner_mock.cast = mock.Mock(return_value=None)
        mock_prepare.return_value = inner_mock

        values = {
            'name': 'example.org.',
            'pool_id': '794ccc2c-d751-44fe-b57f-8894c9f5c842'
        }
        domain = objects.Domain.from_dict(values)
        values = {
            'host': '127.0.0.1',
            'port': '53'
        }
        nameserver = objects.PoolNameserver.from_dict(values)
        PoolManagerAPI.get_instance().update_status(
            self.admin_context, domain, nameserver, 'SUCCESS', 1)

        mock_prepare.assert_called_once_with(
            topic='pool_manager.%s' % domain.pool_id)
        mock_prepare.return_value.cast.assert_called_once_with(
            self.admin_context, 'update_status', domain=domain,
            nameserver=nameserver, status='SUCCESS', actual_serial=1)
