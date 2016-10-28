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
    Unit-test the Djbdns agent backend

    These tests do not rely on creating directories and files or running
    executables from the djbdns suite
"""

import dns.zone
import fixtures
import mock

from designate import exceptions
from designate.backend.agent_backend.impl_djbdns import DjbdnsBackend
from designate.tests import TestCase
import designate.backend.agent_backend.impl_djbdns  # noqa


class DjbdnsAgentBackendUnitTestCase(TestCase):

    def setUp(self):
        super(DjbdnsAgentBackendUnitTestCase, self).setUp()
        self.CONF.set_override('masters', ['127.0.0.1:5354'], 'service:agent')
        self.useFixture(fixtures.MockPatchObject(
            DjbdnsBackend, '_check_dirs'
        ))
        self.backend = DjbdnsBackend('foo')
        self.patch_ob(self.backend._resolver, 'query')

    def tearDown(self):
        super(DjbdnsAgentBackendUnitTestCase, self).tearDown()

    def _create_dnspy_zone(self, name):
        zone_text = (
            '$ORIGIN %(name)s\n%(name)s 3600 IN SOA %(ns)s '
            'email.email.com. 1421777854 3600 600 86400 3600\n%(name)s '
            '3600 IN NS %(ns)s\n') % {'name': name, 'ns': 'ns1.designate.com'}

        return dns.zone.from_text(zone_text, check_origin=False)

    def patch_ob(self, *a, **kw):
        self.useFixture(fixtures.MockPatchObject(*a, **kw))

    def test_init(self):
        self.assertTrue(hasattr(self.backend, '_resolver'))
        self.assertEqual(1, self.backend._resolver.timeout)
        self.assertEqual(1, self.backend._resolver.lifetime)
        self.assertEqual(['127.0.0.1'], self.backend._resolver.nameservers)
        self.assertEqual('/var/lib/djbdns/root/data.cdb',
                         self.backend._tinydns_cdb_filename)
        self.assertEqual('/var/lib/djbdns/datafiles',
                         self.backend._datafiles_dir)
        self.assertEqual('/var/lib/djbdns/datafiles/%s.zonedata',
                         self.backend._datafiles_path_tpl)
        self.assertEqual([('127.0.0.1', 5354)], self.backend._masters)

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

    @mock.patch('designate.backend.agent_backend.impl_djbdns.execute')
    def test_create_zone(self, mock_exe):
        self.patch_ob(self.backend, '_perform_axfr_from_minidns')
        self.patch_ob(self.backend, '_rebuild_data_cdb')
        zone = self._create_dnspy_zone('example.org')
        self.backend.create_zone(zone)

    def test_update_zone(self):
        self.patch_ob(self.backend, '_perform_axfr_from_minidns')
        self.patch_ob(self.backend, '_rebuild_data_cdb')
        zone = self._create_dnspy_zone('example.org')
        self.backend.update_zone(zone)

    @mock.patch('designate.backend.agent_backend.impl_djbdns.os.remove')
    def test_delete_zone(self, mock_rm):
        self.patch_ob(self.backend, '_rebuild_data_cdb')

        self.backend.delete_zone('foo')

        mock_rm.assert_called_once_with(
            '/var/lib/djbdns/datafiles/foo.zonedata'
        )

    @mock.patch('designate.backend.agent_backend.impl_djbdns.os.remove')
    def test_exception_filter(self, *mocks):
        self.patch_ob(self.backend, '_rebuild_data_cdb')
        self.assertRaises(
            exceptions.Backend,
            self.backend.delete_zone,
            None
        )

    @mock.patch('designate.backend.agent_backend.impl_djbdns.os.remove')
    def test_exception_filter_pass_through(self, mock_rm):
        self.patch_ob(self.backend, '_rebuild_data_cdb')
        mock_rm.side_effect = exceptions.Backend
        self.assertRaises(
            exceptions.Backend,
            self.backend.delete_zone,
            'foo'
        )
