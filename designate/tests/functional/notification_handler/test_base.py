# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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


from designate.notification_handler import base
import designate.tests.functional


class InheritFormBaseAddressHandler(base.BaseAddressHandler):
    """Class to inherit from BaseAddressHandler to test its methods

    Because BaseAddressHandler is an abstract class, in order to test methods
    we need to create something to inherit from it so we have something
    instantiatable.
    """
    __plugin_name__ = 'nova_fixed'

    def get_event_types(self):
        pass

    def get_exchange_topics(self):
        pass

    def process_notification(self):
        pass


class BaseAddressHandlerTest(designate.tests.functional.TestCase):
    def setUp(self):
        super().setUp()

        self.zone = self.create_zone()
        self.zone_id = self.zone['id']
        self.base = InheritFormBaseAddressHandler()

    def test_get_ip_data_support_v6(self):
        # Test IPv6 with compressed notation (::)
        addr_dict = {'address': '1762::B03:1:AF18', 'version': 6}
        observe = self.base._get_ip_data(addr_dict)
        # The address expands to: 1762:0000:0000:0000:0000:0b03:0001:af18
        expect = {
            'octet0': '1762',
            'octet1': '0000',
            'octet2': '0000',
            'octet3': '0000',
            'octet4': '0000',
            'octet5': '0b03',
            'octet6': '0001',
            'octet7': 'af18',
            'ip_version': 6,
            'ip_address': '1762--B03-1-AF18'
        }
        self.assertEqual(observe, expect)

    def test_get_ip_data_support_v6_full_address(self):
        # Test fully specified IPv6 address
        addr_dict = {
            'address': '2001:0db8:0000:0000:0000:ff00:0042:8329',
            'version': 6
        }
        observe = self.base._get_ip_data(addr_dict)
        expect = {
            'octet0': '2001',
            'octet1': '0db8',
            'octet2': '0000',
            'octet3': '0000',
            'octet4': '0000',
            'octet5': 'ff00',
            'octet6': '0042',
            'octet7': '8329',
            'ip_version': 6,
            'ip_address': '2001-0db8-0000-0000-0000-ff00-0042-8329'
        }
        self.assertEqual(observe, expect)

    def test_get_ip_data_support_v6_compressed(self):
        # Test common compressed IPv6 address (2001:db8::1)
        addr_dict = {'address': '2001:db8::1', 'version': 6}
        observe = self.base._get_ip_data(addr_dict)
        # Expands to: 2001:0db8:0000:0000:0000:0000:0000:0001
        expect = {
            'octet0': '2001',
            'octet1': '0db8',
            'octet2': '0000',
            'octet3': '0000',
            'octet4': '0000',
            'octet5': '0000',
            'octet6': '0000',
            'octet7': '0001',
            'ip_version': 6,
            'ip_address': '2001-db8--1'
        }
        self.assertEqual(observe, expect)

    def test_create_record(self):
        self.base._create([
            {'address': '172.16.0.15', 'version': 4}],
            {'hostname': 'test01'},
            self.zone_id,
            resource_id='1fb1feba-2ea4-4925-ba2c-9a3706348a70',
            resource_type='instance'
        )

        criterion = {
            'zone_id': self.zone_id,
            'type': 'A',
        }

        recordsets = self.central_service.find_recordsets(
            self.admin_context, criterion)

        self.assertEqual('test01.example.com.', recordsets[0].name)
        self.assertEqual('A', recordsets[0].type)

    def test_create_record_skips_invalid_ip_address(self):
        self.base._create([
            {'address': 'not-an-ip-address', 'version': 6},
            {'address': '172.16.0.15', 'version': 4}],
            {'hostname': 'test01'},
            self.zone_id,
            resource_id='1fb1feba-2ea4-4925-ba2c-9a3706348a70',
            resource_type='instance'
        )

        recordsets = self.central_service.find_recordsets(
            self.admin_context, {'zone_id': self.zone_id, 'type': 'AAAA'})
        self.assertEqual(0, len(recordsets))

        recordsets = self.central_service.find_recordsets(
            self.admin_context, {'zone_id': self.zone_id, 'type': 'A'})
        self.assertEqual('test01.example.com.', recordsets[0].name)

    def test_delete_record(self):
        self.base._create([
            {'address': '172.16.0.15', 'version': 4}],
            {'hostname': 'test01'},
            self.zone_id,
            resource_id='6d6deb76-e4e7-492e-8f9d-4d906653c511',
            resource_type='instance'
        )

        criterion = {
            'zone_id': self.zone_id,
            'type': 'A',
        }

        recordsets = self.central_service.find_recordsets(
            self.admin_context, criterion)

        self.assertEqual('test01.example.com.', recordsets[0].name)
        self.assertEqual('A', recordsets[0].type)

        self.base._delete(self.zone_id, '6d6deb76-e4e7-492e-8f9d-4d906653c511')

        recordsets = self.central_service.find_recordsets(
            self.admin_context, criterion)
        self.assertEqual(0, len(recordsets))

    def test_delete_record_with_no_zone_id(self):
        self.base._create([
            {'address': '172.16.0.15', 'version': 4}],
            {'hostname': 'test01'},
            self.zone_id,
            resource_id='6d6deb76-e4e7-492e-8f9d-4d906653c511',
            resource_type='instance'
        )

        criterion = {
            'zone_id': self.zone_id,
            'type': 'A',
        }
        recordsets = self.central_service.find_recordsets(
            self.admin_context, criterion)

        self.assertEqual('test01.example.com.', recordsets[0].name)
        self.assertEqual('A', recordsets[0].type)

        self.base._delete(
            zone_id=None,
            resource_id='6d6deb76-e4e7-492e-8f9d-4d906653c511',
            resource_type='instance'
        )

        recordsets = self.central_service.find_recordsets(
            self.admin_context, criterion)
        self.assertEqual(0, len(recordsets))
