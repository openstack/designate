# coding=utf-8
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
import datetime

import testtools
from mock import patch
import oslo_messaging as messaging
from oslo_config import cfg
from oslo_log import log as logging

from designate import exceptions
from designate.central import service as central_service
from designate.tests.test_api.test_v1 import ApiV1Test


LOG = logging.getLogger(__name__)


class ApiV1zonesTest(ApiV1Test):
    def test_get_zone_schema(self):
        response = self.get('schemas/domain')
        self.assertIn('description', response.json)
        self.assertIn('links', response.json)
        self.assertIn('title', response.json)
        self.assertIn('id', response.json)
        self.assertIn('additionalProperties', response.json)
        self.assertIn('properties', response.json)
        self.assertIn('description', response.json['properties'])
        self.assertIn('created_at', response.json['properties'])
        self.assertIn('updated_at', response.json['properties'])
        self.assertIn('name', response.json['properties'])
        self.assertIn('email', response.json['properties'])
        self.assertIn('ttl', response.json['properties'])
        self.assertIn('serial', response.json['properties'])

    def test_get_zones_schema(self):
        response = self.get('schemas/domains')
        self.assertIn('description', response.json)
        self.assertIn('additionalProperties', response.json)
        self.assertIn('properties', response.json)
        self.assertIn('title', response.json)
        self.assertIn('id', response.json)

    def test_create_zone(self):
        # Create a zone
        fixture = self.get_zone_fixture(0)

        # V1 doesn't have these
        del fixture['type']

        response = self.post('domains', data=fixture)

        self.assertIn('id', response.json)
        self.assertIn('name', response.json)
        self.assertEqual(response.json['name'], fixture['name'])

    def test_create_zone_junk(self):
        # Create a zone
        fixture = self.get_zone_fixture(0)

        # Add a junk property
        fixture['junk'] = 'Junk Field'

        # Ensure it fails with a 400
        self.post('domains', data=fixture, status_code=400)

    @patch.object(central_service.Service, 'create_zone',
                  side_effect=messaging.MessagingTimeout())
    def test_create_zone_timeout(self, _):
        # Create a zone
        fixture = self.get_zone_fixture(0)

        # V1 doesn't have these
        del fixture['type']

        self.post('domains', data=fixture, status_code=504)

    @patch.object(central_service.Service, 'create_zone',
                  side_effect=exceptions.DuplicateZone())
    def test_create_zone_duplicate(self, _):
        # Create a zone
        fixture = self.get_zone_fixture(0)

        # V1 doesn't have these
        del fixture['type']

        self.post('domains', data=fixture, status_code=409)

    def test_create_zone_null_ttl(self):
        # Create a zone
        fixture = self.get_zone_fixture(0)
        fixture['ttl'] = None
        self.post('domains', data=fixture, status_code=400)

    def test_create_zone_negative_ttl(self):
        # Create a zone
        fixture = self.get_zone_fixture(0)
        fixture['ttl'] = -1
        self.post('domains', data=fixture, status_code=400)

    def test_create_zone_zero_ttl(self):
        # Create a zone
        fixture = self.get_zone_fixture(0)
        fixture['ttl'] = 0
        self.post('domains', data=fixture, status_code=400)

    def test_create_zone_invalid_ttl(self):
        # Create a zone
        fixture = self.get_zone_fixture(0)
        fixture['ttl'] = "$?>&"
        self.post('domains', data=fixture, status_code=400)

    def test_create_zone_ttl_greater_than_max(self):
        fixture = self.get_zone_fixture(0)
        fixture['ttl'] = 2147483648
        self.post('domains', data=fixture, status_code=400)

    def test_create_zone_utf_description(self):
        # Create a zone
        fixture = self.get_zone_fixture(0)

        # V1 doesn't have type
        del fixture['type']

        # Give it a UTF-8 filled description
        fixture['description'] = "utf-8:2H₂+O₂⇌2H₂O,R=4.7kΩ,⌀200mm∮E⋅da=Q,n" \
                                 ",∑f(i)=∏g(i),∀x∈ℝ:⌈x⌉"
        # Create the zone, ensuring it succeeds, thus UTF-8 is supported
        self.post('domains', data=fixture)

    def test_create_zone_description_too_long(self):
        # Create a zone
        fixture = self.get_zone_fixture(0)
        fixture['description'] = "x" * 161

        # Create the zone, ensuring it fails with a 400
        self.post('domains', data=fixture, status_code=400)

    def test_create_zone_with_unwanted_attributes(self):

        zone_id = "2d1d1d1d-1324-4a80-aa32-1f69a91bf2c8"
        created_at = datetime.datetime(2014, 6, 22, 21, 50, 0)
        updated_at = datetime.datetime(2014, 6, 22, 21, 50, 0)
        serial = 1234567

        # Create a zone
        fixture = self.get_zone_fixture(0)
        fixture['id'] = zone_id
        fixture['created_at'] = created_at
        fixture['updated_at'] = updated_at
        fixture['serial'] = serial

        self.post('domains', data=fixture, status_code=400)

    def test_create_invalid_name(self):
        # Prepare a zone
        fixture = self.get_zone_fixture(0)

        invalid_names = [
            'org',
            'example.org',
            'example.321',
        ]

        for invalid_name in invalid_names:
            fixture['name'] = invalid_name

            # Create a record
            response = self.post('domains', data=fixture, status_code=400)

            self.assertNotIn('id', response.json)

    def test_create_zone_name_too_long(self):
        fixture = self.get_zone_fixture(0)

        long_name = 'a' * 255 + ".org."
        fixture['name'] = long_name

        response = self.post('domains', data=fixture, status_code=400)

        self.assertNotIn('id', response.json)

    def test_create_zone_name_is_not_present(self):
        fixture = self.get_zone_fixture(0)
        del fixture['name']
        self.post('domains', data=fixture, status_code=400)

    def test_create_invalid_email(self):
        # Prepare a zone
        fixture = self.get_zone_fixture(0)

        invalid_emails = [
            'org',
            'example.org',
            'bla.example.org',
            'org.',
            'example.org.',
            'bla.example.org.',
            'bla.example.org.',
        ]

        for invalid_email in invalid_emails:
            fixture['email'] = invalid_email

            # Create a record
            response = self.post('domains', data=fixture, status_code=400)

            self.assertNotIn('id', response.json)

    def test_create_zone_email_too_long(self):
        fixture = self.get_zone_fixture(0)

        long_email = 'a' * 255 + "@org.com"
        fixture['email'] = long_email

        response = self.post('domains', data=fixture, status_code=400)

        self.assertNotIn('id', response.json)

    def test_create_zone_email_not_present(self):
        fixture = self.get_zone_fixture(0)
        del fixture['email']
        self.post('domains', data=fixture, status_code=400)

    def test_create_zone_twice(self):
        self.create_zone()
        with testtools.ExpectedException(exceptions.DuplicateZone):
            self.create_zone()

    def test_create_zone_pending_deletion(self):
        zone = self.create_zone()
        self.delete('domains/%s' % zone['id'])
        with testtools.ExpectedException(exceptions.DuplicateZone):
            self.create_zone()

    def test_get_zones(self):
        response = self.get('domains')

        self.assertIn('domains', response.json)
        self.assertEqual(0, len(response.json['domains']))

        # Create a zone
        self.create_zone()

        response = self.get('domains')

        self.assertIn('domains', response.json)
        self.assertEqual(1, len(response.json['domains']))

        # Create a second zone
        self.create_zone(fixture=1)

        response = self.get('domains')

        self.assertIn('domains', response.json)
        self.assertEqual(2, len(response.json['domains']))

    def test_get_zone_servers(self):
        # Create a zone
        zone = self.create_zone()
        response = self.get('domains/%s/servers' % zone['id'])
        # Verify length of zone servers
        self.assertEqual(1, len(response.json['servers']))

    @patch.object(central_service.Service, 'find_zones',
                  side_effect=messaging.MessagingTimeout())
    def test_get_zones_timeout(self, _):
        self.get('domains', status_code=504)

    def test_get_zone(self):
        # Create a zone
        zone = self.create_zone()

        response = self.get('domains/%s' % zone['id'])

        self.assertIn('id', response.json)
        self.assertEqual(response.json['id'], zone['id'])

    @patch.object(central_service.Service, 'find_zone',
                  side_effect=messaging.MessagingTimeout())
    def test_get_zone_timeout(self, _):
        # Create a zone
        zone = self.create_zone()

        self.get('domains/%s' % zone['id'], status_code=504)

    def test_get_zone_missing(self):
        self.get('domains/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980',
                 status_code=404)

    def test_get_zone_invalid_id(self):
        # The letter "G" is not valid in a UUID
        self.get('domains/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff9GG',
                 status_code=404)

        self.get('domains/2fdadfb1cf964259ac6bbb7b6d2ff980', status_code=404)

    def test_update_zone(self):
        # Create a zone
        zone = self.create_zone()

        data = {'email': 'prefix-%s' % zone['email']}

        response = self.put('domains/%s' % zone['id'], data=data)

        self.assertIn('id', response.json)
        self.assertEqual(response.json['id'], zone['id'])

        self.assertIn('email', response.json)
        self.assertEqual('prefix-%s' % zone['email'], response.json['email'])

    def test_update_zone_junk(self):
        # Create a zone
        zone = self.create_zone()

        data = {'email': 'prefix-%s' % zone['email'], 'junk': 'Junk Field'}

        self.put('domains/%s' % zone['id'], data=data, status_code=400)

    def test_update_zone_name_fail(self):
        # Create a zone
        zone = self.create_zone()

        data = {'name': 'renamed.com.'}

        self.put('domains/%s' % zone['id'], data=data, status_code=400)

    def test_update_zone_null_ttl(self):
        # Create a zone
        zone = self.create_zone()

        data = {'ttl': None}

        self.put('domains/%s' % zone['id'], data=data, status_code=400)

    def test_update_zone_negative_ttl(self):
        # Create a zone
        zone = self.create_zone()

        data = {'ttl': -1}

        self.put('domains/%s' % zone['id'], data=data, status_code=400)

    def test_update_zone_zero_ttl(self):
        # Create a zone
        zone = self.create_zone()

        data = {'ttl': 0}

        self.put('domains/%s' % zone['id'], data=data, status_code=400)

    @patch.object(central_service.Service, 'update_zone',
                  side_effect=messaging.MessagingTimeout())
    def test_update_zone_timeout(self, _):
        # Create a zone
        zone = self.create_zone()

        data = {'email': 'prefix-%s' % zone['email']}

        self.put('domains/%s' % zone['id'], data=data, status_code=504)

    @patch.object(central_service.Service, 'update_zone',
                  side_effect=exceptions.DuplicateZone())
    def test_update_zone_duplicate(self, _):
        # Create a zone
        zone = self.create_zone()

        data = {'email': 'prefix-%s' % zone['email']}

        self.put('domains/%s' % zone['id'], data=data, status_code=409)

    def test_update_zone_missing(self):
        data = {'email': 'bla@bla.com'}

        self.put('domains/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980', data=data,
                 status_code=404)

    def test_update_zone_invalid_id(self):
        data = {'email': 'bla@bla.com'}

        # The letter "G" is not valid in a UUID
        self.put('domains/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff9GG', data=data,
                 status_code=404)

        self.put('domains/2fdadfb1cf964259ac6bbb7b6d2ff980', data=data,
                 status_code=404)

    def test_update_zone_ttl_greter_than_max(self):
        # Create a zone
        zone = self.create_zone()

        data = {'ttl': 2147483648}

        self.put('domains/%s' % zone['id'], data=data, status_code=400)

    def test_update_zone_invalid_email(self):
        # Create a zone
        zone = self.create_zone()

        invalid_emails = [
            'org',
            'example.org',
            'bla.example.org',
            'org.',
            'example.org.',
            'bla.example.org.',
            'bla.example.org.',
            'a' * 255 + "@com",
            ''
        ]

        for invalid_email in invalid_emails:
            data = {'email': invalid_email}
            self.put('domains/%s' % zone['id'], data=data, status_code=400)

    def test_update_zone_description_too_long(self):
        # Create a zone
        zone = self.create_zone()

        invalid_des = 'a' * 165

        data = {'description': invalid_des}
        self.put('domains/%s' % zone['id'], data=data, status_code=400)

    def test_update_zone_in_pending_deletion(self):
        zone = self.create_zone()
        self.delete('domains/%s' % zone['id'])
        self.put('domains/%s' % zone['id'], data={}, status_code=404)

    def test_delete_zone(self):
        # Create a zone
        zone = self.create_zone()

        self.delete('domains/%s' % zone['id'])

        # Simulate the zone having been deleted on the backend
        zone_serial = self.central_service.get_zone(
            self.admin_context, zone['id']).serial
        self.central_service.update_status(
            self.admin_context, zone['id'], "SUCCESS", zone_serial)

        # Ensure we can no longer fetch the zone
        self.get('domains/%s' % zone['id'], status_code=404)

    def test_zone_in_pending_deletion(self):
        zone1 = self.create_zone()
        self.create_zone(fixture=1)
        response = self.get('domains')
        self.assertEqual(2, len(response.json['domains']))

        # Delete zone1
        self.delete('domains/%s' % zone1['id'])

        # Ensure we can no longer list nor fetch the deleted zone
        response = self.get('domains')
        self.assertEqual(1, len(response.json['domains']))

        self.get('domains/%s' % zone1['id'], status_code=404)

    @patch.object(central_service.Service, 'delete_zone',
                  side_effect=messaging.MessagingTimeout())
    def test_delete_zone_timeout(self, _):
        # Create a zone
        zone = self.create_zone()

        self.delete('domains/%s' % zone['id'], status_code=504)

    def test_delete_zone_missing(self):
        self.delete('domains/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980',
                    status_code=404)

    def test_delete_zone_invalid_id(self):
        # The letter "G" is not valid in a UUID
        self.delete('domains/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff9GG',
                    status_code=404)

        self.delete('domains/2fdadfb1cf964259ac6bbb7b6d2ff980',
                    status_code=404)

    def test_get_secondary_missing(self):
        fixture = self.get_zone_fixture('SECONDARY', 0)
        fixture['email'] = cfg.CONF['service:central'].managed_resource_email

        zone = self.create_zone(**fixture)

        self.get('domains/%s' % zone.id, status_code=404)

    def test_update_secondary_missing(self):
        fixture = self.get_zone_fixture('SECONDARY', 0)
        fixture['email'] = cfg.CONF['service:central'].managed_resource_email

        zone = self.create_zone(**fixture)

        self.put('domains/%s' % zone.id, {}, status_code=404)

    def test_delete_secondary_missing(self):
        fixture = self.get_zone_fixture('SECONDARY', 0)
        fixture['email'] = cfg.CONF['service:central'].managed_resource_email

        zone = self.create_zone(**fixture)
        self.delete('domains/%s' % zone.id, status_code=404)

    def test_get_zone_servers_from_secondary(self):
        fixture = self.get_zone_fixture('SECONDARY', 0)
        fixture['email'] = cfg.CONF['service:central'].managed_resource_email

        zone = self.create_zone(**fixture)
        self.get('domains/%s/servers' % zone.id, status_code=404)
