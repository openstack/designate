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
# under the License.mport threading


from unittest import mock

import oslotest.base

import designate.conf
from designate import rpc
import designate.tests
from designate.worker import rpcapi


CONF = designate.conf.CONF


class TestService(oslotest.base.BaseTestCase):
    @mock.patch.object(rpc, 'get_client', mock.Mock())
    def setUp(self):
        super().setUp()

        self.worker = rpcapi.WorkerAPI()
        self.worker.client = mock.Mock()

    def test_create_zone(self):
        self.worker.create_zone('context', 'zone')

        self.worker.client.cast.assert_called_with(
            'context', 'create_zone', zone='zone'
        )

    def test_update_zone(self):
        self.worker.update_zone('context', 'zone')

        self.worker.client.cast.assert_called_with(
            'context', 'update_zone', zone='zone'
        )

    def test_delete_zone(self):
        self.worker.delete_zone('context', 'zone', 'hard_delete')

        self.worker.client.cast.assert_called_with(
            'context', 'delete_zone', zone='zone', hard_delete='hard_delete'
        )

    def test_recover_shard(self):
        self.worker.recover_shard('context', 'begin', 'end')

        self.worker.client.cast.assert_called_with(
            'context', 'recover_shard', begin='begin', end='end'
        )

    def test_start_zone_export(self):
        self.worker.start_zone_export('context', 'zone', 'export')

        self.worker.client.cast.assert_called_with(
            'context', 'start_zone_export', zone='zone', export='export'
        )

    def test_perform_zone_xfr(self):
        self.worker.perform_zone_xfr('context', 'zone', 'servers')

        self.worker.client.cast.assert_called_with(
            'context', 'perform_zone_xfr', zone='zone', servers='servers'
        )

    def test_get_serial_number(self):
        self.worker.get_serial_number('context', 'zone', 'host', 53)

        self.worker.client.call.assert_called_with(
            'context', 'get_serial_number', zone='zone', host='host', port=53
        )
