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

"""
    Unit-test the MSDNS agent backend
"""

import dns
import mock
from os_win import constants
from os_win import exceptions as os_win_exc

from designate.backend.agent_backend import impl_msdns
from designate.tests import TestCase


class MSDNSAgentBackendUnitTestCase(TestCase):

    _FAKE_ZONE_NAME = 'example.com'

    def setUp(self):
        super(MSDNSAgentBackendUnitTestCase, self).setUp()
        self.CONF.set_override('masters', ['127.0.0.1:5354'], 'service:agent')

        patcher = mock.patch('os_win.utilsfactory.get_dnsutils')
        self._dnsutils = patcher.start().return_value
        self.addCleanup(patcher.stop)
        self.backend = impl_msdns.MSDNSBackend('foo')

    def _create_dnspy_zone(self, name):
        zone_text = (
            '$ORIGIN %(name)s\n%(name)s 3600 IN SOA %(ns)s '
            'email.email.com. 1421777854 3600 600 86400 3600\n%(name)s '
            '3600 IN NS %(ns)s\n') % {'name': name, 'ns': 'ns1.designate.com'}

        return dns.zone.from_text(zone_text, check_origin=False)

    def test_init(self):
        self.assertEqual(['127.0.0.1'], self.backend._masters)
        self.assertEqual(self._dnsutils, self.backend._dnsutils)

    def test_find_zone_serial(self):
        serial = self.backend.find_zone_serial(self._FAKE_ZONE_NAME)

        expected_serial = self._dnsutils.get_zone_serial.return_value
        self.assertEqual(expected_serial, serial)
        self._dnsutils.get_zone_serial.assert_called_once_with(
            self._FAKE_ZONE_NAME)

    def test_find_zone_serial_error(self):
        self._dnsutils.get_zone_serial.side_effect = (
            os_win_exc.DNSZoneNotFound(zone_name=self._FAKE_ZONE_NAME))

        serial = self.backend.find_zone_serial(self._FAKE_ZONE_NAME)

        self.assertIsNone(serial)
        self._dnsutils.get_zone_serial.assert_called_once_with(
            self._FAKE_ZONE_NAME)

    def test_create_zone(self):
        zone = self._create_dnspy_zone(self._FAKE_ZONE_NAME)

        self.backend.create_zone(zone)

        self._dnsutils.zone_create.assert_called_once_with(
            zone_name=self._FAKE_ZONE_NAME,
            zone_type=constants.DNS_ZONE_TYPE_SECONDARY,
            ds_integrated=False,
            ip_addrs=self.backend._masters)

    def test_create_zone_already_existing_diff(self):
        zone = self._create_dnspy_zone(self._FAKE_ZONE_NAME)
        self._dnsutils.zone_create.side_effect = (
            os_win_exc.DNSZoneAlreadyExists(zone_name=self._FAKE_ZONE_NAME))

        self.assertRaises(os_win_exc.DNSZoneAlreadyExists,
                          self.backend.create_zone,
                          zone)
        self._dnsutils.get_zone_properties.assert_called_once_with(
            self._FAKE_ZONE_NAME)

    def test_create_zone_already_existing_identical(self):
        zone = self._create_dnspy_zone(self._FAKE_ZONE_NAME)
        self._dnsutils.zone_create.side_effect = (
            os_win_exc.DNSZoneAlreadyExists(zone_name=self._FAKE_ZONE_NAME))
        mock_zone_properties = {'zone_type': constants.DNS_ZONE_TYPE_SECONDARY,
                                'ds_integrated': False,
                                'master_servers': self.backend._masters}
        self._dnsutils.get_zone_properties.return_value = mock_zone_properties

        self.backend.create_zone(zone)

        self._dnsutils.get_zone_properties.assert_called_once_with(
            self._FAKE_ZONE_NAME)

    def test_update_zone(self):
        zone = self._create_dnspy_zone(self._FAKE_ZONE_NAME)

        self.backend.update_zone(zone)

        self._dnsutils.zone_update.assert_called_once_with(
            self._FAKE_ZONE_NAME)

    def test_delete_zone(self):
        self.backend.delete_zone(self._FAKE_ZONE_NAME)

        self._dnsutils.zone_delete.assert_called_once_with(
            self._FAKE_ZONE_NAME)
