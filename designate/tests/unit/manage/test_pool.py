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

from designate.manage import pool
from designate import objects


class TestManagePool(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_get_masters_from_pool_handle_duplicate(self):
        result = pool.PoolCommands._get_masters_from_pool(
            objects.Pool.from_dict({
                'targets': [
                    {
                        'masters': [
                            {'host': '192.0.2.3', 'port': 53},
                            {'host': '192.0.2.3', 'port': 53}
                        ],
                    }
                ]
            })
        )

        self.assertEqual([{'host': '192.0.2.3', 'port': 53}], result)

    @mock.patch('yaml.dump')
    @mock.patch('builtins.open')
    def test_write_config_to_file(self, mock_open, mock_yaml_dump):
        pool.PoolCommands._write_config_to_file('filename', 'data')

        mock_open.assert_called_with('filename', 'w')
        mock_yaml_dump.assert_called_with(
            'data', mock.ANY, default_flow_style=False
        )
