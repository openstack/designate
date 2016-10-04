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
from mock import patch
import oslo_messaging as messaging
from oslo_log import log as logging

from designate.central import service as central_service
from designate.tests.test_api.test_v1 import ApiV1Test


LOG = logging.getLogger(__name__)


class ApiV1RecordsTest(ApiV1Test):
    def setUp(self):
        super(ApiV1RecordsTest, self).setUp()

        self.zone = self.create_zone()
        self.recordset = self.create_recordset(self.zone, 'A')

    def test_get_record_schema(self):
        response = self.get('schemas/record')
        self.assertIn('description', response.json)
        self.assertIn('links', response.json)
        self.assertIn('title', response.json)
        self.assertIn('id', response.json)
        self.assertIn('additionalProperties', response.json)
        self.assertIn('properties', response.json)
        self.assertIn('id', response.json['properties'])
        self.assertIn('domain_id', response.json['properties'])
        self.assertIn('type', response.json['properties'])
        self.assertIn('data', response.json['properties'])
        self.assertIn('priority', response.json['properties'])
        self.assertIn('description', response.json['properties'])
        self.assertIn('created_at', response.json['properties'])
        self.assertIn('updated_at', response.json['properties'])
        self.assertIn('name', response.json['properties'])
        self.assertIn('ttl', response.json['properties'])
        self.assertIn('oneOf', response.json)

    def test_get_records_schema(self):
        response = self.get('schemas/records')
        self.assertIn('description', response.json)
        self.assertIn('additionalProperties', response.json)
        self.assertIn('properties', response.json)
        self.assertIn('title', response.json)
        self.assertIn('id', response.json)

    def test_create_record(self):
        recordset_fixture = self.get_recordset_fixture(
            self.zone['name'])

        fixture = self.get_record_fixture(recordset_fixture['type'])
        fixture.update({
            'name': recordset_fixture['name'],
            'type': recordset_fixture['type'],
        })

        # Create a record
        response = self.post('domains/%s/records' % self.zone['id'],
                             data=fixture)

        self.assertIn('id', response.json)
        self.assertIn('name', response.json)
        self.assertEqual(response.json['name'], fixture['name'])

    def test_create_record_existing_recordset(self):
        fixture = self.get_record_fixture(self.recordset['type'])
        fixture.update({
            'name': self.recordset['name'],
            'type': self.recordset['type'],
        })

        # Create a record
        response = self.post('domains/%s/records' % self.zone['id'],
                             data=fixture)

        self.assertIn('id', response.json)
        self.assertIn('name', response.json)
        self.assertEqual(response.json['name'], fixture['name'])

    def test_create_record_name_reuse(self):
        fixture_1 = self.get_record_fixture(self.recordset['type'])
        fixture_1.update({
            'name': self.recordset['name'],
            'type': self.recordset['type'],
        })

        fixture_2 = self.get_record_fixture(self.recordset['type'], fixture=1)
        fixture_2.update({
            'name': self.recordset['name'],
            'type': self.recordset['type'],
        })

        # Create 2 records
        record_1 = self.post('domains/%s/records' % self.zone['id'],
                             data=fixture_1)
        record_2 = self.post('domains/%s/records' % self.zone['id'],
                             data=fixture_2)

        # Delete record 1, this should not have any side effects
        self.delete('domains/%s/records/%s' % (self.zone['id'],
                                               record_1.json['id']))

        # Simulate the record 1 having been deleted on the backend
        zone_serial = self.central_service.get_zone(
            self.admin_context, self.zone['id']).serial
        self.central_service.update_status(
            self.admin_context, self.zone['id'], "SUCCESS", zone_serial)

        # Get the record 2 to ensure recordset did not get deleted
        rec_2_get_response = self.get('domains/%s/records/%s' %
                                      (self.zone['id'], record_2.json['id']))

        self.assertIn('id', rec_2_get_response.json)
        self.assertIn('name', rec_2_get_response.json)
        self.assertEqual(rec_2_get_response.json['name'], fixture_1['name'])

        # Delete record 2, this should delete the null recordset too
        self.delete('domains/%s/records/%s' % (self.zone['id'],
                                               record_2.json['id']))

        # Simulate the record 2 having been deleted on the backend
        zone_serial = self.central_service.get_zone(
            self.admin_context, self.zone['id']).serial
        self.central_service.update_status(
            self.admin_context, self.zone['id'], "SUCCESS", zone_serial)

        # Re-create as a different type, but use the same name
        fixture = self.get_record_fixture('CNAME')
        fixture.update({
            'name': self.recordset['name'],
            'type': 'CNAME'
        })

        response = self.post('domains/%s/records' % self.zone['id'],
                             data=fixture)

        self.assertIn('id', response.json)
        self.assertIn('name', response.json)
        self.assertEqual(response.json['name'], fixture['name'])

    def test_create_record_junk(self):
        fixture = self.get_record_fixture(self.recordset['type'])
        fixture.update({
            'name': self.recordset['name'],
            'type': self.recordset['type'],
        })

        # Add a junk property
        fixture['junk'] = 'Junk Field'

        # Create a record, ensuring it fails with a 400
        self.post('domains/%s/records' % self.zone['id'], data=fixture,
                  status_code=400)

    def test_create_wildcard_record_after_named(self):
        # We want to test that a wildcard record rs does not use the
        # previous one
        # https://bugs.launchpad.net/designate/+bug/1391426

        name = "foo.%s" % self.zone.name
        fixture = {
            "name": name,
            "type": "A",
            "data": "10.0.0.1"
        }

        self.post('domains/%s/records' % self.zone['id'],
                  data=fixture)

        wildcard_name = '*.%s' % self.zone["name"]

        fixture['name'] = wildcard_name
        self.post('domains/%s/records' % self.zone['id'],
                  data=fixture)

        named_rs = self.central_service.find_recordset(
            self.admin_context, {"name": name})
        wildcard_rs = self.central_service.find_recordset(
            self.admin_context, {"name": wildcard_name})

        self.assertNotEqual(named_rs.name, wildcard_rs.name)
        self.assertNotEqual(named_rs.id, wildcard_rs.id)

    def test_create_record_utf_description(self):
        fixture = self.get_record_fixture(self.recordset['type'])
        fixture.update({
            'name': self.recordset['name'],
            'type': self.recordset['type'],
        })

        # Add a UTF-8 riddled description
        fixture['description'] = "utf-8:2H₂+O₂⇌2H₂O,R=4.7kΩ,⌀200mm∮E⋅da=Q,n" \
                                 ",∑f(i)=∏g(i),∀x∈ℝ:⌈x⌉"

        # Create a record, ensuring it succeeds
        self.post('domains/%s/records' % self.zone['id'], data=fixture)

    def test_create_record_description_too_long(self):
        fixture = self.get_record_fixture(self.recordset['type'])
        fixture.update({
            'name': self.recordset['name'],
            'type': self.recordset['type'],
        })

        # Add a description that is too long
        fixture['description'] = "x" * 161

        # Create a record, ensuring it fails with a 400
        self.post('domains/%s/records' % self.zone['id'], data=fixture,
                  status_code=400)

    def test_create_record_name_too_long(self):
        fixture = self.get_record_fixture(self.recordset['type'])
        fixture.update({'type': self.recordset['type']})
        fixture['name'] = 'w' * 255 + ".%s" % self.zone.name
        self.post('domains/%s/records' % self.zone['id'], data=fixture,
                  status_code=400)

    def test_create_record_name_is_missing(self):
        fixture = self.get_record_fixture(self.recordset['type'])
        fixture.update({'type': self.recordset['type']})
        self.post('domains/%s/records' % self.zone['id'], data=fixture,
                  status_code=400)

    def test_create_record_type_is_missing(self):
        fixture = self.get_record_fixture(self.recordset['type'])
        fixture['name'] = "www.%s" % self.zone.name
        self.post('domains/%s/records' % self.zone['id'], data=fixture,
                  status_code=400)

    def test_create_record_invalid_type(self):
        fixture = self.get_record_fixture(self.recordset['type'])
        fixture.update({'type': "ABC", 'name': self.recordset['name']})
        self.post('domains/%s/records' % self.zone['id'], data=fixture,
                  status_code=400)

    def test_create_record_data_is_missing(self):
        fixture = self.get_record_fixture(self.recordset['type'])
        fixture.update({'type': self.recordset['type'],
                        'name': self.recordset['name']})
        del fixture['data']
        self.post('domains/%s/records' % self.zone['id'], data=fixture,
                  status_code=400)

    def test_create_record_ttl_greater_than_max(self):
        fixture = self.get_record_fixture(self.recordset['type'])
        fixture.update({
            'name': self.recordset['name'],
            'type': self.recordset['type'],
        })

        fixture['ttl'] = 2174483648
        self.post('domains/%s/records' % self.zone['id'], data=fixture,
                  status_code=400)

    def test_create_record_negative_ttl(self):
        fixture = self.get_record_fixture(self.recordset['type'])
        fixture.update({
            'name': self.recordset['name'],
            'type': self.recordset['type'],
        })

        # Set the TTL to a negative value
        fixture['ttl'] = -1

        # Create a record, ensuring it fails with a 400
        self.post('domains/%s/records' % self.zone['id'], data=fixture,
                  status_code=400)

    def test_create_record_zero_ttl(self):
        fixture = self.get_record_fixture(self.recordset['type'])
        fixture.update({
            'name': self.recordset['name'],
            'type': self.recordset['type'],
        })

        # Set the TTL to a value zero
        fixture['ttl'] = 0

        # Create a record, ensuring it fails with a 400
        self.post('domains/%s/records' % self.zone['id'], data=fixture,
                  status_code=400)

    def test_create_record_invalid_ttl(self):
        fixture = self.get_record_fixture(self.recordset['type'])
        fixture.update({
            'name': self.recordset['name'],
            'type': self.recordset['type'],
        })

        # Set the TTL to an invalid value
        fixture['ttl'] = "$?!."

        # Create a record, ensuring it fails with a 400
        self.post('domains/%s/records' % self.zone['id'], data=fixture,
                  status_code=400)

    def test_create_record_invalid_priority(self):
        fixture = self.get_record_fixture(self.recordset['type'])
        fixture.update({
            'name': self.recordset['name'],
            'type': self.recordset['type'],
        })
        fixture['priority'] = "$?!."
        self.post('domains/%s/records' % self.zone['id'], data=fixture,
                  status_code=400)

    def test_create_record_negative_priority(self):
        fixture = self.get_record_fixture(self.recordset['type'])
        fixture.update({
            'name': self.recordset['name'],
            'type': self.recordset['type'],
        })
        fixture['priority'] = -1
        self.post('domains/%s/records' % self.zone['id'], data=fixture,
                  status_code=400)

    def test_create_record_priority_greater_than_max(self):
        fixture = self.get_record_fixture(self.recordset['type'])
        fixture.update({
            'name': self.recordset['name'],
            'type': self.recordset['type'],
        })
        fixture['priority'] = 65536
        self.post('domains/%s/records' % self.zone['id'], data=fixture,
                  status_code=400)

    @patch.object(central_service.Service, 'create_record',
                  side_effect=messaging.MessagingTimeout())
    def test_create_record_timeout(self, _):
        fixture = self.get_record_fixture(self.recordset['type'])
        fixture.update({
            'name': self.recordset['name'],
            'type': self.recordset['type'],
        })

        # Create a record
        self.post('domains/%s/records' % self.zone['id'], data=fixture,
                  status_code=504)

    def test_create_wildcard_record(self):
        # Prepare a record
        fixture = self.get_record_fixture(self.recordset['type'])
        fixture.update({
            'name': '*.%s' % self.recordset['name'],
            'type': self.recordset['type'],
        })

        # Create a record
        response = self.post('domains/%s/records' % self.zone['id'],
                             data=fixture)

        self.assertIn('id', response.json)
        self.assertIn('name', response.json)
        self.assertEqual(response.json['name'], fixture['name'])

    def test_create_srv_record(self):
        recordset_fixture = self.get_recordset_fixture(
            self.zone['name'], 'SRV')

        fixture = self.get_record_fixture(recordset_fixture['type'])
        priority, _, data = fixture['data'].partition(" ")

        fixture.update({
            'data': data,
            'priority': int(priority),
            'name': recordset_fixture['name'],
            'type': recordset_fixture['type'],
        })

        # Create a record
        response = self.post('domains/%s/records' % self.zone['id'],
                             data=fixture)

        self.assertIn('id', response.json)
        self.assertEqual(fixture['type'], response.json['type'])
        self.assertEqual(fixture['name'], response.json['name'])

        self.assertEqual(fixture['priority'], response.json['priority'])
        self.assertEqual(fixture['data'], response.json['data'])

    def test_create_invalid_data_srv_record(self):
        recordset_fixture = self.get_recordset_fixture(
            self.zone['name'], 'SRV')

        fixture = self.get_record_fixture(recordset_fixture['type'])
        fixture.update({
            'name': recordset_fixture['name'],
            'type': recordset_fixture['type'],
        })

        invalid_datas = [
            'I 5060 sip.%s' % self.zone['name'],
            '5060 sip.%s' % self.zone['name'],
            '5060 I sip.%s' % self.zone['name'],
            '0 5060 sip',
            'sip',
            'sip.%s' % self.zone['name'],
        ]

        for invalid_data in invalid_datas:
            fixture['data'] = invalid_data
            # Attempt to create the record
            self.post('domains/%s/records' % self.zone['id'], data=fixture,
                      status_code=400)

    def test_create_invalid_name_srv_record(self):
        recordset_fixture = self.get_recordset_fixture(
            self.zone['name'], 'SRV')

        fixture = self.get_record_fixture(recordset_fixture['type'])
        fixture.update({
            'name': recordset_fixture['name'],
            'type': recordset_fixture['type'],
        })

        invalid_names = [
            '%s' % self.zone['name'],
            '_udp.%s' % self.zone['name'],
            'sip._udp.%s' % self.zone['name'],
            '_sip.udp.%s' % self.zone['name'],
        ]

        for invalid_name in invalid_names:
            fixture['name'] = invalid_name

            # Attempt to create the record
            self.post('domains/%s/records' % self.zone['id'], data=fixture,
                      status_code=400)

    def test_create_invalid_name(self):
        # Prepare a record
        fixture = self.get_record_fixture(self.recordset['type'])
        fixture.update({
            'name': self.recordset['name'],
            'type': self.recordset['type'],
        })

        invalid_names = [
            'org',
            'example.org',
            '$$.example.org',
            '*example.org.',
            '*.*.example.org.',
            'abc.*.example.org.',
        ]

        for invalid_name in invalid_names:
            fixture['name'] = invalid_name

            # Create a record
            response = self.post('domains/%s/records' % self.zone['id'],
                                 data=fixture, status_code=400)

            self.assertNotIn('id', response.json)

    def test_get_records(self):
        response = self.get('domains/%s/records' % self.zone['id'])

        # Verify that the SOA & NS records are already created
        self.assertIn('records', response.json)
        self.assertEqual(2, len(response.json['records']))

        # Create a record
        self.create_record(self.zone, self.recordset)

        response = self.get('domains/%s/records' % self.zone['id'])

        # Verify that one more record has been added
        self.assertIn('records', response.json)
        self.assertEqual(3, len(response.json['records']))

        # Create a second record
        self.create_record(self.zone, self.recordset, fixture=1)

        response = self.get('domains/%s/records' % self.zone['id'])

        # Verfiy that all 4 records are there
        self.assertIn('records', response.json)
        self.assertEqual(4, len(response.json['records']))

    @patch.object(central_service.Service, 'get_zone',
                  side_effect=messaging.MessagingTimeout())
    def test_get_records_timeout(self, _):
        self.get('domains/%s/records' % self.zone['id'],
                 status_code=504)

    def test_get_records_missing_zone(self):
        self.get('domains/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980/records',
                 status_code=404)

    def test_get_records_invalid_zone_id(self):
        self.get('domains/2fdadfb1cf964259ac6bbb7b6d2ff980/records',
                 status_code=404)

    def test_get_record_missing(self):
        self.get('domains/%s/records/2fdadfb1-cf96-4259-ac6b-'
                 'bb7b6d2ff980' % self.zone['id'],
                 status_code=404)

    def test_get_record_with_invalid_id(self):
        self.get('domains/%s/records/2fdadfb1-cf96-4259-ac6b-'
                 'bb7b6d2ff980GH' % self.zone['id'],
                 status_code=404)

    def test_get_record(self):
        # Create a record
        record = self.create_record(self.zone, self.recordset)

        response = self.get('domains/%s/records/%s' % (self.zone['id'],
                                                       record['id']))

        self.assertIn('id', response.json)
        self.assertEqual(response.json['id'], record['id'])
        self.assertEqual(response.json['name'], self.recordset['name'])
        self.assertEqual(response.json['type'], self.recordset['type'])

    def test_update_record(self):
        # Create a record
        record = self.create_record(self.zone, self.recordset)

        # Fetch another fixture to use in the update
        fixture = self.get_record_fixture(self.recordset['type'], fixture=1)

        # Update the record
        data = {'data': fixture['data']}
        response = self.put('domains/%s/records/%s' % (self.zone['id'],
                                                       record['id']),
                            data=data)

        self.assertIn('id', response.json)
        self.assertEqual(response.json['id'], record['id'])
        self.assertEqual(response.json['data'], fixture['data'])
        self.assertEqual(response.json['type'], self.recordset['type'])

    def test_update_record_ttl(self):
        # Create a record
        record = self.create_record(self.zone, self.recordset)

        # Update the record
        data = {'ttl': 100}
        response = self.put('domains/%s/records/%s' % (self.zone['id'],
                                                       record['id']),
                            data=data)

        self.assertIn('id', response.json)
        self.assertEqual(record['id'], response.json['id'])
        self.assertEqual(record['data'], response.json['data'])
        self.assertEqual(self.recordset['type'], response.json['type'])
        self.assertEqual(100, response.json['ttl'])

    def test_update_record_junk(self):
        # Create a record
        record = self.create_record(self.zone, self.recordset)

        data = {'ttl': 100, 'junk': 'Junk Field'}

        self.put('domains/%s/records/%s' % (self.zone['id'], record['id']),
                 data=data, status_code=400)

    def test_update_record_negative_ttl(self):
        # Create a record
        record = self.create_record(self.zone, self.recordset)

        data = {'ttl': -1}

        self.put('domains/%s/records/%s' % (self.zone['id'], record['id']),
                 data=data, status_code=400)

    def test_update_record_ttl_greater_than_max(self):
        record = self.create_record(self.zone, self.recordset)
        data = {'ttl': 2174483648}
        self.put('domains/%s/records/%s' % (self.zone['id'], record['id']),
                 data=data, status_code=400)

    def test_update_record_zero_ttl(self):
        # Create a record
        record = self.create_record(self.zone, self.recordset)

        data = {'ttl': 0}

        self.put('domains/%s/records/%s' % (self.zone['id'], record['id']),
                 data=data, status_code=400)

    def test_update_record_invalid_ttl(self):
        # Create a record
        record = self.create_record(self.zone, self.recordset)

        data = {'ttl': "$?>%"}

        self.put('domains/%s/records/%s' % (self.zone['id'], record['id']),
                 data=data, status_code=400)

    def test_update_record_description_too_long(self):
        record = self.create_record(self.zone, self.recordset)
        data = {'description': 'x' * 165}
        self.put('domains/%s/records/%s' % (self.zone['id'], record['id']),
                 data=data, status_code=400)

    def test_update_record_negative_priority(self):
        record = self.create_record(self.zone, self.recordset)
        data = {'priority': -1}
        self.put('domains/%s/records/%s' % (self.zone['id'], record['id']),
                 data=data, status_code=400)

    def test_update_record_invalid_priority(self):
        record = self.create_record(self.zone, self.recordset)
        data = {'priority': "?!:>"}
        self.put('domains/%s/records/%s' % (self.zone['id'], record['id']),
                 data=data, status_code=400)

    def test_update_record_priority_greater_than_max(self):
        record = self.create_record(self.zone, self.recordset)
        data = {'priority': 65536}
        self.put('domains/%s/records/%s' % (self.zone['id'], record['id']),
                 data=data, status_code=400)

    def test_update_record_name_too_long(self):
        record = self.create_record(self.zone, self.recordset)
        data = {'name': 'w' * 256 + ".%s" % self.zone.name}
        self.put('domains/%s/records/%s' % (self.zone['id'], record['id']),
                 data=data, status_code=400)

    def test_update_record_invalid_type(self):
        record = self.create_record(self.zone, self.recordset)
        data = {'type': 'ABC'}
        self.put('domains/%s/records/%s' % (self.zone['id'], record['id']),
                 data=data, status_code=400)

    def test_update_record_data_too_long(self):
        record = self.create_record(self.zone, self.recordset)
        data = {'data': '1' * 255 + '.2.3.4'}
        self.put('domains/%s/records/%s' % (self.zone['id'], record['id']),
                 data=data, status_code=400)

    def test_update_record_outside_zone_fail(self):
        # Create a record
        record = self.create_record(self.zone, self.recordset)

        data = {'name': 'test.someotherzone.com.'}

        self.put('domains/%s/records/%s' % (self.zone['id'], record['id']),
                 data=data, status_code=400)

    @patch.object(central_service.Service, 'find_zone',
                  side_effect=messaging.MessagingTimeout())
    def test_update_record_timeout(self, _):
        # Create a record
        record = self.create_record(self.zone, self.recordset)

        data = {'name': 'test.example.org.'}

        self.put('domains/%s/records/%s' % (self.zone['id'], record['id']),
                 data=data, status_code=504)

    def test_update_record_missing(self):
        data = {'name': 'test.example.org.'}

        self.put('domains/%s/records/2fdadfb1-cf96-4259-ac6b-'
                 'bb7b6d2ff980' % self.zone['id'],
                 data=data,
                 status_code=404)

    def test_update_record_invalid_id(self):
        data = {'name': 'test.example.org.'}

        self.put('domains/%s/records/2fdadfb1cf964259ac6bbb7b6d2ff980' %
                 self.zone['id'],
                 data=data,
                 status_code=404)

    def test_update_record_missing_zone(self):
        data = {'name': 'test.example.org.'}

        self.put('domains/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980/records/'
                 '2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980',
                 data=data,
                 status_code=404)

    def test_update_record_invalid_zone_id(self):
        data = {'name': 'test.example.org.'}

        self.put('domains/2fdadfb1cf964259ac6bbb7b6d2ff980/records/'
                 '2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980',
                 data=data,
                 status_code=404)

    def test_delete_record(self):
        # Create a record
        record = self.create_record(self.zone, self.recordset)

        self.delete('domains/%s/records/%s' % (self.zone['id'],
                                               record['id']))

        # Simulate the record having been deleted on the backend
        zone_serial = self.central_service.get_zone(
            self.admin_context, self.zone['id']).serial
        self.central_service.update_status(
            self.admin_context, self.zone['id'], "SUCCESS", zone_serial)

        # Ensure we can no longer fetch the record
        self.get('domains/%s/records/%s' % (self.zone['id'],
                                            record['id']),
                 status_code=404)

    @patch.object(central_service.Service, 'find_zone',
                  side_effect=messaging.MessagingTimeout())
    def test_delete_record_timeout(self, _):
        # Create a record
        record = self.create_record(self.zone, self.recordset)

        self.delete('domains/%s/records/%s' % (self.zone['id'],
                                               record['id']),
                    status_code=504)

    def test_delete_record_missing(self):
        self.delete('domains/%s/records/2fdadfb1-cf96-4259-ac6b-'
                    'bb7b6d2ff980' % self.zone['id'],
                    status_code=404)

    def test_delete_record_missing_zone(self):
        self.delete('domains/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980/records/'
                    '2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980',
                    status_code=404)

    def test_delete_record_invalid_zone_id(self):
        self.delete('domains/2fdadfb1cf964259ac6bbb7b6d2ff980/records/'
                    '2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980',
                    status_code=404)

    def test_delete_record_invalid_id(self):
        self.delete('domains/%s/records/2fdadfb1-cf96-4259-ac6b-'
                    'bb7b6d2ff980GH' % self.zone['id'],
                    status_code=404)

    def test_get_record_in_secondary(self):
        fixture = self.get_zone_fixture('SECONDARY', 1)
        fixture['email'] = "root@example.com"

        zone = self.create_zone(**fixture)

        record = self.create_record(zone, self.recordset)

        url = 'zones/%s/records/%s' % (zone.id, record.id)
        self.get(url, status_code=404)

    def test_create_record_in_secondary(self):
        fixture = self.get_zone_fixture('SECONDARY', 1)
        fixture['email'] = "root@example.com"

        zone = self.create_zone(**fixture)

        record = {
            "name": "foo.%s" % zone.name,
            "type": "A",
            "data": "10.0.0.1"
        }

        url = 'zones/%s/records' % zone.id
        self.post(url, record, status_code=404)

    def test_update_record_in_secondary(self):
        fixture = self.get_zone_fixture('SECONDARY', 1)
        fixture['email'] = "root@example.com"

        zone = self.create_zone(**fixture)

        record = self.create_record(zone, self.recordset)

        url = 'zones/%s/records/%s' % (zone.id, record.id)
        self.put(url, {"data": "10.0.0.1"}, status_code=404)

    def test_delete_record_in_secondary(self):
        fixture = self.get_zone_fixture('SECONDARY', 1)
        fixture['email'] = "root@example.com"

        zone = self.create_zone(**fixture)

        record = self.create_record(zone, self.recordset)

        url = 'zones/%s/records/%s' % (zone.id, record.id)
        self.delete(url, status_code=404)

    def test_create_record_deleting_zone(self):
        recordset_fixture = self.get_recordset_fixture(
            self.zone['name'])

        fixture = self.get_record_fixture(recordset_fixture['type'])
        fixture.update({
            'name': recordset_fixture['name'],
            'type': recordset_fixture['type'],
        })

        self.delete('/domains/%s' % self.zone['id'])
        self.post('domains/%s/records' % self.zone['id'],
                  data=fixture, status_code=404)

    def test_update_record_deleting_zone(self):
        # Create a record
        record = self.create_record(self.zone, self.recordset)

        # Fetch another fixture to use in the update
        fixture = self.get_record_fixture(self.recordset['type'], fixture=1)

        # Update the record
        data = {'data': fixture['data']}
        self.delete('/domains/%s' % self.zone['id'])
        self.put('domains/%s/records/%s' % (self.zone['id'],
                                            record['id']),
                 data=data, status_code=404)

    def test_delete_record_deleting_zone(self):
        # Create a record
        record = self.create_record(self.zone, self.recordset)

        self.delete('/domains/%s' % self.zone['id'])
        self.delete('domains/%s/records/%s' % (self.zone['id'],
                                               record['id']),
                    status_code=404)


class ApiV1TxtRecordsTest(ApiV1Test):
    def setUp(self):
        super(ApiV1TxtRecordsTest, self).setUp()

        self.zone = self.create_zone()
        self.recordset = self.create_recordset(self.zone, 'TXT')

    def test_create_txt_record(self):
        # See bug #1474012
        record = self.create_record(self.zone, self.recordset)
        data = {'data': 'a' * 255}
        self.put(
            'domains/%s/records/%s' % (self.zone['id'], record['id']),
            data=data
        )

    def test_create_txt_record_too_long(self):
        # See bug #1474012
        record = self.create_record(self.zone, self.recordset)
        data = {'data': 'a' * 256}
        self.put(
            'domains/%s/records/%s' % (self.zone['id'], record['id']),
            data=data,
            status_code=400
        )
