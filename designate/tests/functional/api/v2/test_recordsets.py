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
from oslo_log import log as logging

from designate.tests.functional.api import v2

LOG = logging.getLogger(__name__)


class ApiV2RecordSetsTest(v2.ApiV2TestCase):
    def setUp(self):
        super().setUp()
        self.zone = self.create_zone()

    def test_get_recordsets_owned_by_project(self):
        response = self.client.get(
            '/recordsets', headers={'X-Test-Role': 'member'}
        )

        self.assertIn('recordsets', response.json)
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        self.assertEqual(2, len(response.json['recordsets']))

        fixture = self.get_recordset_fixture(self.zone['name'], fixture=0)
        response = self.client.post_json(
            '/zones/%s/recordsets' % self.zone['id'], fixture,
            headers={'X-Test-Role': 'member'}
        )

        # Check the headers are what we expect
        self.assertEqual(201, response.status_int)
        self.assertEqual('application/json', response.content_type)

        response = self.client.get(
            '/recordsets', headers={'X-Test-Role': 'member'}
        )

        self.assertIn('recordsets', response.json)
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        self.assertEqual(3, len(response.json['recordsets']))

    def test_get_recordset_redirects(self):
        fixture = self.get_recordset_fixture(self.zone['name'], fixture=0)
        response = self.client.post_json(
            '/zones/%s/recordsets' % self.zone['id'], fixture,
            headers={'X-Test-Role': 'member'}
        )

        # Check the headers are what we expect
        self.assertEqual(201, response.status_int)
        self.assertEqual('application/json', response.content_type)

        url = '/recordsets/%s' % response.json['id']
        response = self.client.get(url, headers={'X-Test-Role': 'member'})
        self.assertEqual(301, response.status_int)
