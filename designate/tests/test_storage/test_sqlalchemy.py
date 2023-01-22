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
from oslo_log import log as logging
from sqlalchemy import text

from designate import storage
from designate.storage import sql
from designate.tests.test_storage import StorageTestCase
from designate.tests import TestCase

LOG = logging.getLogger(__name__)


class SqlalchemyStorageTest(StorageTestCase, TestCase):
    def setUp(self):
        super(SqlalchemyStorageTest, self).setUp()

        self.storage = storage.get_storage('sqlalchemy')

    def test_schema_table_names(self):
        table_names = [
            'blacklists',
            'pool_also_notifies',
            'pool_attributes',
            'pool_nameservers',
            'pool_ns_records',
            'pool_target_masters',
            'pool_target_options',
            'pool_targets',
            'pools',
            'quotas',
            'records',
            'recordsets',
            'service_statuses',
            'shared_zones',
            'tlds',
            'tsigkeys',
            'zone_attributes',
            'zone_masters',
            'zone_tasks',
            'zone_transfer_accepts',
            'zone_transfer_requests',
            'zones'
        ]

        inspector = self.storage.get_inspector()

        actual_table_names = inspector.get_table_names()

        # We have transitioned database schema migration tools.
        # They use different tracking tables. Accomidate that one or both
        # may exist in this test.
        migration_table_found = False
        if ('migrate_version' in actual_table_names or
                'alembic_version' in actual_table_names):
            migration_table_found = True
        self.assertTrue(
            migration_table_found, 'A DB migration table was not found.'
        )
        try:
            actual_table_names.remove('migrate_version')
        except ValueError:
            pass
        try:
            actual_table_names.remove('alembic_version')
        except ValueError:
            pass

        self.assertEqual(table_names, actual_table_names)

    def test_schema_table_indexes(self):
        with sql.get_read_session() as session:
            indexes_t = session.execute(
                text("SELECT * FROM sqlite_master WHERE type = 'index';"))

            indexes = {}  # table name -> index names -> cmd
            for _, index_name, table_name, num, cmd in indexes_t:
                if index_name.startswith("sqlite_"):
                    continue  # ignore sqlite-specific indexes
                if table_name not in indexes:
                    indexes[table_name] = {}
                indexes[table_name][index_name] = cmd

        expected = {
            "records": {
                "record_created_at": "CREATE INDEX record_created_at ON records (created_at)",  # noqa
                "records_tenant": "CREATE INDEX records_tenant ON records (tenant_id)",  # noqa
                "update_status_index": "CREATE INDEX update_status_index ON records (status, zone_id, tenant_id, created_at, serial)",  # noqa
            },
            "recordsets": {
                "recordset_created_at": "CREATE INDEX recordset_created_at ON recordsets (created_at)",  # noqa
                "recordset_type_name": "CREATE INDEX recordset_type_name ON recordsets (type, name)",  # noqa
                "reverse_name_dom_id": "CREATE INDEX reverse_name_dom_id ON recordsets (reverse_name, zone_id)",  # noqa
                "rrset_type_domainid": "CREATE INDEX rrset_type_domainid ON recordsets (type, zone_id)",  # noqa
                "rrset_updated_at": "CREATE INDEX rrset_updated_at ON recordsets (updated_at)",  # noqa
                "rrset_zoneid": "CREATE INDEX rrset_zoneid ON recordsets (zone_id)",  # noqa
                "rrset_type": "CREATE INDEX rrset_type ON recordsets (type)",  # noqa
                "rrset_ttl": "CREATE INDEX rrset_ttl ON recordsets (ttl)",  # noqa
                "rrset_tenant_id": "CREATE INDEX rrset_tenant_id ON recordsets (tenant_id)",  # noqa
            },
            "zones": {
                "delayed_notify": "CREATE INDEX delayed_notify ON zones (delayed_notify)",  # noqa
                "increment_serial": "CREATE INDEX increment_serial ON zones (increment_serial)",  # noqa
                "reverse_name_deleted": "CREATE INDEX reverse_name_deleted ON zones (reverse_name, deleted)",  # noqa
                "zone_created_at": "CREATE INDEX zone_created_at ON zones (created_at)",  # noqa
                "zone_deleted": "CREATE INDEX zone_deleted ON zones (deleted)",
                "zone_tenant_deleted": "CREATE INDEX zone_tenant_deleted ON zones (tenant_id, deleted)",  # noqa
            }
        }
        self.assertDictEqual(expected, indexes)
