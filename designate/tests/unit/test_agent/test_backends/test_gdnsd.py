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
    Unit-test the Gdnsd 2 agent backend

    These tests do not rely on creating directories and files or running
    executables from the gdnsd suite
"""

import dns.zone
import fixtures
import mock

from designate.backend.agent_backend.impl_gdnsd import GdnsdBackend
from designate.tests import TestCase
import designate.backend.agent_backend.impl_gdnsd  # noqa


class GdnsdAgentBackendUnitTestCase(TestCase):

    def setUp(self):
        super(GdnsdAgentBackendUnitTestCase, self).setUp()
        self.useFixture(fixtures.MockPatchObject(
            GdnsdBackend, '_check_dirs'
        ))
        self.backend = GdnsdBackend('foo')
        self.useFixture(fixtures.MockPatchObject(self.backend._resolver,
                                                 'query'))

    def tearDown(self):
        super(GdnsdAgentBackendUnitTestCase, self).tearDown()

    def _create_dnspy_zone(self, name):
        zone_text = (
            '$ORIGIN %(name)s\n%(name)s 3600 IN SOA %(ns)s '
            'email.email.com. 1421777854 3600 600 86400 3600\n%(name)s '
            '3600 IN NS %(ns)s\n') % {'name': name, 'ns': 'ns1.designate.com'}

        return dns.zone.from_text(zone_text, check_origin=False)

    def test_init(self):
        self.assertEqual(1, self.backend._resolver.timeout)
        self.assertEqual(1, self.backend._resolver.lifetime)
        self.assertEqual(['127.0.0.1'], self.backend._resolver.nameservers)
        self.assertEqual('/etc/gdnsd/zones',
                         self.backend._zonedir_path)
        self.assertEqual('gdnsd', self.backend._gdnsd_cmd_name)

    def test__generate_zone_filename(self):
        fn = self.backend._generate_zone_filename("A/bc-d_e.f")
        self.assertEqual("a@bc-d_e.f", fn)

    def test_find_zone_serial(self):
        class Data(object):
            serial = 3

        self.backend._resolver.query.return_value = [Data(), ]
        serial = self.backend.find_zone_serial('example.com')
        self.assertEqual(3, serial)

    def test_find_zone_serial_error(self):
        self.backend._resolver.query.side_effect = RuntimeError('foo')

        serial = self.backend.find_zone_serial('example.com')
        self.assertIsNone(serial)

    @mock.patch('designate.backend.agent_backend.impl_gdnsd.os.remove')
    def test_delete_zone(self, mock_osremove):
        self.backend.delete_zone('foo-bar.example.org.')
        mock_osremove.assert_called_once_with(
            "/etc/gdnsd/zones/foo-bar.example.org")
