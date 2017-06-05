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
import oslo_messaging as messaging

from designate import objects
from designate.pool_manager.rpcapi import PoolManagerAPI
from designate.tests.test_pool_manager import PoolManagerTestCase


class PoolManagerAPITest(PoolManagerTestCase):

    @patch.object(messaging.RPCClient, 'prepare')
    def test_create_zone(self, mock_prepare):
        inner_mock = mock.Mock()
        inner_mock.cast = mock.Mock(return_value=None)
        mock_prepare.return_value = inner_mock

        values = {
            'name': 'example.org.',
            'pool_id': '794ccc2c-d751-44fe-b57f-8894c9f5c842'
        }
        zone = objects.Zone.from_dict(values)
        PoolManagerAPI.get_instance().create_zone(self.admin_context, zone)

        mock_prepare.assert_called_once_with(
            topic='pool_manager.%s' % zone.pool_id)
        mock_prepare.return_value.cast.assert_called_once_with(
            self.admin_context, 'create_zone', zone=zone)

    @patch.object(messaging.RPCClient, 'prepare')
    def test_delete_zone(self, mock_prepare):
        inner_mock = mock.Mock()
        inner_mock.cast = mock.Mock(return_value=None)
        mock_prepare.return_value = inner_mock

        values = {
            'name': 'example.org.',
            'pool_id': '794ccc2c-d751-44fe-b57f-8894c9f5c842'
        }
        zone = objects.Zone.from_dict(values)
        PoolManagerAPI.get_instance().delete_zone(self.admin_context, zone)

        mock_prepare.assert_called_once_with(
            topic='pool_manager.%s' % zone.pool_id)
        mock_prepare.return_value.cast.assert_called_once_with(
            self.admin_context, 'delete_zone', zone=zone)

    @patch.object(messaging.RPCClient, 'prepare')
    def test_update_zone(self, mock_prepare):
        inner_mock = mock.Mock()
        inner_mock.cast = mock.Mock(return_value=None)
        mock_prepare.return_value = inner_mock

        values = {
            'name': 'example.org.',
            'pool_id': '794ccc2c-d751-44fe-b57f-8894c9f5c842'
        }
        zone = objects.Zone.from_dict(values)
        PoolManagerAPI.get_instance().update_zone(self.admin_context, zone)

        mock_prepare.assert_called_once_with(
            topic='pool_manager.%s' % zone.pool_id)
        mock_prepare.return_value.cast.assert_called_once_with(
            self.admin_context, 'update_zone', zone=zone)

    @patch.object(messaging.RPCClient, 'prepare')
    def test_update_status(self, mock_prepare):
        inner_mock = mock.Mock()
        inner_mock.cast = mock.Mock(return_value=None)
        mock_prepare.return_value = inner_mock

        values = {
            'name': 'example.org.',
            'pool_id': '794ccc2c-d751-44fe-b57f-8894c9f5c842'
        }
        zone = objects.Zone.from_dict(values)
        values = {
            'host': '127.0.0.1',
            'port': 53
        }
        nameserver = objects.PoolNameserver.from_dict(values)
        PoolManagerAPI.get_instance().update_status(
            self.admin_context, zone, nameserver, 'SUCCESS', 1)

        mock_prepare.assert_called_once_with(
            topic='pool_manager.%s' % zone.pool_id)
        mock_prepare.return_value.cast.assert_called_once_with(
            self.admin_context, 'update_status', zone=zone,
            nameserver=nameserver, status='SUCCESS', actual_serial=1)
