# -*- coding: utf-8 -*-
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
from unittest import mock

from oslo_log import log as logging

from designate.notification_handler.nova import NovaFixedHandler
from designate.tests.test_notification_handler import \
    NotificationHandlerMixin
from designate.tests import TestCase

LOG = logging.getLogger(__name__)


class NovaFixedHandlerTest(TestCase, NotificationHandlerMixin):
    def setUp(self):
        super(NovaFixedHandlerTest, self).setUp()

        zone = self.create_zone()
        self.zone_id = zone['id']
        self.config(zone_id=zone['id'], group='handler:nova_fixed')
        self.config(formatv4=['%(host)s.%(zone)s',
                              '%(host)s.foo.%(zone)s'],
                    formatv6=['%(host)s.%(zone)s',
                              '%(host)s.foo.%(zone)s'],
                    group='handler:nova_fixed')

        self.plugin = NovaFixedHandler()

    def test_instance_create_end(self):
        event_type = 'compute.instance.create.end'
        fixture = self.get_notification_fixture('nova', event_type)

        self.assertIn(event_type, self.plugin.get_event_types())

        criterion = {
            'zone_id': self.zone_id,
            'managed': True,
            'managed_resource_type': 'instance',
        }

        records = self.central_service.find_records(self.admin_context,
                                                    criterion)
        # Ensure we start with zero managed records
        self.assertFalse(records)

        self.plugin.process_notification(
            self.admin_context.to_dict(), event_type, fixture['payload'])

        # Ensure we now have exactly 2 records.
        records = self.central_service.find_records(self.admin_context,
                                                    criterion)

        self.assertEqual(2, len(records))

    def test_instance_create_end_utf8(self):
        self.config(formatv4=['%(display_name)s.%(zone)s'],
                    formatv6=['%(display_name)s.%(zone)s'],
                    group='handler:nova_fixed')

        event_type = 'compute.instance.create.end'
        fixture = self.get_notification_fixture('nova', event_type)

        # Set the instance display_name to a string containing UTF8.
        fixture['payload']['display_name'] = 'Test↟Instance'

        self.assertIn(event_type, self.plugin.get_event_types())

        criterion = {
            'zone_id': self.zone_id,
        }

        recordsets = self.central_service.find_recordsets(
            self.admin_context, criterion)

        # Ensure that we only have SOA and NS recordsets.
        self.assertEqual(2, len(recordsets))

        self.plugin.process_notification(
            self.admin_context.to_dict(), event_type, fixture['payload'])

        # Ensure we now have exactly 1 more recordset
        recordsets = self.central_service.find_recordsets(
            self.admin_context, criterion)

        self.assertEqual(3, len(recordsets))

        # Ensure the created record was correctly converted per IDN rules.
        criterion['type'] = 'A'
        recordsets = self.central_service.find_recordsets(
            self.admin_context, criterion)

        self.assertEqual('xn--testinstance-q83g.example.com.',
                         recordsets[0].name)

    def test_instance_delete_start(self):
        # Prepare for the test
        start_event_type = 'compute.instance.create.end'
        start_fixture = self.get_notification_fixture('nova', start_event_type)

        self.plugin.process_notification(self.admin_context.to_dict(),
                                         start_event_type,
                                         start_fixture['payload'])

        # Now - Onto the real test
        event_type = 'compute.instance.delete.start'
        fixture = self.get_notification_fixture('nova', event_type)

        self.assertIn(event_type, self.plugin.get_event_types())

        criterion = {
            'zone_id': self.zone_id,
            'managed': True,
            'managed_resource_type': 'instance',
        }

        # Ensure we start with exactly 2 records.
        records = self.central_service.find_records(self.admin_context,
                                                    criterion)

        self.assertEqual(2, len(records))

        self.plugin.process_notification(
            self.admin_context.to_dict(), event_type, fixture['payload'])

        # Ensure we now have exactly zero active records
        records = self.central_service.find_records(self.admin_context,
                                                    criterion)

        self.assertEqual(2, len(records), records)

        # The two deleted records should now be in action state DELETE.
        for record in records:
            self.assertEqual('DELETE', record.action)
            self.assertEqual('172.16.0.14', record.data)

    def test_instance_delete_one_with_multiple_records_with_same_name(self):
        # Prepare for the test
        for start_event_type in ['compute.instance.create.end',
                                 'compute.instance.create.end-2']:
            start_fixture = self.get_notification_fixture(
                'nova', start_event_type
            )
            self.plugin.process_notification(
                self.admin_context.to_dict(),
                start_fixture['event_type'],
                start_fixture['payload']
            )

        # Now - Onto the real test
        event_type = 'compute.instance.delete.start'
        fixture = self.get_notification_fixture('nova', event_type)

        self.assertIn(event_type, self.plugin.get_event_types())

        criterion = {
            'zone_id': self.zone_id,
            'managed': True,
            'managed_resource_type': 'instance',
        }

        records = self.central_service.find_records(self.admin_context,
                                                    criterion)

        # Ensure we start with exactly 4 records.
        self.assertEqual(4, len(records))

        self.plugin.process_notification(
            self.admin_context.to_dict(), event_type, fixture['payload'])

        # Ensure we now have exactly 2 records
        records = self.central_service.find_records(self.admin_context,
                                                    criterion)

        self.assertEqual(2, len(records), records)

        # The two remaining records should be in waiting UPDATE.
        for record in records:
            self.assertEqual('UPDATE', record.action)
            self.assertEqual('172.16.0.15', record.data)

    def test_instance_delete_with_no_record(self):
        event_type = 'compute.instance.delete.start'
        fixture = self.get_notification_fixture('nova', event_type)

        self.assertIn(event_type, self.plugin.get_event_types())

        criterion = {
            'zone_id': self.zone_id,
            'managed': True,
            'managed_resource_type': 'instance',
        }

        records = self.central_service.find_records(self.admin_context,
                                                    criterion)

        # Ensure we start with zero records
        self.assertFalse(records)

        # Make sure we don't fail here, even though there is nothing to
        # do, since the record we are trying to delete does not actually exist.
        self.plugin.process_notification(
            self.admin_context.to_dict(), event_type, fixture['payload'])

        # Ensure we still have zero records
        records = self.central_service.find_records(self.admin_context,
                                                    criterion)

        self.assertFalse(records)

    def test_label_in_format_v4_v6(self):
        event_type = 'compute.instance.create.end'
        self.config(formatv4=['%(label)s.example.com.'],
                    formatv6=['%(label)s.example.com.'],
                    group='handler:nova_fixed')
        fixture = self.get_notification_fixture('nova', event_type)
        with mock.patch.object(
                self.plugin, '_create_or_update_recordset') as finder:
            with mock.patch.object(self.plugin.central_api,
                                   'create_recordset'):
                finder.return_value = {'id': 'fakeid'}
                self.plugin.process_notification(
                    self.admin_context.to_dict(),
                    event_type, fixture['payload'])
                finder.assert_called_once_with(
                    mock.ANY, mock.ANY, type='A', zone_id=self.zone_id,
                    name='private.example.com.')

    def test_formatv4(self):
        event_type = 'compute.instance.create.end'
        self.config(formatv4=['%(label)s-v4.example.com.'],
                    group='handler:nova_fixed')
        fixture = self.get_notification_fixture('nova', event_type)
        with mock.patch.object(
                self.plugin, '_create_or_update_recordset') as finder:
            with mock.patch.object(self.plugin.central_api,
                                   'create_recordset'):
                finder.return_value = {'id': 'fakeid'}
                self.plugin.process_notification(
                    self.admin_context.to_dict(),
                    event_type, fixture['payload'])
                finder.assert_called_once_with(
                    mock.ANY, mock.ANY, type='A', zone_id=self.zone_id,
                    name='private-v4.example.com.')

    def test_formatv6(self):
        event_type = 'compute.instance.create.end'
        self.config(formatv6=['%(label)s-v6.example.com.'],
                    group='handler:nova_fixed')
        fixture = self.get_notification_fixture('nova', event_type)
        with mock.patch.object(
                self.plugin, '_create_or_update_recordset') as finder:
            with mock.patch.object(self.plugin.central_api,
                                   'create_recordset'):
                finder.return_value = {'id': 'fakeid'}
                self.plugin.process_notification(
                    self.admin_context.to_dict(),
                    event_type, fixture['payload_v6'])
                finder.assert_called_once_with(
                    mock.ANY, mock.ANY, type='AAAA', zone_id=self.zone_id,
                    name='private-v6.example.com.')
