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

from openstack import exceptions as sdk_exceptions
from oslo_config import fixture as cfg_fixture
import oslotest.base

import designate.conf
from designate import context
from designate import exceptions
from designate.network_api import get_network_api
from designate.network_api import neutron
from designate import version


CONF = designate.conf.CONF


class NeutronNetworkAPITest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

        CONF.set_override(
            'endpoints', ['RegionOne|http://192.0.2.5:9696'],
            'network_api:neutron'
        )
        self.ca_certificates_file = 'fake_ca_cert_file'
        self.client_certificate_file = 'fake_client_cert_file'
        CONF.set_override('client_certificate_file',
                          self.client_certificate_file,
                          'network_api:neutron')
        self.neutron_timeout = 100
        CONF.set_override('timeout', self.neutron_timeout,
                          'network_api:neutron')

        self.api = get_network_api('neutron')
        self.context = context.DesignateContext(
            user_id='12345', project_id='54321',
        )

    @mock.patch('keystoneauth1.token_endpoint.Token')
    @mock.patch('keystoneauth1.session.Session')
    @mock.patch('openstack.connection.Connection')
    def test_get_client(self, mock_client, mock_session, mock_token):
        auth_token_mock = mock.MagicMock()
        mock_token.return_value = auth_token_mock

        user_session_mock = mock.MagicMock()
        mock_session.return_value = user_session_mock

        connection_mock = mock.MagicMock()
        mock_client.return_value = connection_mock

        self.context = context.DesignateContext(
            user_id='12345', project_id='54321', auth_token='token',
        )
        endpoint = 'http://192.0.2.5:9696'

        result = neutron.get_client(self.context, endpoint)

        mock_token.assert_called_once_with(endpoint, self.context.auth_token)

        mock_session.assert_called_once_with(
            auth=auth_token_mock, verify=True,
            cert=self.client_certificate_file, timeout=self.neutron_timeout,
            app_name='designate',
            app_version=version.version_info.version_string())

        self.assertEqual(connection_mock, result)

        # Test with CA certs file configuration
        mock_token.reset_mock()
        mock_session.reset_mock()

        CONF.set_override('ca_certificates_file', self.ca_certificates_file,
                          'network_api:neutron')

        result = neutron.get_client(self.context, endpoint)

        mock_token.assert_called_once_with(endpoint, self.context.auth_token)

        mock_session.assert_called_once_with(
            auth=auth_token_mock, verify=self.ca_certificates_file,
            cert=self.client_certificate_file, timeout=self.neutron_timeout,
            app_name='designate',
            app_version=version.version_info.version_string())

        self.assertEqual(connection_mock, result)

        # Test with insecure configuration
        mock_token.reset_mock()
        mock_session.reset_mock()

        CONF.set_override('insecure', True, 'network_api:neutron')

        result = neutron.get_client(self.context, endpoint)

        mock_token.assert_called_once_with(endpoint, self.context.auth_token)

        mock_session.assert_called_once_with(
            auth=auth_token_mock, verify=False,
            cert=self.client_certificate_file, timeout=self.neutron_timeout,
            app_name='designate',
            app_version=version.version_info.version_string())

        self.assertEqual(connection_mock, result)

    @mock.patch('designate.network_api.neutron.get_client')
    def test_list_floatingips(self, get_client):
        driver = mock.Mock()
        driver.network.ips.return_value = [
            {
                'id': '123',
                'floating_ip_address': '192.0.2.100',
                'region': 'RegionOne'
            },
            {
                'id': '456',
                'floating_ip_address': '192.0.2.200',
                'region': 'RegionOne'
            },
        ]
        get_client.return_value = driver

        self.assertEqual(2, len(self.api.list_floatingips(self.context)))

    @mock.patch('designate.network_api.neutron.get_client')
    def test_list_floatingips_unauthorized(self, get_client):
        driver = mock.Mock()
        driver.network.ips.side_effect = sdk_exceptions.HttpException
        get_client.return_value = driver

        self.assertEqual(0, len(self.api.list_floatingips(self.context)))

    @mock.patch('designate.network_api.neutron.get_client')
    def test_list_floatingips_communication_failure(self, get_client):
        driver = mock.Mock()
        driver.network.ips.side_effect = (
            Exception
        )
        get_client.return_value = driver

        self.assertRaises(
            exceptions.NeutronCommunicationFailure,
            self.api.list_floatingips, self.context
        )
