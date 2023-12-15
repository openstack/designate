# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
from unittest.mock import patch

from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_utils import timeutils

from designate.central import service as central_service
from designate import exceptions
from designate import objects
from designate.tests.functional.api import v2

LOG = logging.getLogger(__name__)


class ApiV2RecordSetsTest(v2.ApiV2TestCase):
    def setUp(self):
        super().setUp()

        # Create a zone
        self.zone = self.create_zone()

    def test_create_recordset(self):
        # Prepare a RecordSet fixture
        fixture = self.get_recordset_fixture(self.zone['name'], fixture=0)
        response = self.client.post_json(
            '/zones/%s/recordsets' % self.zone['id'], fixture,
            headers={'X-Test-Role': 'member'})

        # Check the headers are what we expect
        self.assertEqual(201, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIn('created_at', response.json)
        self.assertIsNone(response.json['updated_at'])
        self.assertIn('records', response.json)
        # The action and status are NONE and ACTIVE as there are no records
        self.assertEqual('NONE', response.json['action'])
        self.assertEqual('ACTIVE', response.json['status'])

    def test_create_recordset_with_zero_ttl(self):
        fixture = self.get_recordset_fixture(self.zone['name'], fixture=0)
        fixture['ttl'] = 0
        response = self.client.post_json(
            '/zones/%s/recordsets' % self.zone['id'], fixture,
            headers={'X-Test-Role': 'member'})

        # Check the headers are what we expect
        self.assertEqual(201, response.status_int)
        self.assertEqual('application/json', response.content_type)

    def test_update_recordset_zero_ttl(self):
        # Create a recordset
        recordset = self.create_recordset(self.zone, records=[])

        # Prepare an update body
        body = {'ttl': 0}

        url = '/zones/{}/recordsets/{}'.format(
            recordset['zone_id'], recordset['id']
        )
        response = self.client.put_json(url, body, status=200,
                                        headers={'X-Test-Role': 'member'})

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # The action and status are NONE and ACTIVE as there are no records
        self.assertEqual('NONE', response.json['action'])
        self.assertEqual('ACTIVE', response.json['status'])
        self.assertEqual(0, response.json['ttl'])

        # Check the zone's status is as expected
        response = self.client.get(
            '/zones/{}/recordsets/{}'.format(
                recordset['zone_id'], recordset['id']
            ),
            headers={'Accept': 'application/json',
                     'X-Test-Role': 'member'}
        )
        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        self.assertEqual(0, response.json['ttl'])

    def test_create_recordset_with_records(self):
        # Prepare a RecordSet fixture
        fixture = self.get_recordset_fixture(
            self.zone['name'], 'A', fixture=0, values={'records': [
                '192.0.2.1',
                '192.0.2.2',
            ]}
        )

        response = self.client.post_json(
            '/zones/%s/recordsets' % self.zone['id'], fixture,
            headers={'X-Test-Role': 'member'})

        # Check the headers are what we expect
        self.assertEqual(202, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the values returned are what we expect
        self.assertIn('records', response.json)
        self.assertEqual(2, len(response.json['records']))
        self.assertEqual('CREATE', response.json['action'])
        self.assertEqual('PENDING', response.json['status'])

        # Check the zone's status is as expected
        response = self.client.get('/zones/%s' % self.zone['id'],
                                   headers={'Accept': 'application/json',
                                            'X-Test-Role': 'member'})
        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        self.assertEqual('UPDATE', response.json['action'])
        self.assertEqual('PENDING', response.json['status'])

    def test_create_recordset_with_invalid_name(self):
        # Prepare a RecordSet fixture
        body = self.get_recordset_fixture(
            self.zone['name'],
            'A',
            fixture=0,
            values={
                'name': '`invalid`label`.%s' % self.zone['name'],
                'records': [
                    '192.0.2.1',
                    '192.0.2.2',
                ]
            }
        )

        url = '/zones/%s/recordsets' % self.zone['id']

        # Ensure it fails with a 400
        self._assert_exception(
            'invalid_object', 400, self.client.post_json, url, body,
            headers={'X-Test-Role': 'member'})

    def test_create_recordset_with_name_too_long(self):
        fixture = self.get_recordset_fixture(self.zone['name'], fixture=0)
        fixture['name'] = 'x' * 255 + ".%s" % self.zone['name']
        body = fixture
        url = '/zones/%s/recordsets' % self.zone['id']
        self._assert_exception(
            'invalid_object', 400, self.client.post_json, url, body,
            headers={'X-Test-Role': 'member'})

    def test_create_recordset_with_name_missing(self):
        fixture = self.get_recordset_fixture(self.zone['name'], fixture=0)
        del fixture['name']
        body = fixture
        url = '/zones/%s/recordsets' % self.zone['id']
        self._assert_exception(
            'invalid_object', 400, self.client.post_json, url, body,
            headers={'X-Test-Role': 'member'})

    def test_create_recordset_type_is_missing(self):
        # Prepare a RecordSet fixture
        body = self.get_recordset_fixture(
            self.zone['name'],
            'A',
            fixture=0,
            values={
                'name': 'name.%s' % self.zone['name'],
                'records': [
                    '192.0.2.1',
                    '192.0.2.2',
                ]
            }
        )

        del body['type']

        url = '/zones/%s/recordsets' % self.zone['id']

        # Ensure it fails with a 400
        self._assert_exception(
            'invalid_object', 400, self.client.post_json, url, body,
            headers={'X-Test-Role': 'member'})

    def test_create_recordset_with_invalid_type(self):
        fixture = self.get_recordset_fixture(self.zone['name'], fixture=0)
        fixture['type'] = "ABC"
        body = fixture
        url = '/zones/%s/recordsets' % self.zone['id']
        self._assert_exception(
            'invalid_object', 400, self.client.post_json, url, body,
            headers={'X-Test-Role': 'member'})

    def test_create_recordset_description_too_long(self):
        fixture = self.get_recordset_fixture(self.zone['name'], fixture=0)
        fixture['description'] = "x" * 161
        body = fixture
        url = '/zones/%s/recordsets' % self.zone['id']
        self._assert_exception(
            'invalid_object', 400, self.client.post_json, url, body,
            headers={'X-Test-Role': 'member'})

    def test_create_recordset_with_negative_ttl(self):
        fixture = self.get_recordset_fixture(self.zone['name'], fixture=0)
        fixture['ttl'] = -1
        body = fixture
        url = '/zones/%s/recordsets' % self.zone['id']
        self._assert_exception(
            'invalid_object', 400, self.client.post_json, url, body,
            headers={'X-Test-Role': 'member'})

    def test_create_recordset_with_ttl_greater_than_max(self):
        fixture = self.get_recordset_fixture(self.zone['name'], fixture=0)
        fixture['ttl'] = 2147483648
        body = fixture
        url = '/zones/%s/recordsets' % self.zone['id']
        self._assert_exception(
            'invalid_object', 400, self.client.post_json, url, body,
            headers={'X-Test-Role': 'member'})

    def test_create_recordset_with_invalid_ttl(self):
        fixture = self.get_recordset_fixture(self.zone['name'], fixture=0)
        fixture['ttl'] = ">?!?"
        body = fixture
        url = '/zones/%s/recordsets' % self.zone['id']
        self._assert_exception(
            'invalid_object', 400, self.client.post_json, url, body,
            headers={'X-Test-Role': 'member'})

    def test_create_recordset_invalid_id(self):
        self._assert_invalid_uuid(self.client.post, '/zones/%s/recordsets',
                                  headers={'X-Test-Role': 'member'})

    def test_create_recordset_validation(self):
        # NOTE: The schemas should be tested separatly to the API. So we
        #       don't need to test every variation via the API itself.
        # Fetch a fixture
        fixture = self.get_recordset_fixture(self.zone['name'], fixture=0)

        url = '/zones/%s/recordsets' % self.zone['id']

        # Add a junk field to the body
        fixture['junk'] = 'Junk Field'
        body = fixture

        # Ensure it fails with a 400
        self._assert_exception(
            'invalid_object', 400, self.client.post_json, url, body,
            headers={'X-Test-Role': 'member'})

    @patch.object(central_service.Service, 'create_recordset',
                  side_effect=messaging.MessagingTimeout())
    def test_create_recordset_timeout(self, _):
        fixture = self.get_recordset_fixture(self.zone['name'], fixture=0)

        body = fixture

        url = '/zones/%s/recordsets' % self.zone['id']

        self._assert_exception('timeout', 504, self.client.post_json, url,
                               body, headers={'X-Test-Role': 'member'})

    @patch.object(central_service.Service, 'create_recordset',
                  side_effect=exceptions.DuplicateRecordSet())
    def test_create_recordset_duplicate(self, _):
        fixture = self.get_recordset_fixture(self.zone['name'], fixture=0)

        body = fixture

        url = '/zones/%s/recordsets' % self.zone['id']

        self._assert_exception('duplicate_recordset', 409,
                               self.client.post_json, url, body,
                               headers={'X-Test-Role': 'member'})

    def test_create_recordset_invalid_zone(self):
        fixture = self.get_recordset_fixture(self.zone['name'], fixture=0)

        body = fixture

        url = '/zones/ba751950-6193-11e3-949a-0800200c9a66/recordsets'

        self._assert_exception('zone_not_found', 404, self.client.post_json,
                               url, body, headers={'X-Test-Role': 'member'})

    def test_recordsets_invalid_url(self):
        url = '/zones/recordsets'
        self._assert_exception('not_found', 404, self.client.get, url,
                               headers={'X-Test-Role': 'member'})
        self._assert_exception('not_found', 404, self.client.post_json, url,
                               headers={'X-Test-Role': 'member'})

        # Pecan returns a 405 for Patch and delete operations
        response = self.client.patch_json(url, status=405,
                                          headers={'X-Test-Role': 'member'})
        self.assertEqual(405, response.status_int)

        response = self.client.delete(url, status=405,
                                      headers={'X-Test-Role': 'member'})
        self.assertEqual(405, response.status_int)

    def test_get_recordsets(self):
        url = '/zones/%s/recordsets' % self.zone['id']

        response = self.client.get(url, headers={'X-Test-Role': 'member'})

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('recordsets', response.json)
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # We should start with 2 pending recordsets for SOA & NS
        # pending because pool manager is not active
        self.assertEqual(2, len(response.json['recordsets']))
        for recordset in response.json['recordsets']:
            self.assertEqual('CREATE', recordset['action'])
            self.assertEqual('PENDING', recordset['status'])

        soa = self.central_service.find_recordset(
            self.admin_context, criterion={'zone_id': self.zone['id'],
                                           'type': 'SOA'})
        ns = self.central_service.find_recordset(
            self.admin_context, criterion={'zone_id': self.zone['id'],
                                           'type': 'NS'})
        data = [self.create_recordset(self.zone,
                                      name='x-{}.{}'.format(i,
                                                            self.zone['name']))
                for i in range(0, 10)]
        data.insert(0, ns)
        data.insert(0, soa)

        self._assert_paging(data, url, key='recordsets')

        self._assert_invalid_paging(data, url, key='recordsets')

    def test_get_recordsets_filter(self):
        # Add recordsets for testing
        fixtures = [
            self.get_recordset_fixture(
                self.zone['name'], 'A', fixture=0, values={
                    'records': ['192.0.2.1', '192.0.2.2'],
                    'description': 'Tester1',
                    'ttl': 3600
                }
            ),
            self.get_recordset_fixture(
                self.zone['name'], 'A', fixture=1, values={
                    'records': ['192.0.2.1'],
                    'description': 'Tester2',
                    'ttl': 4000
                }
            )
        ]

        for fixture in fixtures:
            response = self.client.post_json(
                '/zones/%s/recordsets' % self.zone['id'],
                fixture, headers={'X-Test-Role': 'member'})

        get_urls = [
            # Filter by Name
            '/zones/{}/recordsets?name={}'.format(
                self.zone['id'], fixtures[0]['name']),
            '/zones/{}/recordsets?data=192.0.2.1&name={}'.format(
                self.zone['id'], fixtures[1]['name']),

            # Filter by Type
            '/zones/%s/recordsets?type=A' % self.zone['id'],
            '/zones/{}/recordsets?type=A&name={}'.format(
                self.zone['id'], fixtures[0]['name']),

            # Filter by TTL
            '/zones/%s/recordsets?ttl=3600' % self.zone['id'],

            # Filter by Data
            '/zones/%s/recordsets?data=192.0.2.1' % self.zone['id'],
            '/zones/%s/recordsets?data=192.0.2.2' % self.zone['id'],

            # Filter by Description
            '/zones/%s/recordsets?description=Tester1' % self.zone['id']
        ]

        correct_results = [1, 1, 2, 1, 1, 2, 1, 1]

        for get_url, correct_result in zip(get_urls, correct_results):
            response = self.client.get(get_url,
                                       headers={'X-Test-Role': 'member'})

            # Check the headers are what we expect
            self.assertEqual(200, response.status_int)
            self.assertEqual('application/json', response.content_type)

            # Check that the correct number of recordsets match
            self.assertEqual(correct_result, len(response.json['recordsets']))

    def test_get_recordsets_invalid_id(self):
        self._assert_invalid_uuid(self.client.get, '/zones/%s/recordsets')

    @patch.object(central_service.Service, 'get_zone',
                  side_effect=messaging.MessagingTimeout())
    def test_get_recordsets_timeout(self, _):
        url = '/zones/ba751950-6193-11e3-949a-0800200c9a66/recordsets'

        self._assert_exception('timeout', 504, self.client.get, url,
                               headers={'X-Test-Role': 'member'})

    def test_get_deleted_recordsets(self):
        zone = self.create_zone(fixture=1)
        recordset = self.create_recordset(zone, records=[])
        url = '/zones/%s/recordsets' % zone['id']

        response = self.client.get(url, headers={'X-Test-Role': 'member'})

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)

        # Now delete the recordset
        url = '/zones/{}/recordsets/{}'.format(zone['id'], recordset.id)
        self.client.delete(url, status=202, headers={'X-Test-Role': 'member'})

        # Simulate the zone having been deleted on the backend
        self.central_service.update_status(
            self.admin_context, zone['id'], 'SUCCESS', timeutils.utcnow_ts(),
            'DELETE'
        )

        # Try to get the record and ensure that we get a
        # recordset_not_found error
        self._assert_exception('recordset_not_found', 404, self.client.get,
                               url, headers={'X-Test-Role': 'member'})

    def test_get_deleted_recordset_after_deleting_zone(self):
        zone = self.create_zone(fixture=1)
        self.create_recordset(zone)
        url = '/zones/%s/recordsets' % zone['id']

        response = self.client.get(url, headers={'X-Test-Role': 'member'})

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)

        # Now delete the zone
        self.client.delete('/zones/%s' % zone['id'], status=202,
                           headers={'X-Test-Role': 'member'})

        # Simulate the zone having been deleted on the backend
        zone_serial = self.central_service.get_zone(
            self.admin_context, zone['id']).serial
        self.central_service.update_status(
            self.admin_context, zone['id'], 'SUCCESS', zone_serial, 'DELETE'
        )

        # Try to get the record and ensure that we get a
        # zone_not_found error
        self._assert_exception('zone_not_found', 404, self.client.get, url,
                               headers={'X-Test-Role': 'member'})

    def test_get_recordset(self):
        # Create a recordset
        recordset = self.create_recordset(self.zone, records=[])

        url = '/zones/{}/recordsets/{}'.format(
            self.zone['id'], recordset['id']
        )
        response = self.client.get(url, headers={'X-Test-Role': 'member'})

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIn('created_at', response.json)
        self.assertIsNone(response.json['updated_at'])
        self.assertEqual(recordset['name'], response.json['name'])
        self.assertEqual(recordset['type'], response.json['type'])
        # The action and status are NONE and ACTIVE as there are no records
        self.assertEqual('NONE', response.json['action'])
        self.assertEqual('ACTIVE', response.json['status'])

    def test_get_recordset_invalid_id(self):
        self._assert_invalid_uuid(self.client.get, '/zones/%s/recordsets/%s',
                                  headers={'X-Test-Role': 'member'})

    @patch.object(central_service.Service, 'get_recordset',
                  side_effect=messaging.MessagingTimeout())
    def test_get_recordset_timeout(self, _):
        url = '/zones/%s/recordsets/ba751950-6193-11e3-949a-0800200c9a66' % (
            self.zone['id'])

        self._assert_exception('timeout', 504, self.client.get, url,
                               headers={'Accept': 'application/json',
                                        'X-Test-Role': 'member'})

    @patch.object(central_service.Service, 'get_recordset',
                  side_effect=exceptions.RecordSetNotFound())
    def test_get_recordset_missing(self, _):
        url = '/zones/%s/recordsets/ba751950-6193-11e3-949a-0800200c9a66' % (
            self.zone['id'])

        self._assert_exception('recordset_not_found', 404,
                               self.client.get, url,
                               headers={'Accept': 'application/json',
                                        'X-Test-Role': 'member'})

    def test_update_recordset(self):
        # Create a recordset
        recordset = self.create_recordset(self.zone, records=[])

        # Prepare an update body
        body = {'description': 'Tester'}

        url = '/zones/{}/recordsets/{}'.format(recordset['zone_id'],
                                               recordset['id'])
        response = self.client.put_json(url, body, status=200,
                                        headers={'X-Test-Role': 'member'})

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIsNotNone(response.json['updated_at'])
        self.assertEqual('Tester', response.json['description'])
        # The action and status are NONE and ACTIVE as there are no records
        self.assertEqual('NONE', response.json['action'])
        self.assertEqual('ACTIVE', response.json['status'])

        # Check the zone's status is as expected
        response = self.client.get('/zones/%s' % recordset['zone_id'],
                                   headers={'Accept': 'application/json',
                                            'X-Test-Role': 'member'})
        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        self.assertEqual('UPDATE', response.json['action'])
        self.assertEqual('PENDING', response.json['status'])

    def test_update_recordset_with_record_create(self):
        # Create a recordset
        recordset = self.create_recordset(self.zone, 'A', records=[])

        # The action and status are NONE and ACTIVE as there are no records
        self.assertEqual('NONE', recordset['action'])
        self.assertEqual('ACTIVE', recordset['status'])

        # Prepare an update body
        body = {'description': 'Tester',
                'type': 'A',
                'records': ['192.0.2.1', '192.0.2.2']}

        url = '/zones/{}/recordsets/{}'.format(
            recordset['zone_id'], recordset['id']
        )
        response = self.client.put_json(url, body, status=202,
                                        headers={'X-Test-Role': 'member'})

        # Check the headers are what we expect
        self.assertEqual(202, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the values returned are what we expect
        self.assertIn('records', response.json)
        self.assertEqual(2, len(response.json['records']))
        self.assertEqual({'192.0.2.1', '192.0.2.2'},
                         set(response.json['records']))
        self.assertEqual('UPDATE', response.json['action'])
        self.assertEqual('PENDING', response.json['status'])

        # Check the zone's status is as expected
        response = self.client.get('/zones/%s' % recordset['zone_id'],
                                   headers={'Accept': 'application/json',
                                            'X-Test-Role': 'member'})
        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        self.assertEqual('UPDATE', response.json['action'])
        self.assertEqual('PENDING', response.json['status'])

    def test_update_recordset_with_record_replace(self):
        # Create a recordset with one record
        recordset = self.create_recordset(self.zone, 'A')

        # Prepare an update body
        body = {'description': 'Tester',
                'records': ['192.0.2.201', '192.0.2.202']}

        url = '/zones/{}/recordsets/{}'.format(
            recordset['zone_id'], recordset['id']
        )
        response = self.client.put_json(url, body, status=202,
                                        headers={'X-Test-Role': 'member'})

        # Check the headers are what we expect
        self.assertEqual(202, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the values returned are what we expect
        self.assertIn('records', response.json)
        self.assertEqual(2, len(response.json['records']))
        self.assertEqual({'192.0.2.201', '192.0.2.202'},
                         set(response.json['records']))

        # Check the zone's status is as expected
        response = self.client.get('/zones/%s' % recordset['zone_id'],
                                   headers={'Accept': 'application/json',
                                            'X-Test-Role': 'member'})
        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        self.assertEqual('UPDATE', response.json['action'])
        self.assertEqual('PENDING', response.json['status'])

    def test_create_txt_record(self):
        # See bug #1474012
        new_zone = self.create_zone(name='example.net.')
        recordset = self.create_recordset(new_zone, 'TXT')
        body = {'description': 'Tester', 'records': ['a' * 255]}

        url = '/zones/{}/recordsets/{}'.format(
            recordset['zone_id'], recordset['id']
        )
        self.client.put_json(url, body, status=202,
                             headers={'X-Test-Role': 'member'})

    def test_create_txt_record_too_long(self):
        # See bug #1474012
        new_zone = self.create_zone(name='example.net.')
        recordset = self.create_recordset(new_zone, 'TXT')
        body = {'description': 'Tester', 'records': ['a' * 512]}
        url = '/zones/{}/recordsets/{}'.format(
            recordset['zone_id'], recordset['id']
        )
        self._assert_exception('invalid_object', 400,
                               self.client.put_json, url, body,
                               headers={'X-Test-Role': 'member'})

    def test_create_txt_record_multiple_strings(self):
        # create TXT record with string split in 2
        new_zone = self.create_zone(name='example.net.')
        recordset = self.create_recordset(new_zone, 'TXT')
        record = '"{}" "{}"'.format('a' * 250, 'a' * 250)
        body = {'description': 'Tester', 'records': [record]}
        url = '/zones/{}/recordsets/{}'.format(
            recordset['zone_id'], recordset['id']
        )
        self.client.put_json(url, body, status=202,
                             headers={'X-Test-Role': 'member'})

    def test_update_recordset_with_record_clear(self):
        # Create a recordset with one record
        recordset = self.create_recordset(self.zone, 'A')

        # Prepare an update body
        body = {'description': 'Tester', 'records': []}

        url = '/zones/{}/recordsets/{}'.format(recordset['zone_id'],
                                               recordset['id'])
        response = self.client.put_json(url, body, status=200,
                                        headers={'X-Test-Role': 'member'})

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the values returned are what we expect
        self.assertIn('records', response.json)
        self.assertEqual(0, len(response.json['records']))

        # Check the zone's status is as expected
        response = self.client.get('/zones/%s' % recordset['zone_id'],
                                   headers={'Accept': 'application/json',
                                            'X-Test-Role': 'member'})
        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        self.assertEqual('UPDATE', response.json['action'])
        self.assertEqual('PENDING', response.json['status'])

    def test_update_recordset_invalid_id(self):
        self._assert_invalid_uuid(
            self.client.put_json, '/zones/%s/recordsets/%s',
            headers={'X-Test-Role': 'member'})

    def test_update_recordset_validation(self):
        # NOTE: The schemas should be tested separatly to the API. So we
        #       don't need to test every variation via the API itself.
        # Create a zone
        recordset = self.create_recordset(self.zone)

        # Prepare an update body with junk in the wrapper
        body = {'description': 'Tester',
                'records': ['192.3.3.17'],
                'junk': 'Junk Field'}

        # Ensure it fails with a 400
        url = '/zones/{}/recordsets/{}'.format(recordset['zone_id'],
                                               recordset['id'])

        self._assert_exception('invalid_object', 400, self.client.put_json,
                               url, body, headers={'X-Test-Role': 'member'})

        # Prepare an update body with junk in the body
        body = {'description': 'Tester', 'junk': 'Junk Field'}

        # Ensure it fails with a 400
        self._assert_exception('invalid_object', 400, self.client.put_json,
                               url, body, headers={'X-Test-Role': 'member'})

    @patch.object(central_service.Service, 'get_recordset',
                  side_effect=exceptions.DuplicateRecordSet())
    def test_update_recordset_duplicate(self, _):
        # Prepare an update body
        body = {'description': 'Tester'}

        # Ensure it fails with a 409
        url = ('/zones/%s/recordsets/ba751950-6193-11e3-949a-0800200c9a66'
               % (self.zone['id']))

        self._assert_exception('duplicate_recordset', 409,
                               self.client.put_json, url, body,
                               headers={'X-Test-Role': 'member'})

    @patch.object(central_service.Service, 'get_recordset',
                  side_effect=messaging.MessagingTimeout())
    def test_update_recordset_timeout(self, _):
        # Prepare an update body
        body = {'description': 'Tester'}

        # Ensure it fails with a 504
        url = ('/zones/%s/recordsets/ba751950-6193-11e3-949a-0800200c9a66'
               % (self.zone['id']))

        self._assert_exception('timeout', 504, self.client.put_json, url,
                               body, headers={'X-Test-Role': 'member'})

    @patch.object(central_service.Service, 'get_recordset',
                  side_effect=exceptions.RecordSetNotFound())
    def test_update_recordset_missing(self, _):
        # Prepare an update body
        body = {'description': 'Tester'}

        # Ensure it fails with a 404
        url = ('/zones/%s/recordsets/ba751950-6193-11e3-949a-0800200c9a66'
               % (self.zone['id']))

        self._assert_exception('recordset_not_found', 404,
                               self.client.put_json, url, body,
                               headers={'X-Test-Role': 'member'})

    def test_update_recordset_invalid_ttl(self):
        recordset = self.create_recordset(self.zone)
        body = {'ttl': '>?!@'}
        url = '/zones/{}/recordsets/{}'.format(recordset['zone_id'],
                                               recordset['id'])
        self._assert_exception('invalid_object', 400,
                               self.client.put_json, url, body,
                               headers={'X-Test-Role': 'member'})

    def test_update_recordset_negative_ttl(self):
        recordset = self.create_recordset(self.zone)
        body = {'ttl': -1}
        url = '/zones/{}/recordsets/{}'.format(recordset['zone_id'],
                                               recordset['id'])
        self._assert_exception('invalid_object', 400,
                               self.client.put_json, url, body,
                               headers={'X-Test-Role': 'member'})

    def test_update_recordset_ttl_greater_than_max(self):
        recordset = self.create_recordset(self.zone)
        body = {'ttl': 2174483648}
        url = '/zones/{}/recordsets/{}'.format(recordset['zone_id'],
                                               recordset['id'])
        self._assert_exception('invalid_object', 400,
                               self.client.put_json, url, body,
                               headers={'X-Test-Role': 'member'})

    def test_update_recordset_description_too_long(self):
        recordset = self.create_recordset(self.zone)
        body = {'description': 'x' * 161}
        url = '/zones/{}/recordsets/{}'.format(recordset['zone_id'],
                                               recordset['id'])
        self._assert_exception('invalid_object', 400,
                               self.client.put_json, url, body,
                               headers={'X-Test-Role': 'member'})

    def test_delete_recordset(self):
        recordset = self.create_recordset(self.zone, records=[])

        url = '/zones/{}/recordsets/{}'.format(recordset['zone_id'],
                                               recordset['id'])
        response = self.client.delete(url, status=202,
                                      headers={'X-Test-Role': 'member'})

        self.assertEqual('application/json', response.content_type)
        # Currently recordset does not have a status field. As there are no
        # records, the recordset action/status show up as 'NONE', 'ACTIVE'
        self.assertEqual('NONE', response.json['action'])
        self.assertEqual('ACTIVE', response.json['status'])

        # Check the zone's status is as expected
        response = self.client.get('/zones/%s' % recordset['zone_id'],
                                   headers={'Accept': 'application/json',
                                            'X-Test-Role': 'member'})
        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        self.assertEqual('UPDATE', response.json['action'])
        self.assertEqual('PENDING', response.json['status'])

    def test_delete_recordset_with_records(self):
        # Create a recordset with one record
        recordset = self.create_recordset(self.zone, 'A')

        url = '/zones/{}/recordsets/{}'.format(recordset['zone_id'],
                                               recordset['id'])
        response = self.client.delete(url, status=202,
                                      headers={'X-Test-Role': 'member'})

        self.assertEqual('application/json', response.content_type)
        self.assertEqual('DELETE', response.json['action'])
        self.assertEqual('PENDING', response.json['status'])

        # Check the zone's status is as expected
        response = self.client.get('/zones/%s' % recordset['zone_id'],
                                   headers={'Accept': 'application/json',
                                            'X-Test-Role': 'member'})
        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        self.assertEqual('UPDATE', response.json['action'])
        self.assertEqual('PENDING', response.json['status'])

    @patch.object(central_service.Service, 'delete_recordset',
                  side_effect=exceptions.RecordSetNotFound())
    def test_delete_recordset_missing(self, _):
        url = ('/zones/%s/recordsets/ba751950-6193-11e3-949a-0800200c9a66'
               % (self.zone['id']))

        self._assert_exception('recordset_not_found', 404,
                               self.client.delete, url,
                               headers={'X-Test-Role': 'member'})

    def test_delete_recordset_invalid_id(self):
        self._assert_invalid_uuid(
            self.client.delete, '/zones/%s/recordsets/%s',
            headers={'X-Test-Role': 'member'})

    def test_metadata_exists(self):
        url = '/zones/%s/recordsets' % self.zone['id']

        response = self.client.get(url, headers={'X-Test-Role': 'member'})

        # Make sure the fields exist
        self.assertIn('metadata', response.json)
        self.assertIn('total_count', response.json['metadata'])

    def test_total_count(self):
        url = '/zones/%s/recordsets' % self.zone['id']

        response = self.client.get(url, headers={'X-Test-Role': 'member'})

        # The NS and SOA records are there by default
        self.assertEqual(2, response.json['metadata']['total_count'])

        # Create a recordset
        fixture = self.get_recordset_fixture(self.zone['name'], fixture=0)
        response = self.client.post_json(
            '/zones/%s/recordsets' % self.zone['id'], fixture,
            headers={'X-Test-Role': 'member'})

        response = self.client.get(url, headers={'X-Test-Role': 'member'})

        # Make sure total_count picked up the change
        self.assertEqual(3, response.json['metadata']['total_count'])

    def test_total_count_filtered_by_data(self):
        # Closes bug 1447325
        url = '/zones/%s/recordsets' % self.zone['id']

        # Create a recordset
        fixture = self.get_recordset_fixture(self.zone['name'], fixture=0)
        response = self.client.post_json(
            '/zones/%s/recordsets' % self.zone['id'], fixture,
            headers={'X-Test-Role': 'member'})

        response = self.client.get(url, headers={'X-Test-Role': 'member'})

        # Make sure total_count picked up the change
        self.assertEqual(3, response.json['metadata']['total_count'])

        url = '/zones/%s/recordsets?data=nyan' % self.zone['id']
        response = self.client.get(url, headers={'X-Test-Role': 'member'})
        self.assertEqual(0, response.json['metadata']['total_count'])

        url = '/zones/%s/recordsets?data=ns1.example.org.' % self.zone['id']
        response = self.client.get(url, headers={'X-Test-Role': 'member'})
        self.assertEqual(1, response.json['metadata']['total_count'])

        # Test paging
        new_zone = self.create_zone(name='example.net.')
        record_1 = objects.Record.from_dict({'data': 'nyan'})
        self.create_recordset(
            new_zone, 'A',
            records=[record_1],
        )
        record_2 = objects.Record.from_dict({'data': 'nyan'})
        self.create_recordset(
            new_zone, 'CNAME',
            records=[record_2],
        )

        # Even with paging enabled, total_count is still the total number of
        # recordsets matching the "data" filter
        url = '/zones/%s/recordsets?limit=1&data=nyan' % new_zone.id
        response = self.client.get(url, headers={'X-Test-Role': 'member'})
        self.assertEqual(2, response.json['metadata']['total_count'])

    def test_total_count_pagination(self):
        # Create two recordsets
        fixture = self.get_recordset_fixture(self.zone['name'], fixture=0)
        response = self.client.post_json(
            '/zones/%s/recordsets' % self.zone['id'], fixture,
            headers={'X-Test-Role': 'member'})

        fixture = self.get_recordset_fixture(self.zone['name'], fixture=1)
        response = self.client.post_json(
            '/zones/%s/recordsets' % self.zone['id'], fixture,
            headers={'X-Test-Role': 'member'})

        # Paginate the recordsets to two, there should be four now
        url = '/zones/%s/recordsets?limit=2' % self.zone['id']

        response = self.client.get(url, headers={'X-Test-Role': 'member'})

        # There are two recordsets returned
        self.assertEqual(2, len(response.json['recordsets']))

        # But there should be four in total (NS/SOA + the created)
        self.assertEqual(4, response.json['metadata']['total_count'])

    # Secondary Zones specific tests
    def test_get_secondary_zone_recordset(self):
        fixture = self.get_zone_fixture('SECONDARY', 1)
        fixture['email'] = 'root@example.com'
        secondary = self.create_zone(**fixture)

        # Create a recordset
        recordset = self.create_recordset(secondary)

        url = '/zones/{}/recordsets/{}'.format(
            secondary['id'], recordset['id'])
        response = self.client.get(url, headers={'X-Test-Role': 'member'})

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIn('created_at', response.json)
        self.assertIsNone(response.json['updated_at'])
        self.assertEqual(recordset['name'], response.json['name'])
        self.assertEqual(recordset['type'], response.json['type'])

    def test_get_secondary_zone_recordsets(self):
        fixture = self.get_zone_fixture('SECONDARY', 1)
        fixture['email'] = 'foo@bar.io'
        secondary = self.create_zone(**fixture)

        url = '/zones/%s/recordsets' % secondary['id']

        response = self.client.get(url, headers={'X-Test-Role': 'member'})

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('recordsets', response.json)
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # We should start with 2 recordsets for SOA & NS
        self.assertEqual(1, len(response.json['recordsets']))

        soa = self.central_service.find_recordset(
            self.admin_context, criterion={'zone_id': secondary['id'],
                                           'type': 'SOA'})
        data = [self.create_recordset(secondary,
                                      name='x-{}.{}'.format(i,
                                                            secondary['name']))
                for i in range(0, 10)]
        data.insert(0, soa)

        self._assert_paging(data, url, key='recordsets')

        self._assert_invalid_paging(data, url, key='recordsets')

    def test_create_secondary_zone_recordset(self):
        fixture = self.get_zone_fixture('SECONDARY', 1)
        fixture['email'] = 'foo@bar.io'
        secondary = self.create_zone(**fixture)

        fixture = self.get_recordset_fixture(secondary['name'], fixture=0)

        url = '/zones/%s/recordsets' % secondary['id']
        self._assert_exception('forbidden', 403, self.client.post_json, url,
                               fixture, headers={'X-Test-Role': 'member'})

    def test_update_secondary_zone_recordset(self):
        fixture = self.get_zone_fixture('SECONDARY', 1)
        fixture['email'] = 'foo@bar.io'
        secondary = self.create_zone(**fixture)

        # Set the context so that we can create a RRSet
        recordset = self.create_recordset(secondary)

        url = '/zones/{}/recordsets/{}'.format(recordset['zone_id'],
                                               recordset['id'])

        self._assert_exception('forbidden', 403, self.client.put_json, url,
                               {'ttl': 100}, headers={'X-Test-Role': 'member'})

    def test_delete_secondary_zone_recordset(self):
        fixture = self.get_zone_fixture('SECONDARY', 1)
        fixture['email'] = 'foo@bar.io'
        secondary = self.create_zone(**fixture)

        # Set the context so that we can create a RRSet
        recordset = self.create_recordset(secondary)

        url = '/zones/{}/recordsets/{}'.format(recordset['zone_id'],
                                               recordset['id'])

        self._assert_exception('forbidden', 403, self.client.delete, url,
                               headers={'X-Test-Role': 'member'})

    def test_no_create_rs_deleting_zone(self):
        # Prepare a create
        fixture = self.get_recordset_fixture(self.zone['name'], fixture=0)
        body = fixture

        self.client.delete('/zones/%s' % self.zone['id'], status=202,
                           headers={'X-Test-Role': 'member'})
        self._assert_exception('bad_request', 400, self.client.post_json,
                               '/zones/%s/recordsets' % self.zone['id'],
                               body, headers={'X-Test-Role': 'member'})

    def test_no_update_rs_deleting_zone(self):
        # Create a recordset
        recordset = self.create_recordset(self.zone)

        # Prepare an update body
        body = {'description': 'Tester'}
        url = '/zones/{}/recordsets/{}'.format(recordset['zone_id'],
                                               recordset['id'])
        self.client.delete('/zones/%s' % self.zone['id'], status=202,
                           headers={'X-Test-Role': 'member'})
        self._assert_exception('bad_request', 400, self.client.put_json, url,
                               body, headers={'X-Test-Role': 'member'})

    def test_no_delete_rs_deleting_zone(self):
        # Create a recordset
        recordset = self.create_recordset(self.zone)

        url = '/zones/{}/recordsets/{}'.format(recordset['zone_id'],
                                               recordset['id'])

        self.client.delete('/zones/%s' % self.zone['id'], status=202,
                           headers={'X-Test-Role': 'member'})
        self._assert_exception('bad_request', 400, self.client.delete, url,
                               headers={'X-Test-Role': 'member'})

    def test_invalid_recordset_filter(self):
        invalid_url = '/zones/%s/recordsets?action=NONE' % self.zone['id']
        self._assert_exception(
            'bad_request', 400, self.client.get, invalid_url,
            headers={'X-Test-Role': 'member'})
