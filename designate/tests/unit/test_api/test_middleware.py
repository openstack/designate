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

"""
Test API middleware
"""

import fixtures
import oslotest.base
import mock

from designate.api import middleware


class FakeRequest(object):
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


class KeystoneContextMiddlewareTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super(KeystoneContextMiddlewareTest, self).setUp()
        self.app = middleware.KeystoneContextMiddleware({})

        self.request = FakeRequest()

        # Replace the DesignateContext class..
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


class SSLMiddlewareTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super(SSLMiddlewareTest, self).setUp()
        self.app = middleware.SSLMiddleware({})

        self.request = FakeRequest()

    def test_bogus_header(self):
        self.request.environ['wsgi.url_scheme'] = 'http'
        # If someone sends something bogus, it will infect their self links
        self.request.environ['HTTP_X_FORWARDED_PROTO'] = 'poo'
        self.app(self.request)

        self.assertEqual('poo', self.request.environ['wsgi.url_scheme'])

    def test_http_header(self):
        self.request.environ['wsgi.url_scheme'] = ''
        self.request.environ['HTTP_X_FORWARDED_PROTO'] = 'http'
        self.app(self.request)

        self.assertEqual('http', self.request.environ['wsgi.url_scheme'])

    def test_https_header(self):
        self.request.environ['wsgi.url_scheme'] = 'http'
        self.request.environ['HTTP_X_FORWARDED_PROTO'] = 'https'
        self.app(self.request)

        self.assertEqual('https', self.request.environ['wsgi.url_scheme'])

    def test_override_proto(self):
        self.request.environ['wsgi.url_scheme'] = 'http'
        self.request.environ['HTTP_X_FORWARDED_PROTO'] = 'https'
        self.app.override = 'poo'

        self.app(self.request)

        self.assertEqual('poo', self.request.environ['wsgi.url_scheme'])
