# Copyright 2015 Hewlett-Packard Development Company, L.P.
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

import fixtures
import oslotest.base

from designate.api import middleware


class FakeRequest:
    def __init__(self):
        self.headers = {}
        self.environ = {}
        self.GET = {}
        self.POST = {}

    @property
    def params(self):
        data = self.GET.copy()
        data.update(self.POST)
        return data

    def get_response(self, app):
        return "FakeResponse"


class ContextMiddlewareTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.app = middleware.ContextMiddleware({})
        self.request = FakeRequest()

    def test_extract_all_projects(self):
        mock_context = mock.Mock()

        self.request.headers.update({
            'X-Auth-All-Projects': 'True',
        })

        self.app._extract_all_projects(mock_context, self.request)

        self.assertTrue(mock_context.all_tenants)

    def test_extract_dns_hide_counts(self):
        mock_context = mock.Mock()

        self.request.headers.update({
            'OpenStack-DNS-Hide-Counts': 'True',
        })

        self.app._extract_dns_hide_counts(mock_context, self.request)

        self.assertTrue(mock_context.hide_counts)


class KeystoneContextMiddlewareTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.app = middleware.KeystoneContextMiddleware({})

        self.request = FakeRequest()

        # Replace the DesignateContext class.
        self.ctxt = mock.Mock()
        self.useFixture(fixtures.MockPatch(
            'designate.context.DesignateContext',
            return_value=self.ctxt
        ))

    def test_sudo_by_project_id(self):
        self.request.headers.update({
            'X-Tenant-ID': 'TenantID',
            'X-Roles': 'admin',
            'X-Auth-Sudo-Project-ID': 'foo',
        })

        self.app(self.request)
        self.ctxt.sudo.assert_called_once_with("foo")

    def test_sudo_by_tenant_id(self):
        self.request.headers.update({
            'X-Tenant-ID': 'TenantID',
            'X-Roles': 'admin',
            'X-Auth-Sudo-Tenant-ID': 'foo',
        })

        self.app(self.request)
        self.ctxt.sudo.assert_called_once_with("foo")

    def test_sudo_not_set(self):
        self.request.headers.update({
            'X-Tenant-ID': 'TenantID',
            'X-Roles': 'admin',
        })

        self.app(self.request)
        self.assertFalse(self.ctxt.sudo.called)

    def test_all_projects_in_params(self):
        self.request.headers.update({
            'X-Tenant-ID': 'TenantID',
            'X-Roles': 'admin',
        })
        self.request.GET["all_projects"] = "True"

        self.app(self.request)

        self.assertNotIn('all_tenants', self.request.params)
        self.assertTrue(self.ctxt.all_tenants)

    def test_all_tenants_in_params(self):
        self.request.headers.update({
            'X-Tenant-ID': 'TenantID',
            'X-Roles': 'admin',
        })
        self.request.GET["all_tenants"] = "True"

        self.app(self.request)

        self.assertNotIn('all_tenants', self.request.params)
        self.assertTrue(self.ctxt.all_tenants)

    def test_all_tenants_not_set(self):
        self.request.headers.update({
            'X-Tenant-ID': 'TenantID',
            'X-Roles': 'admin',
        })

        self.app(self.request)
        self.assertFalse(self.ctxt.all_tenants)

    def test_edit_managed_records_in_params(self):
        self.request.headers.update({
            'X-Tenant-ID': 'TenantID',
            'X-Roles': 'admin',
        })
        self.request.GET["edit_managed_records"] = "True"

        self.app(self.request)

        self.assertNotIn('edit_managed_records', self.request.params)
        self.assertTrue(self.ctxt.edit_managed_records)

    def test_edit_managed_records_in_headers(self):
        self.request.headers.update({
            'X-Tenant-ID': 'TenantID',
            'X-Roles': 'admin',
            'X-Designate-Edit-Managed-Records': 'True'
        })

        self.app(self.request)
        self.assertTrue(self.ctxt.edit_managed_records)

    def test_edit_managed_records_not_set(self):
        self.request.headers.update({
            'X-Tenant-ID': 'TenantID',
            'X-Roles': 'admin',
        })

        self.app(self.request)
        self.assertFalse(self.ctxt.edit_managed_records)

    def test_hard_delete_in_headers(self):
        self.request.headers.update({
            'X-Tenant-ID': 'TenantID',
            'X-Roles': 'admin',
            'X-Designate-Hard-Delete': 'True'
        })

        self.app(self.request)
        self.assertTrue(self.ctxt.hard_delete)

    def test_hard_delete_not_set(self):
        self.request.headers.update({
            'X-Tenant-ID': 'TenantID',
            'X-Roles': 'admin',
        })

        self.app(self.request)
        self.assertFalse(self.ctxt.hard_delete)

    def test_delete_shares_not_set(self):
        self.request.headers.update({
            'X-Tenant-ID': 'TenantID',
            'X-Roles': 'admin',
        })

        self.app(self.request)
        self.assertFalse(self.ctxt.delete_shares)

    def test_delete_shares_false(self):
        self.request.headers.update({
            'X-Tenant-ID': 'TenantID',
            'X-Roles': 'admin',
            'X-Designate-Delete-Shares': 'false'
        })

        self.app(self.request)
        self.assertFalse(self.ctxt.delete_shares)

    def test_delete_shares_true(self):
        self.request.headers.update({
            'X-Tenant-ID': 'TenantID',
            'X-Roles': 'admin',
            'X-Designate-Delete-Shares': 'True'
        })

        self.app(self.request)
        self.assertTrue(self.ctxt.delete_shares)
