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
import json
import os
from moniker.notification_handler.base import Handler
from moniker.tests.test_plugins import PluginTestCase

FIXTURES_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             '..',
                                             'sample_notifications'))


class NotificationHandlerTestCase(PluginTestCase):
    __test__ = False
    __plugin_base__ = Handler

    def get_notification_fixture(self, service, name):
        filename = os.path.join(FIXTURES_PATH, service, '%s.json' % name)

        if not os.path.exists(filename):
            raise Exception('Invalid notification fixture requested')

        with open(filename, 'r') as fh:
            return json.load(fh)

    def test_invalid_event_type(self):
        event_type = 'invalid'

        self.assertNotIn(event_type, self.plugin.get_event_types())

        with self.assertRaises(ValueError):
            self.plugin.process_notification(event_type, 'payload')

    def pre_invoke(self):
        self.central_service = self.get_central_service()
        self.invoke_args = [self.central_service]


class AddressHandlerTestCase(NotificationHandlerTestCase):
    """
    Test something that receives notifications with regards to addresses
    """
    def pre_invoke(self):
        super(AddressHandlerTestCase, self).pre_invoke()
        values = {'name': 'exampe.com', 'email': 'info@example.com'}
        domain = self.central_service.create_domain(self.admin_context, values)
        self.domain_id = str(domain['id'])

        return {'domain_id': self.domain_id}
