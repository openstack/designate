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

from designate.api.v2.controllers import quotas
from designate.central import rpcapi
from designate import exceptions


class TestQuotasAPI(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.central_api = mock.Mock()
        mock.patch.object(rpcapi.CentralAPI, 'get_instance',
                          return_value=self.central_api).start()

        self.controller = quotas.QuotasController()

    @mock.patch('pecan.response')
    @mock.patch('pecan.request')
    def test_post_all_move_error(self, mock_request, mock_response):
        mock_context = mock.Mock()
        mock_context.project_id = None
        mock_context.all_tenants = False
        mock_request.environ = {'context': mock_context}

        self.assertRaisesRegex(
            exceptions.MissingProjectID,
            'The all-projects flag must be used when using non-project '
            'scoped tokens.',
            self.controller.patch_one, 'b0758367-4ac7-436d-917e-390d2b3df734'
        )
