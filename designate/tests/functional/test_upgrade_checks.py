# Copyright 2018 Red Hat Inc.
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

from oslo_upgradecheck import upgradecheck
from sqlalchemy.schema import MetaData
from sqlalchemy.schema import Table

from designate.cmd import status
from designate.storage import sql
import designate.tests.functional


class TestDuplicateServiceStatus(designate.tests.functional.TestCase):
    def setUp(self):
        super().setUp()
        self.meta = MetaData()
        self.meta.bind = sql.get_read_engine()
        self.service_statuses_table = Table(
            'service_statuses', self.meta,
            autoload_with=sql.get_read_engine()
        )

    def test_success(self):
        fake_record = {'id': '1',
                       'service_name': 'worker',
                       'hostname': '203.0.113.1',
                       'status': 'UP',
                       'stats': '',
                       'capabilities': '',
                       }
        with sql.get_write_session() as session:
            query = (
                self.service_statuses_table.insert().
                values(fake_record)
            )
            session.execute(query)

            # Different hostname should be fine
            fake_record['id'] = '2'
            fake_record['hostname'] = 'otherhost'
            query = (
                self.service_statuses_table.insert().
                values(fake_record)
            )
            session.execute(query)

            # Different service_name should be fine
            fake_record['id'] = '3'
            fake_record['service_name'] = 'producer'
            query = (
                self.service_statuses_table.insert().
                values(fake_record)
            )
            session.execute(query)

            checks = status.Checks()
            self.assertEqual(upgradecheck.Code.SUCCESS,
                             checks._duplicate_service_status().code)

    @mock.patch('designate.storage.sql.get_read_session')
    @mock.patch('designate.storage.sql.get_read_engine')
    def test_failure(self, mock_get_engine, mock_get_read):
        mock_sql_execute = mock.Mock()
        mock_sql_fetchall = mock.Mock()

        mock_get_read().__enter__.return_value = mock_sql_execute
        mock_sql_execute.execute.return_value = mock_sql_fetchall
        mock_sql_fetchall.fetchall.return_value = [(2,)]

        checks = status.Checks()

        result = checks._duplicate_service_status().code
        self.assertEqual(upgradecheck.Code.FAILURE, result)
