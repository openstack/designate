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

from keystoneauth1 import exceptions as kse
import oslotest.base

from designate.common import keystone
from designate import exceptions


class TestVerifyProjectid(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()

    @mock.patch('keystoneauth1.adapter.Adapter.get')
    def test_verify_project_id(self, mock_get):
        mock_result = mock.Mock()
        mock_result.ok = True
        mock_result.status_code = 200
        mock_get.return_value = mock_result
        self.assertTrue(keystone.verify_project_id(mock.Mock(), '1'))

    @mock.patch('keystoneauth1.adapter.Adapter.get')
    def test_verify_project_id_request_returns_403(self, mock_get):
        mock_result = mock.Mock()
        mock_result.ok = False
        mock_result.status_code = 403
        mock_get.return_value = mock_result
        self.assertTrue(keystone.verify_project_id(mock.Mock(), '1'))

    @mock.patch('keystoneauth1.adapter.Adapter.get')
    def test_verify_project_id_request_returns_404(self, mock_get):
        mock_result = mock.Mock()
        mock_result.ok = False
        mock_result.status_code = 404
        mock_get.return_value = mock_result
        self.assertRaisesRegex(
            exceptions.InvalidProject,
            '1 is not a valid project ID.',
            keystone.verify_project_id, mock.Mock(), '1'
        )

    @mock.patch('keystoneauth1.adapter.Adapter.get')
    def test_verify_project_id_request_returns_500(self, mock_get):
        mock_result = mock.Mock()
        mock_result.ok = False
        mock_result.status_code = 500
        mock_get.return_value = mock_result
        self.assertTrue(keystone.verify_project_id(mock.Mock(), '1'))

    @mock.patch('keystoneauth1.adapter.Adapter.get')
    def test_verify_project_endpoint_not_found(self, mock_get):
        mock_get.side_effect = kse.EndpointNotFound
        self.assertRaisesRegex(
            exceptions.KeystoneCommunicationFailure,
            'KeystoneV3 endpoint not found',
            keystone.verify_project_id, mock.Mock(), '1'
        )
