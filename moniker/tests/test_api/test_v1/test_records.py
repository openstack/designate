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
from moniker.openstack.common import log as logging
from moniker.openstack.common.rpc import common as rpc_common
from moniker.central import service as central_service
from moniker.tests.test_api.test_v1 import ApiV1Test


LOG = logging.getLogger(__name__)


class ApiV1RecordsTest(ApiV1Test):
    __test__ = True

    def setUp(self):
        super(ApiV1RecordsTest, self).setUp()

        self.domain = self.create_domain()

    def test_create_record(self):
        fixture = self.get_record_fixture(self.domain['name'], 0)

        # Create a record
        response = self.post('domains/%s/records' % self.domain['id'],
                             data=fixture)

        self.assertIn('id', response.json)
        self.assertIn('name', response.json)
        self.assertEqual(response.json['name'], fixture['name'])

    @patch.object(central_service.Service, 'create_record',
                  side_effect=rpc_common.Timeout())
    def test_create_domain_timeout(self, _):
        fixture = self.get_record_fixture(self.domain['name'], 0)

        # Create a record
        self.post('domains/%s/records' % self.domain['id'], data=fixture,
                  status_code=504)

    def test_create_wildcard_record(self):
        # Prepare a record
        fixture = self.get_record_fixture(self.domain['name'], 0)
        fixture['name'] = '*.%s' % fixture['name']

        # Create a record
        response = self.post('domains/%s/records' % self.domain['id'],
                             data=fixture)

        self.assertIn('id', response.json)
        self.assertIn('name', response.json)
        self.assertEqual(response.json['name'], fixture['name'])

    def test_create_invalid_record_name(self):
        # Prepare a record
        fixture = self.get_record_fixture(self.domain['name'], 0)

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
            response = self.post('domains/%s/records' % self.domain['id'],
                                 data=fixture, status_code=400)

            self.assertNotIn('id', response.json)

    def test_get_records(self):
        response = self.get('domains/%s/records' % self.domain['id'])

        self.assertIn('records', response.json)
        self.assertEqual(0, len(response.json['records']))

        # Create a record
        self.create_record(self.domain)

        response = self.get('domains/%s/records' % self.domain['id'])

        self.assertIn('records', response.json)
        self.assertEqual(1, len(response.json['records']))

        # Create a second record
        self.create_record(self.domain, fixture=1)

        response = self.get('domains/%s/records' % self.domain['id'])

        self.assertIn('records', response.json)
        self.assertEqual(2, len(response.json['records']))

    @patch.object(central_service.Service, 'get_records',
                  side_effect=rpc_common.Timeout())
    def test_get_records_timeout(self, _):
        self.get('domains/%s/records' % self.domain['id'],
                 status_code=504)

    def test_get_record(self):
        # Create a record
        record = self.create_record(self.domain)

        response = self.get('domains/%s/records/%s' % (self.domain['id'],
                                                       record['id']))

        self.assertIn('id', response.json)
        self.assertEqual(response.json['id'], record['id'])

    def test_update_record(self):
        # Create a record
        record = self.create_record(self.domain)

        data = {'name': 'test.example.org.'}

        response = self.put('domains/%s/records/%s' % (self.domain['id'],
                                                       record['id']),
                            data=data)

        self.assertIn('id', response.json)
        self.assertEqual(response.json['id'], record['id'])

        self.assertIn('name', response.json)
        self.assertEqual(response.json['name'], 'test.example.org.')

    @patch.object(central_service.Service, 'update_record',
                  side_effect=rpc_common.Timeout())
    def test_update_record_timeout(self, _):
        # Create a record
        record = self.create_record(self.domain)

        data = {'name': 'test.example.org.'}

        self.put('domains/%s/records/%s' % (self.domain['id'], record['id']),
                 data=data, status_code=504)

    def test_delete_record(self):
        # Create a record
        record = self.create_record(self.domain)

        self.delete('domains/%s/records/%s' % (self.domain['id'],
                                               record['id']))

        # Esnure we can no longer fetch the record
        self.get('domains/%s/records/%s' % (self.domain['id'],
                                            record['id']),
                 status_code=404)

    @patch.object(central_service.Service, 'delete_record',
                  side_effect=rpc_common.Timeout())
    def test_delete_record_timeout(self, _):
        # Create a record
        record = self.create_record(self.domain)

        self.delete('domains/%s/records/%s' % (self.domain['id'],
                                               record['id']),
                    status_code=504)
