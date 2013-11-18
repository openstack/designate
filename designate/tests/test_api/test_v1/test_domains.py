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
from designate.openstack.common import log as logging
from designate.openstack.common.rpc import common as rpc_common
from designate import exceptions
from designate.central import service as central_service
from designate.tests.test_api.test_v1 import ApiV1Test


LOG = logging.getLogger(__name__)


class ApiV1DomainsTest(ApiV1Test):
    def test_create_domain(self):
        # Create a server
        self.create_server()

        # Create a domain
        fixture = self.get_domain_fixture(0)

        response = self.post('domains', data=fixture)

        self.assertIn('id', response.json)
        self.assertIn('name', response.json)
        self.assertEqual(response.json['name'], fixture['name'])

    @patch.object(central_service.Service, 'create_domain')
    def test_create_domain_trailing_slash(self, mock):
        # Create a server
        self.create_server()
        self.post('domains/', data=self.get_domain_fixture(0))

        # verify that the central service is called
        self.assertTrue(mock.called)

    def test_create_domain_junk(self):
        # Create a server
        self.create_server()

        # Create a domain
        fixture = self.get_domain_fixture(0)

        # Add a junk property
        fixture['junk'] = 'Junk Field'

        # Ensure it fails with a 400
        self.post('domains', data=fixture, status_code=400)

    def test_create_domain_no_servers(self):
        # Create a domain
        fixture = self.get_domain_fixture(0)

        self.post('domains', data=fixture, status_code=500)

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

    def test_create_domain_null_ttl(self):
        # Create a domain
        fixture = self.get_domain_fixture(0)
        fixture['ttl'] = None
        self.post('domains', data=fixture, status_code=400)

    def test_create_domain_negative_ttl(self):
        # Create a domain
        fixture = self.get_domain_fixture(0)
        fixture['ttl'] = -1
        self.post('domains', data=fixture, status_code=400)

    def test_create_domain_utf_description(self):
        # Create a server
        self.create_server()

        # Create a domain
        fixture = self.get_domain_fixture(0)

        #Give it a UTF-8 filled description
        fixture['description'] = "utf-8:2H₂+O₂⇌2H₂O,R=4.7kΩ,⌀200mm∮E⋅da=Q,n" \
                                 ",∑f(i)=∏g(i),∀x∈ℝ:⌈x⌉"
        #Create the domain, ensuring it suceeds, thus UTF-8 is supported
        self.post('domains', data=fixture)

    def test_create_domain_description_too_long(self):
        # Create a server
        self.create_server()

        # Create a domain
        fixture = self.get_domain_fixture(0)
        fixture['description'] = "x" * 161

        #Create the domain, ensuring it fails with a 400
        self.post('domains', data=fixture, status_code=400)

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

    def test_create_invalid_email(self):
        # Prepare a domain
        fixture = self.get_domain_fixture(0)

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

    @patch.object(central_service.Service, 'find_domains')
    def test_get_domains_trailing_slash(self, mock):
        self.get('domains/')

        # verify that the central service is called
        self.assertTrue(mock.called)

    @patch.object(central_service.Service, 'find_domains',
                  side_effect=rpc_common.Timeout())
    def test_get_domains_timeout(self, _):
        self.get('domains', status_code=504)

    def test_get_domain(self):
        # Create a domain
        domain = self.create_domain()

        response = self.get('domains/%s' % domain['id'])

        self.assertIn('id', response.json)
        self.assertEqual(response.json['id'], domain['id'])

    @patch.object(central_service.Service, 'get_domain')
    def test_get_domain_trailing_slash(self, mock):
        # Create a domain
        domain = self.create_domain()

        self.get('domains/%s/' % domain['id'])

        # verify that the central service is called
        self.assertTrue(mock.called)

    @patch.object(central_service.Service, 'get_domain',
                  side_effect=rpc_common.Timeout())
    def test_get_domain_timeout(self, _):
        # Create a domain
        domain = self.create_domain()

        self.get('domains/%s' % domain['id'], status_code=504)

    def test_get_domain_missing(self):
        self.get('domains/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980',
                 status_code=404)

    def test_get_domain_invalid_id(self):
        # The letter "G" is not valid in a UUID
        self.get('domains/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff9GG',
                 status_code=404)

        self.get('domains/2fdadfb1cf964259ac6bbb7b6d2ff980', status_code=404)

    def test_update_domain(self):
        # Create a domain
        domain = self.create_domain()

        data = {'email': 'prefix-%s' % domain['email']}

        response = self.put('domains/%s' % domain['id'], data=data)

        self.assertIn('id', response.json)
        self.assertEqual(response.json['id'], domain['id'])

        self.assertIn('email', response.json)
        self.assertEqual(response.json['email'], 'prefix-%s' % domain['email'])

    @patch.object(central_service.Service, 'update_domain')
    def test_update_domain_trailing_slash(self, mock):
        # Create a domain
        domain = self.create_domain()

        data = {'email': 'prefix-%s' % domain['email']}

        self.put('domains/%s/' % domain['id'], data=data)

        # verify that the central service is called
        self.assertTrue(mock.called)

    def test_update_domain_junk(self):
        # Create a domain
        domain = self.create_domain()

        data = {'email': 'prefix-%s' % domain['email'], 'junk': 'Junk Field'}

        self.put('domains/%s' % domain['id'], data=data, status_code=400)

    def test_update_domain_name_fail(self):
        # Create a domain
        domain = self.create_domain()

        data = {'name': 'renamed.com.'}

        self.put('domains/%s' % domain['id'], data=data, status_code=400)

    def test_update_domain_null_ttl(self):
        # Create a domain
        domain = self.create_domain()

        data = {'ttl': None}

        self.put('domains/%s' % domain['id'], data=data, status_code=400)

    @patch.object(central_service.Service, 'update_domain',
                  side_effect=rpc_common.Timeout())
    def test_update_domain_timeout(self, _):
        # Create a domain
        domain = self.create_domain()

        data = {'email': 'prefix-%s' % domain['email']}

        self.put('domains/%s' % domain['id'], data=data, status_code=504)

    @patch.object(central_service.Service, 'update_domain',
                  side_effect=exceptions.DuplicateDomain())
    def test_update_domain_duplicate(self, _):
        # Create a domain
        domain = self.create_domain()

        data = {'email': 'prefix-%s' % domain['email']}

        self.put('domains/%s' % domain['id'], data=data, status_code=409)

    def test_update_domain_missing(self):
        data = {'email': 'bla@bla.com'}

        self.put('domains/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980', data=data,
                 status_code=404)

    def test_update_domain_invalid_id(self):
        data = {'email': 'bla@bla.com'}

        # The letter "G" is not valid in a UUID
        self.put('domains/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff9GG', data=data,
                 status_code=404)

        self.put('domains/2fdadfb1cf964259ac6bbb7b6d2ff980', data=data,
                 status_code=404)

    def test_delete_domain(self):
        # Create a domain
        domain = self.create_domain()

        self.delete('domains/%s' % domain['id'])

        # Esnure we can no longer fetch the domain
        self.get('domains/%s' % domain['id'], status_code=404)

    @patch.object(central_service.Service, 'delete_domain')
    def test_delete_domain_trailing_slash(self, mock):
        # Create a domain
        domain = self.create_domain()

        self.delete('domains/%s/' % domain['id'])

        # verify that the central service is called
        self.assertTrue(mock.called)

    @patch.object(central_service.Service, 'delete_domain',
                  side_effect=rpc_common.Timeout())
    def test_delete_domain_timeout(self, _):
        # Create a domain
        domain = self.create_domain()

        self.delete('domains/%s' % domain['id'], status_code=504)

    def test_delete_domain_missing(self):
        self.delete('domains/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980',
                    status_code=404)

    def test_delete_domain_invalid_id(self):
        # The letter "G" is not valid in a UUID
        self.delete('domains/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff9GG',
                    status_code=404)

        self.delete('domains/2fdadfb1cf964259ac6bbb7b6d2ff980',
                    status_code=404)
