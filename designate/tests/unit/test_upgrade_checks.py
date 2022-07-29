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
from designate.sqlalchemy import session
from designate import tests


class TestDuplicateServiceStatus(tests.TestCase):
    def setUp(self):
        super(TestDuplicateServiceStatus, self).setUp()
        self.engine = session.get_engine('storage:sqlalchemy')
        self.meta = MetaData()
        self.meta.bind = self.engine
        self.service_statuses_table = Table('service_statuses', self.meta,
                                            autoload=True)

    def test_success(self):
        fake_record = {'id': '1',
                       'service_name': 'worker',
                       'hostname': 'localhost',
                       'status': 'UP',
                       'stats': '',
                       'capabilities': '',
                       }
        self.service_statuses_table.insert().execute(fake_record)
        # Different hostname should be fine
        fake_record['id'] = '2'
        fake_record['hostname'] = 'otherhost'
        self.service_statuses_table.insert().execute(fake_record)
        # Different service_name should be fine
        fake_record['id'] = '3'
        fake_record['service_name'] = 'producer'
        self.service_statuses_table.insert().execute(fake_record)
        checks = status.Checks()
        self.assertEqual(upgradecheck.Code.SUCCESS,
                         checks._duplicate_service_status().code)

    @mock.patch('designate.sqlalchemy.session.get_engine')
    def test_failure(self, mock_get_engine):
        mock_engine = mock.MagicMock()
        mock_execute = mock.MagicMock()
        mock_engine.execute.return_value = mock_execute
        mock_execute.fetchall.return_value = [(2,)]
        mock_get_engine.return_value = mock_engine

        checks = status.Checks()
        self.assertEqual(upgradecheck.Code.FAILURE,
                         checks._duplicate_service_status().code)
