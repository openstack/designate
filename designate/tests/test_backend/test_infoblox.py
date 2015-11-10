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
import six
from mock import MagicMock

from designate import objects
from designate.tests.test_backend import BackendTestCase
from designate.backend.impl_infoblox import InfobloxBackend
from designate.exceptions import ConfigurationError
from designate.backend.impl_infoblox import ibexceptions


class InfobloxBackendTestCase(BackendTestCase):

    def get_zone_fixture(self):
        return super(InfobloxBackendTestCase, self).get_zone_fixture(
            values={
                'name': 'test.example.com.'
            }
        )

    def setUp(self):
        super(InfobloxBackendTestCase, self).setUp()

        self.config(group='backend:infoblox',
                    wapi_url=None,
                    username=None,
                    password=None,
                    ns_group=None)

    def get_target_fixture(self, masters=None, options=None):
        if not masters:
            masters = [{'host': '1.1.1.1', 'port': 53}]

        if not options:
            options = [{'key': 'wapi_url', 'value': 'test'},
                       {'key': 'username', 'value': 'test'},
                       {'key': 'password', 'value': 'test'},
                       {'key': 'ns_group', 'value': 'test'}]

        return objects.PoolTarget.from_dict({
            'id': '4588652b-50e7-46b9-b688-a9bad40a873e',
            'type': 'infoblox',
            'masters': masters,
            'options': options
        })

    def set_up_backend(self, target=None):
        if not target:
            target = self.get_target_fixture()

        self.backend = InfobloxBackend(target)
        self.backend.start()
        self.backend.infoblox = MagicMock()

    def test_create_zone(self):
        self.set_up_backend()
        context = self.get_context()
        zone = self.get_zone_fixture()
        self.backend.infoblox.get_dns_view = MagicMock(return_value='default')
        self.backend.create_zone(context, zone)
        self.backend.infoblox.create_zone_auth.assert_called_once_with(
                                fqdn='test.example.com',
                                dns_view='default')

    def test_update_zone(self):
        self.set_up_backend()
        context = self.get_context()
        zone = objects.Zone().from_dict(self.get_zone_fixture())
        self.backend.update_zone(context, zone)

    def test_delete_zone(self):
        self.set_up_backend()
        context = self.get_context()
        zone = self.get_zone_fixture()
        self.backend.create_zone(context, zone)
        self.backend.delete_zone(context, zone)
        self.backend.infoblox.delete_zone_auth.assert_called_once_with(
                                'test.example.com')

    def test_missing_wapi_url(self):
        options = [{'key': 'username', 'value': 'test'},
                   {'key': 'password', 'value': 'test'},
                   {'key': 'ns_group', 'value': 'test'}]

        target = self.get_target_fixture(options=options)
        six.assertRaisesRegex(self, ibexceptions.InfobloxIsMisconfigured,
                              "wapi_url",
                              self.set_up_backend, target)

    def test_missing_username(self):
        options = [{'key': 'wapi_url', 'value': 'test'},
                   {'key': 'password', 'value': 'test'},
                   {'key': 'ns_group', 'value': 'test'}]

        target = self.get_target_fixture(options=options)
        six.assertRaisesRegex(self, ibexceptions.InfobloxIsMisconfigured,
                              "username",
                              self.set_up_backend, target)

    def test_missing_password(self):
        options = [{'key': 'wapi_url', 'value': 'test'},
                   {'key': 'username', 'value': 'test'},
                   {'key': 'ns_group', 'value': 'test'}]

        target = self.get_target_fixture(options=options)
        six.assertRaisesRegex(self, ibexceptions.InfobloxIsMisconfigured,
                              "password",
                              self.set_up_backend, target)

    def test_missing_ns_group(self):
        options = [{'key': 'wapi_url', 'value': 'test'},
                   {'key': 'username', 'value': 'test'},
                   {'key': 'password', 'value': 'test'}]

        target = self.get_target_fixture(options=options)
        six.assertRaisesRegex(self, ibexceptions.InfobloxIsMisconfigured,
                              "ns_group",
                              self.set_up_backend, target)

    def test_wrong_port(self):
        masters = [{'host': '1.1.1.1', 'port': 100}]
        target = self.get_target_fixture(masters=masters)
        six.assertRaisesRegex(self, ConfigurationError,
                              "port 53",
                              self.set_up_backend, target)
