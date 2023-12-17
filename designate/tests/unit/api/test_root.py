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

from oslo_config import fixture as cfg_fixture
import oslotest.base

from designate.api.admin.controllers import root as admin_root
from designate.api.v2.controllers import root as v2_root
import designate.conf
import designate.tests


CONF = designate.conf.CONF


class RootTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

    @mock.patch('stevedore.named.NamedExtensionManager')
    def test_admin_root(self, mock_manger):
        mock_extension = mock.Mock()
        mock_extension.obj.get_path.return_value = 'a'
        mock_manger.return_value = [mock_extension]
        CONF.set_override(
            'enabled_extensions_admin',
            ['admin'],
            'service:api'
        )
        admin_root.RootController()

        mock_manger.assert_called_with(
            namespace=mock.ANY, names=['admin'], invoke_on_load=True
        )

    @mock.patch('stevedore.named.NamedExtensionManager')
    def test_admin_root_no_extensions(self, mock_manger):
        mock_manger.return_value = []
        CONF.set_override(
            'enabled_extensions_admin',
            [],
            'service:api'
        )
        admin_root.RootController()

        mock_manger.assert_not_called()

    @mock.patch('stevedore.named.NamedExtensionManager')
    def test_v2_root(self, mock_manger):
        mock_extension = mock.Mock()
        mock_extension.obj.get_path.return_value = 'a'
        mock_manger.return_value = [mock_extension]
        CONF.set_override(
            'enabled_extensions_v2',
            ['v2'],
            'service:api'
        )
        v2_root.RootController()

        mock_manger.assert_called_with(
            namespace=mock.ANY, names=['v2'], invoke_on_load=True
        )

    @mock.patch('stevedore.named.NamedExtensionManager')
    def test_v2_root_object_not_found(self, mock_manger):
        mock_extension = mock.Mock()
        mock_extension.obj.get_path.return_value = '..test.a'
        mock_manger.return_value = [mock_extension]
        CONF.set_override(
            'enabled_extensions_v2',
            ['v2'],
            'service:api'
        )

        self.assertRaisesRegex(
            AttributeError,
            "object has no attribute 'test'",
            v2_root.RootController
        )

        mock_manger.assert_called_with(
            namespace=mock.ANY, names=['v2'], invoke_on_load=True
        )

    @mock.patch('stevedore.named.NamedExtensionManager')
    def test_v2_root_no_extensions(self, mock_manger):
        mock_manger.return_value = []
        CONF.set_override(
            'enabled_extensions_v2',
            [],
            'service:api'
        )
        v2_root.RootController()

        mock_manger.assert_not_called()
