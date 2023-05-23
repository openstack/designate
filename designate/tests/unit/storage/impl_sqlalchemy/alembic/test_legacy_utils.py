# Copyright 2022 Red Hat
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

from designate.storage.sqlalchemy.alembic import legacy_utils


class TestLegacyUtils(oslotest.base.BaseTestCase):

    @mock.patch('sqlalchemy.MetaData')
    @mock.patch('alembic.op.get_bind')
    def test_is_migration_needed(self, mock_get_bind, mock_metadata):
        mock_bind = mock.MagicMock()
        mock_get_bind.return_value = mock_bind
        mock_execute = mock.MagicMock()
        mock_bind.execute.return_value = mock_execute
        mock_metadata_obj = mock.MagicMock()
        mock_metadata_obj.tables.keys.side_effect = [
                [], ['migrate_version'], ['migrate_version'],
                ['migrate_version'], ['migrate_version'],
                ['migrate_version'], ['migrate_version']]
        mock_metadata.return_value = mock_metadata_obj

        mock_execute.scalar_one_or_none.side_effect = [
            None, '79', '80', '81', Exception('boom')]

        # No existing migrate_version table
        self.assertTrue(legacy_utils.is_migration_needed(2022))

        # DB revision None
        self.assertTrue(legacy_utils.is_migration_needed(80))

        # DB revision 79
        self.assertTrue(legacy_utils.is_migration_needed(80))

        # DB revision 80
        self.assertFalse(legacy_utils.is_migration_needed(80))

        # DB revision 81
        self.assertFalse(legacy_utils.is_migration_needed(80))

        # DB revision query exception (no table, etc.)
        self.assertTrue(legacy_utils.is_migration_needed(80))
