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
from moniker.openstack.common import log as logging
from moniker.tests.test_api.test_v1 import ApiV1Test


LOG = logging.getLogger(__name__)


class ApiV1DomainsTest(ApiV1Test):
    __test__ = True

    def test_create_domain(self):
        # Create a domain
        fixture = self.get_domain_fixture(0)

        response = self.post('domains', data=fixture)

        self.assertIn('id', response.json)
        self.assertIn('name', response.json)
        self.assertEqual(response.json['name'], fixture['name'])

    def test_get_domains(self):
        response = self.get('domains')

        self.assertIn('domains', response.json)
        self.assertEqual(0, len(response.json['domains']))

        # Create a domain
        self.create_domain()

        response = self.get('domains')

        self.assertIn('domains', response.json)
        self.assertEqual(1, len(response.json['domains']))

        # Create a second domain
        self.create_domain(fixture=1)

        response = self.get('domains')

        self.assertIn('domains', response.json)
        self.assertEqual(2, len(response.json['domains']))

    def test_get_domain(self):
        # Create a domain
        domain = self.create_domain()

        response = self.get('domains/%s' % domain['id'])

        self.assertIn('id', response.json)
        self.assertEqual(response.json['id'], domain['id'])

    def test_update_domain(self):
        # Create a domain
        domain = self.create_domain()

        data = {'name': 'test.org.'}

        response = self.put('domains/%s' % domain['id'], data=data)

        self.assertIn('id', response.json)
        self.assertEqual(response.json['id'], domain['id'])

        self.assertIn('name', response.json)
        self.assertEqual(response.json['name'], 'test.org.')

    def test_delete_domain(self):
        # Create a domain
        domain = self.create_domain()

        self.delete('domains/%s' % domain['id'])

        # Esnure we can no longer fetch the domain
        self.get('domains/%s' % domain['id'], status_code=404)
