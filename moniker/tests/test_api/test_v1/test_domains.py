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
from moniker import exceptions
from moniker.central import service as central_service
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

    @patch.object(central_service.Service, 'create_domain',
                  side_effect=rpc_common.Timeout())
    def test_create_domain_timeout(self, _):
        # Create a domain
        fixture = self.get_domain_fixture(0)

        self.post('domains', data=fixture, status_code=504)

    @patch.object(central_service.Service, 'create_domain',
                  side_effect=exceptions.DuplicateDomain())
    def test_create_domain_duplicate(self, _):
        # Create a domain
        fixture = self.get_domain_fixture(0)
        self.post('domains', data=fixture, status_code=409)

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

    @patch.object(central_service.Service, 'get_domains',
                  side_effect=rpc_common.Timeout())
    def test_get_domains_timeout(self, _):
        self.get('domains', status_code=504)

    def test_create_invalid_name(self):
        # Prepare a domain
        fixture = self.get_domain_fixture(0)

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

    # TODO: Failing..
    # def test_create_invalid_email(self):
    #     # Prepare a domain
    #     fixture = self.get_domain_fixture(0)

    #     invalid_emails = [
    #         'org',
    #         'example.org',
    #         'bla.example.org',
    #         'org.',
    #         'example.org.',
    #         'bla.example.org.',
    #     ]

    #     for invalid_email in invalid_emails:
    #         fixture['email'] = invalid_email

    #         # Create a record
    #         response = self.post('domains', data=fixture, status_code=400)

    #         self.assertNotIn('id', response.json)

    def test_get_domain(self):
        # Create a domain
        domain = self.create_domain()

        response = self.get('domains/%s' % domain['id'])

        self.assertIn('id', response.json)
        self.assertEqual(response.json['id'], domain['id'])

    @patch.object(central_service.Service, 'get_domain',
                  side_effect=rpc_common.Timeout())
    def test_get_domain_timeout(self, _):
        # Create a domain
        domain = self.create_domain()

        self.get('domains/%s' % domain['id'], status_code=504)

    def test_get_domain_missing(self):
        self.get('domains/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980',
                 status_code=404)

    def test_update_domain(self):
        # Create a domain
        domain = self.create_domain()

        data = {'name': 'test.org.'}

        response = self.put('domains/%s' % domain['id'], data=data)

        self.assertIn('id', response.json)
        self.assertEqual(response.json['id'], domain['id'])

        self.assertIn('name', response.json)
        self.assertEqual(response.json['name'], 'test.org.')

    @patch.object(central_service.Service, 'update_domain',
                  side_effect=rpc_common.Timeout())
    def test_update_domain_timeout(self, _):
        # Create a domain
        domain = self.create_domain()

        data = {'name': 'test.org.'}

        self.put('domains/%s' % domain['id'], data=data, status_code=504)

    @patch.object(central_service.Service, 'update_domain',
                  side_effect=exceptions.DuplicateDomain())
    def test_update_domain_duplicate(self, _):
        # Create a domain
        domain = self.create_domain()

        data = {'name': 'test.org.'}

        self.put('domains/%s' % domain['id'], data=data, status_code=409)

    def test_update_domain_missing(self):
        data = {'name': 'test.org.'}

        self.put('domains/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980', data=data,
                 status_code=404)

    def test_delete_domain(self):
        # Create a domain
        domain = self.create_domain()

        self.delete('domains/%s' % domain['id'])

        # Esnure we can no longer fetch the domain
        self.get('domains/%s' % domain['id'], status_code=404)

    @patch.object(central_service.Service, 'delete_domain',
                  side_effect=rpc_common.Timeout())
    def test_delete_domain_timeout(self, _):
        # Create a domain
        domain = self.create_domain()

        self.delete('domains/%s' % domain['id'], status_code=504)

    def test_delete_domain_missing(self):
        self.delete('domains/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980',
                    status_code=404)
