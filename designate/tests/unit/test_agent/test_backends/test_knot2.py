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

"""
    Unit-test the Knot 2 agent backend
    knotc is not being executed
"""

from mock import call
from oslo_concurrency.processutils import ProcessExecutionError
import dns.zone
import fixtures
import mock

from designate import exceptions
from designate.backend.agent_backend.impl_knot2 import Knot2Backend
from designate.tests import TestCase
import designate.backend.agent_backend.impl_knot2  # noqa


class Knot2AgentBackendBasicUnitTestCase(TestCase):

    def test_init(self):
        kb = Knot2Backend('foo')
        self.assertEqual('knotc', kb._knotc_cmd_name)

    @mock.patch('designate.backend.agent_backend.impl_knot2.execute')
    def test__execute_knotc_ok(self, mock_exe):
        mock_exe.return_value = ('OK', '')
        kb = Knot2Backend('foo')
        kb._execute_knotc('a1', 'a2')
        mock_exe.assert_called_with('knotc', 'a1', 'a2')
        self.assertEqual(1, mock_exe.call_count)

    @mock.patch('designate.backend.agent_backend.impl_knot2.execute')
    def test__execute_knotc_expected_error(self, mock_exe):
        mock_exe.return_value = ('xyz', '')
        kb = Knot2Backend('foo')
        kb._execute_knotc('a1', 'a2', expected_error='xyz')
        mock_exe.assert_called_once_with('knotc', 'a1', 'a2')

    @mock.patch('designate.backend.agent_backend.impl_knot2.execute')
    def test__execute_knotc_expected_output(self, mock_exe):
        mock_exe.return_value = ('xyz', '')
        kb = Knot2Backend('foo')
        kb._execute_knotc('a1', 'a2', expected_output='xyz')
        mock_exe.assert_called_once_with('knotc', 'a1', 'a2')

    @mock.patch('designate.backend.agent_backend.impl_knot2.execute')
    def test__execute_knotc_with_error(self, mock_exe):
        mock_exe.return_value = ('xyz', '')
        kb = Knot2Backend('foo')
        self.assertRaises(
            exceptions.Backend,
            kb._execute_knotc, 'a1', 'a2')
        mock_exe.assert_called_once_with('knotc', 'a1', 'a2')

    @mock.patch('designate.backend.agent_backend.impl_knot2.execute')
    def test__execute_knotc_raising_exception(self, mock_exe):
        mock_exe.side_effect = ProcessExecutionError
        kb = Knot2Backend('foo')
        self.assertRaises(
            exceptions.Backend,
            kb._execute_knotc, 'a1', 'a2')
        mock_exe.assert_called_once_with('knotc', 'a1', 'a2')


class Knot2AgentBackendUnitTestCase(TestCase):

    def _create_dnspy_zone(self, name):
        zone_text = (
            '$ORIGIN %(name)s\n%(name)s 3600 IN SOA %(ns)s '
            'email.email.com. 1421777854 3600 600 86400 3600\n%(name)s '
            '3600 IN NS %(ns)s\n') % {'name': name, 'ns': 'ns1.designate.com'}

        return dns.zone.from_text(zone_text, check_origin=False)

    def setUp(self):
        super(Knot2AgentBackendUnitTestCase, self).setUp()
        self.kb = Knot2Backend('foo')
        self.patch_ob(self.kb, '_execute_knotc')

    def tearDown(self):
        super(Knot2AgentBackendUnitTestCase, self).tearDown()

    def patch_ob(self, *a, **kw):
        self.useFixture(fixtures.MockPatchObject(*a, **kw))

    def test_create_zone(self, *mocks):
        zone = self._create_dnspy_zone('example.org')
        self.kb.create_zone(zone)
        self.kb._execute_knotc.assert_has_calls([
            call('conf-begin'),
            call('conf-set', 'zone[example.org]',
                 expected_error='duplicate identifier'),
            call('conf-commit'),
            call('zone-refresh', 'example.org')
        ])

    def test_create_zone_already_there(self, *mocks):
        self.kb._execute_knotc.return_value = 'duplicate identifier'
        zone = self._create_dnspy_zone('example.org')
        self.kb.create_zone(zone)
        self.kb._execute_knotc.assert_has_calls([
            call('conf-begin'),
            call('conf-set', 'zone[example.org]',
                 expected_error='duplicate identifier'),
            call('conf-commit'),
            call('zone-refresh', 'example.org')
        ])

    def test__start_minidns_to_knot_axfr(self):
        self.kb._start_minidns_to_knot_axfr('foo')
        self.kb._execute_knotc.assert_called_with('zone-refresh', 'foo')

    @mock.patch('oslo_concurrency.lockutils.lock')
    def test__modify_zone(self, *mocks):
        self.kb._modify_zone('blah', 'bar')
        self.assertEqual(3, self.kb._execute_knotc.call_count)
        self.kb._execute_knotc.assert_called_with('conf-commit')

    @mock.patch('oslo_concurrency.lockutils.lock')
    def test__modify_zone_exception(self, *mocks):
        # Raise an exception during the second call to _execute_knotc
        self.kb._execute_knotc.side_effect = [None, exceptions.Backend, None]
        self.assertRaises(
            exceptions.Backend,
            self.kb._modify_zone, 'blah', 'bar')
        self.assertEqual(3, self.kb._execute_knotc.call_count)
        self.kb._execute_knotc.assert_has_calls([
            call('conf-begin'),
            call('blah', 'bar'),
            call('conf-abort'),
        ])

    @mock.patch('designate.backend.agent_backend.impl_knot2.execute')
    def test_find_zone_serial(self, mock_exe):
        mock_exe.return_value = "[example.com.] type: slave | serial: 20 | " \
            "next-event: idle | auto-dnssec: disabled]", ""
        serial = self.kb.find_zone_serial('example.com')
        self.assertEqual(20, serial)

    @mock.patch('designate.backend.agent_backend.impl_knot2.execute')
    def test_find_zone_serial__zone_not_found(self, mock_exe):
        mock_exe.side_effect = ProcessExecutionError(
            "error: [example.com.] (no such zone found)")
        serial = self.kb.find_zone_serial('example.com')
        self.assertIsNone(serial)

    @mock.patch('designate.backend.agent_backend.impl_knot2.execute')
    def test_find_zone_serial_unexpected_output(self, mock_exe):
        mock_exe.return_value = "bogus output", ""
        self.assertRaises(
            exceptions.Backend,
            self.kb.find_zone_serial, 'example.com')

    @mock.patch('designate.backend.agent_backend.impl_knot2.execute')
    def test_find_zone_serial_error(self, mock_exe):
        mock_exe.side_effect = ProcessExecutionError("blah")
        self.assertRaises(
            exceptions.Backend,
            self.kb.find_zone_serial, 'example.com')

    def test_update_zone(self):
        zone = self._create_dnspy_zone('example.org')
        self.kb.update_zone(zone)
        self.kb._execute_knotc.assert_called_once_with(
            'zone-refresh', 'example.org')

    def test_delete_zone(self):
        self.kb.delete_zone('example.org')
        self.kb._execute_knotc.assert_has_calls([
            call('conf-begin'),
            call('conf-unset', 'zone[example.org]',
                 expected_error='invalid identifier'),
            call('conf-commit'),
        ])

    def test_delete_zone_already_gone(self):
        self.kb._execute_knotc.return_value = 'duplicate identifier'
        self.kb.delete_zone('example.org')
        self.kb._execute_knotc.assert_has_calls([
            call('conf-begin'),
            call('conf-unset', 'zone[example.org]',
                 expected_error='invalid identifier'),
            call('conf-commit'),
        ])
