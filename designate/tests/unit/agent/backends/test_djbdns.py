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

from designate.backend.agent_backend import impl_djbdns
from designate import exceptions
import designate.tests
from designate.tests.unit.agent import backends


class DjbdnsAgentBackendTestCase(designate.tests.TestCase):
    @mock.patch.object(impl_djbdns.DjbdnsBackend, '_check_dirs')
    def setUp(self, mock_check_dirs):
        super(DjbdnsAgentBackendTestCase, self).setUp()

        self.CONF.set_override('masters', ['127.0.0.1:5354'], 'service:agent')

        self.backend = impl_djbdns.DjbdnsBackend('foo')

    def test_start_backend(self):
        self.backend.start()

    def test_stop_backend(self):
        self.backend.stop()

    def test_init(self):
        self.assertTrue(hasattr(self.backend, '_resolver'))
        self.assertEqual(1, self.backend._resolver.timeout)
        self.assertEqual(1, self.backend._resolver.lifetime)
        self.assertEqual(['127.0.0.1'], self.backend._resolver.nameservers)
        self.assertEqual(
            '/var/lib/djbdns/root/data.cdb',
            self.backend._tinydns_cdb_filename
        )
        self.assertEqual(
            '/var/lib/djbdns/datafiles',
            self.backend._datafiles_dir

        )
        self.assertEqual(
            '/var/lib/djbdns/datafiles/%s.zonedata',
            self.backend._datafiles_path_tpl
        )
        self.assertEqual([('127.0.0.1', 5354)], self.backend._masters)

    @mock.patch.object(impl_djbdns.DjbdnsBackend, '_check_dirs')
    def test_init_no_masters(self, mock_check_dirs):
        self.CONF.set_override('masters', [], 'service:agent')

        self.assertRaisesRegex(
            exceptions.Backend,
            'Missing agent AXFR masters',
            impl_djbdns.DjbdnsBackend, 'foo'
        )

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

    @mock.patch('designate.backend.agent_backend.impl_djbdns.execute')
    def test_create_zone(self, mock_execute):
        self.backend._perform_axfr_from_minidns = mock.Mock()
        self.backend._rebuild_data_cdb = mock.Mock()
        zone = backends.create_dnspy_zone('example.org')
        self.backend.create_zone(zone)

    def test_update_zone(self):
        self.backend._perform_axfr_from_minidns = mock.Mock()
        self.backend._rebuild_data_cdb = mock.Mock()
        zone = backends.create_dnspy_zone('example.org')
        self.backend.update_zone(zone)

    @mock.patch('designate.backend.agent_backend.impl_djbdns.os.remove')
    def test_delete_zone(self, mock_rm):
        self.backend._rebuild_data_cdb = mock.Mock()

        self.backend.delete_zone('foo')

        mock_rm.assert_called_once_with(
            '/var/lib/djbdns/datafiles/foo.zonedata'
        )

    @mock.patch('designate.backend.agent_backend.impl_djbdns.os.remove')
    def test_exception_filter(self, mock_os_remove):
        self.backend._rebuild_data_cdb = mock.Mock()

        self.assertRaises(
            exceptions.Backend,
            self.backend.delete_zone, None
        )

    @mock.patch('designate.backend.agent_backend.impl_djbdns.os.remove')
    def test_exception_filter_pass_through(self, mock_os_remove):
        self.backend._rebuild_data_cdb = mock.Mock()

        mock_os_remove.side_effect = exceptions.Backend
        self.assertRaises(
            exceptions.Backend,
            self.backend.delete_zone, 'foo'
        )
