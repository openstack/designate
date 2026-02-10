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
        self.pool_cmd = pool.PoolCommands()
        self.pool_cmd.replace = False

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

    @mock.patch.object(pool.PoolCommands, '_update_zones')
    @mock.patch.object(pool.PoolCommands, '_validate_pool')
    def test_update_pool_with_replace_clears_optional_fields(
            self, mock_validate, mock_update_zones):
        """Test that --replace clears optional fields not in YAML"""
        # Create an existing pool with optional fields set
        existing_pool = objects.Pool.from_dict({
            'id': '1',
            'name': 'test-pool',
            'ns_records': [{'hostname': 'ns1.example.com.', 'priority': 1}],
            'also_notifies': [{'host': '192.0.2.1', 'port': 53}],
            'attributes': {'key': 'value'},
            'catalog_zone': {
                'catalog_zone_fqdn': 'catalog.example.com.'
            }
        })

        # YAML data without optional fields
        pool_data = {
            'name': 'test-pool',
            'ns_records': [{'hostname': 'ns1.example.com.', 'priority': 1}],
        }

        # Enable replace mode
        self.pool_cmd.replace = True
        self.pool_cmd.dry_run = False

        # Mock central_api
        with mock.patch.object(
                self.pool_cmd, 'central_api') as mock_central_api:
            mock_central_api.update_pool.return_value = existing_pool

            # Call _update_pool
            self.pool_cmd._update_pool(pool_data, existing_pool)

            # Verify optional fields were cleared before update
            updated_pool = mock_central_api.update_pool.call_args[0][1]
            # Fields should be empty lists/None
            self.assertEqual(0, len(updated_pool.also_notifies))
            self.assertEqual(0, len(updated_pool.attributes))
            self.assertIsNone(updated_pool.catalog_zone)

    @mock.patch.object(pool.PoolCommands, '_update_zones')
    @mock.patch.object(pool.PoolCommands, '_validate_pool')
    def test_update_pool_without_replace_preserves_optional_fields(
            self, mock_validate, mock_update_zones):
        """Test that without --replace, optional fields are preserved"""
        # Create an existing pool with optional fields set
        existing_pool = objects.Pool.from_dict({
            'id': '1',
            'name': 'test-pool',
            'ns_records': [{'hostname': 'ns1.example.com.', 'priority': 1}],
            'also_notifies': [{'host': '192.0.2.1', 'port': 53}],
            'attributes': {'key': 'value'},
        })

        # YAML data without optional fields
        pool_data = {
            'name': 'test-pool',
            'ns_records': [{'hostname': 'ns1.example.com.', 'priority': 1}],
        }

        # Default merge mode (replace=False)
        self.pool_cmd.replace = False
        self.pool_cmd.dry_run = False

        # Mock central_api
        with mock.patch.object(
                self.pool_cmd, 'central_api') as mock_central_api:
            mock_central_api.update_pool.return_value = existing_pool

            # Call _update_pool
            self.pool_cmd._update_pool(pool_data, existing_pool)

            # Verify optional fields were NOT cleared and retain values
            updated_pool = mock_central_api.update_pool.call_args[0][1]

            # Verify also_notifies preserved
            self.assertEqual(1, len(updated_pool.also_notifies))
            self.assertEqual(
                '192.0.2.1', updated_pool.also_notifies[0].host)
            self.assertEqual(53, updated_pool.also_notifies[0].port)

            # Verify attributes preserved
            self.assertEqual(1, len(updated_pool.attributes))
            self.assertEqual('value', updated_pool.attributes[0].value)
