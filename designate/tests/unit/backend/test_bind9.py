# Copyright 2015 FUJITSU LIMITED
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

from designate.backend import impl_bind9
from designate import context
from designate import exceptions
from designate import objects
from designate.tests import fixtures
from designate import utils

import subprocess


class Bind9BackendTestCase(oslotest.base.BaseTestCase):
    def setUp(self):
        super(Bind9BackendTestCase, self).setUp()
        self.admin_context = mock.Mock()
        mock.patch.object(
            context.DesignateContext, 'get_admin_context',
            return_value=self.admin_context).start()

        self.zone = objects.Zone(
            id='cca7908b-dad4-4c50-adba-fb67d4c556e8',
            name='example.com.',
            email='example@example.com'
        )
        self.target = {
            'id': '4588652b-50e7-46b9-b688-a9bad40a873e',
            'type': 'bind9',
            'masters': [
                {'host': '192.168.1.1', 'port': 53},
                {'host': '192.168.1.2', 'port': 35}
            ],
            'options': [
                {'key': 'host', 'value': '192.168.2.3'},
                {'key': 'port', 'value': '53'},
                {'key': 'rndc_host', 'value': '192.168.2.4'},
                {'key': 'rndc_port', 'value': '953'},
                {'key': 'rndc_bin_path', 'value': '/usr/sbin/rndc'},
                {'key': 'rndc_config_file', 'value': '/etc/rndc.conf'},
                {'key': 'rndc_key_file', 'value': '/etc/rndc.key'},
                {'key': 'clean_zonefile', 'value': 'true'}
            ],
        }

        self.backend = impl_bind9.Bind9Backend(
            objects.PoolTarget.from_dict(self.target)
        )

    @mock.patch.object(impl_bind9.Bind9Backend, '_execute_rndc')
    def test_create_zone(self, mock_execute):
        with fixtures.random_seed(0):
            self.backend.create_zone(self.admin_context, self.zone)

        mock_execute.assert_called_with(
            [
                'addzone',
                'example.com  { type slave; masters { 192.168.1.1 port 53; 192.168.1.2 port 35;}; file "slave.example.com.cca7908b-dad4-4c50-adba-fb67d4c556e8"; };'  # noqa
            ]
        )

    @mock.patch.object(impl_bind9.Bind9Backend, '_execute_rndc')
    def test_update_zone(self, mock_execute):
        with fixtures.random_seed(0):
            self.backend.update_zone(self.admin_context, self.zone)

        mock_execute.assert_called_with(
            [
                'modzone',
                'example.com  { type slave; masters { 192.168.1.1 port 53; 192.168.1.2 port 35;}; file "slave.example.com.cca7908b-dad4-4c50-adba-fb67d4c556e8"; };'  # noqa
            ]
        )

    @mock.patch.object(impl_bind9.Bind9Backend, '_execute_rndc')
    def test_get_zone(self, mock_execute):
        with fixtures.random_seed(0):
            self.backend.get_zone(self.admin_context, self.zone)

        mock_execute.assert_called_with(
            ['showzone', 'example.com ']
        )

    @mock.patch.object(impl_bind9.Bind9Backend, '_execute_rndc')
    def test_create_zone_with_view(self, mock_execute):
        self.target['options'].append(
            {'key': 'view', 'value': 'guest'},
        )

        backend = impl_bind9.Bind9Backend(
            objects.PoolTarget.from_dict(self.target)
        )

        with fixtures.random_seed(1):
            backend.create_zone(self.admin_context, self.zone)

        mock_execute.assert_called_with(
            [
                'addzone',
                'example.com in guest { type slave; masters { 192.168.1.2 port 35; 192.168.1.1 port 53;}; file "slave.example.com.cca7908b-dad4-4c50-adba-fb67d4c556e8"; };'  # noqa
            ]
        )

    @mock.patch.object(impl_bind9.Bind9Backend, '_execute_rndc')
    def test_create_zone_raises_on_exception(self, mock_execute):
        mock_execute.side_effect = exceptions.Backend('badop')
        self.assertRaises(
            exceptions.Backend,
            self.backend.create_zone, self.admin_context, self.zone
        )

    @mock.patch.object(impl_bind9.Bind9Backend, '_execute_rndc')
    def test_create_zone_already_exists(self, mock_execute):
        mock_execute.side_effect = exceptions.Backend('already exists')

        self.backend.create_zone(self.admin_context, self.zone)

    @mock.patch.object(impl_bind9.Bind9Backend, '_execute_rndc')
    def test_delete_zone(self, mock_execute):
        self.backend.delete_zone(self.admin_context, self.zone)

        mock_execute.assert_called_with(
            ['delzone', '-clean', 'example.com ']
        )

    @mock.patch.object(impl_bind9.Bind9Backend, '_execute_rndc')
    def test_delete_zone_with_view(self, mock_execute):
        self.target['options'].append(
            {'key': 'view', 'value': 'guest'},
        )

        backend = impl_bind9.Bind9Backend(
            objects.PoolTarget.from_dict(self.target)
        )

        backend.delete_zone(self.admin_context, self.zone)

        mock_execute.assert_called_with(
            ['delzone', '-clean', 'example.com in guest']
        )

    @mock.patch.object(impl_bind9.Bind9Backend, '_execute_rndc')
    def test_delete_zone_without_clean_zonefile(self, mock_execute):
        self.target['options'] = [
            {'key': 'clean_zonefile', 'value': 'false'}
        ]

        backend = impl_bind9.Bind9Backend(
            objects.PoolTarget.from_dict(self.target)
        )

        backend.delete_zone(self.admin_context, self.zone, {})

        mock_execute.assert_called_with(
            ['delzone', 'example.com ']
        )

    @mock.patch.object(impl_bind9.Bind9Backend, '_execute_rndc')
    def test_delete_zone_raises_on_exception(self, mock_execute):
        mock_execute.side_effect = exceptions.Backend('badop')
        self.assertRaises(
            exceptions.Backend,
            self.backend.delete_zone, self.admin_context, self.zone
        )

    @mock.patch.object(impl_bind9.Bind9Backend, '_execute_rndc')
    def test_delete_zone_already_deleted(self, mock_execute):
        mock_execute.side_effect = exceptions.Backend('not found')

        self.backend.delete_zone(self.admin_context, self.zone)

    def test_generate_rndc_base_call(self):
        self.assertEqual(
            [
                '/usr/sbin/rndc', '-s', '192.168.2.4', '-p', '953',
                '-c', '/etc/rndc.conf', '-k', '/etc/rndc.key'
            ],
            self.backend._generate_rndc_base_call()
        )

    def test_generate_rndc_base_call_without_config_file(self):
        self.target['options'] = [
            {'key': 'rndc_host', 'value': '192.168.4.4'},
            {'key': 'rndc_port', 'value': '953'},
            {'key': 'rndc_bin_path', 'value': '/usr/sbin/rndc'},
            {'key': 'rndc_key_file', 'value': '/etc/rndc.key'},
        ]

        backend = impl_bind9.Bind9Backend(
            objects.PoolTarget.from_dict(self.target)
        )

        self.assertEqual(
            [
                '/usr/sbin/rndc', '-s', '192.168.4.4', '-p', '953',
                '-k', '/etc/rndc.key'
            ],
            backend._generate_rndc_base_call()
        )

    def test_generate_rndc_base_call_without_key_file(self):
        self.target['options'] = [
            {'key': 'rndc_host', 'value': '192.168.3.4'},
            {'key': 'rndc_port', 'value': '953'},
            {'key': 'rndc_bin_path', 'value': '/usr/sbin/rndc'},
            {'key': 'rndc_config_file', 'value': '/etc/rndc.conf'},
        ]

        backend = impl_bind9.Bind9Backend(
            objects.PoolTarget.from_dict(self.target)
        )

        self.assertEqual(
            [
                '/usr/sbin/rndc', '-s', '192.168.3.4', '-p', '953',
                '-c', '/etc/rndc.conf'
            ],
            backend._generate_rndc_base_call()
        )

    @mock.patch('designate.utils.execute')
    def test_execute_rndc(self, mock_execute):
        rndc_op = ['delzone', 'example.com ']

        self.backend._execute_rndc(rndc_op)

        mock_execute.assert_called_with(
            '/usr/sbin/rndc', '-s', '192.168.2.4', '-p', '953',
            '-c', '/etc/rndc.conf', '-k', '/etc/rndc.key',
            'delzone', 'example.com ', timeout=None
        )

    @mock.patch('designate.utils.execute')
    def test_execute_rndc_timeout(self, mock_execute):
        rndc_op = ['delzone', 'example.com ']

        self.backend._rndc_timeout = 10
        self.backend._execute_rndc(rndc_op)

        mock_execute.assert_called_with(
            '/usr/sbin/rndc', '-s', '192.168.2.4', '-p', '953',
            '-c', '/etc/rndc.conf', '-k', '/etc/rndc.key',
            'delzone', 'example.com ', timeout=10
        )

    @mock.patch('designate.utils.execute')
    def test_execute_rndc_timeout_exception(self, mock_execute):
        rndc_op = ['delzone', 'example.com ']

        self.backend._rndc_timeout = 10

        mock_execute.side_effect = subprocess.TimeoutExpired([
            '/usr/sbin/rndc', '-s', '192.168.2.4', '-p', '953',
            '-c', '/etc/rndc.conf', '-k', '/etc/rndc.key',
            'delzone', 'example.com '], 10)

        self.assertRaises(
            exceptions.Backend,
            self.backend._execute_rndc, rndc_op
        )

    @mock.patch('designate.utils.execute')
    def test_execute_rndc_raises_on_exception(self, mock_execute):
        mock_execute.side_effect = utils.processutils.ProcessExecutionError()
        rndc_op = ['badop', 'example.com ']

        self.assertRaises(
            exceptions.Backend,
            self.backend._execute_rndc, rndc_op
        )
