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
import random
import testtools
from designate.openstack.common import log as logging
from designate import exceptions
from designate.tests.test_central import CentralTestCase

LOG = logging.getLogger(__name__)


class CentralServiceTest(CentralTestCase):
    def setUp(self):
        super(CentralServiceTest, self).setUp()
        self.central_service = self.start_service('central')

    def test_stop(self):
        # Test stopping the service
        self.central_service.stop()

    def test_is_valid_domain_name(self):
        self.config(max_domain_name_len=10,
                    group='service:central')

        context = self.get_context()

        self.central_service._is_valid_domain_name(context, 'valid.org.')

        with testtools.ExpectedException(exceptions.InvalidDomainName):
            self.central_service._is_valid_domain_name(context, 'example.org.')

        with testtools.ExpectedException(exceptions.InvalidDomainName):
            self.central_service._is_valid_domain_name(context, 'example.tld.')

    def test_is_valid_recordset_name(self):
        self.config(max_recordset_name_len=18,
                    group='service:central')

        context = self.get_context()

        domain = self.create_domain(name='example.org.')

        self.central_service._is_valid_recordset_name(
            context, domain, 'valid.example.org.')

        with testtools.ExpectedException(exceptions.InvalidRecordSetName):
            self.central_service._is_valid_recordset_name(
                context, domain, 'toolong.example.org.')

        with testtools.ExpectedException(exceptions.InvalidRecordSetLocation):
            self.central_service._is_valid_recordset_name(
                context, domain, 'a.example.COM.')

    def test_is_blacklisted_domain_name(self):
        # Create blacklisted zones with specific names
        self.create_blacklist(pattern='example.org.')
        self.create_blacklist(pattern='example.net.')
        self.create_blacklist(pattern='^blacklisted.org.$')
        self.create_blacklist(pattern='com.$')

        # Set the policy to reject the authz
        self.policy({'use_blacklisted_domain': '!'})

        context = self.get_context()

        result = self.central_service._is_blacklisted_domain_name(
            context, 'org.')
        self.assertFalse(result)

        # Subdomains should not be allowed from a blacklisted domain
        result = self.central_service._is_blacklisted_domain_name(
            context, 'www.example.org.')
        self.assertTrue(result)

        result = self.central_service._is_blacklisted_domain_name(
            context, 'example.org.')
        self.assertTrue(result)

        # Check for blacklisted domains containing regexps
        result = self.central_service._is_blacklisted_domain_name(
            context, 'example.net.')
        self.assertTrue(result)

        result = self.central_service._is_blacklisted_domain_name(
            context, 'example.com.')
        self.assertTrue(result)

        result = self.central_service._is_blacklisted_domain_name(
            context, 'blacklisted.org.')
        self.assertTrue(result)

    def test_is_subdomain(self):
        context = self.get_context()

        # Create a domain (using the specified domain name)
        self.create_domain(name='example.org.')

        result = self.central_service._is_subdomain(context, 'org.')
        self.assertFalse(result)

        result = self.central_service._is_subdomain(context,
                                                    'www.example.net.')
        self.assertFalse(result)

        result = self.central_service._is_subdomain(context, 'example.org.')
        self.assertFalse(result)

        result = self.central_service._is_subdomain(context,
                                                    'www.example.org.')
        self.assertTrue(result)

    def test_is_valid_recordset_placement_subdomain(self):
        context = self.get_context()

        # Create a domain (using the specified domain name)
        domain = self.create_domain(name='example.org.')
        sub_domain = self.create_domain(name='sub.example.org.')

        def _fail(domain_, name):
            with testtools.ExpectedException(
                    exceptions.InvalidRecordSetLocation):
                self.central_service._is_valid_recordset_placement_subdomain(
                    context, domain_, name)

        def _ok(domain_, name):
            self.central_service._is_valid_recordset_placement_subdomain(
                context, domain_, name)

        _fail(domain, 'record.sub.example.org.')
        _fail(domain, 'sub.example.org.')
        _ok(domain, 'example.org.')
        _ok(domain, 'record.example.org.')

        _ok(sub_domain, 'record.example.org.')

    # Server Tests
    def test_create_server(self):
        values = dict(
            name='ns1.example.org.'
        )

        # Create a server
        server = self.central_service.create_server(
            self.admin_context, values=values)

        # Ensure all values have been set correctly
        self.assertIsNotNone(server['id'])
        self.assertEqual(server['name'], values['name'])

    def test_find_servers(self):
        # Ensure we have no servers to start with.
        servers = self.central_service.find_servers(self.admin_context)
        self.assertEqual(len(servers), 0)

        # Create a single server (using default values)
        self.create_server()

        # Ensure we can retrieve the newly created server
        servers = self.central_service.find_servers(self.admin_context)
        self.assertEqual(len(servers), 1)
        self.assertEqual(servers[0]['name'], 'ns1.example.org.')

        # Create a second server
        self.create_server(name='ns2.example.org.')

        # Ensure we can retrieve both servers
        servers = self.central_service.find_servers(self.admin_context)
        self.assertEqual(len(servers), 2)
        self.assertEqual(servers[0]['name'], 'ns1.example.org.')
        self.assertEqual(servers[1]['name'], 'ns2.example.org.')

    def test_get_server(self):
        # Create a server
        server_name = 'ns%d.example.org.' % random.randint(10, 1000)
        expected_server = self.create_server(name=server_name)

        # Retrieve it, and ensure it's the same
        server = self.central_service.get_server(
            self.admin_context, expected_server['id'])

        self.assertEqual(server['id'], expected_server['id'])
        self.assertEqual(server['name'], expected_server['name'])

    def test_update_server(self):
        # Create a server
        expected_server = self.create_server()

        # Update the server
        values = dict(name='prefix.%s' % expected_server['name'])
        self.central_service.update_server(
            self.admin_context, expected_server['id'], values=values)

        # Fetch the server again
        server = self.central_service.get_server(
            self.admin_context, expected_server['id'])

        # Ensure the server was updated correctly
        self.assertEqual(server['name'], 'prefix.%s' % expected_server['name'])

    def test_delete_server(self):
        # Create a server
        server = self.create_server()

        # Create a second server
        server2 = self.create_server(fixture=1)

        # Delete one server
        self.central_service.delete_server(self.admin_context, server['id'])

        # Fetch the server again, ensuring an exception is raised
        self.assertRaises(
            exceptions.ServerNotFound,
            self.central_service.get_server,
            self.admin_context, server['id'])

        # Try to delete last remaining server - expect exception
        self.assertRaises(
            exceptions.LastServerDeleteNotAllowed,
            self.central_service.delete_server, self.admin_context,
            server2['id'])

    # TLD Tests
    def test_create_tld(self):
        # Create a TLD with one label
        tld = self.create_tld(fixture=0)

        # Ensure all values have been set correctly
        self.assertIsNotNone(tld['id'])
        self.assertEqual(tld['name'], self.get_tld_fixture(fixture=0)['name'])

        # Create a TLD with more than one label
        tld = self.create_tld(fixture=1)

        # Ensure all values have been set correctly
        self.assertIsNotNone(tld['id'])
        self.assertEqual(tld['name'], self.get_tld_fixture(fixture=1)['name'])

    def test_find_tlds(self):
        # Ensure we have no tlds to start with.
        tlds = self.central_service.find_tlds(self.admin_context)
        self.assertEqual(len(tlds), 0)

        # Create a single tld
        self.create_tld(fixture=0)
        # Ensure we can retrieve the newly created tld
        tlds = self.central_service.find_tlds(self.admin_context)
        self.assertEqual(len(tlds), 1)
        self.assertEqual(tlds[0]['name'],
                         self.get_tld_fixture(fixture=0)['name'])

        # Create a second tld
        self.create_tld(fixture=1)

        # Ensure we can retrieve both tlds
        tlds = self.central_service.find_tlds(self.admin_context)
        self.assertEqual(len(tlds), 2)
        self.assertEqual(tlds[0]['name'],
                         self.get_tld_fixture(fixture=0)['name'])
        self.assertEqual(tlds[1]['name'],
                         self.get_tld_fixture(fixture=1)['name'])

    def test_get_tld(self):
        # Create a tld
        tld_name = 'ns%d.co.uk' % random.randint(10, 1000)
        expected_tld = self.create_tld(name=tld_name)

        # Retrieve it, and ensure it's the same
        tld = self.central_service.get_tld(
            self.admin_context, expected_tld['id'])

        self.assertEqual(tld['id'], expected_tld['id'])
        self.assertEqual(tld['name'], expected_tld['name'])

    def test_update_tld(self):
        # Create a tld
        expected_tld = self.create_tld(fixture=0)

        # Update the tld
        values = dict(name='prefix.%s' % expected_tld['name'])
        self.central_service.update_tld(
            self.admin_context, expected_tld['id'], values=values)

        # Fetch the tld again
        tld = self.central_service.get_tld(
            self.admin_context, expected_tld['id'])

        # Ensure the tld was updated correctly
        self.assertEqual(tld['name'], 'prefix.%s' % expected_tld['name'])

    def test_delete_tld(self):
        # Create a tld
        tld = self.create_tld(fixture=0)
        # Delete the tld
        self.central_service.delete_tld(self.admin_context, tld['id'])

        # Fetch the tld again, ensuring an exception is raised
        self.assertRaises(
            exceptions.TLDNotFound,
            self.central_service.get_tld,
            self.admin_context, tld['id'])

    # TsigKey Tests
    def test_create_tsigkey(self):
        values = self.get_tsigkey_fixture(fixture=0)

        # Create a tsigkey
        tsigkey = self.central_service.create_tsigkey(
            self.admin_context, values=values)

        # Ensure all values have been set correctly
        self.assertIsNotNone(tsigkey['id'])
        self.assertEqual(tsigkey['name'], values['name'])
        self.assertEqual(tsigkey['algorithm'], values['algorithm'])
        self.assertEqual(tsigkey['secret'], values['secret'])

    def test_find_tsigkeys(self):
        # Ensure we have no tsigkeys to start with.
        tsigkeys = self.central_service.find_tsigkeys(self.admin_context)
        self.assertEqual(len(tsigkeys), 0)

        # Create a single tsigkey (using default values)
        tsigkey_one = self.create_tsigkey()

        # Ensure we can retrieve the newly created tsigkey
        tsigkeys = self.central_service.find_tsigkeys(self.admin_context)
        self.assertEqual(len(tsigkeys), 1)
        self.assertEqual(tsigkeys[0]['name'], tsigkey_one['name'])

        # Create a second tsigkey
        tsigkey_two = self.create_tsigkey(fixture=1)

        # Ensure we can retrieve both tsigkeys
        tsigkeys = self.central_service.find_tsigkeys(self.admin_context)
        self.assertEqual(len(tsigkeys), 2)
        self.assertEqual(tsigkeys[0]['name'], tsigkey_one['name'])
        self.assertEqual(tsigkeys[1]['name'], tsigkey_two['name'])

    def test_get_tsigkey(self):
        # Create a tsigkey
        expected = self.create_tsigkey()

        # Retrieve it, and ensure it's the same
        tsigkey = self.central_service.get_tsigkey(
            self.admin_context, expected['id'])

        self.assertEqual(tsigkey['id'], expected['id'])
        self.assertEqual(tsigkey['name'], expected['name'])
        self.assertEqual(tsigkey['algorithm'], expected['algorithm'])
        self.assertEqual(tsigkey['secret'], expected['secret'])

    def test_update_tsigkey(self):
        # Create a tsigkey using default values
        expected = self.create_tsigkey()

        # Update the tsigkey
        fixture = self.get_tsigkey_fixture(fixture=1)
        values = dict(name=fixture['name'])

        self.central_service.update_tsigkey(
            self.admin_context, expected['id'], values=values)

        # Fetch the tsigkey again
        tsigkey = self.central_service.get_tsigkey(
            self.admin_context, expected['id'])

        # Ensure the tsigkey was updated correctly
        self.assertEqual(tsigkey['name'], fixture['name'])

    def test_delete_tsigkey(self):
        # Create a tsigkey
        tsigkey = self.create_tsigkey()

        # Delete the tsigkey
        self.central_service.delete_tsigkey(self.admin_context, tsigkey['id'])

        # Fetch the tsigkey again, ensuring an exception is raised
        with testtools.ExpectedException(exceptions.TsigKeyNotFound):
            self.central_service.get_tsigkey(self.admin_context, tsigkey['id'])

    # Tenant Tests
    def test_count_tenants(self):
        admin_context = self.get_admin_context()
        admin_context.all_tenants = True

        tenant_one_context = self.get_context(tenant=1)
        tenant_two_context = self.get_context(tenant=2)

        # in the beginning, there should be nothing
        tenants = self.central_service.count_tenants(admin_context)
        self.assertEqual(tenants, 0)

        # Explicitly set a tenant_id
        self.create_domain(fixture=0, context=tenant_one_context)
        self.create_domain(fixture=1, context=tenant_two_context)

        tenants = self.central_service.count_tenants(admin_context)
        self.assertEqual(tenants, 2)

    def test_count_tenants_policy_check(self):
        # Set the policy to reject the authz
        self.policy({'count_tenants': '!'})

        with testtools.ExpectedException(exceptions.Forbidden):
            self.central_service.count_tenants(self.get_context())

    # Domain Tests
    def _test_create_domain(self, values):
        # Create a server
        self.create_server()

        # Reset the list of notifications
        self.reset_notifications()

        # Create a domain
        domain = self.central_service.create_domain(
            self.admin_context, values=values)

        # Ensure all values have been set correctly
        self.assertIsNotNone(domain['id'])
        self.assertEqual(domain['name'], values['name'])
        self.assertEqual(domain['email'], values['email'])
        self.assertIn('status', domain)

        # Ensure we sent exactly 1 notification
        notifications = self.get_notifications()
        self.assertEqual(len(notifications), 1)

        # Ensure the notification wrapper contains the correct info
        notification = notifications.pop()
        self.assertEqual(notification['event_type'], 'dns.domain.create')
        self.assertEqual(notification['priority'], 'INFO')
        self.assertIsNotNone(notification['timestamp'])
        self.assertIsNotNone(notification['message_id'])

        # Ensure the notification payload contains the correct info
        payload = notification['payload']
        self.assertEqual(payload['id'], domain['id'])
        self.assertEqual(payload['name'], domain['name'])
        self.assertEqual(payload['tenant_id'], domain['tenant_id'])

    def test_create_domain_over_tld(self):
        values = dict(
            name='example.com',
            email='info@example.com'
        )
        self._test_create_domain(values)

    def test_idn_create_domain_over_tld(self):
        values = dict(
            name='xn--3e0b707e'
        )

        # Create the appropriate TLD
        self.central_service.create_tld(self.admin_context, values=values)

        # Test creation of a domain in 한국 (kr)
        values = dict(
            name='example.xn--3e0b707e.',
            email='info@example.xn--3e0b707e'
        )
        self._test_create_domain(values)

    def test_create_domain_over_quota(self):
        self.config(quota_domains=1)

        self.create_domain()

        with testtools.ExpectedException(exceptions.OverQuota):
            self.create_domain()

    def test_create_subdomain(self):
        # Create the Parent Domain using fixture 0
        parent_domain = self.create_domain(fixture=0)

        # Prepare values for the subdomain using fixture 1 as a base
        values = self.get_domain_fixture(1)
        values['name'] = 'www.%s' % parent_domain['name']

        # Create the subdomain
        domain = self.central_service.create_domain(
            self.admin_context, values=values)

        # Ensure all values have been set correctly
        self.assertIsNotNone(domain['id'])
        self.assertEqual(domain['parent_domain_id'], parent_domain['id'])

    def test_create_subdomain_failure(self):
        context = self.get_admin_context()

        # Explicitly set a tenant_id
        context.tenant_id = '1'

        # Create the Parent Domain using fixture 0
        parent_domain = self.create_domain(fixture=0, context=context)

        context = self.get_admin_context()

        # Explicitly use a different tenant_id
        context.tenant_id = '2'

        # Prepare values for the subdomain using fixture 1 as a base
        values = self.get_domain_fixture(1)
        values['name'] = 'www.%s' % parent_domain['name']

        # Attempt to create the subdomain
        with testtools.ExpectedException(exceptions.Forbidden):
            self.central_service.create_domain(context, values=values)

    def test_create_blacklisted_domain_success(self):
        # Create blacklisted zone using default values
        self.create_blacklist()

        # Set the policy to accept the authz
        self.policy({'use_blacklisted_domain': '@'})

        values = dict(
            name='blacklisted.com.',
            email='info@blacklisted.com'
        )

        # Create a server
        self.create_server()

        # Create a zone that is blacklisted
        domain = self.central_service.create_domain(
            self.admin_context, values=values)

        # Ensure all values have been set correctly
        self.assertIsNotNone(domain['id'])
        self.assertEqual(domain['name'], values['name'])
        self.assertEqual(domain['email'], values['email'])

    def test_create_blacklisted_domain_fail(self):
        self.create_blacklist()

        # Set the policy to reject the authz
        self.policy({'use_blacklisted_domain': '!'})

        values = dict(
            name='blacklisted.com.',
            email='info@blacklisted.com'
        )

        with testtools.ExpectedException(exceptions.InvalidDomainName):
            # Create a domain
            self.central_service.create_domain(
                self.admin_context, values=values)

    def _test_create_domain_fail(self, values, exception):

        with testtools.ExpectedException(exception):
            # Create an invalid domain
            self.central_service.create_domain(
                self.admin_context, values=values)

    def test_create_domain_invalid_tld_fail(self):
        # Create a server
        self.create_server()

        # add a tld for com
        self.create_tld(fixture=0)

        values = dict(
            name='example.com.',
            email='info@example.com'
        )

        # Create a valid domain
        self.central_service.create_domain(self.admin_context, values=values)

        values = dict(
            name='example.net.',
            email='info@example.net'
        )

        # There is no TLD for net so it should fail
        with testtools.ExpectedException(exceptions.InvalidDomainName):
            # Create an invalid domain
            self.central_service.create_domain(
                self.admin_context, values=values)

    def test_find_domains(self):
        # Ensure we have no domains to start with.
        domains = self.central_service.find_domains(self.admin_context)
        self.assertEqual(len(domains), 0)

        # Create a single domain (using default values)
        self.create_domain()

        # Ensure we can retrieve the newly created domain
        domains = self.central_service.find_domains(self.admin_context)
        self.assertEqual(len(domains), 1)
        self.assertEqual(domains[0]['name'], 'example.com.')

        # Create a second domain
        self.create_domain(name='example.net.')

        # Ensure we can retrieve both domain
        domains = self.central_service.find_domains(self.admin_context)
        self.assertEqual(len(domains), 2)
        self.assertEqual(domains[0]['name'], 'example.com.')
        self.assertEqual(domains[1]['name'], 'example.net.')

    def test_find_domains_criteria(self):
        # Create a domain
        domain_name = '%d.example.com.' % random.randint(10, 1000)
        expected_domain = self.create_domain(name=domain_name)

        # Retrieve it, and ensure it's the same
        criterion = {'name': domain_name}

        domains = self.central_service.find_domains(
            self.admin_context, criterion)

        self.assertEqual(domains[0]['id'], expected_domain['id'])
        self.assertEqual(domains[0]['name'], expected_domain['name'])
        self.assertEqual(domains[0]['email'], expected_domain['email'])

    def test_find_domains_tenant_restrictions(self):
        admin_context = self.get_admin_context()
        admin_context.all_tenants = True

        tenant_one_context = self.get_context(tenant=1)
        tenant_two_context = self.get_context(tenant=2)

        # Ensure we have no domains to start with.
        domains = self.central_service.find_domains(admin_context)
        self.assertEqual(len(domains), 0)

        # Create a single domain (using default values)
        domain = self.create_domain(context=tenant_one_context)

        # Ensure admins can retrieve the newly created domain
        domains = self.central_service.find_domains(admin_context)
        self.assertEqual(len(domains), 1)
        self.assertEqual(domains[0]['name'], domain['name'])

        # Ensure tenant=1 can retrieve the newly created domain
        domains = self.central_service.find_domains(tenant_one_context)
        self.assertEqual(len(domains), 1)
        self.assertEqual(domains[0]['name'], domain['name'])

        # Ensure tenant=2 can NOT retrieve the newly created domain
        domains = self.central_service.find_domains(tenant_two_context)
        self.assertEqual(len(domains), 0)

    def test_get_domain(self):
        # Create a domain
        domain_name = '%d.example.com.' % random.randint(10, 1000)
        expected_domain = self.create_domain(name=domain_name)

        # Retrieve it, and ensure it's the same
        domain = self.central_service.get_domain(
            self.admin_context, expected_domain['id'])

        self.assertEqual(domain['id'], expected_domain['id'])
        self.assertEqual(domain['name'], expected_domain['name'])
        self.assertEqual(domain['email'], expected_domain['email'])

    def test_get_domain_servers(self):
        # Create a domain
        domain = self.create_domain()

        # Retrieve the servers list
        servers = self.central_service.get_domain_servers(
            self.admin_context, domain['id'])

        self.assertTrue(len(servers) > 0)

    def test_find_domain(self):
        # Create a domain
        domain_name = '%d.example.com.' % random.randint(10, 1000)
        expected_domain = self.create_domain(name=domain_name)

        # Retrieve it, and ensure it's the same
        criterion = {'name': domain_name}

        domain = self.central_service.find_domain(
            self.admin_context, criterion)

        self.assertEqual(domain['id'], expected_domain['id'])
        self.assertEqual(domain['name'], expected_domain['name'])
        self.assertEqual(domain['email'], expected_domain['email'])
        self.assertIn('status', domain)

    def test_update_domain(self):
        # Create a domain
        expected_domain = self.create_domain()

        # Reset the list of notifications
        self.reset_notifications()

        # Update the domain
        values = dict(email='new@example.com')

        self.central_service.update_domain(
            self.admin_context, expected_domain['id'], values=values)

        # Fetch the domain again
        domain = self.central_service.get_domain(
            self.admin_context, expected_domain['id'])

        # Ensure the domain was updated correctly
        self.assertTrue(domain['serial'] > expected_domain['serial'])
        self.assertEqual(domain['email'], 'new@example.com')

        # Ensure we sent exactly 1 notification
        notifications = self.get_notifications()
        self.assertEqual(len(notifications), 1)

        # Ensure the notification wrapper contains the correct info
        notification = notifications.pop()
        self.assertEqual(notification['event_type'], 'dns.domain.update')
        self.assertEqual(notification['priority'], 'INFO')
        self.assertIsNotNone(notification['timestamp'])
        self.assertIsNotNone(notification['message_id'])

        # Ensure the notification payload contains the correct info
        payload = notification['payload']
        self.assertEqual(payload['id'], domain['id'])
        self.assertEqual(payload['name'], domain['name'])
        self.assertEqual(payload['tenant_id'], domain['tenant_id'])

    def test_update_domain_without_incrementing_serial(self):
        # Create a domain
        expected_domain = self.create_domain()

        # Update the domain
        values = dict(email='new@example.com')

        self.central_service.update_domain(
            self.admin_context, expected_domain['id'], values=values,
            increment_serial=False)

        # Fetch the domain again
        domain = self.central_service.get_domain(
            self.admin_context, expected_domain['id'])

        # Ensure the domain was updated correctly
        self.assertEqual(domain['serial'], expected_domain['serial'])
        self.assertEqual(domain['email'], 'new@example.com')

    def test_update_domain_name_fail(self):
        # Create a domain
        expected_domain = self.create_domain()

        # Update the domain
        with testtools.ExpectedException(exceptions.BadRequest):
            values = dict(name='renamed-domain.com.')

            self.central_service.update_domain(
                self.admin_context, expected_domain['id'], values=values)

    def test_delete_domain(self):
        # Create a domain
        domain = self.create_domain()

        # Reset the list of notifications
        self.reset_notifications()

        # Delete the domain
        self.central_service.delete_domain(self.admin_context, domain['id'])

        # Fetch the domain again, ensuring an exception is raised
        with testtools.ExpectedException(exceptions.DomainNotFound):
            self.central_service.get_domain(self.admin_context, domain['id'])

        # Ensure we sent exactly 1 notification
        notifications = self.get_notifications()
        self.assertEqual(len(notifications), 1)

        # Ensure the notification wrapper contains the correct info
        notification = notifications.pop()
        self.assertEqual(notification['event_type'], 'dns.domain.delete')
        self.assertEqual(notification['priority'], 'INFO')
        self.assertIsNotNone(notification['timestamp'])
        self.assertIsNotNone(notification['message_id'])

        # Ensure the notification payload contains the correct info
        payload = notification['payload']
        self.assertEqual(payload['id'], domain['id'])
        self.assertEqual(payload['name'], domain['name'])
        self.assertEqual(payload['tenant_id'], domain['tenant_id'])

    def test_delete_parent_domain(self):
        # Create the Parent Domain using fixture 0
        parent_domain = self.create_domain(fixture=0)

        # Create the subdomain
        self.create_domain(fixture=1, name='www.%s' % parent_domain['name'])

        # Attempt to delete the parent domain
        with testtools.ExpectedException(exceptions.DomainHasSubdomain):
            self.central_service.delete_domain(
                self.admin_context, parent_domain['id'])

    def test_count_domains(self):
        # in the beginning, there should be nothing
        domains = self.central_service.count_domains(self.admin_context)
        self.assertEqual(domains, 0)

        # Create a single domain
        self.create_domain()

        # count 'em up
        domains = self.central_service.count_domains(self.admin_context)

        # well, did we get 1?
        self.assertEqual(domains, 1)

    def test_count_domains_policy_check(self):
        # Set the policy to reject the authz
        self.policy({'count_domains': '!'})

        with testtools.ExpectedException(exceptions.Forbidden):
            self.central_service.count_domains(self.get_context())

    def test_touch_domain(self):
        # Create a domain
        expected_domain = self.create_domain()

        # Touch the domain
        self.central_service.touch_domain(
            self.admin_context, expected_domain['id'])

        # Fetch the domain again
        domain = self.central_service.get_domain(
            self.admin_context, expected_domain['id'])

        # Ensure the serial was incremented
        self.assertTrue(domain['serial'] > expected_domain['serial'])

    # RecordSet Tests
    def test_create_recordset(self):
        domain = self.create_domain()

        values = dict(
            name='www.%s' % domain['name'],
            type='A'
        )

        # Create a recordset
        recordset = self.central_service.create_recordset(
            self.admin_context, domain['id'], values=values)

        # Ensure all values have been set correctly
        self.assertIsNotNone(recordset['id'])
        self.assertEqual(recordset['name'], values['name'])
        self.assertEqual(recordset['type'], values['type'])

    # def test_create_recordset_over_quota(self):
    #     self.config(quota_domain_recordsets=1)

    #     domain = self.create_domain()

    #     self.create_recordset(domain)

    #     with testtools.ExpectedException(exceptions.OverQuota):
    #         self.create_recordset(domain)

    def test_create_invalid_recordset_location_cname_at_apex(self):
        domain = self.create_domain()

        values = dict(
            name=domain['name'],
            type='CNAME'
        )

        # Attempt to create a CNAME record at the apex
        with testtools.ExpectedException(exceptions.InvalidRecordSetLocation):
            self.central_service.create_recordset(
                self.admin_context, domain['id'], values=values)

    def test_create_invalid_recordset_location_cname_sharing(self):
        domain = self.create_domain()
        expected = self.create_recordset(domain)

        values = dict(
            name=expected['name'],
            type='CNAME'
        )

        # Attempt to create a CNAME record alongside another record
        with testtools.ExpectedException(exceptions.InvalidRecordSetLocation):
            self.central_service.create_recordset(
                self.admin_context, domain['id'], values=values)

    def test_create_invalid_recordset_location_wrong_domain(self):
        domain = self.create_domain()
        other_domain = self.create_domain(fixture=1)

        values = dict(
            name=other_domain['name'],
            type='A'
        )

        # Attempt to create a record in the incorrect domain
        with testtools.ExpectedException(exceptions.InvalidRecordSetLocation):
            self.central_service.create_recordset(
                self.admin_context, domain['id'], values=values)

    def test_get_recordset(self):
        domain = self.create_domain()

        # Create a recordset
        expected = self.create_recordset(domain)

        # Retrieve it, and ensure it's the same
        recordset = self.central_service.get_recordset(
            self.admin_context, domain['id'], expected['id'])

        self.assertEqual(recordset['id'], expected['id'])
        self.assertEqual(recordset['name'], expected['name'])
        self.assertEqual(recordset['type'], expected['type'])

    def test_get_recordset_incorrect_domain_id(self):
        domain = self.create_domain()
        other_domain = self.create_domain(fixture=1)

        # Create a recordset
        expected = self.create_recordset(domain)

        # Ensure we get a 404 if we use the incorrect domain_id
        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            self.central_service.get_recordset(
                self.admin_context, other_domain['id'], expected['id'])

    def test_find_recordsets(self):
        domain = self.create_domain()

        criterion = {'domain_id': domain['id']}

        # Ensure we have no recordsets to start with.
        recordsets = self.central_service.find_recordsets(
            self.admin_context, criterion)

        self.assertEqual(len(recordsets), 0)

        # Create a single recordset (using default values)
        self.create_recordset(domain, name='www.%s' % domain['name'])

        # Ensure we can retrieve the newly created recordset
        recordsets = self.central_service.find_recordsets(
            self.admin_context, criterion)

        self.assertEqual(len(recordsets), 1)
        self.assertEqual(recordsets[0]['name'], 'www.%s' % domain['name'])

        # Create a second recordset
        self.create_recordset(domain, name='mail.%s' % domain['name'])

        # Ensure we can retrieve both recordsets
        recordsets = self.central_service.find_recordsets(
            self.admin_context, criterion)

        self.assertEqual(len(recordsets), 2)
        self.assertEqual(recordsets[0]['name'], 'www.%s' % domain['name'])
        self.assertEqual(recordsets[1]['name'], 'mail.%s' % domain['name'])

    def test_find_recordset(self):
        domain = self.create_domain()

        # Create a recordset
        expected = self.create_recordset(domain)

        # Retrieve it, and ensure it's the same
        criterion = {'domain_id': domain['id'], 'name': expected['name']}

        recordset = self.central_service.find_recordset(
            self.admin_context, criterion)

        self.assertEqual(recordset['id'], expected['id'])
        self.assertEqual(recordset['name'], expected['name'])

    def test_update_recordset(self):
        domain = self.create_domain()

        # Create a recordset
        expected = self.create_recordset(domain)

        # Update the recordset
        values = dict(ttl=1800)
        self.central_service.update_recordset(
            self.admin_context, domain['id'], expected['id'], values=values)

        # Fetch the recordset again
        recordset = self.central_service.get_recordset(
            self.admin_context, domain['id'], expected['id'])

        # Ensure the record was updated correctly
        self.assertEqual(recordset['ttl'], 1800)

    def test_update_recordset_without_incrementing_serial(self):
        domain = self.create_domain()

        # Create a recordset
        expected = self.create_recordset(domain)

        # Fetch the domain so we have the latest serial number
        domain_before = self.central_service.get_domain(
            self.admin_context, domain['id'])

        # Update the recordset
        values = dict(ttl=1800)
        self.central_service.update_recordset(
            self.admin_context, domain['id'], expected['id'], values,
            increment_serial=False)

        # Fetch the recordset again
        recordset = self.central_service.get_recordset(
            self.admin_context, domain['id'], expected['id'])

        # Ensure the recordset was updated correctly
        self.assertEqual(recordset['ttl'], 1800)

        # Ensure the domains serial number was not updated
        domain_after = self.central_service.get_domain(
            self.admin_context, domain['id'])

        self.assertEqual(domain_before['serial'], domain_after['serial'])

    def test_update_recordset_incorrect_domain_id(self):
        domain = self.create_domain()
        other_domain = self.create_domain(fixture=1)

        # Create a recordset
        expected = self.create_recordset(domain)

        # Update the recordset
        values = dict(ttl=1800)

        # Ensure we get a 404 if we use the incorrect domain_id
        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            self.central_service.update_recordset(
                self.admin_context, other_domain['id'], expected['id'],
                values=values)

    def test_delete_recordset(self):
        domain = self.create_domain()

        # Create a recordset
        recordset = self.create_recordset(domain)

        # Delete the recordset
        self.central_service.delete_recordset(
            self.admin_context, domain['id'], recordset['id'])

        # Fetch the recordset again, ensuring an exception is raised
        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            self.central_service.get_recordset(
                self.admin_context, domain['id'], recordset['id'])

    def test_delete_recordset_without_incrementing_serial(self):
        domain = self.create_domain()

        # Create a recordset
        recordset = self.create_recordset(domain)

        # Fetch the domain so we have the latest serial number
        domain_before = self.central_service.get_domain(
            self.admin_context, domain['id'])

        # Delete the recordset
        self.central_service.delete_recordset(
            self.admin_context, domain['id'], recordset['id'],
            increment_serial=False)

        # Fetch the record again, ensuring an exception is raised
        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            self.central_service.get_recordset(
                self.admin_context, domain['id'], recordset['id'])

        # Ensure the domains serial number was not updated
        domain_after = self.central_service.get_domain(
            self.admin_context, domain['id'])

        self.assertEqual(domain_before['serial'], domain_after['serial'])

    def test_delete_recordset_incorrect_domain_id(self):
        domain = self.create_domain()
        other_domain = self.create_domain(fixture=1)

        # Create a recordset
        recordset = self.create_recordset(domain)

        # Ensure we get a 404 if we use the incorrect domain_id
        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            self.central_service.delete_recordset(
                self.admin_context, other_domain['id'], recordset['id'])

    def test_count_recordsets(self):
        # in the beginning, there should be nothing
        recordsets = self.central_service.count_recordsets(self.admin_context)
        self.assertEqual(recordsets, 0)

        # Create a domain to put our recordset in
        domain = self.create_domain()

        # Create a recordset
        self.create_recordset(domain)

        # We should have 1 recordset now
        recordsets = self.central_service.count_recordsets(self.admin_context)
        self.assertEqual(recordsets, 1)

    def test_count_recordsets_policy_check(self):
        # Set the policy to reject the authz
        self.policy({'count_recordsets': '!'})

        with testtools.ExpectedException(exceptions.Forbidden):
            self.central_service.count_recordsets(self.get_context())

    # Record Tests
    def test_create_record(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain, type='A')

        values = dict(
            data='127.0.0.1'
        )

        # Create a record
        record = self.central_service.create_record(
            self.admin_context, domain['id'], recordset['id'], values=values)

        # Ensure all values have been set correctly
        self.assertIsNotNone(record['id'])
        self.assertEqual(record['data'], values['data'])
        self.assertIn('status', record)

    def test_create_record_over_quota(self):
        self.config(quota_domain_records=1)

        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        self.create_record(domain, recordset)

        with testtools.ExpectedException(exceptions.OverQuota):
            self.create_record(domain, recordset)

    def test_create_record_without_incrementing_serial(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain, type='A')

        values = dict(
            data='127.0.0.1'
        )

        # Create a record
        self.central_service.create_record(
            self.admin_context, domain['id'], recordset['id'], values=values,
            increment_serial=False)

        # Ensure the domains serial number was not updated
        updated_domain = self.central_service.get_domain(
            self.admin_context, domain['id'])

        self.assertEqual(domain['serial'], updated_domain['serial'])

    def test_get_record(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        # Create a record
        expected = self.create_record(domain, recordset)

        # Retrieve it, and ensure it's the same
        record = self.central_service.get_record(
            self.admin_context, domain['id'], recordset['id'], expected['id'])

        self.assertEqual(record['id'], expected['id'])
        self.assertEqual(record['data'], expected['data'])
        self.assertIn('status', record)

    def test_get_record_incorrect_domain_id(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)
        other_domain = self.create_domain(fixture=1)

        # Create a record
        expected = self.create_record(domain, recordset)

        # Ensure we get a 404 if we use the incorrect domain_id
        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.central_service.get_record(
                self.admin_context, other_domain['id'], recordset['id'],
                expected['id'])

    def test_get_record_incorrect_recordset_id(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)
        other_recordset = self.create_recordset(domain, fixture=1)

        # Create a record
        expected = self.create_record(domain, recordset)

        # Ensure we get a 404 if we use the incorrect recordset_id
        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.central_service.get_record(
                self.admin_context, domain['id'], other_recordset['id'],
                expected['id'])

    def test_find_records(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        criterion = {
            'domain_id': domain['id'],
            'recordset_id': recordset['id']
        }

        # Ensure we have no records to start with.
        records = self.central_service.find_records(
            self.admin_context, criterion)

        self.assertEqual(len(records), 0)

        # Create a single record (using default values)
        expected_one = self.create_record(domain, recordset)

        # Ensure we can retrieve the newly created record
        records = self.central_service.find_records(
            self.admin_context, criterion)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['data'], expected_one['data'])

        # Create a second record
        expected_two = self.create_record(domain, recordset, fixture=1)

        # Ensure we can retrieve both records
        records = self.central_service.find_records(
            self.admin_context, criterion)

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]['data'], expected_one['data'])
        self.assertEqual(records[1]['data'], expected_two['data'])

    def test_find_record(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        # Create a record
        expected = self.create_record(domain, recordset)

        # Retrieve it, and ensure it's the same
        criterion = {
            'domain_id': domain['id'],
            'recordset_id': recordset['id'],
            'data': expected['data']
        }

        record = self.central_service.find_record(
            self.admin_context, criterion)

        self.assertEqual(record['id'], expected['id'])
        self.assertEqual(record['data'], expected['data'])
        self.assertIn('status', record)

    def test_update_record(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain, 'A')

        # Create a record
        expected = self.create_record(domain, recordset)

        # Update the record
        values = dict(data='127.0.0.2')
        self.central_service.update_record(
            self.admin_context, domain['id'], recordset['id'], expected['id'],
            values=values)

        # Fetch the record again
        record = self.central_service.get_record(
            self.admin_context, domain['id'], recordset['id'], expected['id'])

        # Ensure the record was updated correctly
        self.assertEqual(record['data'], '127.0.0.2')

    def test_update_record_without_incrementing_serial(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain, 'A')

        # Create a record
        expected = self.create_record(domain, recordset)

        # Fetch the domain so we have the latest serial number
        domain_before = self.central_service.get_domain(
            self.admin_context, domain['id'])

        # Update the record
        values = dict(data='127.0.0.2')

        self.central_service.update_record(
            self.admin_context, domain['id'], recordset['id'], expected['id'],
            values, increment_serial=False)

        # Fetch the record again
        record = self.central_service.get_record(
            self.admin_context, domain['id'], recordset['id'], expected['id'])

        # Ensure the record was updated correctly
        self.assertEqual(record['data'], '127.0.0.2')

        # Ensure the domains serial number was not updated
        domain_after = self.central_service.get_domain(
            self.admin_context, domain['id'])

        self.assertEqual(domain_before['serial'], domain_after['serial'])

    def test_update_record_incorrect_domain_id(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain, 'A')
        other_domain = self.create_domain(fixture=1)

        # Create a record
        expected = self.create_record(domain, recordset)

        # Update the record
        values = dict(data='127.0.0.2')

        # Ensure we get a 404 if we use the incorrect domain_id
        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.central_service.update_record(
                self.admin_context, other_domain['id'], recordset['id'],
                expected['id'], values=values)

    def test_update_record_incorrect_recordset_id(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain, 'A')
        other_recordset = self.create_recordset(domain, 'A', fixture=1)

        # Create a record
        expected = self.create_record(domain, recordset)

        # Update the record
        values = dict(data='127.0.0.2')

        # Ensure we get a 404 if we use the incorrect domain_id
        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.central_service.update_record(
                self.admin_context, domain['id'], other_recordset['id'],
                expected['id'], values=values)

    def test_delete_record(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        # Create a record
        record = self.create_record(domain, recordset)

        # Delete the record
        self.central_service.delete_record(
            self.admin_context, domain['id'], recordset['id'], record['id'])

        # Fetch the record again, ensuring an exception is raised
        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.central_service.get_record(
                self.admin_context, domain['id'], recordset['id'],
                record['id'])

    def test_delete_record_without_incrementing_serial(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        # Create a record
        record = self.create_record(domain, recordset)

        # Fetch the domain so we have the latest serial number
        domain_before = self.central_service.get_domain(
            self.admin_context, domain['id'])

        # Delete the record
        self.central_service.delete_record(
            self.admin_context, domain['id'], recordset['id'], record['id'],
            increment_serial=False)

        # Fetch the record again, ensuring an exception is raised
        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.central_service.get_record(
                self.admin_context, domain['id'], recordset['id'],
                record['id'])

        # Ensure the domains serial number was not updated
        domain_after = self.central_service.get_domain(
            self.admin_context, domain['id'])

        self.assertEqual(domain_before['serial'], domain_after['serial'])

    def test_delete_record_incorrect_domain_id(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)
        other_domain = self.create_domain(fixture=1)

        # Create a record
        record = self.create_record(domain, recordset)

        # Ensure we get a 404 if we use the incorrect domain_id
        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.central_service.delete_record(
                self.admin_context, other_domain['id'], recordset['id'],
                record['id'])

    def test_delete_record_incorrect_recordset_id(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)
        other_recordset = self.create_recordset(domain, fixture=1)

        # Create a record
        record = self.create_record(domain, recordset)

        # Ensure we get a 404 if we use the incorrect recordset_id
        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.central_service.delete_record(
                self.admin_context, domain['id'], other_recordset['id'],
                record['id'])

    def test_count_records(self):
        # in the beginning, there should be nothing
        records = self.central_service.count_records(self.admin_context)
        self.assertEqual(records, 0)

        # Create a domain and recordset to put our record in
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        # Create a record
        self.create_record(domain, recordset)

        # we should have 1 record now
        records = self.central_service.count_records(self.admin_context)
        self.assertEqual(records, 1)

    def test_count_records_policy_check(self):
        # Set the policy to reject the authz
        self.policy({'count_records': '!'})

        with testtools.ExpectedException(exceptions.Forbidden):
            self.central_service.count_records(self.get_context())

    def test_get_floatingip_no_record(self):
        self.create_server()

        context = self.get_context(tenant='a')

        fip = self.network_api.fake.allocate_floatingip(context.tenant_id)

        fip_ptr = self.central_service.get_floatingip(
            context, fip['region'], fip['id'])

        self.assertEqual(fip['region'], fip_ptr['region'])
        self.assertEqual(fip['id'], fip_ptr['id'])
        self.assertEqual(fip['address'], fip_ptr['address'])
        self.assertEqual(None, fip_ptr['ptrdname'])

    def test_get_floatingip_with_record(self):
        self.create_server()

        context = self.get_context(tenant='a')

        fixture = self.get_ptr_fixture()

        fip = self.network_api.fake.allocate_floatingip(context.tenant_id)

        expected = self.central_service.update_floatingip(
            context, fip['region'], fip['id'], fixture)

        actual = self.central_service.get_floatingip(
            context, fip['region'], fip['id'])
        self.assertEqual(expected, actual)

        self.assertEqual(expected, actual)

    def test_get_floatingip_not_allocated(self):
        context = self.get_context(tenant='a')

        fip = self.network_api.fake.allocate_floatingip(context.tenant_id)
        self.network_api.fake.deallocate_floatingip(fip['id'])

        with testtools.ExpectedException(exceptions.NotFound):
            self.central_service.get_floatingip(
                context, fip['region'], fip['id'])

    def test_get_floatingip_deallocated_and_invalidate(self):
        self.create_server()

        context_a = self.get_context(tenant='a')
        elevated_a = context_a.elevated()
        elevated_a.all_tenants = True

        context_b = self.get_context(tenant='b')

        fixture = self.get_ptr_fixture()

        # First allocate and create a FIP as tenant a
        fip = self.network_api.fake.allocate_floatingip(context_a.tenant_id)

        self.central_service.update_floatingip(
            context_a, fip['region'], fip['id'], fixture)

        self.network_api.fake.deallocate_floatingip(fip['id'])

        with testtools.ExpectedException(exceptions.NotFound):
            self.central_service.get_floatingip(
                context_a, fip['region'], fip['id'])

        # Ensure that the record is still in DB (No invalidation)
        criterion = {
            'managed_resource_id': fip['id'],
            'managed_tenant_id': context_a.tenant_id}
        self.central_service.find_record(elevated_a, criterion)

        # Now give the fip id to tenant 'b' and see that it get's deleted
        self.network_api.fake.allocate_floatingip(
            context_b.tenant_id, fip['id'])

        # There should be a fip returned with ptrdname of None
        fip_ptr = self.central_service.get_floatingip(
            context_b, fip['region'], fip['id'])
        self.assertEqual(None, fip_ptr['ptrdname'])

        # Ensure that the old record for tenant a for the fip now owned by
        # tenant b is gone
        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.central_service.find_record(elevated_a, criterion)

    def test_list_floatingips_no_allocations(self):
        context = self.get_context(tenant='a')

        fips = self.central_service.list_floatingips(context)

        self.assertEqual(0, len(fips))

    def test_list_floatingips_no_record(self):
        context = self.get_context(tenant='a')

        fip = self.network_api.fake.allocate_floatingip(context.tenant_id)

        fips = self.central_service.list_floatingips(context)

        self.assertEqual(1, len(fips))
        self.assertEqual(None, fips[0]['ptrdname'])
        self.assertEqual(fip['id'], fips[0]['id'])
        self.assertEqual(fip['region'], fips[0]['region'])
        self.assertEqual(fip['address'], fips[0]['address'])
        self.assertEqual(None, fips[0]['description'])

    def test_list_floatingips_with_record(self):
        self.create_server()

        context = self.get_context(tenant='a')

        fixture = self.get_ptr_fixture()

        fip = self.network_api.fake.allocate_floatingip(context.tenant_id)

        fip_ptr = self.central_service.update_floatingip(
            context, fip['region'], fip['id'], fixture)

        fips = self.central_service.list_floatingips(context)

        self.assertEqual(1, len(fips))
        self.assertEqual(fip_ptr['ptrdname'], fips[0]['ptrdname'])
        self.assertEqual(fip_ptr['id'], fips[0]['id'])
        self.assertEqual(fip_ptr['region'], fips[0]['region'])
        self.assertEqual(fip_ptr['address'], fips[0]['address'])
        self.assertEqual(fip_ptr['description'], fips[0]['description'])

    def test_list_floatingips_deallocated_and_invalidate(self):
        self.create_server()

        context_a = self.get_context(tenant='a')
        elevated_a = context_a.elevated()
        elevated_a.all_tenants = True

        context_b = self.get_context(tenant='b')

        fixture = self.get_ptr_fixture()

        # First allocate and create a FIP as tenant a
        fip = self.network_api.fake.allocate_floatingip(context_a.tenant_id)

        self.central_service.update_floatingip(
            context_a, fip['region'], fip['id'], fixture)

        self.network_api.fake.deallocate_floatingip(fip['id'])

        fips = self.central_service.list_floatingips(context_a)
        self.assertEqual([], fips)

        # Ensure that the record is still in DB (No invalidation)
        criterion = {
            'managed_resource_id': fip['id'],
            'managed_tenant_id': context_a.tenant_id}
        self.central_service.find_record(elevated_a, criterion)

        # Now give the fip id to tenant 'b' and see that it get's deleted
        self.network_api.fake.allocate_floatingip(
            context_b.tenant_id, fip['id'])

        # There should be a fip returned with ptrdname of None
        fips = self.central_service.list_floatingips(context_b)
        self.assertEqual(1, len(fips))
        self.assertEqual(None, fips[0]['ptrdname'])

        # Ensure that the old record for tenant a for the fip now owned by
        # tenant b is gone
        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.central_service.find_record(elevated_a, criterion)

    def test_set_floatingip(self):
        self.create_server()

        context = self.get_context(tenant='a')

        fixture = self.get_ptr_fixture()

        fip = self.network_api.fake.allocate_floatingip(context.tenant_id)

        fip_ptr = self.central_service.update_floatingip(
            context, fip['region'], fip['id'], fixture)

        self.assertEqual(fixture['ptrdname'], fip_ptr['ptrdname'])
        self.assertEqual(fip['address'], fip_ptr['address'])
        self.assertEqual(None, fip_ptr['description'])
        self.assertIsNotNone(fip_ptr['ttl'])

    def test_set_floatingip_removes_old_rrset_and_record(self):
        self.create_server()

        context_a = self.get_context(tenant='a')
        elevated_a = context_a.elevated()
        elevated_a.all_tenants = True

        context_b = self.get_context(tenant='b')

        fixture = self.get_ptr_fixture()

        # Test that re-setting as tenant a an already set floatingip leaves
        # only 1 record
        fip = self.network_api.fake.allocate_floatingip(context_a.tenant_id)

        self.central_service.update_floatingip(
            context_a, fip['region'], fip['id'], fixture)

        fixture2 = self.get_ptr_fixture(fixture=1)
        self.central_service.update_floatingip(
            context_a, fip['region'], fip['id'], fixture2)

        count = self.central_service.count_records(
            elevated_a, {'managed_resource_id': fip['id']})

        self.assertEqual(1, count)

        self.network_api.fake.deallocate_floatingip(fip['id'])

        # Now test that tenant b allocating the same fip and setting a ptr
        # deletes any records
        fip = self.network_api.fake.allocate_floatingip(
            context_b.tenant_id, fip['id'])

        self.central_service.update_floatingip(
            context_b, fip['region'], fip['id'], fixture)

        count = self.central_service.count_records(
            elevated_a, {'managed_resource_id': fip['id']})

        self.assertEqual(1, count)

    def test_set_floatingip_not_allocated(self):
        context = self.get_context(tenant='a')
        fixture = self.get_ptr_fixture()

        fip = self.network_api.fake.allocate_floatingip(context.tenant_id)
        self.network_api.fake.deallocate_floatingip(fip['id'])

        # If one attempts to assign a de-allocated FIP or not-owned it should
        # fail with BadRequest
        with testtools.ExpectedException(exceptions.NotFound):
            fixture = self.central_service.update_floatingip(
                context, fip['region'], fip['id'], fixture)

    def test_unset_floatingip(self):
        self.create_server()

        context = self.get_context(tenant='a')

        fixture = self.get_ptr_fixture()

        fip = self.network_api.fake.allocate_floatingip(context.tenant_id)

        fip_ptr = self.central_service.update_floatingip(
            context, fip['region'], fip['id'], fixture)

        self.assertEqual(fixture['ptrdname'], fip_ptr['ptrdname'])
        self.assertEqual(fip['address'], fip_ptr['address'])
        self.assertEqual(None, fip_ptr['description'])
        self.assertIsNotNone(fip_ptr['ttl'])

        self.central_service.update_floatingip(
            context, fip['region'], fip['id'], {'ptrdname': None})

        self.central_service.get_floatingip(
            context, fip['region'], fip['id'])

    # Blacklist Tests
    def test_create_blacklist(self):
        values = self.get_blacklist_fixture(fixture=0)

        blacklist = self.create_blacklist(fixture=0)

        # Verify all values have been set correctly
        self.assertIsNotNone(blacklist['id'])
        self.assertEqual(blacklist['pattern'], values['pattern'])
        self.assertEqual(blacklist['description'], values['description'])

    def test_get_blacklist(self):
        # Create a blacklisted zone
        expected = self.create_blacklist(fixture=0)

        # Retrieve it, and verify it is the same
        blacklist = self.central_service.get_blacklist(
            self.admin_context, expected['id'])

        self.assertEqual(blacklist['id'], expected['id'])
        self.assertEqual(blacklist['pattern'], expected['pattern'])
        self.assertEqual(blacklist['description'], expected['description'])

    def test_find_blacklists(self):
        # Verify there are no blacklisted zones to start with
        blacklists = self.central_service.find_blacklists(
            self.admin_context)

        self.assertEqual(len(blacklists), 0)

        # Create a single blacklisted zone
        self.create_blacklist()

        # Verify we can retrieve the newly created blacklist
        blacklists = self.central_service.find_blacklists(
            self.admin_context)
        values1 = self.get_blacklist_fixture(fixture=0)

        self.assertEqual(len(blacklists), 1)
        self.assertEqual(blacklists[0]['pattern'], values1['pattern'])

        # Create a second blacklisted zone
        self.create_blacklist(fixture=1)

        # Verify we can retrieve both blacklisted zones
        blacklists = self.central_service.find_blacklists(
            self.admin_context)

        values2 = self.get_blacklist_fixture(fixture=1)

        self.assertEqual(len(blacklists), 2)
        self.assertEqual(blacklists[0]['pattern'], values1['pattern'])
        self.assertEqual(blacklists[1]['pattern'], values2['pattern'])

    def test_find_blacklist(self):
        #Create a blacklisted zone
        expected = self.create_blacklist(fixture=0)

        # Retrieve the newly created blacklist
        blacklist = self.central_service.find_blacklist(
            self.admin_context, {'id': expected['id']})

        self.assertEqual(blacklist['pattern'], expected['pattern'])
        self.assertEqual(blacklist['description'], expected['description'])

    def test_update_blacklist(self):
        # Create a blacklisted zone
        expected = self.create_blacklist(fixture=0)
        new_comment = "This is a different comment."

        # Update the blacklist
        updated_values = dict(
            description=new_comment
        )
        self.central_service.update_blacklist(self.admin_context,
                                              expected['id'],
                                              updated_values)

        # Fetch the blacklist
        blacklist = self.central_service.get_blacklist(self.admin_context,
                                                       expected['id'])

        # Verify that the record was updated correctly
        self.assertEqual(blacklist['description'], new_comment)

    def test_delete_blacklist(self):
        # Create a blacklisted zone
        blacklist = self.create_blacklist()

        # Delete the blacklist
        self.central_service.delete_blacklist(self.admin_context,
                                              blacklist['id'])

        # Try to fetch the blacklist to verify an exception is raised
        with testtools.ExpectedException(exceptions.BlacklistNotFound):
            self.central_service.get_blacklist(self.admin_context,
                                               blacklist['id'])
