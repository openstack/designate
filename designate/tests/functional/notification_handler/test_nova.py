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

from designate import exceptions
from designate.notification_handler import nova
from designate import objects
from designate.tests import base_fixtures
import designate.tests.functional


LOG = logging.getLogger(__name__)


class NovaFixedHandlerTest(designate.tests.functional.TestCase):
    def setUp(self):
        super().setUp()

        zone = self.create_zone()
        self.zone_id = zone['id']
        self.config(zone_id=zone['id'], group='handler:nova_fixed')
        self.config(formatv4=['%(host)s.bar.%(zone)s',
                              '%(host)s.baz.%(zone)s',
                              '%(host)s.foo.%(zone)s',
                              '%(host)s.%(zone)s'],
                    formatv6=['%(host)s.%(zone)s',
                              '%(host)s.foo.%(zone)s'],
                    group='handler:nova_fixed')

        self.plugin = nova.NovaFixedHandler()

    def test_instance_create_end(self):
        event_type = 'compute.instance.create.end'
        fixture = base_fixtures.get_notification_fixture('nova', event_type)

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

        # Ensure we now have exactly 4 records.
        records = self.central_service.find_records(self.admin_context,
                                                    criterion)

        self.assertEqual(4, len(records))

    def test_instance_create_end_utf8(self):
        self.config(formatv4=['%(display_name)s.%(zone)s'],
                    formatv6=['%(display_name)s.%(zone)s'],
                    group='handler:nova_fixed')

        event_type = 'compute.instance.create.end'
        fixture = base_fixtures.get_notification_fixture('nova', event_type)

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
        start_fixture = base_fixtures.get_notification_fixture(
            'nova', start_event_type
        )

        self.plugin.process_notification(self.admin_context.to_dict(),
                                         start_event_type,
                                         start_fixture['payload'])

        # Now - Onto the real test
        event_type = 'compute.instance.delete.start'
        fixture = base_fixtures.get_notification_fixture('nova', event_type)

        self.assertIn(event_type, self.plugin.get_event_types())

        criterion = {
            'zone_id': self.zone_id,
            'managed': True,
            'managed_resource_type': 'instance',
        }

        # Ensure we start with exactly 4 records.
        records = self.central_service.find_records(self.admin_context,
                                                    criterion)

        self.assertEqual(4, len(records))

        self.plugin.process_notification(
            self.admin_context.to_dict(), event_type, fixture['payload'])

        # Ensure we now have exactly zero active records
        records = self.central_service.find_records(self.admin_context,
                                                    criterion)

        self.assertEqual(4, len(records), records)

        # The four deleted records should now be in action state DELETE.
        for record in records:
            self.assertEqual('DELETE', record.action)
            self.assertEqual('172.16.0.14', record.data)

    def test_instance_delete_start_record_status_changed(self):
        start_event_type = 'compute.instance.create.end'
        start_fixture = base_fixtures.get_notification_fixture(
            'nova', start_event_type
        )

        self.plugin.process_notification(self.admin_context.to_dict(),
                                         start_event_type,
                                         start_fixture['payload'])

        event_type = 'compute.instance.delete.start'
        fixture = base_fixtures.get_notification_fixture('nova', event_type)

        self.assertIn(event_type, self.plugin.get_event_types())

        criterion = {
            'zone_id': self.zone_id,
            'managed': True,
            'managed_resource_type': 'instance',
        }

        records = self.central_service.find_records(self.admin_context,
                                                    criterion)

        self.assertEqual(4, len(records))

        org_find_recordset = self.central_service.find_recordset

        def mock_find_recordset(context, criterion):
            results = org_find_recordset(context, criterion)
            for r in results.records:
                r.status = 'PENDING'
            return results

        with mock.patch.object(self.central_service, 'find_recordset',
                               side_effect=mock_find_recordset):
            self.plugin.process_notification(
                self.admin_context.to_dict(), event_type, fixture['payload'])

        records = self.central_service.find_records(self.admin_context,
                                                    criterion)

        self.assertEqual(4, len(records), records)

        for record in records:
            self.assertEqual('DELETE', record.action)
            self.assertEqual('172.16.0.14', record.data)

    def test_instance_delete_one_with_multiple_records_with_same_name(self):
        # Prepare for the test
        for start_event_type in ['compute.instance.create.end',
                                 'compute.instance.create.end-2']:
            start_fixture = base_fixtures.get_notification_fixture(
                'nova', start_event_type
            )
            self.plugin.process_notification(
                self.admin_context.to_dict(),
                start_fixture['event_type'],
                start_fixture['payload']
            )

        # Now - Onto the real test
        event_type = 'compute.instance.delete.start'
        fixture = base_fixtures.get_notification_fixture('nova', event_type)

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

        # Ensure we now have exactly 4 records
        records = self.central_service.find_records(self.admin_context,
                                                    criterion)

        self.assertEqual(4, len(records), records)

        # The two remaining records should be in waiting UPDATE.
        for record in records:
            self.assertEqual('UPDATE', record.action)
            self.assertEqual('172.16.0.15', record.data)

    def test_instance_delete_with_no_record(self):
        event_type = 'compute.instance.delete.start'
        fixture = base_fixtures.get_notification_fixture('nova', event_type)

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

    def test_instance_delete_with_no_recordset(self):
        start_event_type = 'compute.instance.create.end'
        start_fixture = base_fixtures.get_notification_fixture(
            'nova', start_event_type
        )

        self.plugin.process_notification(self.admin_context.to_dict(),
                                         start_event_type,
                                         start_fixture['payload'])

        event_type = 'compute.instance.delete.start'
        fixture = base_fixtures.get_notification_fixture('nova', event_type)

        # Make sure we don't fail here, even though there is nothing to
        # do, since the recordset we are trying to delete does not actually
        # exist.
        with mock.patch.object(self.central_service, 'find_recordset',
                               side_effect=exceptions.RecordSetNotFound):
            self.plugin.process_notification(
                self.admin_context.to_dict(), event_type, fixture['payload'])

    def test_instance_delete_with_no_records_in_recordset(self):
        start_event_type = 'compute.instance.create.end'
        start_fixture = base_fixtures.get_notification_fixture(
            'nova', start_event_type
        )

        self.plugin.process_notification(self.admin_context.to_dict(),
                                         start_event_type,
                                         start_fixture['payload'])

        event_type = 'compute.instance.delete.start'
        fixture = base_fixtures.get_notification_fixture('nova', event_type)

        # Make sure we don't fail here, even though there is nothing to
        # do, since the recordset we are trying to delete contains no records.
        with mock.patch.object(
                self.central_service, 'find_recordset',
                return_value=objects.RecordSet(records=objects.RecordList())):
            self.plugin.process_notification(
                self.admin_context.to_dict(), event_type, fixture['payload'])

    def test_label_in_format_v4_v6(self):
        event_type = 'compute.instance.create.end'
        self.config(formatv4=['%(label)s.example.com.'],
                    formatv6=['%(label)s.example.com.'],
                    group='handler:nova_fixed')
        fixture = base_fixtures.get_notification_fixture('nova', event_type)
        with mock.patch.object(
                self.central_service.storage, 'find_recordset') as finder:
            with mock.patch.object(self.central_service, 'update_recordset'):
                self.plugin.process_notification(
                    self.admin_context.to_dict(),
                    event_type, fixture['payload'])
                finder.assert_called_once_with(
                    mock.ANY,
                    {
                        'zone_id': self.zone_id,
                        'name': 'private.example.com.',
                        'type': 'A'
                    }
                )

    def test_formatv4(self):
        event_type = 'compute.instance.create.end'
        self.config(formatv4=['%(label)s-v4.example.com.'],
                    group='handler:nova_fixed')
        fixture = base_fixtures.get_notification_fixture('nova', event_type)
        with mock.patch.object(
                self.central_service.storage, 'find_recordset') as finder:
            with mock.patch.object(self.central_service, 'update_recordset'):
                self.plugin.process_notification(
                    self.admin_context.to_dict(),
                    event_type, fixture['payload'])
                finder.assert_called_once_with(
                    mock.ANY,
                    {
                        'zone_id': self.zone_id,
                        'name': 'private-v4.example.com.',
                        'type': 'A'
                    }
                )

    def test_formatv6(self):
        event_type = 'compute.instance.create.end'
        self.config(
            formatv6=['%(label)s-v6.example.com.'],
            group='handler:nova_fixed'
        )
        fixture = base_fixtures.get_notification_fixture('nova', event_type)
        with mock.patch.object(
                self.central_service.storage, 'find_recordset') as finder:
            with mock.patch.object(self.central_service, 'update_recordset'):
                self.plugin.process_notification(
                    self.admin_context.to_dict(),
                    event_type, fixture['payload_v6']
                )
                finder.assert_called_once_with(
                    mock.ANY,
                    {
                        'zone_id': self.zone_id,
                        'name': 'private-v6.example.com.',
                        'type': 'AAAA'
                    }
                )
