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
import mock

from designate import storage
from designate.tests import TestCase
from designate.tests.test_storage import StorageTestCase

LOG = logging.getLogger(__name__)


class SqlalchemyStorageTest(StorageTestCase, TestCase):
    def setUp(self):
        super(SqlalchemyStorageTest, self).setUp()

        self.storage = storage.get_storage('sqlalchemy')

    def test_ping_negative(self):
        with mock.patch.object(self.storage.engine, 'execute',
                               return_value=0):
            pong = self.storage.ping(self.admin_context)

            self.assertFalse(pong['status'])
            self.assertIsNotNone(pong['rtt'])

    def test_schema_table_names(self):
        table_names = [
            u'blacklists',
            u'migrate_version',
            u'pool_also_notifies',
            u'pool_attributes',
            u'pool_nameservers',
            u'pool_ns_records',
            u'pool_target_masters',
            u'pool_target_options',
            u'pool_targets',
            u'pools',
            u'quotas',
            u'records',
            u'recordsets',
            u'service_statuses',
            u'tlds',
            u'tsigkeys',
            u'zone_attributes',
            u'zone_masters',
            u'zone_tasks',
            u'zone_transfer_accepts',
            u'zone_transfer_requests',
            u'zones'
        ]
        self.assertEqual(table_names, self.storage.engine.table_names())

    def test_schema_table_indexes(self):
        indexes_t = self.storage.engine.execute("SELECT * FROM sqlite_master WHERE type = 'index';")  # noqa

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
                "reverse_name_deleted": "CREATE INDEX reverse_name_deleted ON zones (reverse_name, deleted)",  # noqa
                "zone_created_at": "CREATE INDEX zone_created_at ON zones (created_at)",  # noqa
                "zone_deleted": "CREATE INDEX zone_deleted ON zones (deleted)",
                "zone_tenant_deleted": "CREATE INDEX zone_tenant_deleted ON zones (tenant_id, deleted)",  # noqa
            }
        }
        self.assertDictEqual(expected, indexes)
