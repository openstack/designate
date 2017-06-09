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

import os
import tempfile
import unittest

import mock

from designate import exceptions
from designate import objects
from designate.tests.test_backend import BackendTestCase
from designate.backend.impl_bind9 import Bind9Backend

RNDC_BIN_PATH = "/usr/sbin/rndc"
RNDC_NOT_AVAILABLE = not os.path.isfile(RNDC_BIN_PATH)


class Bind9BackendTestCase(BackendTestCase):

    def setUp(self):
        super(Bind9BackendTestCase, self).setUp()

        self.zone = objects.Zone(id='cca7908b-dad4-4c50-adba-fb67d4c556e8',
                                 name='example.com.',
                                 email='example@example.com')

        target = objects.PoolTarget.from_dict({
            'id': '4588652b-50e7-46b9-b688-a9bad40a873e',
            'type': 'bind9',
            'masters': [{'host': '192.0.2.1', 'port': 53},
                        {'host': '192.0.2.2', 'port': 35}],
            'options': [{'key': 'host', 'value': '192.0.2.3'},
                        {'key': 'port', 'value': '53'},
                        {'key': 'rndc_host', 'value': '192.0.2.4'},
                        {'key': 'rndc_port', 'value': '953'},
                        {'key': 'rndc_bin_path', 'value': '/usr/sbin/rndc'},
                        {'key': 'rndc_config_file', 'value': '/etc/rndc.conf'},
                        {'key': 'rndc_key_file', 'value': '/etc/rndc.key'},
                        {'key': 'clean_zonefile', 'value': 'true'}],
        })

        self.backend = Bind9Backend(target)

    def test_backend_init(self):
        expected = ['/usr/sbin/rndc', '-s', '192.0.2.4', '-p', '953',
                    '-c', '/etc/rndc.conf', '-k', '/etc/rndc.key']
        self.assertEqual(expected, self.backend._rndc_call_base)

    def test_backend_init_using_defaults(self):
        target = objects.PoolTarget.from_dict({
            'id': '4588652b-50e7-46b9-b688-a9bad40a873e',
            'type': 'bind9',
            'masters': [{'host': '192.0.2.1', 'port': 53},
                        {'host': '192.0.2.2', 'port': 35}],
            'options': []
        })
        backend = Bind9Backend(target)
        expected = ['rndc', '-s', '127.0.0.1', '-p', '953']
        self.assertEqual(expected, backend._rndc_call_base)

    @mock.patch('designate.utils.execute')
    def test_create_zone(self, mock_exe):
        context = self.get_context()
        self.backend.create_zone(context, self.zone)
        self.assertEqual(1, mock_exe.call_count)
        args = mock_exe.call_args[0]
        self.assertEqual((
            '/usr/sbin/rndc', '-s', '192.0.2.4', '-p', '953',
            '-c', '/etc/rndc.conf', '-k', '/etc/rndc.key', 'addzone',
        ), args[:10])

        e1 = 'example.com  { type slave; masters { 192.0.2.1 port 53; 192.0.2.2 port 35;}; file "slave.example.com.cca7908b-dad4-4c50-adba-fb67d4c556e8"; };'  # noqa
        e2 = 'example.com  { type slave; masters { 192.0.2.2 port 35; 192.0.2.1 port 53;}; file "slave.example.com.cca7908b-dad4-4c50-adba-fb67d4c556e8"; };'  # noqa
        self.assertTrue(args[-1] == e1 or args[-1] == e2)

    @mock.patch('designate.utils.execute')
    def test_delete_zone(self, mock_exe):
        context = self.get_context()
        self.backend.delete_zone(context, self.zone)
        mock_exe.assert_called_with(
            '/usr/sbin/rndc', '-s', '192.0.2.4', '-p', '953',
            '-c', '/etc/rndc.conf', '-k', '/etc/rndc.key',
            'delzone', '-clean', 'example.com '
        )


class Bind9BackendFunctionalTestCase(BackendTestCase):

    # Run the real rndc, if available

    def setUp(self):
        super(Bind9BackendFunctionalTestCase, self).setUp()

        self.CONF.set_override('root_helper', '  ')  # disable rootwrap
        self._conf_fn = tempfile.mkstemp(prefix='rndc-', suffix='.conf')[1]
        self._key_fn = tempfile.mkstemp(prefix='rndc-', suffix='.key')[1]
        with open(self._key_fn, 'w') as f:
            f.write("""
key "rndc-key" {
    algorithm hmac-md5;
    secret "iNeLyEHGbOrogTw+nB/KwQ==";
};
""")
        with open(self._conf_fn, 'w') as f:
            f.write("""
key "rndc-key" {
    algorithm hmac-md5;
    secret "iNeLyEHGbOrogTw+nB/KwQ==";
};

options {
    default-key "rndc-key";
    default-server 127.0.0.1;
    default-port 953;
};
""")
        self.zone = objects.Zone(id='cca7908b-dad4-4c50-adba-fb67d4c556e8',
                                 name='example.com.',
                                 email='example@example.com')
        target = objects.PoolTarget.from_dict({
            'id': '4588652b-50e7-46b9-b688-a9bad40a873e',
            'type': 'bind9',
            'masters': [{'host': '127.0.0.1', 'port': 33353}],
            'options': [{'key': 'host', 'value': '127.0.0.1'},
                        {'key': 'port', 'value': 33353},
                        {'key': 'rndc_host', 'value': '127.0.0.1'},
                        {'key': 'rndc_port', 'value': 33953},
                        {'key': 'rndc_bin_path', 'value': RNDC_BIN_PATH},
                        {'key': 'rndc_config_file', 'value': self._conf_fn},
                        {'key': 'rndc_key_file', 'value': self._key_fn},
                        {'key': 'clean_zonefile', 'value': 'true'}],
        })

        self.backend = Bind9Backend(target)

    @unittest.skipIf(RNDC_NOT_AVAILABLE, "rndc binary not installed")
    def test_create_zone_call_rndc_connection_refused(self):
        # Run rndc againts a closed port. Albeit this does not perform a
        # successful rndc run, it is enough to test the argument parsing
        context = self.get_context()
        exp_msg = 'rndc: connect failed: 127.0.0.1#33953: connection refused'
        try:
            self.backend.create_zone(context, self.zone)
            unittest.fail("Did not raise an exception")
        except exceptions.Backend as e:
            self.assertTrue(exp_msg in str(e))
