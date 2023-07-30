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

import oslotest.base
import requests_mock

from designate.backend import impl_infoblox
from designate.backend.impl_infoblox import connector
from designate.backend.impl_infoblox import ibexceptions
from designate import context
from designate import exceptions
from designate import objects


class InfobloxConnectorTestCase(oslotest.base.BaseTestCase):
    def setUp(self):
        super(InfobloxConnectorTestCase, self).setUp()
        self.options = {
            'wapi_url': 'https://localhost/wapi/v2.0/',
            'username': 'username',
            'password': 'password',
            'ns_group': 'ns_group',
            'sslverify': '1'
        }
        self.infoblox = connector.Infoblox(self.options)

    def test_infoblox_constructor(self):
        options = {
            'wapi_url': 'https://localhost/wapi/v2.0/',
            'username': 'username',
            'password': 'password',
            'ns_group': 'ns_group',
            'sslverify': '0'
        }
        infoblox = connector.Infoblox(options)

        self.assertIsInstance(infoblox, connector.Infoblox)
        self.assertFalse(infoblox.sslverify)

    def test_construct_url(self):
        self.assertEqual(
            'https://localhost/wapi/v2.0/test',
            self.infoblox._construct_url('test')
        )
        self.assertEqual(
            'https://localhost/wapi/v2.0/test?*foo=bar&foo=0&bar=1',
            self.infoblox._construct_url(
                'test', {'foo': 0, 'bar': 1}, {'foo': {'value': 'bar'}}
            )
        )
        self.assertEqual(
            'https://localhost/wapi/v2.0/test?*foo=bar&foo=0',
            self.infoblox._construct_url(
                'test', {'foo': 0}, {'foo': {'value': 'bar'}}
            )
        )
        self.assertEqual(
            'https://localhost/wapi/v2.0/test?foo=0',
            self.infoblox._construct_url(
                'test', {'foo': 0}
            )
        )

    def test_construct_url_no_relative_path(self):
        self.assertRaisesRegex(
            ValueError,
            'Path in request must be relative.',
            self.infoblox._construct_url, None
        )

    def test_validate_objtype_or_die(self):
        self.assertRaisesRegex(
            ValueError,
            'WAPI object type can\'t be empty.',
            self.infoblox._validate_objtype_or_die, None
        )
        self.assertRaisesRegex(
            ValueError,
            'WAPI object type can\'t contains slash.',
            self.infoblox._validate_objtype_or_die, '/'
        )


class InfobloxBackendTestCase(oslotest.base.BaseTestCase):
    def setUp(self):
        super(InfobloxBackendTestCase, self).setUp()
        self.base_address = 'https://localhost/wapi'

        self.context = mock.Mock()
        self.admin_context = mock.Mock()
        mock.patch.object(
            context.DesignateContext, 'get_admin_context',
            return_value=self.admin_context).start()

        self.zone = objects.Zone(
            id='e2bed4dc-9d01-11e4-89d3-123b93f75cba',
            name='example.com.',
            email='example@example.com',
        )
        self.target = {
            'id': '4588652b-50e7-46b9-b688-a9bad40a873e',
            'type': 'infoblox',
            'masters': [
                {'host': '1.1.1.1', 'port': 53},
            ],
            'options': [
                {'key': 'wapi_url', 'value': 'https://localhost/wapi/v2.0/'},
                {'key': 'username', 'value': 'test'},
                {'key': 'password', 'value': 'test'},
                {'key': 'ns_group', 'value': 'test'},
            ]
        }

        self.backend = impl_infoblox.InfobloxBackend(
            objects.PoolTarget.from_dict(self.target)
        )

    @requests_mock.mock()
    def test_create_zone(self, req_mock):
        req_mock.post(
            '%s/v2.0/zone_auth' % self.base_address,
            json={},
        )

        req_mock.get(
            '%s/v2.0/zone_auth' % self.base_address,
            json={},
        )

        self.backend.create_zone(self.context, self.zone)

    def test_update_zone(self):
        self.backend.update_zone(self.context, self.zone)

    @requests_mock.mock()
    def test_delete_zone(self, req_mock):
        req_mock.post(
            '%s/v2.0/zone_auth' % self.base_address,
            json={},
        )

        req_mock.get(
            '%s/v2.0/zone_auth' % self.base_address,
            json={},
        )

        req_mock.get(
            '%s/v2.0/grid' % self.base_address,
            json={},
        )

        self.backend.create_zone(self.context, self.zone)
        self.backend.delete_zone(self.context, self.zone)

    def test_missing_wapi_url(self):
        target = dict(self.target)
        target['options'] = [
            {'key': 'username', 'value': 'test'},
            {'key': 'password', 'value': 'test'},
            {'key': 'ns_group', 'value': 'test'},
        ]

        pool_target = objects.PoolTarget.from_dict(target)

        self.assertRaisesRegex(
            ibexceptions.InfobloxIsMisconfigured, "wapi_url",
            impl_infoblox.InfobloxBackend, pool_target,
        )

    def test_missing_username(self):
        target = dict(self.target)
        target['options'] = [
            {'key': 'wapi_url', 'value': 'test'},
            {'key': 'password', 'value': 'test'},
            {'key': 'ns_group', 'value': 'test'}
        ]

        pool_target = objects.PoolTarget.from_dict(target)

        self.assertRaisesRegex(
            ibexceptions.InfobloxIsMisconfigured, "username",
            impl_infoblox.InfobloxBackend, pool_target,
        )

    def test_missing_password(self):
        target = dict(self.target)
        target['options'] = [
            {'key': 'wapi_url', 'value': 'test'},
            {'key': 'username', 'value': 'test'},
            {'key': 'ns_group', 'value': 'test'},
        ]

        pool_target = objects.PoolTarget.from_dict(target)

        self.assertRaisesRegex(
            ibexceptions.InfobloxIsMisconfigured, "password",
            impl_infoblox.InfobloxBackend, pool_target,
        )

    def test_missing_ns_group(self):
        target = dict(self.target)
        target['options'] = [
            {'key': 'wapi_url', 'value': 'test'},
            {'key': 'username', 'value': 'test'},
            {'key': 'password', 'value': 'test'},
        ]

        pool_target = objects.PoolTarget.from_dict(target)

        self.assertRaisesRegex(
            ibexceptions.InfobloxIsMisconfigured, "ns_group",
            impl_infoblox.InfobloxBackend, pool_target,
        )

    def test_wrong_port(self):
        target = dict(self.target)
        target['masters'] = [
            {'host': '1.1.1.1', 'port': 100},
        ]

        pool_target = objects.PoolTarget.from_dict(target)

        self.assertRaisesRegex(
            exceptions.ConfigurationError,
            'Infoblox only supports mDNS instances on port 53',
            impl_infoblox.InfobloxBackend, pool_target,
        )
