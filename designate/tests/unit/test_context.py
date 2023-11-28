# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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

from designate import context
from designate import policy


class TestDesignateContext(oslotest.base.BaseTestCase):
    def test_tsigkey_id_override(self):
        orig = context.DesignateContext(
            tsigkey_id='12345', project_id='54321'
        )
        copy = orig.to_dict()

        self.assertEqual('TSIG:12345 54321 - - -', copy['user_identity'])

    @mock.patch.object(policy, 'check')
    def test_sudo(self, mock_policy_check):
        ctxt = context.DesignateContext(
            user_id='12345', project_id='old_project'
        )
        ctxt.sudo('new_project')

        self.assertTrue(mock_policy_check.called)
        self.assertEqual('new_project', ctxt.project_id)
        self.assertEqual('old_project', ctxt.original_project_id)

    def test_get_auth_plugin(self):
        ctx = context.DesignateContext()
        self.assertIsInstance(
            ctx.get_auth_plugin(), context._ContextAuthPlugin
        )

    @mock.patch('keystoneauth1.access.service_catalog.ServiceCatalogV2')
    def test_get_auth_plugin_get_endpoint(self, mock_sc):
        mock_session = mock.Mock()
        mock_service_catalog = mock.Mock()
        mock_sc.return_value = mock_service_catalog

        ctx = context.DesignateContext(
            auth_token='token', service_catalog='catalog'
        )

        auth_plugin = ctx.get_auth_plugin()
        auth_plugin.get_endpoint_data = mock.Mock()
        auth_plugin.get_endpoint(mock_session)

        mock_sc.assert_called_with('catalog')
        mock_service_catalog.url_for.assert_called_with(
            service_type=None, service_name=None, interface=None,
            region_name=None
        )
        auth_plugin.get_endpoint_data.assert_called()

    def test_get_auth_plugin_user(self):
        ctx = context.DesignateContext(
            user_auth_plugin='user_auth_plugin'
        )
        self.assertEqual('user_auth_plugin', ctx.get_auth_plugin())
