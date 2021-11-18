# Copyright 2016 Hewlett Packard Enterprise Development Company LP
#
# Author: Federico Ceratto <federico.ceratto@hpe.com>
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
from unittest.mock import call

from oslo_concurrency import processutils

from designate.backend.agent_backend import impl_knot2
from designate import exceptions
import designate.tests
from designate.tests.unit.agent import backends


class Knot2AgentBackendTestCase(designate.tests.TestCase):
    def setUp(self):
        super(Knot2AgentBackendTestCase, self).setUp()

        self.backend = impl_knot2.Knot2Backend('foo')
        self.backend._execute_knotc = mock.Mock()

    def test_start_backend(self):
        self.backend.start()

    def test_stop_backend(self):
        self.backend.stop()

    def test_create_zone(self):
        zone = backends.create_dnspy_zone('example.org')

        self.backend.create_zone(zone)

        self.backend._execute_knotc.assert_has_calls([
            call('conf-begin'),
            call('conf-set', 'zone[example.org]',
                 expected_error='duplicate identifier'),
            call('conf-commit'),
            call('zone-refresh', 'example.org')
        ])

    def test_create_zone_already_there(self):
        self.backend._execute_knotc.return_value = 'duplicate identifier'

        zone = backends.create_dnspy_zone('example.org')

        self.backend.create_zone(zone)

        self.backend._execute_knotc.assert_has_calls([
            call('conf-begin'),
            call('conf-set', 'zone[example.org]',
                 expected_error='duplicate identifier'),
            call('conf-commit'),
            call('zone-refresh', 'example.org')
        ])

    def test_start_minidns_to_knot_axfr(self):
        self.backend._start_minidns_to_knot_axfr('foo')

        self.backend._execute_knotc.assert_called_with('zone-refresh', 'foo')

    @mock.patch('oslo_concurrency.lockutils.lock')
    def test_modify_zone(self, mock_lock):
        self.backend._modify_zone('blah', 'bar')

        self.assertEqual(3, self.backend._execute_knotc.call_count)

        self.backend._execute_knotc.assert_called_with('conf-commit')

    @mock.patch('oslo_concurrency.lockutils.lock')
    def test_modify_zone_exception(self, mock_lock):
        # Raise an exception during the second call to _execute_knotc
        self.backend._execute_knotc.side_effect = [None, exceptions.Backend,
                                                   None]
        self.assertRaises(
            exceptions.Backend,
            self.backend._modify_zone, 'blah', 'bar'
        )

        self.assertEqual(3, self.backend._execute_knotc.call_count)

        self.backend._execute_knotc.assert_has_calls([
            call('conf-begin'),
            call('blah', 'bar'),
            call('conf-abort'),
        ])

    @mock.patch('designate.backend.agent_backend.impl_knot2.execute')
    def test_find_zone_serial(self, mock_execute):
        result = (
            '[example.com.] type: slave | serial: 20 | next-event: idle | '
            'auto-dnssec: disabled]'
        )
        mock_execute.return_value = result, ''

        serial = self.backend.find_zone_serial('example.com')

        self.assertEqual(20, serial)

    @mock.patch('designate.backend.agent_backend.impl_knot2.execute')
    def test_find_zone_serial_zone_not_found(self, mock_execute):
        mock_execute.side_effect = processutils.ProcessExecutionError(
            'error: [example.com.] (no such zone found)'
        )

        serial = self.backend.find_zone_serial('example.com')

        self.assertIsNone(serial)

    @mock.patch('designate.backend.agent_backend.impl_knot2.execute')
    def test_find_zone_serial_unexpected_output(self, mock_execute):
        mock_execute.return_value = 'bogus output', ''

        self.assertRaises(
            exceptions.Backend,
            self.backend.find_zone_serial, 'example.com'
        )

    @mock.patch('designate.backend.agent_backend.impl_knot2.execute')
    def test_find_zone_serial_error(self, mock_execute):
        mock_execute.side_effect = processutils.ProcessExecutionError('blah')

        self.assertRaises(
            exceptions.Backend,
            self.backend.find_zone_serial, 'example.com'
        )

    def test_update_zone(self):
        zone = backends.create_dnspy_zone('example.org')

        self.backend.update_zone(zone)

        self.backend._execute_knotc.assert_called_once_with(
            'zone-refresh', 'example.org'
        )

    def test_delete_zone(self):
        self.backend.delete_zone('example.org')

        self.backend._execute_knotc.assert_has_calls([
            call('conf-begin'),
            call('conf-unset', 'zone[example.org]',
                 expected_error='invalid identifier'),
            call('conf-commit'),
        ])

    def test_delete_zone_already_gone(self):
        self.backend._execute_knotc.return_value = 'duplicate identifier'

        self.backend.delete_zone('example.org')

        self.backend._execute_knotc.assert_has_calls([
            call('conf-begin'),
            call('conf-unset', 'zone[example.org]',
                 expected_error='invalid identifier'),
            call('conf-commit'),
        ])


class Knot2AgentExecuteTestCase(designate.tests.TestCase):
    def setUp(self):
        super(Knot2AgentExecuteTestCase, self).setUp()

        self.backend = impl_knot2.Knot2Backend('foo')

    def test_init(self):
        self.assertEqual('knotc', self.backend._knotc_cmd_name)

    @mock.patch('designate.backend.agent_backend.impl_knot2.execute')
    def test_execute_knotc_ok(self, mock_execute):
        mock_execute.return_value = ('OK', '')

        self.backend._execute_knotc('a1', 'a2')

        mock_execute.assert_called_with('knotc', 'a1', 'a2')

        self.assertEqual(1, mock_execute.call_count)

    @mock.patch('designate.backend.agent_backend.impl_knot2.execute')
    def test_execute_knotc_expected_error(self, mock_execute):
        mock_execute.return_value = ('xyz', '')

        self.backend._execute_knotc('a1', 'a2', expected_error='xyz')

        mock_execute.assert_called_once_with('knotc', 'a1', 'a2')

    @mock.patch('designate.backend.agent_backend.impl_knot2.execute')
    def test_execute_knotc_expected_output(self, mock_execute):
        mock_execute.return_value = ('xyz', '')

        self.backend._execute_knotc('a1', 'a2', expected_output='xyz')

        mock_execute.assert_called_once_with('knotc', 'a1', 'a2')

    @mock.patch('designate.backend.agent_backend.impl_knot2.execute')
    def test_execute_knotc_with_error(self, mock_execute):
        mock_execute.return_value = ('xyz', '')

        self.assertRaises(
            exceptions.Backend,
            self.backend._execute_knotc, 'a1', 'a2'
        )

        mock_execute.assert_called_once_with('knotc', 'a1', 'a2')

    @mock.patch('designate.backend.agent_backend.impl_knot2.execute')
    def test_execute_knotc_raising_exception(self, mock_execute):
        mock_execute.side_effect = processutils.ProcessExecutionError

        self.assertRaises(
            exceptions.Backend,
            self.backend._execute_knotc, 'a1', 'a2'
        )

        mock_execute.assert_called_once_with('knotc', 'a1', 'a2')
