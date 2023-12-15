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
        addr_dict = {'address': '1762::B03:1:AF18', 'version': 6}
        observe = self.base._get_ip_data(addr_dict)
        expect = {'octet1': 'B03', 'octet0': '1762', 'octet3': 'AF18',
                  'octet2': '1', 'ip_version': 6,
                  'ip_address': '1762--B03-1-AF18'}
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
