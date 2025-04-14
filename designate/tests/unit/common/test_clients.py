# Copyright 2025 Red Hat
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

from designate.common import clients
import designate.conf
from designate import exceptions


CONF = designate.conf.CONF


class TestNeutronAuth(oslotest.base.BaseTestCase):

    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))
        clients.NeutronAuth.neutron_client = None
        designate.conf.neutron.register_opts(CONF)

    @mock.patch('keystoneauth1.loading.load_session_from_conf_options')
    @mock.patch('keystoneauth1.loading.load_auth_from_conf_options')
    @mock.patch('designate.common.clients.Connection')
    def test_get_neutron_client(self, mock_connection, mock_load_auth,
                                mock_load_session):
        mock_auth = mock.Mock()
        mock_session = mock.Mock()
        mock_load_auth.return_value = mock_auth
        mock_load_session.return_value = mock_session

        clients.NeutronAuth.get_neutron_client()

        mock_load_auth.assert_called_once_with(CONF, 'neutron')
        mock_load_session.assert_called_once_with(CONF, 'neutron',
                                                  auth=mock_auth)
        mock_connection.assert_called_once_with(
            session=mock_session,
            oslo_conf=CONF,
            service_types=['network'],
        )

    @mock.patch('keystoneauth1.loading.load_session_from_conf_options')
    @mock.patch('keystoneauth1.loading.load_auth_from_conf_options')
    @mock.patch('designate.common.clients.Connection')
    def test_get_neutron_client_cached(self, mock_connection, mock_load_auth,
                                       mock_load_session):
        mock_connection.return_value = mock.Mock()

        first = clients.NeutronAuth.get_neutron_client()
        second = clients.NeutronAuth.get_neutron_client()

        self.assertIs(first, second)
        mock_connection.assert_called_once()

    @mock.patch('keystoneauth1.loading.load_auth_from_conf_options')
    def test_get_neutron_client_auth_none(self, mock_load_auth):
        mock_load_auth.return_value = None

        self.assertRaisesRegex(
            exceptions.ConfigurationError,
            "Failed to load authentication.*auth_type",
            clients.NeutronAuth.get_neutron_client
        )


class TestNeutronClient(oslotest.base.BaseTestCase):

    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

    @mock.patch.object(clients.NeutronAuth, 'get_neutron_client')
    def test_get_floating_ips(self, mock_get_client):
        mock_conn = mock.Mock()
        mock_conn.list_floating_ips.return_value = [
            {'id': 'fip1', 'floating_ip_address': '192.168.1.1'},
            {'id': 'fip2', 'floating_ip_address': '192.168.1.2'}
        ]
        mock_get_client.return_value = mock_conn

        result = clients.NeutronClient.get_floating_ips()

        mock_get_client.assert_called_once()
        mock_conn.list_floating_ips.assert_called_once_with()
        self.assertEqual(len(result), 2)

    @mock.patch.object(clients.NeutronAuth, 'get_neutron_client')
    def test_get_floating_ips_exception(self, mock_get_client):
        mock_conn = mock.Mock()
        mock_conn.list_floating_ips.side_effect = (
            sdk_exceptions.SDKException("Network error"))
        mock_get_client.return_value = mock_conn

        self.assertRaises(exceptions.NeutronCommunicationFailure,
                          clients.NeutronClient.get_floating_ips)
