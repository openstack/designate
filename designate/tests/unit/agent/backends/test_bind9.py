# Copyright 2014 Rackspace Inc.
#
# Author: Tim Simmons <tim.simmons@rackspace.com>
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

import dns.resolver

from designate.backend.agent_backend import impl_bind9
from designate import exceptions
import designate.tests
from designate.tests.unit.agent import backends
from designate import utils


class Bind9AgentBackendTestCase(designate.tests.TestCase):
    def setUp(self):
        super(Bind9AgentBackendTestCase, self).setUp()

        self.CONF.set_override('listen', ['0.0.0.0:0'], 'service:agent')

        self.backend = impl_bind9.Bind9Backend('foo')

    def test_start_backend(self):
        self.backend.start()

    def test_stop_backend(self):
        self.backend.stop()

    @mock.patch.object(dns.resolver.Resolver, 'query')
    def test_find_zone_serial(self, mock_query):
        self.assertIsNotNone(self.backend.find_zone_serial('example.org.'))

    @mock.patch.object(dns.resolver.Resolver, 'query')
    def test_find_zone_serial_query_raises(self, mock_query):
        mock_query.side_effect = Exception()
        self.assertIsNone(self.backend.find_zone_serial('example.org.'))

    @mock.patch('designate.utils.execute')
    @mock.patch('designate.backend.agent_backend.impl_bind9.Bind9Backend'
                '._sync_zone')
    def test_create_zone(self, mock_execute, mock_sync_zone):
        zone = backends.create_dnspy_zone('example.org')
        self.backend.create_zone(zone)

    @mock.patch('designate.utils.execute')
    @mock.patch('designate.backend.agent_backend.impl_bind9.Bind9Backend'
                '._sync_zone')
    def test_update_zone(self, mock_execute, mock_sync_zone):
        zone = backends.create_dnspy_zone('example.org')
        self.backend.update_zone(zone)

    @mock.patch('designate.utils.execute')
    @mock.patch('designate.backend.agent_backend.impl_bind9.Bind9Backend'
                '._sync_zone')
    def test_delete_zone(self, mock_execute, mock_sync_zone):
        self.backend.delete_zone('example.org.')

    @mock.patch('designate.utils.execute')
    def test_execute_rndc(self, mock_execute):
        self.CONF.set_override(
            'rndc_config_file', 'config_file', 'backend:agent:bind9'
        )
        self.CONF.set_override(
            'rndc_key_file', 'key_file', 'backend:agent:bind9'
        )

        self.backend._execute_rndc(self.backend._rndc_base())

        mock_execute.assert_called_once_with(
            'rndc', '-s', '127.0.0.1', '-p', '953',
            '-c', 'config_file', '-k', 'key_file'
        )

    @mock.patch('designate.utils.execute')
    def test_execute_rndc_raises(self, mock_execute):
        mock_execute.side_effect = utils.processutils.ProcessExecutionError()

        self.assertRaises(
            exceptions.Backend,
            self.backend._execute_rndc, self.backend._rndc_base()
        )

    @mock.patch('designate.utils.execute')
    @mock.patch.object(dns.zone.Zone, 'to_file')
    def test_sync_zone(self, mock_to_file, mock_execute):
        FAKE_STATE_PATH = '/tmp/fake/state/path'
        self.CONF.set_override('state_path', FAKE_STATE_PATH)

        zone = backends.create_dnspy_zone('example.org')

        self.backend._sync_zone(zone)

        mock_to_file.assert_called_once_with(
            FAKE_STATE_PATH + '/zones/example.org.zone', relativize=False
        )

        mock_execute.assert_called_once_with(
            'rndc', '-s', '127.0.0.1', '-p', '953', 'reload', 'example.org'
        )

    @mock.patch('designate.utils.execute')
    @mock.patch.object(dns.zone.Zone, 'to_file')
    def test_sync_zone_with_new_zone(self, mock_to_file, mock_execute):
        FAKE_STATE_PATH = '/tmp/fake/state/path'
        self.CONF.set_override('state_path', FAKE_STATE_PATH)

        zone = backends.create_dnspy_zone('example.org')

        self.backend._sync_zone(zone, new_zone_flag=True)

        mock_to_file.assert_called_once_with(
            FAKE_STATE_PATH + '/zones/example.org.zone', relativize=False
        )

        mock_execute.assert_called_once_with(
            'rndc', '-s', '127.0.0.1', '-p', '953', 'addzone',
            'example.org { type master; '
            'file "' + FAKE_STATE_PATH + '/zones/example.org.zone"; };'
        )
