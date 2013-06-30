# Copyright 2012 Managed I.T.
# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
from designate.tests.test_api import ApiTestCase
from designate.api import middleware


class FakeContext(object):
    def __init__(self, roles=[]):
        self.roles = roles


class FakeRequest(object):
    def __init__(self):
        self.headers = {}
        self.environ = {}

    def get_response(self, app):
        return "FakeResponse"


class MaintenanceMiddlewareTest(ApiTestCase):
    __test__ = True

    def test_process_request_disabled(self):
        self.config(maintenance_mode=False, group='service:api')

        request = FakeRequest()
        app = middleware.MaintenanceMiddleware({})

        # Process the request
        response = app(request)

        # Ensure request was not blocked
        self.assertEqual(response, 'FakeResponse')

    def test_process_request_enabled_reject(self):
        self.config(maintenance_mode=True, maintenance_mode_role='admin',
                    group='service:api')

        request = FakeRequest()
        request.environ['context'] = FakeContext(roles=['user'])

        app = middleware.MaintenanceMiddleware({})

        # Process the request
        response = app(request)

        # Ensure request was blocked
        self.assertEqual(response.status_code, 503)

    def test_process_request_enabled_reject_no_roles(self):
        self.config(maintenance_mode=True, maintenance_mode_role='admin',
                    group='service:api')

        request = FakeRequest()
        request.environ['context'] = FakeContext(roles=[])

        app = middleware.MaintenanceMiddleware({})

        # Process the request
        response = app(request)

        # Ensure request was blocked
        self.assertEqual(response.status_code, 503)

    def test_process_request_enabled_reject_no_context(self):
        self.config(maintenance_mode=True, maintenance_mode_role='admin',
                    group='service:api')

        request = FakeRequest()
        app = middleware.MaintenanceMiddleware({})

        # Process the request
        response = app(request)

        # Ensure request was blocked
        self.assertEqual(response.status_code, 503)

    def test_process_request_enabled_bypass(self):
        self.config(maintenance_mode=True, maintenance_mode_role='admin',
                    group='service:api')

        request = FakeRequest()
        request.environ['context'] = FakeContext(roles=['admin'])

        app = middleware.MaintenanceMiddleware({})

        # Process the request
        response = app(request)

        # Ensure request was not blocked
        self.assertEqual(response, 'FakeResponse')


class KeystoneContextMiddlewareTest(ApiTestCase):
    __test__ = True

    def test_process_request(self):
        app = middleware.KeystoneContextMiddleware({})

        request = FakeRequest()

        request.headers = {
            'X-Auth-Token': 'AuthToken',
            'X-User-ID': 'UserID',
            'X-Tenant-ID': 'TenantID',
            'X-Roles': 'admin,Member',
        }

        # Process the request
        app.process_request(request)

        self.assertIn('context', request.environ)

        context = request.environ['context']

        self.assertFalse(context.is_admin)
        self.assertEqual('AuthToken', context.auth_token)
        self.assertEqual('UserID', context.user_id)
        self.assertEqual('TenantID', context.tenant_id)
        self.assertEqual(['admin', 'Member'], context.roles)

    def test_process_request_sudo(self):
        # Set the policy to accept the authz
        self.policy({'use_sudo': '@'})

        app = middleware.KeystoneContextMiddleware({})

        request = FakeRequest()

        request.headers = {
            'X-Auth-Token': 'AuthToken',
            'X-User-ID': 'UserID',
            'X-Tenant-ID': 'TenantID',
            'X-Roles': 'admin,Member',
            'X-Designate-Sudo-Tenant-ID':
            '5a993bf8-d521-420a-81e1-192d9cc3d5a0'
        }

        # Process the request
        app.process_request(request)

        self.assertIn('context', request.environ)

        context = request.environ['context']

        self.assertFalse(context.is_admin)
        self.assertEqual('AuthToken', context.auth_token)
        self.assertEqual('UserID', context.user_id)
        self.assertEqual('TenantID', context.original_tenant_id)
        self.assertEqual('5a993bf8-d521-420a-81e1-192d9cc3d5a0',
                         context.tenant_id)
        self.assertEqual(['admin', 'Member'], context.roles)


class NoAuthContextMiddlewareTest(ApiTestCase):
    __test__ = True

    def test_process_request(self):
        app = middleware.NoAuthContextMiddleware({})

        request = FakeRequest()

        # Process the request
        app.process_request(request)

        self.assertIn('context', request.environ)

        context = request.environ['context']

        self.assertTrue(context.is_admin)
        self.assertIsNone(context.auth_token)
        self.assertIsNone(context.user_id)
        self.assertIsNone(context.tenant_id)
        self.assertEqual([], context.roles)
