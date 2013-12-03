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
                    accepted_tlds_file='tlds-alpha-by-domain.txt.sample',
                    group='service:central')

        context = self.get_context()

        self.central_service._is_valid_domain_name(context, 'valid.org.')

        with testtools.ExpectedException(exceptions.InvalidDomainName):
            self.central_service._is_valid_domain_name(context, 'example.org.')

        with testtools.ExpectedException(exceptions.InvalidDomainName):
            self.central_service._is_valid_domain_name(context, 'example.tld.')

    def test_is_valid_record_name(self):
        self.config(max_record_name_len=18,
                    group='service:central')

        context = self.get_context()

        domain = self.create_domain(name='example.org.')

        self.central_service._is_valid_record_name(context,
                                                   domain,
                                                   'valid.example.org.',
                                                   'A')

        with testtools.ExpectedException(exceptions.InvalidRecordName):
            self.central_service._is_valid_record_name(
                context, domain, 'toolong.example.org.', 'A')

        with testtools.ExpectedException(exceptions.InvalidRecordLocation):
            self.central_service._is_valid_record_name(
                context, domain, 'a.example.COM.', 'A')

        with testtools.ExpectedException(exceptions.InvalidRecordLocation):
            self.central_service._is_valid_record_name(
                context, domain, 'example.org.', 'CNAME')

    def test_is_blacklisted_domain_name(self):
        self.config(domain_name_blacklist=['^example.org.$', 'net.$'],
                    group='service:central')

        # Set the policy to reject the authz
        self.policy({'use_blacklisted_domain': '!'})

        context = self.get_context()

        result = self.central_service._is_blacklisted_domain_name(
            context, 'org.')
        self.assertFalse(result)

        result = self.central_service._is_blacklisted_domain_name(
            context, 'www.example.org.')
        self.assertFalse(result)

        result = self.central_service._is_blacklisted_domain_name(
            context, 'example.org.')
        self.assertTrue(result)

        result = self.central_service._is_blacklisted_domain_name(
            context, 'example.net.')
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

    # Server Tests
    def test_create_server(self):
        context = self.get_admin_context()

        values = dict(
            name='ns1.example.org.'
        )

        # Create a server
        server = self.central_service.create_server(context, values=values)

        # Ensure all values have been set correctly
        self.assertIsNotNone(server['id'])
        self.assertEqual(server['name'], values['name'])

    def test_find_servers(self):
        context = self.get_admin_context()

        # Ensure we have no servers to start with.
        servers = self.central_service.find_servers(context)
        self.assertEqual(len(servers), 0)

        # Create a single server (using default values)
        self.create_server()

        # Ensure we can retrieve the newly created server
        servers = self.central_service.find_servers(context)
        self.assertEqual(len(servers), 1)
        self.assertEqual(servers[0]['name'], 'ns1.example.org.')

        # Create a second server
        self.create_server(name='ns2.example.org.')

        # Ensure we can retrieve both servers
        servers = self.central_service.find_servers(context)
        self.assertEqual(len(servers), 2)
        self.assertEqual(servers[0]['name'], 'ns1.example.org.')
        self.assertEqual(servers[1]['name'], 'ns2.example.org.')

    def test_get_server(self):
        context = self.get_admin_context()

        # Create a server
        server_name = 'ns%d.example.org.' % random.randint(10, 1000)
        expected_server = self.create_server(name=server_name)

        # Retrieve it, and ensure it's the same
        server = self.central_service.get_server(context,
                                                 expected_server['id'])
        self.assertEqual(server['id'], expected_server['id'])
        self.assertEqual(server['name'], expected_server['name'])

    def test_update_server(self):
        context = self.get_admin_context()

        # Create a server
        expected_server = self.create_server()

        # Update the server
        values = dict(name='prefix.%s' % expected_server['name'])
        self.central_service.update_server(context, expected_server['id'],
                                           values=values)

        # Fetch the server again
        server = self.central_service.get_server(context,
                                                 expected_server['id'])

        # Ensure the server was updated correctly
        self.assertEqual(server['name'], 'prefix.%s' % expected_server['name'])

    def test_delete_server(self):
        context = self.get_admin_context()

        # Create a server
        server = self.create_server()

        # Create a second server
        server2 = self.create_server(fixture=1)

        # Delete one server
        self.central_service.delete_server(context, server['id'])

        # Fetch the server again, ensuring an exception is raised
        self.assertRaises(
            exceptions.ServerNotFound,
            self.central_service.get_server,
            context, server['id'])

        # Try to delete last remaining server - expect exception
        self.assertRaises(
            exceptions.LastServerDeleteNotAllowed,
            self.central_service.delete_server, context, server2['id'])

    # TsigKey Tests
    def test_create_tsigkey(self):
        context = self.get_admin_context()

        values = self.get_tsigkey_fixture(fixture=0)

        # Create a tsigkey
        tsigkey = self.central_service.create_tsigkey(context, values=values)

        # Ensure all values have been set correctly
        self.assertIsNotNone(tsigkey['id'])
        self.assertEqual(tsigkey['name'], values['name'])
        self.assertEqual(tsigkey['algorithm'], values['algorithm'])
        self.assertEqual(tsigkey['secret'], values['secret'])

    def test_find_tsigkeys(self):
        context = self.get_admin_context()

        # Ensure we have no tsigkeys to start with.
        tsigkeys = self.central_service.find_tsigkeys(context)
        self.assertEqual(len(tsigkeys), 0)

        # Create a single tsigkey (using default values)
        tsigkey_one = self.create_tsigkey()

        # Ensure we can retrieve the newly created tsigkey
        tsigkeys = self.central_service.find_tsigkeys(context)
        self.assertEqual(len(tsigkeys), 1)
        self.assertEqual(tsigkeys[0]['name'], tsigkey_one['name'])

        # Create a second tsigkey
        tsigkey_two = self.create_tsigkey(fixture=1)

        # Ensure we can retrieve both tsigkeys
        tsigkeys = self.central_service.find_tsigkeys(context)
        self.assertEqual(len(tsigkeys), 2)
        self.assertEqual(tsigkeys[0]['name'], tsigkey_one['name'])
        self.assertEqual(tsigkeys[1]['name'], tsigkey_two['name'])

    def test_get_tsigkey(self):
        context = self.get_admin_context()

        # Create a tsigkey
        expected = self.create_tsigkey()

        # Retrieve it, and ensure it's the same
        tsigkey = self.central_service.get_tsigkey(context, expected['id'])
        self.assertEqual(tsigkey['id'], expected['id'])
        self.assertEqual(tsigkey['name'], expected['name'])
        self.assertEqual(tsigkey['algorithm'], expected['algorithm'])
        self.assertEqual(tsigkey['secret'], expected['secret'])

    def test_update_tsigkey(self):
        context = self.get_admin_context()

        # Create a tsigkey using default values
        expected = self.create_tsigkey()

        # Update the tsigkey
        fixture = self.get_tsigkey_fixture(fixture=1)
        values = dict(name=fixture['name'])
        self.central_service.update_tsigkey(context, expected['id'],
                                            values=values)

        # Fetch the tsigkey again
        tsigkey = self.central_service.get_tsigkey(context, expected['id'])

        # Ensure the tsigkey was updated correctly
        self.assertEqual(tsigkey['name'], fixture['name'])

    def test_delete_tsigkey(self):
        context = self.get_admin_context()

        # Create a tsigkey
        tsigkey = self.create_tsigkey()

        # Delete the tsigkey
        self.central_service.delete_tsigkey(context, tsigkey['id'])

        # Fetch the tsigkey again, ensuring an exception is raised
        with testtools.ExpectedException(exceptions.TsigKeyNotFound):
            self.central_service.get_tsigkey(context, tsigkey['id'])

    # Tenant Tests
    def test_count_tenants(self):
        context = self.get_admin_context()
        # in the beginning, there should be nothing
        tenants = self.central_service.count_tenants(self.admin_context)
        self.assertEqual(tenants, 0)

        # Explicitly set a tenant_id
        context.tenant_id = '1'
        self.create_domain(fixture=0, context=context)
        context.tenant_id = '2'
        self.create_domain(fixture=1, context=context)

        tenants = self.central_service.count_tenants(self.admin_context)
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

        context = self.get_admin_context()

        # Create a domain
        domain = self.central_service.create_domain(context, values=values)

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
        # Test creation of a domain in 한국 (kr)
        values = dict(
            name='example.xn--3e0b707e.',
            email='info@example.xn--3e0b707e'
        )
        self._test_create_domain(values)

    def test_create_domain_over_re_effective_tld(self):
        values = dict(
            name='example.co.uk.',
            email='info@example.co.uk'
        )
        self._test_create_domain(values)

    def test_create_domain_over_effective_tld(self):
        values = dict(
            name='example.com.ac.',
            email='info@example.com.ac'
        )
        self._test_create_domain(values)

    def test_idn_create_domain_over_effective_tld(self):
        # Test creation of a domain in 公司.cn
        values = dict(
            name='example.xn--55qx5d.cn.',
            email='info@example.xn--55qx5d.cn'
        )
        self._test_create_domain(values)

    def test_create_domain_over_quota(self):
        self.config(quota_domains=1)

        self.create_domain()

        with testtools.ExpectedException(exceptions.OverQuota):
            self.create_domain()

    def test_create_subdomain(self):
        context = self.get_admin_context()

        # Explicitly set a tenant_id
        context.tenant_id = '1'

        # Create the Parent Domain using fixture 0
        parent_domain = self.create_domain(fixture=0, context=context)

        # Prepare values for the subdomain using fixture 1 as a base
        values = self.get_domain_fixture(1)
        values['name'] = 'www.%s' % parent_domain['name']

        # Create the subdomain
        domain = self.central_service.create_domain(context, values=values)

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
        self.config(domain_name_blacklist=['^blacklisted.com.$'],
                    group='service:central')

        # Set the policy to accept the authz
        self.policy({'use_blacklisted_domain': '@'})

        # Create a server
        self.create_server()

        context = self.get_admin_context()

        values = dict(
            name='blacklisted.com.',
            email='info@blacklisted.com'
        )

        # Create a domain
        domain = self.central_service.create_domain(context, values=values)

        # Ensure all values have been set correctly
        self.assertIsNotNone(domain['id'])
        self.assertEqual(domain['name'], values['name'])
        self.assertEqual(domain['email'], values['email'])

    def test_create_blacklisted_domain_fail(self):
        self.config(domain_name_blacklist=['^blacklisted.com.$'],
                    group='service:central')

        # Set the policy to reject the authz
        self.policy({'use_blacklisted_domain': '!'})

        context = self.get_admin_context()

        values = dict(
            name='blacklisted.com.',
            email='info@blacklisted.com'
        )

        with testtools.ExpectedException(exceptions.InvalidDomainName):
            # Create a domain
            self.central_service.create_domain(context, values=values)

    def _test_create_domain_fail(self, values, exception):
        self.config(accepted_tlds_file='tlds-alpha-by-domain.txt.sample',
                    effective_tlds_file='effective_tld_names.dat.sample',
                    group='service:central')

        # The above configuration values are not overriden at the time when
        # the initializer is called to load the accepted and effective tld
        # lists.  So I need to call them again explicitly to load the correct
        # values
        self.central_service.effective_tld._load_accepted_tld_list()
        self.central_service.effective_tld._load_effective_tld_list()

        context = self.get_admin_context()
        with testtools.ExpectedException(exception):
            # Create an invalid domain
            self.central_service.create_domain(context, values=values)

    def test_create_domain_invalid_tld_fail(self):
        self.config(accepted_tlds_file='tlds-alpha-by-domain.txt.sample',
                    effective_tlds_file='effective_tld_names.dat.sample',
                    group='service:central')

        # The above configuration values are not overriden at the time when
        # the initializer is called to load the accepted and effective tld
        # lists.  So I need to call them again explicitly to load the correct
        # values
        self.central_service.effective_tld._load_accepted_tld_list()
        self.central_service.effective_tld._load_effective_tld_list()

        context = self.get_admin_context()

        # Create a server
        self.create_server()

        values = dict(
            name='invalid.cOM.',
            email='info@invalid.com'
        )

        # Create a valid domain
        self.central_service.create_domain(context, values=values)

        values = dict(
            name='invalid.NeT1.',
            email='info@invalid.com'
        )

        with testtools.ExpectedException(exceptions.InvalidTLD):
            # Create an invalid domain
            self.central_service.create_domain(context, values=values)

    def test_create_domain_effective_tld_fail(self):
        values = dict(
            name='co.ug',
            email='info@invalid.com'
        )

        self._test_create_domain_fail(values,
                                      exceptions.DomainIsSameAsAnEffectiveTLD)

    def test_idn_create_domain_effective_tld_fail(self):
        # Test creation of the effective TLD - brønnøysund.no
        values = dict(
            name='xn--brnnysund-m8ac.no',
            email='info@invalid.com'
        )

        self._test_create_domain_fail(values,
                                      exceptions.DomainIsSameAsAnEffectiveTLD)

    def test_create_domain_re_effective_tld_fail(self):
        # co.uk is in the regular expression list for effective_tlds
        values = dict(
            name='co.uk',
            email='info@invalid.com'
        )

        self._test_create_domain_fail(values,
                                      exceptions.DomainIsSameAsAnEffectiveTLD)

    def test_find_domains(self):
        context = self.get_admin_context()

        # Ensure we have no domains to start with.
        domains = self.central_service.find_domains(context)
        self.assertEqual(len(domains), 0)

        # Create a single domain (using default values)
        self.create_domain()

        # Ensure we can retrieve the newly created domain
        domains = self.central_service.find_domains(context)
        self.assertEqual(len(domains), 1)
        self.assertEqual(domains[0]['name'], 'example.com.')

        # Create a second domain
        self.create_domain(name='example.net.')

        # Ensure we can retrieve both domain
        domains = self.central_service.find_domains(context)
        self.assertEqual(len(domains), 2)
        self.assertEqual(domains[0]['name'], 'example.com.')
        self.assertEqual(domains[1]['name'], 'example.net.')

    def test_find_domains_criteria(self):
        context = self.get_admin_context()

        # Create a domain
        domain_name = '%d.example.com.' % random.randint(10, 1000)
        expected_domain = self.create_domain(name=domain_name)

        # Retrieve it, and ensure it's the same
        criterion = {'name': domain_name}
        domains = self.central_service.find_domains(context, criterion)
        self.assertEqual(domains[0]['id'], expected_domain['id'])
        self.assertEqual(domains[0]['name'], expected_domain['name'])
        self.assertEqual(domains[0]['email'], expected_domain['email'])

    def test_find_domains_tenant_restrictions(self):
        admin_context = self.get_admin_context()
        tenant_one_context = self.get_context(tenant=1)
        tenant_two_context = self.get_context(tenant=2)

        # Ensure we have no domains to start with.
        domains = self.central_service.find_domains(admin_context)
        self.assertEqual(len(domains), 0)

        # Create a single domain (using default values)
        self.create_domain(context=tenant_one_context)

        # Ensure admins can retrieve the newly created domain
        domains = self.central_service.find_domains(admin_context)
        self.assertEqual(len(domains), 1)
        self.assertEqual(domains[0]['name'], 'example.com.')

        # Ensure tenant=1 can retrieve the newly created domain
        domains = self.central_service.find_domains(tenant_one_context)
        self.assertEqual(len(domains), 1)
        self.assertEqual(domains[0]['name'], 'example.com.')

        # Ensure tenant=2 can NOT retrieve the newly created domain
        domains = self.central_service.find_domains(tenant_two_context)
        self.assertEqual(len(domains), 0)

    def test_get_domain(self):
        context = self.get_admin_context()

        # Create a domain
        domain_name = '%d.example.com.' % random.randint(10, 1000)
        expected_domain = self.create_domain(name=domain_name)

        # Retrieve it, and ensure it's the same
        domain = self.central_service.get_domain(context,
                                                 expected_domain['id'])
        self.assertEqual(domain['id'], expected_domain['id'])
        self.assertEqual(domain['name'], expected_domain['name'])
        self.assertEqual(domain['email'], expected_domain['email'])

    def test_get_domain_servers(self):
        context = self.get_admin_context()

        # Create a domain
        domain = self.create_domain()

        # Retrieve the servers list
        servers = self.central_service.get_domain_servers(context,
                                                          domain['id'])
        self.assertTrue(len(servers) > 0)

    def test_find_domain(self):
        context = self.get_admin_context()

        # Create a domain
        domain_name = '%d.example.com.' % random.randint(10, 1000)
        expected_domain = self.create_domain(name=domain_name)

        # Retrieve it, and ensure it's the same
        criterion = {'name': domain_name}
        domain = self.central_service.find_domain(context, criterion)
        self.assertEqual(domain['id'], expected_domain['id'])
        self.assertEqual(domain['name'], expected_domain['name'])
        self.assertEqual(domain['email'], expected_domain['email'])
        self.assertIn('status', domain)

    def test_update_domain(self):
        context = self.get_admin_context()

        # Create a domain
        expected_domain = self.create_domain()

        # Reset the list of notifications
        self.reset_notifications()

        # Update the domain
        values = dict(email='new@example.com')
        self.central_service.update_domain(context, expected_domain['id'],
                                           values=values)

        # Fetch the domain again
        domain = self.central_service.get_domain(context,
                                                 expected_domain['id'])

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
        context = self.get_admin_context()

        # Create a domain
        expected_domain = self.create_domain()

        # Update the domain
        values = dict(email='new@example.com')
        self.central_service.update_domain(context, expected_domain['id'],
                                           values=values,
                                           increment_serial=False)

        # Fetch the domain again
        domain = self.central_service.get_domain(context,
                                                 expected_domain['id'])

        # Ensure the domain was updated correctly
        self.assertEqual(domain['serial'], expected_domain['serial'])
        self.assertEqual(domain['email'], 'new@example.com')

    def test_update_domain_name_fail(self):
        context = self.get_admin_context()

        # Create a domain
        expected_domain = self.create_domain()

        # Update the domain
        with testtools.ExpectedException(exceptions.BadRequest):
            values = dict(name='renamed-domain.com.')
            self.central_service.update_domain(context, expected_domain['id'],
                                               values=values)

    def test_delete_domain(self):
        context = self.get_admin_context()

        # Create a domain
        domain = self.create_domain()

        # Reset the list of notifications
        self.reset_notifications()

        # Delete the domain
        self.central_service.delete_domain(context, domain['id'])

        # Fetch the domain again, ensuring an exception is raised
        with testtools.ExpectedException(exceptions.DomainNotFound):
            self.central_service.get_domain(context, domain['id'])

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
        context = self.get_admin_context()

        # Create the Parent Domain using fixture 0
        parent_domain = self.create_domain(fixture=0)

        # Create the subdomain
        self.create_domain(fixture=1, name='www.%s' % parent_domain['name'])

        # Attempt to delete the parent domain
        with testtools.ExpectedException(exceptions.DomainHasSubdomain):
            self.central_service.delete_domain(context, parent_domain['id'])

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
        context = self.get_admin_context()

        # Create a domain
        expected_domain = self.create_domain()

        # Touch the domain
        self.central_service.touch_domain(context, expected_domain['id'])

        # Fetch the domain again
        domain = self.central_service.get_domain(context,
                                                 expected_domain['id'])

        # Ensure the serial was incremented
        self.assertTrue(domain['serial'] > expected_domain['serial'])

    # Record Tests
    def test_create_record(self):
        context = self.get_admin_context()
        domain = self.create_domain()

        values = dict(
            name='www.%s' % domain['name'],
            type='A',
            data='127.0.0.1'
        )

        # Create a record
        record = self.central_service.create_record(context, domain['id'],
                                                    values=values)

        # Ensure all values have been set correctly
        self.assertIsNotNone(record['id'])
        self.assertIsNone(record['ttl'])
        self.assertEqual(record['name'], values['name'])
        self.assertEqual(record['type'], values['type'])
        self.assertEqual(record['data'], values['data'])
        self.assertIn('status', record)

    def test_create_record_over_quota(self):
        self.config(quota_domain_records=1)

        domain = self.create_domain()

        self.create_record(domain)

        with testtools.ExpectedException(exceptions.OverQuota):
            self.create_record(domain)

    def test_create_record_without_incrementing_serial(self):
        context = self.get_admin_context()
        domain = self.create_domain()

        values = dict(
            name='www.%s' % domain['name'],
            type='A',
            data='127.0.0.1'
        )

        # Create a record
        record = self.central_service.create_record(context, domain['id'],
                                                    values=values,
                                                    increment_serial=False)

        # Ensure all values have been set correctly
        self.assertIsNotNone(record['id'])
        self.assertIsNone(record['ttl'])
        self.assertEqual(record['name'], values['name'])
        self.assertEqual(record['type'], values['type'])
        self.assertEqual(record['data'], values['data'])

        # Ensure the domains serial number was not updated
        updated_domain = self.central_service.get_domain(context, domain['id'])
        self.assertEqual(domain['serial'], updated_domain['serial'])

    def test_create_cname_record_at_apex(self):
        context = self.get_admin_context()
        domain = self.create_domain()

        values = dict(
            name=domain['name'],
            type='CNAME',
            data='example.org.'
        )

        # Attempt to create a CNAME record at the apex
        with testtools.ExpectedException(exceptions.InvalidRecordLocation):
            self.central_service.create_record(context, domain['id'],
                                               values=values)

    def test_create_cname_record_above_an_a_record(self):
        context = self.get_admin_context()
        domain = self.create_domain()

        values = dict(
            name='t.www.%s' % domain['name'],
            type='A',
            data='127.0.0.1'
        )

        self.central_service.create_record(context, domain['id'],
                                           values=values)

        # Create a CNAME record alongside an A record
        values = dict(
            name='www.%s' % domain['name'],
            type='CNAME',
            data='example.org.'
        )

        record = self.central_service.create_record(context, domain['id'],
                                                    values=values)

        self.assertIn('id', record)

    def test_create_cname_record_below_an_a_record(self):
        context = self.get_admin_context()
        domain = self.create_domain()

        values = dict(
            name='t.%s' % domain['name'],
            type='A',
            data='127.0.0.1'
        )

        self.central_service.create_record(context, domain['id'],
                                           values=values)

        # Create a CNAME record alongside an A record
        values = dict(
            name='www.t.%s' % domain['name'],
            type='CNAME',
            data='example.org.'
        )

        record = self.central_service.create_record(context, domain['id'],
                                                    values=values)

        self.assertIn('id', record)

    def test_create_cname_record_alongside_an_a_record(self):
        context = self.get_admin_context()
        domain = self.create_domain()

        values = dict(
            name='www.%s' % domain['name'],
            type='A',
            data='127.0.0.1'
        )

        self.central_service.create_record(context, domain['id'],
                                           values=values)

        # Attempt to create a CNAME record alongside an A record
        with testtools.ExpectedException(exceptions.InvalidRecordLocation):
            values = dict(
                name='www.%s' % domain['name'],
                type='CNAME',
                data='example.org.'
            )

            self.central_service.create_record(context, domain['id'],
                                               values=values)

    def test_create_an_a_record_alongside_a_cname_record(self):
        context = self.get_admin_context()
        domain = self.create_domain()

        values = dict(
            name='www.%s' % domain['name'],
            type='CNAME',
            data='example.org.'
        )

        self.central_service.create_record(context, domain['id'],
                                           values=values)

        # Attempt to create a CNAME record alongside an A record
        with testtools.ExpectedException(exceptions.InvalidRecordLocation):
            values = dict(
                name='www.%s' % domain['name'],
                type='A',
                data='127.0.0.1'
            )

            self.central_service.create_record(context, domain['id'],
                                               values=values)

    def test_create_duplicate_ptr_record(self):
        context = self.get_admin_context()
        domain = self.create_domain(values={'name': '2.0.192.in-addr.arpa.'})

        values = dict(
            name='1.%s' % domain['name'],
            type='PTR',
            data='www.example.org.'
        )

        self.central_service.create_record(context, domain['id'],
                                           values=values)

        # Attempt to create a second PTR with the same name.
        with testtools.ExpectedException(exceptions.DuplicateRecord):
            values = dict(
                name='1.%s' % domain['name'],
                type='PTR',
                data='www.example.com.'
            )

            self.central_service.create_record(context, domain['id'],
                                               values=values)

    def test_find_records(self):
        context = self.get_admin_context()
        domain = self.create_domain()

        # Ensure we have no records to start with.
        records = self.central_service.find_records(context, domain['id'])
        self.assertEqual(len(records), 0)

        # Create a single record (using default values)
        self.create_record(domain)

        # Ensure we can retrieve the newly created record
        records = self.central_service.find_records(context, domain['id'])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['name'], 'www.%s' % domain['name'])

        # Create a second record
        self.create_record(domain, name='mail.%s' % domain['name'])

        # Ensure we can retrieve both records
        records = self.central_service.find_records(context, domain['id'])
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]['name'], 'www.%s' % domain['name'])
        self.assertEqual(records[1]['name'], 'mail.%s' % domain['name'])

    def test_get_record(self):
        context = self.get_admin_context()
        domain = self.create_domain()

        # Create a record
        record_name = '%d.%s' % (random.randint(10, 1000), domain['name'])
        expected_record = self.create_record(domain, name=record_name)

        # Retrieve it, and ensure it's the same
        record = self.central_service.get_record(context, domain['id'],
                                                 expected_record['id'])
        self.assertEqual(record['id'], expected_record['id'])
        self.assertEqual(record['name'], expected_record['name'])
        self.assertIn('status', record)

    def test_find_record(self):
        context = self.get_admin_context()
        domain = self.create_domain()

        # Create a record
        record_name = '%d.%s' % (random.randint(10, 1000), domain['name'])
        expected_record = self.create_record(domain, name=record_name)

        # Retrieve it, and ensure it's the same
        criterion = {'name': record_name}
        record = self.central_service.find_record(context, domain['id'],
                                                  criterion)
        self.assertEqual(record['id'], expected_record['id'])
        self.assertEqual(record['name'], expected_record['name'])
        self.assertIn('status', record)

    def test_get_record_incorrect_domain_id(self):
        context = self.get_admin_context()
        domain = self.create_domain()
        other_domain = self.create_domain(fixture=1)

        # Create a record
        record_name = '%d.%s' % (random.randint(10, 1000), domain['name'])
        expected_record = self.create_record(domain, name=record_name)

        # Ensure we get a 404 if we use the incorrect domain_id
        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.central_service.get_record(context, other_domain['id'],
                                            expected_record['id'])

    def test_update_record(self):
        context = self.get_admin_context()
        domain = self.create_domain()

        # Create a record
        expected_record = self.create_record(domain)

        # Update the record
        values = dict(data='127.0.0.2')
        self.central_service.update_record(context, domain['id'],
                                           expected_record['id'],
                                           values=values)

        # Fetch the record again
        record = self.central_service.get_record(context, domain['id'],
                                                 expected_record['id'])

        # Ensure the record was updated correctly
        self.assertEqual(record['data'], '127.0.0.2')

    def test_update_record_without_incrementing_serial(self):
        context = self.get_admin_context()
        domain = self.create_domain()

        # Create a record
        expected_record = self.create_record(domain)

        # Fetch the domain so we have the latest serial number
        domain_before = self.central_service.get_domain(context, domain['id'])

        # Update the record
        values = dict(data='127.0.0.2')
        self.central_service.update_record(context,
                                           domain['id'],
                                           expected_record['id'],
                                           values,
                                           increment_serial=False)

        # Fetch the record again
        record = self.central_service.get_record(context, domain['id'],
                                                 expected_record['id'])

        # Ensure the record was updated correctly
        self.assertEqual(record['data'], '127.0.0.2')

        # Ensure the domains serial number was not updated
        domain_after = self.central_service.get_domain(context, domain['id'])
        self.assertEqual(domain_before['serial'], domain_after['serial'])

    def test_update_record_incorrect_domain_id(self):
        context = self.get_admin_context()
        domain = self.create_domain()
        other_domain = self.create_domain(fixture=1)

        # Create a record
        expected_record = self.create_record(domain)

        # Update the record
        values = dict(data='127.0.0.2')

        # Ensure we get a 404 if we use the incorrect domain_id
        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.central_service.update_record(context, other_domain['id'],
                                               expected_record['id'],
                                               values=values)

    def test_update_record_duplicate_ptr(self):
        context = self.get_admin_context()
        domain = self.create_domain(values={'name': '2.0.192.in-addr.arpa.'})

        values = dict(
            name='1.%s' % domain['name'],
            type='PTR',
            data='www.example.org.'
        )

        self.central_service.create_record(context, domain['id'],
                                           values=values)

        values = dict(
            name='2.%s' % domain['name'],
            type='PTR',
            data='www.example.org.'
        )

        record = self.central_service.create_record(context, domain['id'],
                                                    values=values)

        # Attempt to create a second PTR with the same name.
        with testtools.ExpectedException(exceptions.DuplicateRecord):
            values = dict(
                name='1.%s' % domain['name']
            )

            self.central_service.update_record(context, domain['id'],
                                               record['id'],
                                               values=values)

    def test_update_record_cname_data(self):
        context = self.get_admin_context()
        domain = self.create_domain()

        # Create a record
        expected_record = self.create_record(domain, type='CNAME',
                                             data='example.org.')

        # Update the record
        values = dict(data='example.com.')
        self.central_service.update_record(context, domain['id'],
                                           expected_record['id'],
                                           values=values)

        # Fetch the record again
        record = self.central_service.get_record(context, domain['id'],
                                                 expected_record['id'])

        # Ensure the record was updated correctly
        self.assertEqual(record['data'], 'example.com.')

    def test_update_record_ptr_data(self):
        context = self.get_admin_context()
        domain = self.create_domain(name='2.0.192.in-addr.arpa.')

        # Create a record
        expected_record = self.create_record(
            domain,
            type='PTR',
            name='1.2.0.192.in-addr.arpa.',
            data='example.org.')

        # Update the record
        values = dict(data='example.com.')
        self.central_service.update_record(context, domain['id'],
                                           expected_record['id'],
                                           values=values)

        # Fetch the record again
        record = self.central_service.get_record(context, domain['id'],
                                                 expected_record['id'])

        # Ensure the record was updated correctly
        self.assertEqual(record['data'], 'example.com.')

    def test_delete_record(self):
        context = self.get_admin_context()
        domain = self.create_domain()

        # Create a record
        record = self.create_record(domain)

        # Delete the record
        self.central_service.delete_record(context, domain['id'], record['id'])

        # Fetch the record again, ensuring an exception is raised
        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.central_service.get_record(context, domain['id'],
                                            record['id'])

    def test_delete_record_without_incrementing_serial(self):
        context = self.get_admin_context()
        domain = self.create_domain()

        # Create a record
        record = self.create_record(domain)

        # Fetch the domain so we have the latest serial number
        domain_before = self.central_service.get_domain(context, domain['id'])

        # Delete the record
        self.central_service.delete_record(context, domain['id'], record['id'],
                                           increment_serial=False)

        # Fetch the record again, ensuring an exception is raised
        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.central_service.get_record(context, domain['id'],
                                            record['id'])

        # Ensure the domains serial number was not updated
        domain_after = self.central_service.get_domain(context, domain['id'])
        self.assertEqual(domain_before['serial'], domain_after['serial'])

    def test_delete_record_incorrect_domain_id(self):
        context = self.get_admin_context()
        domain = self.create_domain()
        other_domain = self.create_domain(fixture=1)

        # Create a record
        record = self.create_record(domain)

        # Ensure we get a 404 if we use the incorrect domain_id
        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.central_service.delete_record(context, other_domain['id'],
                                               record['id'])

    def test_count_records(self):
        # in the beginning, there should be nothing
        records = self.central_service.count_records(self.admin_context)
        self.assertEqual(records, 0)

        # Create a domain to put our record in
        domain = self.create_domain()

        # Create a record
        self.create_record(domain)

        # we should have 1 record now
        records = self.central_service.count_domains(self.admin_context)
        self.assertEqual(records, 1)

    def test_count_records_policy_check(self):
        # Set the policy to reject the authz
        self.policy({'count_records': '!'})

        with testtools.ExpectedException(exceptions.Forbidden):
            self.central_service.count_records(self.get_context())
