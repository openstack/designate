# Copyright 2019 Cloudification GmbH
#
# Author: Sergey Kraynev <contact@cloudification.io>
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

import json
from unittest import mock

import oslotest.base
import requests

from designate.backend import impl_akamai_v2 as akamai
from designate import context
from designate import exceptions
from designate import objects
from designate.tests import base_fixtures


class AkamaiBackendTestCase(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()

        self.admin_context = mock.Mock()
        mock.patch.object(
            context.DesignateContext, 'get_admin_context',
            return_value=self.admin_context).start()

        self.zone = objects.Zone(
            id='cca7908b-dad4-4c50-adba-fb67d4c556e8',
            name='example.com.',
            email='example@example.com'
        )
        self.target = {
            'id': '4588652b-50e7-46b9-b688-a9bad40a873e',
            'type': 'akamai_v2',
            'masters': [
                {'host': '192.0.2.1', 'port': 53},
                {'host': '192.0.2.2', 'port': 35}
            ],
            'options': [
                {'key': 'host', 'value': '192.0.2.3'},
                {'key': 'port', 'value': '53'},
                {'key': 'akamai_client_secret', 'value': 'client_secret'},
                {'key': 'akamai_host', 'value': 'host_value'},
                {'key': 'akamai_access_token', 'value': 'access_token'},
                {'key': 'akamai_client_token', 'value': 'client_token'},
                {'key': 'akamai_contract_id', 'value': 'G-XYW'},
                {'key': 'akamai_gid', 'value': '777'}
            ],
        }

    def gen_response(self, status_code, reason, json_data=None):
        response = requests.models.Response()
        response.status_code = status_code
        response.reason = reason
        response._content = json.dumps(json_data or {}).encode('utf-8')
        return response

    @mock.patch.object(akamai.importutils, 'try_import')
    def test_missing_library(self, mock_import):
        mock_import.return_value = None
        self.assertRaises(
            exceptions.Backend,
            akamai.AkamaiBackend,
            objects.PoolTarget.from_dict(self.target)
        )

    @mock.patch.object(akamai.importutils, 'try_import')
    @mock.patch.object(akamai.requests.Session, 'post')
    def test_create_zone_missed_contract_id(self, mock_post, mock_import):
        mock_auth = mock.Mock()
        mock_import.return_value = mock_auth
        self.target['options'].remove(
            {'key': 'akamai_contract_id', 'value': 'G-XYW'})
        backend = akamai.AkamaiBackend(
            objects.PoolTarget.from_dict(self.target)
        )
        mock_auth.EdgeGridAuth.assert_called_once_with(
            access_token='access_token',
            client_secret='client_secret',
            client_token='client_token'
        )

        with base_fixtures.random_seed(0):
            self.assertRaisesRegex(
                exceptions.Backend,
                'contractId is required for zone creation',
                backend.create_zone, self.admin_context, self.zone)

        mock_post.assert_not_called()

    @mock.patch.object(akamai.importutils, 'try_import')
    @mock.patch.object(akamai.requests.Session, 'post')
    def test_create_zone(self, mock_post, mock_import):
        mock_auth = mock.Mock()
        mock_import.return_value = mock_auth
        backend = akamai.AkamaiBackend(
            objects.PoolTarget.from_dict(self.target)
        )
        mock_auth.EdgeGridAuth.assert_called_once_with(
            access_token='access_token',
            client_secret='client_secret',
            client_token='client_token'
        )

        with base_fixtures.random_seed(0):
            backend.create_zone(self.admin_context, self.zone)

        project_id = self.admin_context.project_id or self.zone.tenant_id
        mock_post.assert_called_once_with(
            json={
                'comment': 'Created by Designate for Tenant %s' % project_id,
                'masters': ['192.0.2.1', '192.0.2.2'],
                'type': 'secondary', 'zone': 'example.com.'
            },
            params={
                'gid': '777',
                'contractId': 'G-XYW'
            },
            url='https://host_value/config-dns/v2/zones'
        )

    @mock.patch.object(akamai.importutils, 'try_import')
    @mock.patch.object(akamai.requests.Session, 'post')
    def test_create_zone_duplicate_zone(self, mock_post, mock_import):
        mock_auth = mock.Mock()
        mock_import.return_value = mock_auth
        backend = akamai.AkamaiBackend(
            objects.PoolTarget.from_dict(self.target)
        )
        mock_auth.EdgeGridAuth.assert_called_once_with(
            access_token='access_token',
            client_secret='client_secret',
            client_token='client_token'
        )

        mock_post.return_value = self.gen_response(409, 'Conflict')

        with base_fixtures.random_seed(0):
            backend.create_zone(self.admin_context, self.zone)

        project_id = self.admin_context.project_id or self.zone.tenant_id
        mock_post.assert_called_once_with(
            json={
                'comment': 'Created by Designate for Tenant %s' % project_id,
                'masters': ['192.0.2.1', '192.0.2.2'],
                'type': 'secondary', 'zone': 'example.com.'
            },
            params={
                'gid': '777',
                'contractId': 'G-XYW'
            },
            url='https://host_value/config-dns/v2/zones'
        )

    @mock.patch.object(akamai.importutils, 'try_import')
    @mock.patch.object(akamai.requests.Session, 'post')
    def test_create_zone_with_tsig_key(self, mock_post, mock_import):
        mock_auth = mock.Mock()
        mock_import.return_value = mock_auth
        self.target['options'].extend([
            {'key': 'tsig_key_name', 'value': 'test_key'},
            {'key': 'tsig_key_algorithm', 'value': 'hmac-sha512'},
            {'key': 'tsig_key_secret', 'value': 'aaaabbbbccc'}
        ])
        backend = akamai.AkamaiBackend(
            objects.PoolTarget.from_dict(self.target)
        )
        mock_auth.EdgeGridAuth.assert_called_once_with(
            access_token='access_token',
            client_secret='client_secret',
            client_token='client_token'
        )

        with base_fixtures.random_seed(0):
            backend.create_zone(self.admin_context, self.zone)

        project_id = self.admin_context.project_id or self.zone.tenant_id
        mock_post.assert_called_once_with(
            json={
                'comment': 'Created by Designate for Tenant %s' % project_id,
                'masters': ['192.0.2.1', '192.0.2.2'],
                'type': 'secondary',
                'zone': 'example.com.',
                'tsigKey': {
                    'name': 'test_key',
                    'algorithm': 'hmac-sha512',
                    'secret': 'aaaabbbbccc',
                }
            },
            params={
                'gid': '777',
                'contractId': 'G-XYW'
            },
            url='https://host_value/config-dns/v2/zones'
        )

    @mock.patch.object(akamai.importutils, 'try_import')
    @mock.patch.object(akamai.requests.Session, 'post')
    def test_create_zone_raise_error(self, mock_post, mock_import):
        mock_auth = mock.Mock()
        mock_import.return_value = mock_auth
        backend = akamai.AkamaiBackend(
            objects.PoolTarget.from_dict(self.target)
        )
        mock_auth.EdgeGridAuth.assert_called_once_with(
            access_token='access_token',
            client_secret='client_secret',
            client_token='client_token'
        )

        json_data = {
            'title': 'Missing parameter',
            'detail': 'Missed A option'
        }
        mock_post.return_value = self.gen_response(
            400, 'Bad Request', json_data)

        with base_fixtures.random_seed(0):
            self.assertRaisesRegex(
                exceptions.Backend,
                'Zone creation failed due to: Missed A option',
                backend.create_zone, self.admin_context, self.zone)

        project_id = self.admin_context.project_id or self.zone.tenant_id
        mock_post.assert_called_once_with(
            json={
                'comment': 'Created by Designate for Tenant %s' % project_id,
                'masters': ['192.0.2.1', '192.0.2.2'],
                'type': 'secondary', 'zone': 'example.com.'
            },
            params={
                'gid': '777',
                'contractId': 'G-XYW'
            },
            url='https://host_value/config-dns/v2/zones'
        )

    @mock.patch.object(akamai.importutils, 'try_import')
    @mock.patch.object(akamai.requests.Session, 'post')
    def test_force_delete_zone(self, mock_post, mock_import):
        mock_auth = mock.Mock()
        mock_import.return_value = mock_auth
        backend = akamai.AkamaiBackend(
            objects.PoolTarget.from_dict(self.target)
        )
        mock_auth.EdgeGridAuth.assert_called_once_with(
            access_token='access_token',
            client_secret='client_secret',
            client_token='client_token'
        )

        mock_post.return_value = self.gen_response(200, 'Success')

        with base_fixtures.random_seed(0):
            backend.delete_zone(self.admin_context, self.zone)

        mock_post.assert_called_once_with(
            json={
                'zones': ['example.com.']
            },
            params={
                'force': True
            },
            url='https://host_value/config-dns/v2/zones/delete-requests'
        )

    @mock.patch.object(akamai.importutils, 'try_import')
    @mock.patch.object(akamai.requests.Session, 'post')
    def test_force_delete_zone_raise_error(self, mock_post, mock_import):
        mock_auth = mock.Mock()
        mock_import.return_value = mock_auth
        backend = akamai.AkamaiBackend(
            objects.PoolTarget.from_dict(self.target)
        )
        mock_auth.EdgeGridAuth.assert_called_once_with(
            access_token='access_token',
            client_secret='client_secret',
            client_token='client_token'
        )

        mock_post.return_value = self.gen_response(
            403, 'Bad Request', {'detail': 'Unexpected error'})

        with base_fixtures.random_seed(0):
            self.assertRaisesRegex(
                exceptions.Backend,
                'Zone deletion failed due to: Unexpected error',
                backend.delete_zone, self.admin_context, self.zone)

        mock_post.assert_called_once_with(
            json={
                'zones': ['example.com.']
            },
            params={
                'force': True
            },
            url='https://host_value/config-dns/v2/zones/delete-requests'
        )

    @mock.patch.object(akamai.importutils, 'try_import')
    @mock.patch.object(akamai.requests.Session, 'post')
    def test_force_delete_zone_raise_error_404(self, mock_post, mock_import):
        mock_auth = mock.Mock()
        mock_import.return_value = mock_auth
        backend = akamai.AkamaiBackend(
            objects.PoolTarget.from_dict(self.target)
        )
        mock_auth.EdgeGridAuth.assert_called_once_with(
            access_token='access_token',
            client_secret='client_secret',
            client_token='client_token'
        )

        mock_post.return_value = self.gen_response(
            404, 'Bad Request', {'detail': 'Unexpected error'})

        with base_fixtures.random_seed(0):
            backend.delete_zone(self.admin_context, self.zone)

        mock_post.assert_called_once_with(
            json={
                'zones': ['example.com.']
            },
            params={
                'force': True
            },
            url='https://host_value/config-dns/v2/zones/delete-requests'
        )

    @mock.patch.object(akamai.importutils, 'try_import')
    @mock.patch.object(akamai.requests.Session, 'post')
    @mock.patch.object(akamai.requests.Session, 'get')
    def test_soft_delete_zone(self, mock_get, mock_post, mock_import):
        mock_auth = mock.Mock()
        mock_import.return_value = mock_auth
        backend = akamai.AkamaiBackend(
            objects.PoolTarget.from_dict(self.target)
        )
        mock_auth.EdgeGridAuth.assert_called_once_with(
            access_token='access_token',
            client_secret='client_secret',
            client_token='client_token'
        )

        mock_post.side_effect = [
            # emulate, when Force=True is forbidden
            self.gen_response(403, 'Forbidden'),
            # emulate request, when Force=False
            self.gen_response(200, 'Success', {'requestId': 'nice_id'}),
        ]

        # emulate max 9 failed attempts and 1 success
        mock_get.side_effect = 9 * [
            self.gen_response(200, 'Success', {'isComplete': False})
        ] + [
            self.gen_response(200, 'Success', {'isComplete': True})
        ]

        with base_fixtures.random_seed(0), mock.patch.object(
                akamai.time, 'sleep') as mock_sleep:
            mock_sleep.return_value = None
            backend.delete_zone(self.admin_context, self.zone)

        self.assertEqual(10, mock_sleep.call_count)

        url = 'https://host_value/config-dns/v2/zones/delete-requests/nice_id'
        mock_get.assert_has_calls(9 * [mock.call(url=url)])

        mock_post.assert_has_calls([
            mock.call(
                json={'zones': ['example.com.']},
                params={'force': True},
                url='https://host_value/config-dns/v2/zones/delete-requests'
            ),
            mock.call(
                json={'zones': ['example.com.']},
                params={'force': False},
                url='https://host_value/config-dns/v2/zones/delete-requests'
            )
        ])

    @mock.patch.object(akamai.importutils, 'try_import')
    @mock.patch.object(akamai.requests.Session, 'post')
    @mock.patch.object(akamai.requests.Session, 'get')
    def test_soft_delete_zone_failed_after_10_attempts(
            self, mock_get, mock_post, mock_import):
        mock_auth = mock.Mock()
        mock_import.return_value = mock_auth
        backend = akamai.AkamaiBackend(
            objects.PoolTarget.from_dict(self.target)
        )
        mock_auth.EdgeGridAuth.assert_called_once_with(
            access_token='access_token',
            client_secret='client_secret',
            client_token='client_token'
        )

        mock_post.side_effect = [
            # emulate, when Force=True is forbidden
            self.gen_response(403, 'Forbidden'),
            # emulate request, when Force=False
            self.gen_response(200, 'Success', {'requestId': 'nice_id'}),
        ]

        # emulate max 10 failed attempts
        mock_get.side_effect = 10 * [
            self.gen_response(200, 'Success', {'isComplete': False})
        ]

        with base_fixtures.random_seed(0), mock.patch.object(
                akamai.time, 'sleep') as mock_sleep:
            mock_sleep.return_value = None
            self.assertRaisesRegex(
                exceptions.Backend,
                'Zone was not deleted after 10 attempts',
                backend.delete_zone, self.admin_context, self.zone)

        self.assertEqual(10, mock_sleep.call_count)

        url = 'https://host_value/config-dns/v2/zones/delete-requests/nice_id'
        mock_get.assert_has_calls(10 * [mock.call(url=url)])

        mock_post.assert_has_calls([
            mock.call(
                json={'zones': ['example.com.']},
                params={'force': True},
                url='https://host_value/config-dns/v2/zones/delete-requests'
            ),
            mock.call(
                json={'zones': ['example.com.']},
                params={'force': False},
                url='https://host_value/config-dns/v2/zones/delete-requests'
            )
        ])

    @mock.patch.object(akamai.importutils, 'try_import')
    @mock.patch.object(akamai.requests.Session, 'post')
    def test_soft_delete_zone_raise_error(self, mock_post, mock_import):
        mock_auth = mock.Mock()
        mock_import.return_value = mock_auth
        backend = akamai.AkamaiBackend(
            objects.PoolTarget.from_dict(self.target)
        )
        mock_auth.EdgeGridAuth.assert_called_once_with(

            access_token='access_token',
            client_secret='client_secret',
            client_token='client_token'
        )

        mock_post.side_effect = [
            # emulate, when Force=True is forbidden
            self.gen_response(403, 'Forbidden'),
            # emulate request, when Force=False
            self.gen_response(409, 'Conflict', {'detail': 'Intenal Error'})
        ]

        with base_fixtures.random_seed(0):
            self.assertRaisesRegex(
                exceptions.Backend,
                'Zone deletion failed due to: Intenal Error',
                backend.delete_zone, self.admin_context, self.zone)

        mock_post.assert_has_calls([
            mock.call(
                json={'zones': ['example.com.']},
                params={'force': True},
                url='https://host_value/config-dns/v2/zones/delete-requests'
            ),
            mock.call(
                json={'zones': ['example.com.']},
                params={'force': False},
                url='https://host_value/config-dns/v2/zones/delete-requests'
            )
        ])

    @mock.patch.object(akamai.importutils, 'try_import')
    @mock.patch.object(akamai.requests.Session, 'post')
    def test_soft_delete_zone_missed_request_id(self, mock_post, mock_import):
        mock_auth = mock.Mock()
        mock_import.return_value = mock_auth
        backend = akamai.AkamaiBackend(
            objects.PoolTarget.from_dict(self.target)
        )
        mock_auth.EdgeGridAuth.assert_called_once_with(

            access_token='access_token',
            client_secret='client_secret',
            client_token='client_token'
        )

        mock_post.side_effect = [
            # emulate, when Force=True is forbidden
            self.gen_response(403, 'Forbidden'),
            # emulate request, when Force=False
            self.gen_response(200, 'Success')
        ]

        with base_fixtures.random_seed(0):
            self.assertRaisesRegex(
                exceptions.Backend,
                'Zone deletion failed due to: requestId missed in response',
                backend.delete_zone, self.admin_context, self.zone)

        mock_post.assert_has_calls([
            mock.call(
                json={'zones': ['example.com.']},
                params={'force': True},
                url='https://host_value/config-dns/v2/zones/delete-requests'
            ),
            mock.call(
                json={'zones': ['example.com.']},
                params={'force': False},
                url='https://host_value/config-dns/v2/zones/delete-requests'
            )
        ])
