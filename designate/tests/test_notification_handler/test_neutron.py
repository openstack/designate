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
from oslo_log import log as logging

from designate.tests import TestCase
from designate.notification_handler.neutron import NeutronFloatingHandler
from designate.tests.test_notification_handler import \
    NotificationHandlerMixin

LOG = logging.getLogger(__name__)


class NeutronFloatingHandlerTest(TestCase, NotificationHandlerMixin):
    def setUp(self):
        super(NeutronFloatingHandlerTest, self).setUp()

        zone = self.create_zone()
        self.zone_id = zone['id']
        self.config(zone_id=zone['id'], group='handler:neutron_floatingip')
        formats = ['%(octet0)s-%(octet1)s-%(octet2)s-%(octet3)s.%(zone)s',
                   '%(octet0)s-%(octet1)s-%(octet2)s-%(octet3)s.X.%(zone)s']
        self.config(formatv4=formats, group='handler:neutron_floatingip')

        self.plugin = NeutronFloatingHandler()

    def test_floatingip_associate(self):
        event_type = 'floatingip.update.end'
        fixture = self.get_notification_fixture(
            'neutron', event_type + '_associate')

        self.assertIn(event_type, self.plugin.get_event_types())

        criterion = {'zone_id': self.zone_id}

        # Ensure we start with only SOA and NS records
        records = self.central_service.find_records(self.admin_context,
                                                    criterion)

        self.assertEqual(2, len(records))

        self.plugin.process_notification(
            self.admin_context.to_dict(), event_type, fixture['payload'])

        # Ensure we now have exactly 1 record, plus SOA & NS
        records = self.central_service.find_records(self.admin_context,
                                                    criterion)

        self.assertEqual(4, len(records))

    def test_floatingip_disassociate(self):
        start_event_type = 'floatingip.update.end'
        start_fixture = self.get_notification_fixture(
            'neutron', start_event_type + '_associate')
        self.plugin.process_notification(self.admin_context.to_dict(),
                                         start_event_type,
                                         start_fixture['payload'])

        event_type = 'floatingip.update.end'
        fixture = self.get_notification_fixture(
            'neutron', event_type + '_disassociate')

        self.assertIn(event_type, self.plugin.get_event_types())

        criterion = {'zone_id': self.zone_id}

        # Ensure we start with at least 1 record, plus NS and SOA
        records = self.central_service.find_records(self.admin_context,
                                                    criterion)

        self.assertEqual(4, len(records))

        self.plugin.process_notification(
            self.admin_context.to_dict(), event_type, fixture['payload'])

        # Simulate the record having been deleted on the backend
        zone_serial = self.central_service.get_zone(
            self.admin_context, self.zone_id).serial
        self.central_service.update_status(
            self.admin_context, self.zone_id, "SUCCESS", zone_serial)

        # Ensure we now have exactly 0 records, plus NS and SOA
        records = self.central_service.find_records(self.admin_context,
                                                    criterion)

        self.assertEqual(2, len(records))

    def test_floatingip_delete(self):
        start_event_type = 'floatingip.update.end'
        start_fixture = self.get_notification_fixture(
            'neutron', start_event_type + '_associate')
        self.plugin.process_notification(self.admin_context.to_dict(),
                                         start_event_type,
                                         start_fixture['payload'])

        event_type = 'floatingip.delete.start'
        fixture = self.get_notification_fixture(
            'neutron', event_type)

        self.assertIn(event_type, self.plugin.get_event_types())

        criterion = {'zone_id': self.zone_id}

        # Ensure we start with at least 1 record, plus NS and SOA
        records = self.central_service.find_records(self.admin_context,
                                                    criterion)
        self.assertEqual(4, len(records))

        self.plugin.process_notification(
            self.admin_context.to_dict(), event_type, fixture['payload'])

        # Simulate the record having been deleted on the backend
        zone_serial = self.central_service.get_zone(
            self.admin_context, self.zone_id).serial
        self.central_service.update_status(
            self.admin_context, self.zone_id, "SUCCESS", zone_serial)

        # Ensure we now have exactly 0 records, plus NS and SOA
        records = self.central_service.find_records(self.admin_context,
                                                    criterion)

        self.assertEqual(2, len(records))
