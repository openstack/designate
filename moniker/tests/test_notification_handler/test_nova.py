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
from nose import SkipTest
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging
from moniker.tests.test_notification_handler import NotificationHandlerTestCase
from moniker.notification_handler import nova

LOG = logging.getLogger(__name__)


class NovaNotificationHandlerTestCase(NotificationHandlerTestCase):
    __test__ = True

    def setUp(self):
        super(NovaNotificationHandlerTestCase, self).setUp()

        self._init_handler()

    def _init_handler(self):
        # Create provider domain
        values = {'name': 'exampe.com', 'email': 'info@example.com'}

        domain = self.central_service.create_domain(self.admin_context, values)
        self.fixed_ip_domain = domain['id']

        # Register handler specific config options
        nova.NovaHandler.register_opts(cfg.CONF)

        # Override default config values
        self.config(nova_fixed_ip_domain=self.fixed_ip_domain)

        # Initialize the handler
        self.handler = nova.NovaHandler(central_service=self.central_service)

    def test_instance_create_end(self):
        event_type = 'compute.instance.create.end'
        fixture = self.get_notification_fixture('nova', event_type)

        self.assertIn(event_type, self.handler.get_event_types())

        # Ensure we start with 0 records
        records = self.central_service.get_records(self.admin_context,
                                                   self.fixed_ip_domain)

        self.assertEqual(0, len(records))

        self.handler.process_notification(event_type, fixture['payload'])

        # Ensure we now have exactly 1 record
        records = self.central_service.get_records(self.admin_context,
                                                   self.fixed_ip_domain)

        self.assertEqual(len(records), 1)

    def test_instance_delete_start(self):
        # Prepare for the test
        start_event_type = 'compute.instance.create.end'
        start_fixture = self.get_notification_fixture('nova', start_event_type)

        self.handler.process_notification(start_event_type,
                                          start_fixture['payload'])

        # Now - Onto the real test
        event_type = 'compute.instance.delete.start'
        fixture = self.get_notification_fixture('nova', event_type)

        self.assertIn(event_type, self.handler.get_event_types())

        # Ensure we start with at least 1 record
        records = self.central_service.get_records(self.admin_context,
                                                   self.fixed_ip_domain)

        self.assertGreaterEqual(len(records), 1)

        self.handler.process_notification(event_type, fixture['payload'])

        # Ensure we now have exactly 0 records
        records = self.central_service.get_records(self.admin_context,
                                                   self.fixed_ip_domain)

        self.assertEqual(0, len(records))

    def test_floating_ip_associate(self):
        raise SkipTest()

        event_type = 'network.floating_ip.associate'
        fixture = self.get_notification_fixture('nova', event_type)

        self.assertIn(event_type, self.handler.get_event_types())

        self.handler.process_notification(event_type, fixture['payload'])

    def test_floating_ip_disassociate(self):
        raise SkipTest()

        event_type = 'network.floating_ip.disassociate'
        fixture = self.get_notification_fixture('nova', event_type)

        self.assertIn(event_type, self.handler.get_event_types())

        self.handler.process_notification(event_type, fixture['payload'])
