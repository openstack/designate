# Copyright 2015 Dyn Inc.
#
# Author: Yasha Bubnov <ybubnov@dyn.com>
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

from oslo_config import cfg

from designate.backend.agent_backend import impl_denominator
from designate import exceptions
from designate import tests
from designate.tests.unit.agent import backends
from designate import utils


class DenominatorAgentBackendTestCase(tests.TestCase):
    def setUp(self):
        super(DenominatorAgentBackendTestCase, self).setUp()

        self.CONF.set_override('listen', ['0.0.0.0:0'], 'service:agent')

        self.backend = impl_denominator.DenominatorBackend('foo')

    def test_start_backend(self):
        self.backend.start()

    def test_stop_backend(self):
        self.backend.stop()

    @mock.patch('designate.utils.execute', return_value=(
            'example.org SOA 86400 ns1.designate.com. '
            'hostmaster@example.org. 475 3600 600 604800 1800', None))
    def test_find_zone_serial(self, mock_execute):
        serial = self.backend.find_zone_serial('example.org.')

        # Ensure returned right serial number
        self.assertEqual(475, serial)

        # Ensure called "denominator zone add"
        self.assertIn('record', mock_execute.call_args[0])
        self.assertIn('get', mock_execute.call_args[0])

    @mock.patch('designate.utils.execute', return_value=('', None))
    def test_find_zone_serial_fail(self, mock_execute):
        serial = self.backend.find_zone_serial('example.org.')
        self.assertIsNone(serial)

    @mock.patch('designate.utils.execute', return_value=(None, None))
    def test_create_zone(self, mock_execute):
        zone = backends.create_dnspy_zone('example.org.')
        self.backend.create_zone(zone)

        # Ensure denominator called for each record (except SOA)
        # plus one to update zone data
        self.assertEqual(
            mock_execute.call_count, len(list(zone.iterate_rdatas()))
        )

    @mock.patch('designate.utils.execute')
    def test_update_zone(self, mock_execute):
        # Output from 'designate record list' command
        records = ('example.org SOA 86400 ns1.designate.com. '
                   'hostmaster@example.org. 475 3600 600 604800 1800\n'
                   'example.org NS 86400 ns1.designator.net.\n'
                   'example.org NS 86400 ns2.designator.net.\n'
                   'example.org MX 86400 10 mx1.designator.net.')

        # That should force update_zone to delete A and AAAA records
        # from the zone and create a new MX record.
        mock_execute.return_value = (records, None)

        zone = backends.create_dnspy_zone('example.org.')
        self.backend.update_zone(zone)

        # Ensure denominator called to:
        # *update zone info
        # *fetch list of zone records
        # *delete one MX record
        # *replace one NS record
        # *create 0 records
        # total: 4 calls

        self.assertEqual(4, mock_execute.call_count)

        methods = ['update_zone',
                   'get_records',
                   'create_record', 'update_record', 'delete_record']
        for method in methods:
            setattr(self.backend.denominator, method, mock.Mock(
                return_value=records))

        self.backend.update_zone(zone)
        self.assertEqual(1, self.backend.denominator.update_zone.call_count)
        self.assertEqual(1, self.backend.denominator.get_records.call_count)
        self.assertEqual(0, self.backend.denominator.create_record.call_count)
        self.assertEqual(1, self.backend.denominator.update_record.call_count)
        self.assertEqual(1, self.backend.denominator.delete_record.call_count)

    @mock.patch('designate.utils.execute', return_value=(None, None))
    def test_delete_zone(self, mock_execute):
        self.backend.delete_zone('example.org.')

        # Ensure called 'denominator zone delete'
        self.assertEqual(1, mock_execute.call_count)
        self.assertIn('zone', mock_execute.call_args[0])
        self.assertIn('delete', mock_execute.call_args[0])


class DenominatorAgentBaseTestCase(tests.TestCase):
    def setUp(self):
        super(DenominatorAgentBaseTestCase, self).setUp()

        self.backend = impl_denominator.Denominator(
            cfg.CONF['backend:agent:denominator']
        )

    def test_base(self):
        self.assertEqual(
            ['denominator', '-q', '-n', 'fake', '-C', '/etc/denominator.conf'],

            self.backend._base()
        )

    def test_base_without_config_file(self):
        self.CONF.set_override(
            'config_file', '', 'backend:agent:denominator'
        )

        self.assertEqual(
            ['denominator', '-q', '-n', 'fake'],
            self.backend._base()
        )

    @mock.patch('designate.utils.execute')
    def test_execute(self, mock_execute):
        mock_execute.return_value = ('stdout', None,)

        self.assertEqual(
            'stdout',
            self.backend._execute(
                ['record', '-z', 'example.org', 'add'], {'name': 'example.org'}
            )
        )

        mock_execute.assert_called_once_with(
            'denominator', '-q', '-n', 'fake', '-C', '/etc/denominator.conf',
            'record', '-z', 'example.org', 'add', '--name', 'example.org'
        )

    @mock.patch('designate.utils.execute')
    def test_execute_raises(self, mock_execute):
        mock_execute.side_effect = utils.processutils.ProcessExecutionError()

        self.assertRaises(
            exceptions.DesignateException,
            self.backend._execute, ['record', '-z', 'example.org', 'add'], {}
        )
