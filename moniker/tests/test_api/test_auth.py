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
from moniker.tests.test_api import ApiTestCase
from moniker.api import auth


class KeystoneContextMiddlewareTest(ApiTestCase):
    __test__ = True

    def test_process_request(self):
        class FakeRequest(object):
            headers = {}
            environ = {}

        app = {}
        middleware = auth.KeystoneContextMiddleware(app)

        request = FakeRequest()

        request.headers = {
            'X-Auth-Token': 'AuthToken',
            'X-User-ID': 'UserID',
            'X-Tenant-ID': 'TenantID',
            'X-Roles': 'admin,Member',
        }

        # Process the request
        middleware.process_request(request)

        self.assertIn('context', request.environ)

        context = request.environ['context']

        self.assertFalse(context.is_admin)
        self.assertEqual('AuthToken', context.auth_tok)
        self.assertEqual('UserID', context.user_id)
        self.assertEqual('TenantID', context.tenant_id)
        self.assertEqual(['admin', 'Member'], context.roles)


class NoAuthMiddlewareTest(ApiTestCase):
    __test__ = True

    def test_process_request(self):
        class FakeRequest(object):
            headers = {}
            environ = {}

        app = {}
        middleware = auth.NoAuthMiddleware(app)

        request = FakeRequest()

        # Process the request
        middleware.process_request(request)

        self.assertIn('context', request.environ)

        context = request.environ['context']

        self.assertTrue(context.is_admin)
        self.assertIsNone(context.auth_tok)
        self.assertIsNone(context.user_id)
        self.assertIsNone(context.tenant_id)
        self.assertEqual([], context.roles)
