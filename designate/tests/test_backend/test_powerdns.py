# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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
import mock
import testtools
import sqlalchemy

from designate.tests.test_backend import BackendTestCase
from designate import objects
from designate import exceptions
from designate.backend import impl_powerdns
from designate.backend.impl_powerdns import tables


class PowerDNSBackendTestCase(BackendTestCase):
    def setUp(self):
        super(PowerDNSBackendTestCase, self).setUp()

        self.zone = objects.Zone(id='e2bed4dc-9d01-11e4-89d3-123b93f75cba',
                                 name='example.com.',
                                 email='example@example.com')

        self.target = objects.PoolTarget.from_dict({
            'id': '4588652b-50e7-46b9-b688-a9bad40a873e',
            'type': 'powerdns',
            'masters': [{'host': '192.0.2.1', 'port': 53},
                        {'host': '192.0.2.2', 'port': 35}],
            'options': [{'key': 'connection', 'value': 'memory://',
                         'key': 'host', 'value': '192.0.2.3',
                         'key': 'port', 'value': '53'}],
        })

        self.backend = impl_powerdns.PowerDNSBackend(self.target)

    # Helper Methpds
    def assertSessionTransactionCalls(self, session_mock, begin=0, commit=0,
                                      rollback=0):
        # Ensure the Sessions Transactions functions are called correctly
        self.assertEqual(begin, session_mock.begin.call_count)
        self.assertEqual(commit, session_mock.commit.call_count)
        self.assertEqual(rollback, session_mock.rollback.call_count)

    # Tests for Public Methods
    @mock.patch.object(impl_powerdns.PowerDNSBackend, 'get_session')
    def test_create_zone(self, get_session_mock):
        session_mock = mock.MagicMock()
        get_session_mock.return_value = session_mock

        context = self.get_context()
        self.backend.create_zone(context, self.zone)

        self.assertSessionTransactionCalls(
            session_mock, begin=1, commit=1, rollback=0)

        # Ensure we have two queries, one INSERT, one SELECT
        self.assertEqual(2, session_mock.execute.call_count)

        self.assertIsInstance(
            session_mock.execute.call_args_list[0][0][0],
            sqlalchemy.sql.dml.Insert)

        self.assertDictContainsSubset(
            {'type': 'SLAVE',
             'designate_id': self.zone.id,
             'master': '192.0.2.1:53,192.0.2.2:35',
             'name': self.zone.name.rstrip('.')},
            session_mock.execute.call_args_list[0][0][1])

        self.assertIsInstance(
            session_mock.execute.call_args_list[1][0][0],
            sqlalchemy.sql.selectable.Select)

    @mock.patch.object(impl_powerdns.PowerDNSBackend, 'get_session')
    @mock.patch.object(impl_powerdns.PowerDNSBackend, '_create',
                       side_effect=Exception)
    def test_create_zone_failure_on_create(self, create_mock,
                                           get_session_mock):
        session_mock = mock.MagicMock()
        get_session_mock.return_value = session_mock

        with testtools.ExpectedException(Exception):
            self.backend.create_zone(self.get_context(), self.zone)

        self.assertSessionTransactionCalls(
            session_mock, begin=1, commit=0, rollback=1)

        # Ensure we called out into the _create method exactly once
        self.assertEqual(1, create_mock.call_count)

    @mock.patch.object(impl_powerdns.PowerDNSBackend, 'get_session')
    @mock.patch.object(impl_powerdns.PowerDNSBackend, '_create',
                       return_value=None)
    def test_create_zone_failure_on_commit(self, create_mock,
                                           get_session_mock):
        session_mock = mock.MagicMock()
        get_session_mock.return_value = session_mock

        # Configure the Session mocks's commit method to raise an exception
        session_mock.commit.side_effect = Exception

        with testtools.ExpectedException(Exception):
            self.backend.create_zone(self.get_context(), self.zone)

        self.assertSessionTransactionCalls(
            session_mock, begin=1, commit=1, rollback=0)

        # Ensure we called out into the _create method exactly once
        self.assertEqual(1, create_mock.call_count)

    @mock.patch.object(impl_powerdns.PowerDNSBackend, 'get_session')
    @mock.patch.object(impl_powerdns.PowerDNSBackend, '_get',
                       return_value=None)
    def test_delete_zone(self, get_mock, get_session_mock):
        session_mock = mock.MagicMock()
        get_session_mock.return_value = session_mock

        # Configure the Session mocks's execute method to return a fudged
        # resultproxy.
        rp_mock = mock.Mock()
        rp_mock.rowcount = 1

        session_mock.execute.return_value = rp_mock

        context = self.get_context()
        self.backend.delete_zone(context, self.zone)

        # Ensure the _get method was called with the correct arguments
        get_mock.assert_called_once_with(
            session_mock, tables.domains, self.zone.id,
            exceptions.ZoneNotFound, id_col=tables.domains.c.designate_id)

        # Ensure we have one query, a DELETE
        self.assertEqual(1, session_mock.execute.call_count)

        self.assertIsInstance(
            session_mock.execute.call_args_list[0][0][0],
            sqlalchemy.sql.dml.Delete)

        # TODO(kiall): Validate the ID being deleted

    @mock.patch.object(impl_powerdns.PowerDNSBackend, 'get_session')
    @mock.patch.object(impl_powerdns.PowerDNSBackend, '_get',
                       side_effect=exceptions.ZoneNotFound)
    @mock.patch.object(impl_powerdns.PowerDNSBackend, '_delete',
                       return_value=None)
    def test_delete_zone_zone_not_found(self, delete_mock, get_mock,
                                        get_session_mock):
        session_mock = mock.MagicMock()
        get_session_mock.return_value = session_mock

        context = self.get_context()
        self.backend.delete_zone(context, self.zone)

        # Ensure the _get method was called with the correct arguments
        get_mock.assert_called_once_with(
            session_mock, tables.domains, self.zone.id,
            exceptions.ZoneNotFound, id_col=tables.domains.c.designate_id)

        # Ensure the _delete method was not called
        self.assertFalse(delete_mock.called)
