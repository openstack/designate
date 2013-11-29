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
from designate.openstack.common import log as logging
from designate.tests import TestCase
from designate.notification_handler.neutron import NeutronFloatingHandler
from designate.tests.test_notification_handler import \
    NotificationHandlerMixin

LOG = logging.getLogger(__name__)


class NeutronFloatingHandlerTest(TestCase, NotificationHandlerMixin):
    def setUp(self):
        super(NeutronFloatingHandlerTest, self).setUp()

        self.central_service = self.start_service('central')

        domain = self.create_domain()
        self.domain_id = domain['id']
        self.config(domain_id=domain['id'], group='handler:neutron_floatingip')

        self.plugin = NeutronFloatingHandler()

    def test_floatingip_associate(self):
        event_type = 'floatingip.update.end'
        fixture = self.get_notification_fixture(
            'neutron', event_type + '_associate')

        self.assertIn(event_type, self.plugin.get_event_types())

        # Ensure we start with 0 records
        records = self.central_service.find_records(self.admin_context,
                                                    self.domain_id)

        self.assertEqual(0, len(records))

        self.plugin.process_notification(event_type, fixture['payload'])

        # Ensure we now have exactly 1 record
        records = self.central_service.find_records(self.admin_context,
                                                    self.domain_id)

        self.assertEqual(len(records), 1)

    def test_floatingip_disassociate(self):
        start_event_type = 'floatingip.update.end'
        start_fixture = self.get_notification_fixture(
            'neutron', start_event_type + '_associate')
        self.plugin.process_notification(start_event_type,
                                         start_fixture['payload'])

        event_type = 'floatingip.update.end'
        fixture = self.get_notification_fixture(
            'neutron', event_type + '_disassociate')

        self.assertIn(event_type, self.plugin.get_event_types())

        # Ensure we start with at least 1 record
        records = self.central_service.find_records(self.admin_context,
                                                    self.domain_id)

        self.assertTrue(len(records) >= 1)

        self.plugin.process_notification(event_type, fixture['payload'])

        records = self.central_service.find_records(self.admin_context,
                                                    self.domain_id)

        self.assertEqual(0, len(records))
