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
from designate.tests import TestCase
from designate.notification_handler import base


class InheritFormBaseAddressHandler(base.BaseAddressHandler):
    """Class to inherit from BaseAddressHandler to test its methods

    Because BaseAddressHandler is an abstract class, in order to test methods
    we need to create something to inherit from it so we have something
    instantiatable.
    """
    def get_event_types(self):
        pass

    def get_exchange_topics(self):
        pass

    def process_notification(self):
        pass


class BaseAddressHandlerTest(TestCase):
    def test_get_ip_data_support_v6(self):
        addr_dict = {'address': '1762::B03:1:AF18', 'version': 6}
        baseaddresshandler = InheritFormBaseAddressHandler()
        observe = baseaddresshandler._get_ip_data(addr_dict)
        expect = {'octet1': 'B03', 'octet0': '1762', 'octet3': 'AF18',
                  'octet2': '1', 'ip_version': 6,
                  'ip_address': '1762--B03-1-AF18'}
        self.assertEqual(observe, expect)
