# Copyright 2014 Hewlett-Packard Development Company, L.P.
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

import oslotest.base
import requests_mock

from designate.backend import impl_dynect
from designate import context
from designate import objects

MASTERS = [
    '192.0.2.1'
]
CONTACT = 'jdoe@example.org'

LOGIN_SUCCESS = {
    'status': 'success',
    'data': {
        'token': 'foo',
        'version': '3.5.6'
    },
    'job_id': 1,
    'msgs': [
        {
            'INFO': 'login: Login successful',
            'SOURCE': 'BLL',
            'ERR_CD': None,
            'LVL': 'INFO'
        }
    ]
}

LOGOUT_SUCCESS = {
    'status': 'success',
    'data': {},
    'job_id': 1345964647,
    'msgs': [
        {
            'INFO': 'logout: Logout successful',
            'SOURCE': 'BLL',
            'ERR_CD': None,
            'LVL': 'INFO'
        }
    ]
}

ZONE_CREATE = {
    'contact_nickname': 'owner',
    'masters': ['192.0.2.1'],
    'token': 'foo',
    'zone': 'example.com',
}

ZONE_DELETE = {
    'token': 'foo',
    'zone': 'example.com',
}

INVALID_ZONE_DELETE_DATA = {
    'status': 'failure',
    'data': {},
    'job_id': 1326038394,
    'msgs': [
        {
            'INFO': 'delete: Zone not deleted',
            'SOURCE': 'BLL',
            'ERR_CD': None,
            'LVL': 'INFO'
        }
    ]
}

INVALID_MASTER_DATA = {
    'status': 'failure',
    'data': {},
    'job_id': 1326038394,
    'msgs': [
        {
            'INFO': 'master: IP address expected',
            'SOURCE': 'DYN',
            'ERR_CD': 'INVALID_DATA',
            'LVL': 'ERROR'
        },
        {
            'INFO': 'create: Zone not created',
            'SOURCE': 'BLL',
            'ERR_CD': None,
            'LVL': 'INFO'
        }
    ]
}

TARGET_EXISTS = {
    'status': 'failure',
    'data': {},
    'job_id': 1345944906,
    'msgs': [
        {
            'INFO': 'name: Name already exists',
            'SOURCE': 'BLL',
            'ERR_CD': 'TARGET_EXISTS',
            'LVL': 'ERROR'
        },
        {
            'INFO': 'create: You already have this zone.',
            'SOURCE': 'BLL',
            'ERR_CD': None,
            'LVL': 'INFO'
        }
    ]
}

ACTIVATE_SUCCESS = {
    'status': 'success',
    'data': {
        'active': 'L',
        'masters': MASTERS,
        'contact_nickname': CONTACT,
        'tsig_key_name': '',
        'zone': 'example.com'
    },
    'job_id': 1345944927,
    'msgs': [
        {
            'INFO': 'activate: Service activated',
            'SOURCE': 'BLL',
            'ERR_CD': None,
            'LVL': 'INFO'
        }
    ]
}


class DynECTTestsCase(oslotest.base.BaseTestCase):
    def setUp(self):
        super(DynECTTestsCase, self).setUp()

        self.context = mock.Mock()
        self.admin_context = mock.Mock()
        mock.patch.object(
            context.DesignateContext, 'get_admin_context',
            return_value=self.admin_context).start()

        self.base_address = 'https://api.dynect.net:443/REST'
        self.zone = objects.Zone(
            id='e2bed4dc-9d01-11e4-89d3-123b93f75cba',
            name='example.com.',
            email='example@example.com',
        )
        self.target = {
            'id': '4588652b-50e7-46b9-b688-a9bad40a873e',
            'type': 'dyndns',
            'masters': [
                {'host': '192.0.2.1', 'port': 53}
            ],
            'options': [
                {'key': 'username', 'value': 'example'},
                {'key': 'password', 'value': 'secret'},
                {'key': 'customer_name', 'value': 'customer'},
                {'key': 'contact_nickname', 'value': 'customer'},
                {'key': 'tsig_key_name', 'value': 'tsig'},
            ],
        }

        self.backend = impl_dynect.DynECTBackend(
            objects.PoolTarget.from_dict(self.target)
        )

    @requests_mock.mock()
    def test_create_zone(self, req_mock):
        req_mock.post(
            '%s/Session' % self.base_address,
            json=LOGIN_SUCCESS,
        )
        req_mock.delete(
            '%s/Session' % self.base_address,
            json=LOGOUT_SUCCESS,
        )

        req_mock.post(
            '%s/Secondary/example.com' % self.base_address,
            json=ZONE_CREATE,
            status_code=200,
        )
        req_mock.put(
            '%s/Secondary/example.com' % self.base_address,
            json=ACTIVATE_SUCCESS,
            status_code=200,
        )

        self.backend.create_zone(self.context, self.zone)

    @requests_mock.mock()
    def test_create_zone_raise_dynclienterror(self, req_mock):
        # https://api.dynect.net:443/REST/Session
        req_mock.post(
            '%s/Session' % self.base_address,
            json=LOGIN_SUCCESS,
        )

        req_mock.post(
            '%s/Secondary/example.com' % self.base_address,
            json=INVALID_MASTER_DATA,
            status_code=400,
        )

        self.assertRaisesRegex(
            impl_dynect.DynClientError, 'Zone not created',
            self.backend.create_zone, self.context, self.zone,
        )

    @requests_mock.mock()
    def test_create_zone_duplicate_updates_existing(self, req_mock):
        req_mock.post(
            '%s/Session' % self.base_address,
            json=LOGIN_SUCCESS,
        )

        req_mock.delete(
            '%s/Session' % self.base_address,
            json=LOGIN_SUCCESS,
        )

        req_mock.post(
            '%s/Secondary/example.com' % self.base_address,
            json=TARGET_EXISTS,
            status_code=400,
        )

        req_mock.put(
            '%s/Secondary/example.com' % self.base_address,
            json=ACTIVATE_SUCCESS,
        )

        self.backend.create_zone(self.context, self.zone)

    @requests_mock.mock()
    def test_delete_zone(self, req_mock):
        req_mock.post(
            '%s/Session' % self.base_address,
            json=LOGIN_SUCCESS,
        )
        req_mock.delete(
            '%s/Session' % self.base_address,
            json=LOGOUT_SUCCESS,
        )

        req_mock.delete(
            '%s/Zone/example.com' % self.base_address,
            json=ZONE_DELETE,
            status_code=200,
        )
        req_mock.put(
            '%s/Secondary/example.com' % self.base_address,
            json=ACTIVATE_SUCCESS,
            status_code=200,
        )

        self.backend.delete_zone(self.context, self.zone)

    @requests_mock.mock()
    def test_delete_zone_raise_dynclienterror(self, req_mock):
        req_mock.post(
            '%s/Session' % self.base_address,
            json=LOGIN_SUCCESS,
        )
        req_mock.delete(
            '%s/Session' % self.base_address,
            json=LOGOUT_SUCCESS,
        )

        req_mock.delete(
            '%s/Zone/example.com' % self.base_address,
            json=INVALID_ZONE_DELETE_DATA,
            status_code=400,
        )
        req_mock.put(
            '%s/Secondary/example.com' % self.base_address,
            json=ACTIVATE_SUCCESS,
            status_code=200,
        )

        self.assertRaisesRegex(
            impl_dynect.DynClientError, 'Zone not deleted',
            self.backend.delete_zone, self.context, self.zone,
        )

    def test_error_from_response(self):
        error_data = dict(INVALID_ZONE_DELETE_DATA)
        mock_response = mock.Mock()
        mock_response.json.return_value = error_data
        error = impl_dynect.DynClientError().from_response(mock_response)

        self.assertEqual(error_data['job_id'], error.job_id)

    def test_error_from_response_login_failed(self):
        error_data = dict(INVALID_ZONE_DELETE_DATA)
        error_data['msgs'] = [
            {
                'INFO': 'login: foo',
                'SOURCE': 'BLL',
                'ERR_CD': None,
                'LVL': 'INFO'
            }
        ]
        mock_response = mock.Mock()
        mock_response.json.return_value = error_data

        self.assertRaisesRegex(
            impl_dynect.DynClientAuthError,
            'login: foo',
            impl_dynect.DynClientError().from_response, mock_response
        )

    def test_error_from_response_operation_failed(self):
        error_data = dict(INVALID_ZONE_DELETE_DATA)
        error_data['msgs'] = [
            {
                'INFO': 'Operation blocked',
                'SOURCE': 'BLL',
                'ERR_CD': None,
                'LVL': 'INFO'
            }
        ]
        mock_response = mock.Mock()
        mock_response.json.return_value = error_data

        self.assertRaisesRegex(
            impl_dynect.DynClientOperationBlocked,
            'Operation blocked',
            impl_dynect.DynClientError().from_response, mock_response
        )
