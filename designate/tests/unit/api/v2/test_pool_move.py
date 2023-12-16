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

from designate.api.v2.controllers.zones.tasks import pool_move
from designate.central import rpcapi
from designate import exceptions
from designate import objects


class TestPoolMoveAPI(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.central_api = mock.Mock()
        self.zone = objects.Zone(
            id='c2c6381f-77f6-4e63-a63d-fda0fc22b0b2',
            pool_id='bddce92d-5ca5-40e0-b787-c1ba9884278f',
            name='example.com.',
            email='example@example.com'
        )
        mock.patch.object(rpcapi.CentralAPI, 'get_instance',
                          return_value=self.central_api).start()

        self.controller = pool_move.PoolMoveController()

    @mock.patch('pecan.response', mock.Mock())
    @mock.patch('pecan.request')
    def test_post_all_target_pool_not_different(self, mock_request):
        mock_request.environ = {'context': mock.Mock()}
        mock_request.body_dict = {
            'pool_id': 'bddce92d-5ca5-40e0-b787-c1ba9884278f'
        }
        mock_pool_move = mock.Mock()
        mock_pool_move.status = 'ERROR'

        self.central_api.get_zone.return_value = self.zone
        self.central_api.pool_move_zone.return_value = mock_pool_move

        self.assertRaisesRegex(
            exceptions.BadRequest,
            'Target pool must be different for zone pool move',
            self.controller.post_all, self.zone.id
        )

    @mock.patch('pecan.response')
    @mock.patch('pecan.request')
    def test_post_all_move_error(self, mock_request, mock_response):
        mock_request.environ = {'context': mock.Mock()}
        mock_pool_move = mock.Mock()
        mock_pool_move.status = 'ERROR'

        self.central_api.get_zone.return_value = self.zone
        self.central_api.pool_move_zone.return_value = mock_pool_move

        self.controller.post_all(self.zone.id)

        self.assertEqual(500, mock_response.status_int)
