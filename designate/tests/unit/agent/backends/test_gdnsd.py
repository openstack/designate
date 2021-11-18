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

from designate.backend.agent_backend import impl_gdnsd
import designate.tests


class GdnsdAgentBackendTestCase(designate.tests.TestCase):
    @mock.patch.object(impl_gdnsd.GdnsdBackend, '_check_dirs')
    def setUp(self, mock_check_dirs):
        super(GdnsdAgentBackendTestCase, self).setUp()

        self.backend = impl_gdnsd.GdnsdBackend('foo')

    @mock.patch.object(impl_gdnsd.GdnsdBackend, '_check_conf')
    def test_start_backend(self, mock_check_conf):
        self.backend.start()
        self.assertTrue(mock_check_conf.called)

    def test_stop_backend(self):
        self.backend.stop()

    def test_init(self):
        self.assertEqual(1, self.backend._resolver.timeout)
        self.assertEqual(1, self.backend._resolver.lifetime)
        self.assertEqual(['127.0.0.1'], self.backend._resolver.nameservers)
        self.assertEqual(
            '/etc/gdnsd/zones',
            self.backend._zonedir_path
        )
        self.assertEqual('gdnsd', self.backend._gdnsd_cmd_name)

    def test_generate_zone_filename(self):
        zone_filename = self.backend._generate_zone_filename('A/bc-d_e.f')
        self.assertEqual('a@bc-d_e.f', zone_filename)

    def test_find_zone_serial(self):
        class Data(object):
            serial = 3

        self.backend._resolver = mock.Mock()
        self.backend._resolver.query.return_value = [Data(), ]
        serial = self.backend.find_zone_serial('example.com')
        self.assertEqual(3, serial)

    def test_find_zone_serial_error(self):
        self.backend._resolver = mock.Mock()
        self.backend._resolver.query.side_effect = RuntimeError('foo')

        serial = self.backend.find_zone_serial('example.com')
        self.assertIsNone(serial)

    @mock.patch('designate.backend.agent_backend.impl_gdnsd.os.remove')
    def test_delete_zone(self, mock_osremove):
        self.backend.delete_zone('foo-bar.example.org.')

        mock_osremove.assert_called_once_with(
            '/etc/gdnsd/zones/foo-bar.example.org'
        )
