# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
from unittest import mock

from neutronclient.common import exceptions as neutron_exceptions
from neutronclient.v2_0 import client as clientv20
from oslo_config import cfg
from oslo_config import fixture as cfg_fixture
import oslotest.base

from designate import context
from designate import exceptions
from designate.network_api import get_network_api
from designate.network_api import neutron

CONF = cfg.CONF


class NeutronNetworkAPITest(oslotest.base.BaseTestCase):
    def setUp(self):
        super(NeutronNetworkAPITest, self).setUp()
        self.useFixture(cfg_fixture.Config(CONF))

        CONF.set_override(
            'endpoints', ['RegionOne|http://localhost:9696'],
            'network_api:neutron'
        )

        self.api = get_network_api('neutron')
        self.context = context.DesignateContext(
            user_id='12345', project_id='54321',
        )

    @mock.patch.object(clientv20, 'Client')
    def test_get_client(self, mock_client):
        neutron.get_client(self.context, 'http://localhost:9696')

        _, kwargs = mock_client.call_args

        self.assertIn('endpoint_url', kwargs)
        self.assertIn('timeout', kwargs)
        self.assertIn('insecure', kwargs)
        self.assertIn('ca_cert', kwargs)

        self.assertNotIn('token', kwargs)
        self.assertNotIn('username', kwargs)

        self.assertEqual('http://localhost:9696', kwargs['endpoint_url'])

    @mock.patch.object(clientv20, 'Client')
    def test_get_client_using_token(self, mock_client):
        self.context = context.DesignateContext(
            user_id='12345', project_id='54321', auth_token='token',
        )

        neutron.get_client(self.context, 'http://localhost:9696')

        _, kwargs = mock_client.call_args

        self.assertIn('token', kwargs)
        self.assertIn('auth_strategy', kwargs)
        self.assertNotIn('username', kwargs)

        self.assertEqual('http://localhost:9696', kwargs['endpoint_url'])
        self.assertEqual(self.context.auth_token, kwargs['token'])

    @mock.patch.object(clientv20, 'Client')
    def test_get_client_using_admin(self, mock_client):
        CONF.set_override(
            'admin_username', 'test',
            'network_api:neutron'
        )

        neutron.get_client(self.context, 'http://localhost:9696')

        _, kwargs = mock_client.call_args

        self.assertIn('auth_strategy', kwargs)
        self.assertIn('username', kwargs)
        self.assertIn('project_name', kwargs)
        self.assertIn('password', kwargs)
        self.assertIn('auth_url', kwargs)
        self.assertNotIn('token', kwargs)

        self.assertEqual('http://localhost:9696', kwargs['endpoint_url'])
        self.assertEqual(
            kwargs['username'], CONF['network_api:neutron'].admin_username
        )

    @mock.patch.object(neutron, 'get_client')
    def test_list_floatingips(self, get_client):
        driver = mock.Mock()
        driver.list_floatingips.return_value = {'floatingips': [
            {
                'id': '123',
                'floating_ip_address': '192.168.0.100',
                'region': 'RegionOne'
            },
            {
                'id': '456',
                'floating_ip_address': '192.168.0.200',
                'region': 'RegionOne'
            },
        ]}
        get_client.return_value = driver

        self.assertEqual(2, len(self.api.list_floatingips(self.context)))

    @mock.patch.object(neutron, 'get_client')
    def test_list_floatingips_unauthorized(self, get_client):
        driver = mock.Mock()
        driver.list_floatingips.side_effect = neutron_exceptions.Unauthorized
        get_client.return_value = driver

        self.assertEqual(0, len(self.api.list_floatingips(self.context)))

    @mock.patch.object(neutron, 'get_client')
    def test_list_floatingips_communication_failure(self, get_client):
        driver = mock.Mock()
        driver.list_floatingips.side_effect = (
            neutron_exceptions.NeutronException
        )
        get_client.return_value = driver

        self.assertRaises(
            exceptions.NeutronCommunicationFailure,
            self.api.list_floatingips, self.context
        )
