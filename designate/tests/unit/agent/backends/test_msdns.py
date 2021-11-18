# Copyright 2016 Cloudbase Solutions Srl
# All Rights Reserved.
#
#    Author: Alin Balutoiu <abalutoiu@cloudbasesolutions.com>
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from unittest import mock

from os_win import constants
from os_win import exceptions as os_win_exc
from os_win import utilsfactory

from designate.backend.agent_backend import impl_msdns
from designate import exceptions
import designate.tests
from designate.tests.unit.agent import backends


class MSDNSAgentBackendTestCase(designate.tests.TestCase):
    @mock.patch.object(utilsfactory, 'get_dnsutils')
    def setUp(self, mock_get_dnsutils):
        super(MSDNSAgentBackendTestCase, self).setUp()
        self.zone_name = 'example.com'

        self.CONF.set_override('masters', ['127.0.0.1:5354'], 'service:agent')

        self.backend = impl_msdns.MSDNSBackend('foo')
        self.backend._dnsutils = mock.MagicMock()

    def test_start_backend(self):
        self.backend.start()

    def test_stop_backend(self):
        self.backend.stop()

    def test_init(self):
        self.assertEqual(['127.0.0.1'], self.backend._masters)

    @mock.patch.object(utilsfactory, 'get_dnsutils')
    def test_init_no_masters(self, mock_get_dnsutils):
        self.CONF.set_override('masters', [], 'service:agent')

        self.assertRaisesRegex(
            exceptions.Backend,
            'Missing agent AXFR masters',
            impl_msdns.MSDNSBackend, 'foo'
        )

    def test_find_zone_serial(self):
        serial = self.backend.find_zone_serial(self.zone_name)

        expected_serial = self.backend._dnsutils.get_zone_serial.return_value
        self.assertEqual(expected_serial, serial)

        self.backend._dnsutils.get_zone_serial.assert_called_once_with(
            self.zone_name
        )

    def test_find_zone_serial_error(self):
        self.backend._dnsutils.get_zone_serial.side_effect = (
            os_win_exc.DNSZoneNotFound(zone_name=self.zone_name))

        serial = self.backend.find_zone_serial(self.zone_name)

        self.assertIsNone(serial)
        self.backend._dnsutils.get_zone_serial.assert_called_once_with(
            self.zone_name
        )

    def test_create_zone(self):
        zone = backends.create_dnspy_zone(self.zone_name)

        self.backend.create_zone(zone)

        self.backend._dnsutils.zone_create.assert_called_once_with(
            zone_name=self.zone_name,
            zone_type=constants.DNS_ZONE_TYPE_SECONDARY,
            ds_integrated=False,
            ip_addrs=self.backend._masters
        )

    def test_create_zone_already_existing_diff(self):
        zone = backends.create_dnspy_zone(self.zone_name)
        self.backend._dnsutils.zone_create.side_effect = (
            os_win_exc.DNSZoneAlreadyExists(zone_name=self.zone_name))

        self.assertRaises(
            os_win_exc.DNSZoneAlreadyExists,
            self.backend.create_zone, zone
        )

        self.backend._dnsutils.get_zone_properties.assert_called_once_with(
            self.zone_name
        )

    def test_create_zone_already_existing_identical(self):
        zone = backends.create_dnspy_zone(self.zone_name)
        self.backend._dnsutils.zone_create.side_effect = (
            os_win_exc.DNSZoneAlreadyExists(zone_name=self.zone_name)
        )

        mock_zone_properties = {
            'zone_type': constants.DNS_ZONE_TYPE_SECONDARY,
            'ds_integrated': False,
            'master_servers': self.backend._masters
        }
        self.backend._dnsutils.get_zone_properties.return_value = (
            mock_zone_properties
        )

        self.backend.create_zone(zone)

        self.backend._dnsutils.get_zone_properties.assert_called_once_with(
            self.zone_name
        )

    def test_update_zone(self):
        zone = backends.create_dnspy_zone(self.zone_name)

        self.backend.update_zone(zone)

        self.backend._dnsutils.zone_update.assert_called_once_with(
            self.zone_name
        )

    def test_delete_zone(self):
        self.backend.delete_zone(self.zone_name)

        self.backend._dnsutils.zone_delete.assert_called_once_with(
            self.zone_name
        )
