# Copyright 2015 Infoblox Inc.
# All Rights Reserved.
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

from infoblox_client import connector as infoblox_connector
from infoblox_client import exceptions as infoblox_exceptions
from infoblox_client import objects as infoblox_objects
import oslotest.base
import requests_mock

from designate.backend import impl_infoblox
from designate import context
from designate import exceptions
from designate import objects
from designate.tests import base_fixtures


class InfobloxBackendTestCase(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(self.stdlog)

        self.project_id = 'f532f66e-0fea-4698-895c-bb7caef815ef'
        self.admin_context = mock.Mock()
        self.admin_context.project_id = self.project_id
        mock.patch.object(
            context.DesignateContext, 'get_admin_context',
            return_value=self.admin_context).start()

        self.zone = objects.Zone(
            id='e2bed4dc-9d01-11e4-89d3-123b93f75cba',
            name='example.com.',
            email='example@example.com',
        )
        self.base_address = 'https://192.0.2.1/wapi/v2.10/'
        self.dns_view = 'my_dns_view'
        self.network_view = 'my_net_view'
        self.ns_group = 'my_ns_group'

        self.target = {
            'id': '4588652b-50e7-46b9-b688-a9bad40a873e',
            'type': 'designate',
            'masters': [
                {'host': '192.0.2.1', 'port': 53},
            ],
            'options': [
                {'key': 'wapi_url', 'value': self.base_address},
                {'key': 'username', 'value': 'user'},
                {'key': 'password', 'value': 'secret'},
                {'key': 'dns_view', 'value': self.dns_view},
                {'key': 'network_view', 'value': self.network_view},
                {'key': 'ns_group', 'value': self.ns_group},
            ],
        }


class BasicInfobloxBackendTestCase(InfobloxBackendTestCase):
    def setUp(self):
        super().setUp()

        self.target['options'].append(
            {'key': 'multi_tenant', 'value': '0'},
        )

        self.backend = impl_infoblox.InfobloxBackend(
            objects.PoolTarget.from_dict(self.target)
        )

        self.backend.connection = mock.Mock()
        self.backend.infoblox = mock.Mock()

    @mock.patch.object(impl_infoblox, 'infoblox_connector', None)
    def test_no_library_installed(self):
        pool_target = objects.PoolTarget.from_dict(self.target)
        self.assertRaisesRegex(
            exceptions.Backend,
            'The infoblox-client library is not available',
            impl_infoblox.InfobloxBackend, pool_target
        )

    def test_get_options(self):
        self.assertEqual('my_dns_view', self.backend.dns_view)
        self.assertEqual('my_net_view', self.backend.network_view)
        self.assertEqual('my_ns_group', self.backend.ns_group)
        self.assertEqual('0', self.backend.multi_project)

    @mock.patch.object(infoblox_connector, 'Connector', mock.Mock())
    def test_backend_with_invalid_master_port(self):
        self.target['masters'] = [
            {'host': '192.0.2.1', 'port': 5354},
        ]
        pool_target = objects.PoolTarget.from_dict(self.target)
        self.assertRaisesRegex(
            exceptions.ConfigurationError,
            'Infoblox only supports mDNS instances on port 53',
            impl_infoblox.InfobloxBackend, pool_target
        )

    @mock.patch.object(infoblox_connector, 'Connector')
    def test_backend_with_host(self, mock_infoblox_connector):
        self.target['options'] = [
            {'key': 'wapi_host', 'value': '192.0.2.100'},
            {'key': 'wapi_version', 'value': '1'},
            {'key': 'username', 'value': 'user'},
            {'key': 'password', 'value': 'secret'},
        ]
        impl_infoblox.InfobloxBackend(
            objects.PoolTarget.from_dict(self.target)
        )
        mock_infoblox_connector.assert_called_with(
            {
                'host': '192.0.2.100',
                'username': 'user',
                'password': 'secret',
                'http_pool_connections': None,
                'http_pool_maxsize': None,
                'wapi_version': '1',
                'ssl_verify': None,
                'cert': None,
                'key': None
            }
        )

    @mock.patch.object(infoblox_connector, 'Connector')
    def test_backend_with_wapi_url(self, mock_infoblox_connector):
        impl_infoblox.InfobloxBackend(
            objects.PoolTarget.from_dict(self.target)
        )
        mock_infoblox_connector.assert_called_with(
            {
                'host': '192.0.2.1',
                'username': 'user',
                'password': 'secret',
                'http_pool_connections': None,
                'http_pool_maxsize': None,
                'wapi_version': '2.10',
                'ssl_verify': None,
                'cert': None,
                'key': None
            }
        )

    def test_is_multi_project(self):
        self.backend.multi_project = True
        self.assertTrue(self.backend.is_multi_project)

        self.backend.multi_project = 1
        self.assertTrue(self.backend.is_multi_project)

        self.backend.multi_project = '1'
        self.assertTrue(self.backend.is_multi_project)

        self.backend.multi_project = False
        self.assertFalse(self.backend.is_multi_project)

        self.backend.multi_project = 0
        self.assertFalse(self.backend.is_multi_project)

        self.backend.multi_project = '0'
        self.assertFalse(self.backend.is_multi_project)

    def test_parse_wapi_url(self):
        self.assertEqual(
            ('192.0.2.1', None),
            self.backend.parse_wapi_url('https://192.0.2.1/')
        )
        self.assertEqual(
            ('192.0.2.2', '1'),
            self.backend.parse_wapi_url('https://192.0.2.2/wapi/v1/')
        )
        self.assertEqual(
            ('192.0.2.3', '2.10'),
            self.backend.parse_wapi_url('https://192.0.2.3/wapi/v2.10/')
        )
        self.assertEqual(
            ('192.0.2.3:443', '2.10'),
            self.backend.parse_wapi_url('https://192.0.2.3:443/wapi/v2.10/')
        )

    def test_get_network_view(self):
        self.backend.connection.get_object.return_value = [{'name': 'fake'}]

        self.assertEqual('fake', self.backend.get_network_view('project_id'))

    def test_get_network_view_no_result(self):
        self.backend.connection.get_object.return_value = []

        self.assertIsNone(self.backend.get_network_view('project_id'))

    def test_get_or_create_network_view(self):
        mock_network_view = mock.Mock()
        mock_network_view.name = 'fake'

        self.backend.connection.get_object.return_value = []
        self.backend.infoblox.create_network_view.return_value = (
            mock_network_view
        )

        self.assertEqual(
            'fake', self.backend.get_or_create_network_view('project_id')
        )

    def test_get_or_create_network_view_not_found(self):
        self.backend.connection.get_object.return_value = [{'name': 'fake'}]

        self.assertEqual(
            'fake', self.backend.get_or_create_network_view('project_id')
        )

    def test_get_or_create_network_view_already_found(self):
        self.backend.connection.get_object.return_value = [{'name': 'fake'}]

        self.assertEqual(
            'fake', self.backend.get_or_create_network_view('project_id')
        )

    @mock.patch.object(infoblox_objects.DNSView, 'search')
    def test_get_or_create_dns_view(self, mock_search):
        mock_dns_view = mock.Mock()
        mock_dns_view.name = 'fake'

        mock_search.return_value = None
        self.backend.infoblox.create_dns_view.return_value = mock_dns_view

        self.assertEqual(
            'fake', self.backend.get_or_create_dns_view('net_view')
        )

    def test_get_or_create_dns_view_no_network_provided(self):
        self.assertFalse(self.backend.get_or_create_dns_view(None))

    @mock.patch.object(infoblox_objects.DNSView, 'search')
    def test_get_or_create_dns_view_not_found(self, mock_search):
        mock_search.return_value = None

        self.assertFalse(
            self.backend.get_or_create_dns_view(
                'net_view', create_if_missing=False
            )
        )

    @mock.patch.object(infoblox_objects.DNSView, 'search')
    def test_get_or_create_dns_view_already_found(self, mock_search):
        mock_dns_view = mock.Mock()
        mock_dns_view.name = 'fake'

        mock_search.return_value = mock_dns_view

        self.assertEqual(
            'fake', self.backend.get_or_create_dns_view('net_view')
        )

    @mock.patch.object(infoblox_objects, 'Grid', mock.Mock())
    def test_restart_if_needed_unable_to_restart(self):
        self.backend.connection.call_func.side_effect = (
            infoblox_exceptions.InfobloxException('')
        )

        self.backend.restart_if_needed()

        self.assertIn(
            'Unable to restart the infoblox dns service.',
            self.stdlog.logger.output
        )

    def test_create_zone(self):
        self.backend.restart_if_needed = mock.Mock()

        self.backend.create_zone(self.admin_context, self.zone)

        self.backend.infoblox.create_dns_zone.assert_called_with(
            dns_zone='example.com',
            dns_view='my_dns_view',
            zone_format='FORWARD',
            ns_group='my_ns_group'
        )
        self.backend.restart_if_needed.assert_called()

    def test_create_zone_handle_error(self):
        self.backend.infoblox.create_dns_zone.side_effect = (
            infoblox_exceptions.InfobloxTimeoutError('error')
        )

        self.assertRaisesRegex(
            exceptions.Backend,
            'Connection to NIOS timed out',
            self.backend.create_zone, self.admin_context, self.zone
        )

    def test_create_zone_ptr(self):
        zone = objects.Zone(
            id='e2bed4dc-9d01-11e4-89d3-123b93f75cba',
            name='example.in-addr.arpa.',
            email='example@example.com',
        )

        self.backend.restart_if_needed = mock.Mock()

        self.backend.create_zone(self.admin_context, zone)

        self.backend.infoblox.create_dns_zone.assert_called_with(
            dns_zone='example.in-addr.arpa',
            dns_view='my_dns_view',
            zone_format='IPV4',
            ns_group='my_ns_group'
        )
        self.backend.restart_if_needed.assert_called()

    def test_create_zone_ipv6_ptr(self):
        zone = objects.Zone(
            id='e2bed4dc-9d01-11e4-89d3-123b93f75cba',
            name='example.ip6.arpa.',
            email='example@example.com',
        )

        self.backend.restart_if_needed = mock.Mock()

        self.backend.create_zone(self.admin_context, zone)

        self.backend.infoblox.create_dns_zone.assert_called_with(
            dns_zone='example.ip6.arpa',
            dns_view='my_dns_view',
            zone_format='IPV6',
            ns_group='my_ns_group'
        )
        self.backend.restart_if_needed.assert_called()

    def test_create_zone_no_dns_view(self):
        self.backend.dns_view = None

        self.assertRaisesRegex(
            exceptions.Backend,
            'Unable to create zone. No DNS View found',
            self.backend.create_zone, self.admin_context, self.zone
        )

    def test_delete_zone(self):
        self.backend.restart_if_needed = mock.Mock()

        self.backend.delete_zone(self.admin_context, self.zone)

        self.backend.infoblox.delete_dns_zone.assert_called_with(
            'my_dns_view',
            'example.com'
        )
        self.backend.restart_if_needed.assert_called()

    def test_delete_zone_handle_error(self):
        self.backend.infoblox.delete_dns_zone.side_effect = (
            infoblox_exceptions.InfobloxTimeoutError('error')
        )

        self.assertRaisesRegex(
            exceptions.Backend,
            'Connection to NIOS timed out',
            self.backend.delete_zone, self.admin_context, self.zone
        )

    def test_delete_zone_no_dns_view(self):
        self.backend.dns_view = None

        self.assertRaisesRegex(
            exceptions.Backend,
            'Unable to delete zone. No DNS View found',
            self.backend.delete_zone, self.admin_context, self.zone
        )


class AdvancedInfobloxBackendTestCase(InfobloxBackendTestCase):
    def setUp(self):
        super().setUp()

        self.target['options'].append(
            {'key': 'multi_tenant', 'value': '1'},
        )

        self.backend = impl_infoblox.InfobloxBackend(
            objects.PoolTarget.from_dict(self.target)
        )

    @requests_mock.mock()
    def test_create_zone(self, req_mock):
        zone_name = self.zone['name'][0:-1]
        network_view = f'{self.network_view}.{self.project_id}'
        view_name = f'{self.dns_view}.{self.network_view}.{self.project_id}'

        req_mock.get(
            f'{self.base_address}networkview?*TenantID={self.project_id}'
            '&_return_fields=name',
            json=[{
                '_ref': f'networkview/mock:{network_view}/false',
                'name': f'{network_view}'
            }]
        )
        req_mock.get(
            f'{self.base_address}view?name={view_name}&_return_fields=name',
            json=[{
                '_ref': f'view/mock:{view_name}/false',
                'name': f'{view_name}'
            }]
        )
        req_mock.get(
            f'{self.base_address}zone_auth?fqdn={zone_name}&view={view_name}',
            json=[{
                '_ref': f'zone_auth/mock:{zone_name}/{view_name}',
                'extattrs': {},
                'fqdn': zone_name,
                'grid_primary': [],
                'grid_secondaries': [],
                'ns_group': self.ns_group,
                'view': view_name
            }]
        )
        req_mock.get(
            f'{self.base_address}grid',
            json=[{'_ref': 'grid/mock:Infoblox'}]
        )
        req_mock.post(
            f'{self.base_address}grid/mock%3AInfoblox?'
            '_function=restartservices',
            json=[]
        )

        self.backend.create_zone(self.admin_context, self.zone)

        self.assertEqual(
            req_mock.last_request.json(),
            {
                'mode': 'GROUPED',
                'restart_option': 'RESTART_IF_NEEDED',
                'services': ['DNS']
            }
        )
        self.assertIn('Create Zone', self.stdlog.logger.output)

    @requests_mock.mock()
    def test_delete_zone(self, req_mock):
        zone_name = self.zone['name'][0:-1]
        network_view = f'{self.network_view}.{self.project_id}'
        view_name = f'{self.dns_view}.{self.network_view}.{self.project_id}'

        req_mock.get(
            f'{self.base_address}networkview?*TenantID={self.project_id}'
            '&_return_fields=name',
            json=[{
                '_ref': f'networkview/mock:{network_view}/false',
                'name': f'{network_view}'
            }]
        )
        req_mock.get(
            f'{self.base_address}view?name={view_name}&_return_fields=name',
            json=[{
                '_ref': f'view/mock:{view_name}/false',
                'name': f'{view_name}'
            }]
        )
        req_mock.get(
            f'{self.base_address}zone_auth?fqdn={zone_name}&view={view_name}',
            json=[{
                '_ref': f'zone_auth/mock:{zone_name}/{view_name}',
                'extattrs': {},
                'fqdn': zone_name,
                'grid_primary': [],
                'grid_secondaries': [],
                'ns_group': self.ns_group,
                'view': view_name
            }]
        )
        req_mock.delete(
            f'{self.base_address}zone_auth/mock%3A{zone_name}/{view_name}',
            json=[]
        )
        req_mock.get(
            f'{self.base_address}grid',
            json=[{'_ref': 'grid/mock:Infoblox'}]
        )
        req_mock.post(
            f'{self.base_address}grid/mock%3AInfoblox?'
            '_function=restartservices',
            json=[]
        )

        self.backend.delete_zone(self.admin_context, self.zone)

        self.assertEqual(
            req_mock.last_request.json(),
            {
                'mode': 'GROUPED',
                'restart_option': 'RESTART_IF_NEEDED',
                'services': ['DNS']
            }
        )

        self.assertIn('Delete Zone', self.stdlog.logger.output)
