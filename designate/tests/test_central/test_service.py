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
import copy
import random

import mock
import testtools
from testtools.matchers import GreaterThan
from oslo.config import cfg
from oslo_log import log as logging
from oslo_db import exception as db_exception
from oslo_messaging.notify import notifier

from designate import exceptions
from designate import objects
from designate.tests.test_central import CentralTestCase

LOG = logging.getLogger(__name__)


class CentralServiceTest(CentralTestCase):
    def test_stop(self):
        # Test stopping the service
        self.central_service.stop()

    def test_start_with_tlds(self):
        # Stop Service
        self.central_service.stop()

        list = objects.TldList()
        list.append(objects.Tld(name='com.'))

        with mock.patch.object(self.central_service.storage, 'find_tlds',
                return_value=list):
            self.central_service.start()
            self.assertTrue(self.central_service.check_for_tlds)

    def test_is_valid_domain_name(self):
        self.config(max_domain_name_len=10,
                    group='service:central')

        context = self.get_context()

        self.central_service._is_valid_domain_name(context, 'valid.org.')

        with testtools.ExpectedException(exceptions.InvalidDomainName):
            self.central_service._is_valid_domain_name(context, 'example.org.')

        with testtools.ExpectedException(exceptions.InvalidDomainName):
            self.central_service._is_valid_domain_name(context, 'example.tld.')

        with testtools.ExpectedException(exceptions.InvalidDomainName):
            self.central_service._is_valid_domain_name(context, 'tld.')

    def test_is_valid_domain_name_with_tlds(self):
        # Stop Service
        self.central_service.stop()
        list = objects.TldList()
        list.append(objects.Tld(name='com'))
        list.append(objects.Tld(name='biz'))
        list.append(objects.Tld(name='z'))

        with mock.patch.object(self.central_service.storage, 'find_tlds',
                return_value=list):
            self.central_service.start()

        context = self.get_context()
        with mock.patch.object(self.central_service.storage, 'find_tld',
                return_value=objects.Tld(name='biz')):
            with testtools.ExpectedException(exceptions.InvalidDomainName):
                self.central_service._is_valid_domain_name(context, 'biz.')

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

        with testtools.ExpectedException(ValueError):
            self.central_service._is_valid_recordset_name(
                context, domain, 'invalidtld.example.org')

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
        domain = self.create_domain(name='example.org.')

        result = self.central_service._is_subdomain(
            context, 'org.', domain.pool_id)
        self.assertFalse(result)

        result = self.central_service._is_subdomain(
            context, 'www.example.net.', domain.pool_id)
        self.assertFalse(result)

        result = self.central_service._is_subdomain(
            context, 'example.org.', domain.pool_id)
        self.assertFalse(result)

        result = self.central_service._is_subdomain(
            context, 'www.example.org.', domain.pool_id)
        self.assertTrue(result)

    def test_is_superdomain(self):
        context = self.get_context()

        # Create a domain (using the specified domain name)
        domain = self.create_domain(name='example.org.')

        LOG.debug("Testing 'org.'")
        result = self.central_service._is_superdomain(
            context, 'org.', domain.pool_id)
        self.assertTrue(result)

        LOG.debug("Testing 'www.example.net.'")
        result = self.central_service._is_superdomain(
            context, 'www.example.net.', domain.pool_id)
        self.assertFalse(result)

        LOG.debug("Testing 'www.example.org.'")
        result = self.central_service._is_superdomain(
            context, 'www.example.org.', domain.pool_id)
        self.assertFalse(result)

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

    def test_is_valid_ttl(self):
        self.policy({'use_low_ttl': '!'})
        self.config(min_ttl="100",
                    group='service:central')
        context = self.get_context()

        values = self.get_domain_fixture(fixture=1)
        values['ttl'] = 0

        with testtools.ExpectedException(exceptions.InvalidTTL):
                    self.central_service._is_valid_ttl(
                        context, values['ttl'])

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
        tld = self.create_tld(name='org.')

        # Update the Object
        tld.name = 'net.'

        # Perform the update
        self.central_service.update_tld(self.admin_context, tld)

        # Fetch the tld again
        tld = self.central_service.get_tld(self.admin_context, tld.id)

        # Ensure the tld was updated correctly
        self.assertEqual('net.', tld.name)

    def test_delete_tld(self):
        # Create a tld
        tld = self.create_tld(fixture=0)
        # Delete the tld
        self.central_service.delete_tld(self.admin_context, tld['id'])

        # Fetch the tld again, ensuring an exception is raised
        self.assertRaises(
            exceptions.TldNotFound,
            self.central_service.get_tld,
            self.admin_context, tld['id'])

    # TsigKey Tests
    def test_create_tsigkey(self):
        values = self.get_tsigkey_fixture(fixture=0)

        # Create a tsigkey
        tsigkey = self.central_service.create_tsigkey(
            self.admin_context, tsigkey=objects.TsigKey.from_dict(values))

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
        # Create a tsigkey
        tsigkey = self.create_tsigkey(name='test-key')

        # Update the Object
        tsigkey.name = 'test-key-updated'

        # Perform the update
        self.central_service.update_tsigkey(self.admin_context, tsigkey)

        # Fetch the tsigkey again
        tsigkey = self.central_service.get_tsigkey(
            self.admin_context, tsigkey.id)

        # Ensure the new value took
        self.assertEqual('test-key-updated', tsigkey.name)

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
    @mock.patch.object(notifier.Notifier, "info")
    def _test_create_domain(self, values, mock_notifier):
        # Reset the mock to avoid the calls from the create_nameserver() call
        mock_notifier.reset_mock()

        # Create a domain
        domain = self.central_service.create_domain(
            self.admin_context, domain=objects.Domain.from_dict(values))

        # Ensure all values have been set correctly
        self.assertIsNotNone(domain['id'])
        self.assertEqual(domain['name'], values['name'])
        self.assertEqual(domain['email'], values['email'])
        self.assertIn('status', domain)

        self.assertEqual(mock_notifier.call_count, 1)

        # Ensure the correct NS Records are in place
        pool = self.central_service.get_pool(
            self.admin_context, domain.pool_id)

        ns_recordset = self.central_service.find_recordset(
            self.admin_context,
            criterion={'domain_id': domain.id, 'type': "NS"})

        self.assertIsNotNone(ns_recordset.id)
        self.assertEqual(ns_recordset.type, 'NS')
        self.assertIsNotNone(ns_recordset.records)
        self.assertEqual(set([n.hostname for n in pool.ns_records]),
                         set([n.data for n in ns_recordset.records]))

        mock_notifier.assert_called_once_with(
            self.admin_context, 'dns.domain.create', domain)
        return domain

    def test_create_domain_duplicate_different_pools(self):
        fixture = self.get_domain_fixture()

        # Create first domain that's placed in default pool
        self.create_domain(**fixture)

        # Create a secondary pool
        second_pool = self.create_pool()
        fixture["pool_id"] = second_pool.id

        self.create_domain(**fixture)

    def test_create_domain_over_tld(self):
        values = dict(
            name='example.com.',
            email='info@example.com',
            type='PRIMARY'
        )
        self._test_create_domain(values)

    def test_idn_create_domain_over_tld(self):
        values = dict(
            name='xn--3e0b707e'
        )

        # Create the appropriate TLD
        self.central_service.create_tld(
            self.admin_context, objects.Tld.from_dict(values))

        # Test creation of a domain in 한국 (kr)
        values = dict(
            name='example.xn--3e0b707e.',
            email='info@example.xn--3e0b707e',
            type='PRIMARY'
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
        values = self.get_domain_fixture(fixture=1)
        values['name'] = 'www.%s' % parent_domain['name']

        # Create the subdomain
        domain = self.central_service.create_domain(
            self.admin_context, objects.Domain.from_dict(values))

        # Ensure all values have been set correctly
        self.assertIsNotNone(domain['id'])
        self.assertEqual(domain['parent_domain_id'], parent_domain['id'])

    def test_create_subdomain_different_pools(self):
        fixture = self.get_domain_fixture()

        # Create first domain that's placed in default pool
        self.create_domain(**fixture)

        # Create a secondary pool
        second_pool = self.create_pool()
        fixture["pool_id"] = second_pool.id
        fixture["name"] = "sub.%s" % fixture["name"]

        subdomain = self.create_domain(**fixture)
        self.assertIsNone(subdomain.parent_domain_id)

    def test_create_superdomain(self):
        # Prepare values for the domain and subdomain
        # using fixture 1 as a base
        domain_values = self.get_domain_fixture(fixture=1)

        subdomain_values = copy.deepcopy(domain_values)
        subdomain_values['name'] = 'www.%s' % domain_values['name']
        subdomain_values['context'] = self.admin_context

        LOG.debug("domain_values: {0}".format(domain_values))
        LOG.debug("subdomain_values: {0}".format(subdomain_values))

        # Create the subdomain
        subdomain = self.create_domain(**subdomain_values)

        # Create the Parent Domain using fixture 1
        parent_domain = self.central_service.create_domain(
            self.admin_context, objects.Domain.from_dict(domain_values))

        # Get updated subdomain values
        subdomain = self.central_service.get_domain(self.admin_context,
                                                    subdomain.id)

        # Ensure all values have been set correctly
        self.assertIsNotNone(parent_domain['id'])
        self.assertEqual(subdomain['parent_domain_id'], parent_domain['id'])

    def test_create_subdomain_failure(self):
        context = self.get_admin_context()

        # Explicitly set a tenant_id
        context.tenant = '1'

        # Create the Parent Domain using fixture 0
        parent_domain = self.create_domain(fixture=0, context=context)

        context = self.get_admin_context()

        # Explicitly use a different tenant_id
        context.tenant = '2'

        # Prepare values for the subdomain using fixture 1 as a base
        values = self.get_domain_fixture(fixture=1)
        values['name'] = 'www.%s' % parent_domain['name']

        # Attempt to create the subdomain
        with testtools.ExpectedException(exceptions.Forbidden):
            self.central_service.create_domain(
                context, objects.Domain.from_dict(values))

    def test_create_superdomain_failure(self):
        context = self.get_admin_context()

        # Explicitly set a tenant_id
        context.tenant = '1'

        # Set up domain and subdomain values
        domain_values = self.get_domain_fixture(fixture=1)
        domain_name = domain_values['name']

        subdomain_values = copy.deepcopy(domain_values)
        subdomain_values['name'] = 'www.%s' % domain_name
        subdomain_values['context'] = context

        # Create sub domain
        self.create_domain(**subdomain_values)

        context = self.get_admin_context()

        # Explicitly use a different tenant_id
        context.tenant = '2'

        # Attempt to create the domain
        with testtools.ExpectedException(exceptions.Forbidden):
            self.central_service.create_domain(
                context, objects.Domain.from_dict(domain_values))

    def test_create_blacklisted_domain_success(self):
        # Create blacklisted zone using default values
        self.create_blacklist()

        # Set the policy to accept the authz
        self.policy({'use_blacklisted_domain': '@'})

        values = dict(
            name='blacklisted.com.',
            email='info@blacklisted.com'
        )

        # Create a zone that is blacklisted
        domain = self.central_service.create_domain(
            self.admin_context, objects.Domain.from_dict(values))

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
                self.admin_context, objects.Domain.from_dict(values))

    def _test_create_domain_fail(self, values, exception):

        with testtools.ExpectedException(exception):
            # Create an invalid domain
            self.central_service.create_domain(
                self.admin_context, objects.Domain.from_dict(values))

    def test_create_domain_invalid_tld_fail(self):
        # add a tld for com
        self.create_tld(fixture=0)

        values = dict(
            name='example.com.',
            email='info@example.com'
        )

        # Create a valid domain
        self.central_service.create_domain(
            self.admin_context, objects.Domain.from_dict(values))

        values = dict(
            name='example.net.',
            email='info@example.net'
        )

        # There is no TLD for net so it should fail
        with testtools.ExpectedException(exceptions.InvalidDomainName):
            # Create an invalid domain
            self.central_service.create_domain(
                self.admin_context, objects.Domain.from_dict(values))

    def test_create_domain_invalid_ttl_fail(self):
        self.policy({'use_low_ttl': '!'})
        self.config(min_ttl="100",
                    group='service:central')
        context = self.get_context()

        values = self.get_domain_fixture(fixture=1)
        values['ttl'] = 0

        with testtools.ExpectedException(exceptions.InvalidTTL):
                    self.central_service.create_domain(
                        context, objects.Domain.from_dict(values))

    def test_create_domain_no_min_ttl(self):
        self.policy({'use_low_ttl': '!'})
        self.config(min_ttl="None",
                    group='service:central')
        values = self.get_domain_fixture(fixture=1)
        values['ttl'] = -100

        # Create domain with random TTL
        domain = self.central_service.create_domain(
            self.admin_context, objects.Domain.from_dict(values))

        # Ensure all values have been set correctly
        self.assertEqual(domain['ttl'], values['ttl'])

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

    @mock.patch.object(notifier.Notifier, "info")
    def test_update_domain(self, mock_notifier):
        # Create a domain
        domain = self.create_domain(email='info@example.org')
        original_serial = domain.serial

        # Update the object
        domain.email = 'info@example.net'

        # Reset the mock to avoid the calls from the create_domain() call
        mock_notifier.reset_mock()

        # Perform the update
        self.central_service.update_domain(self.admin_context, domain)

        # Fetch the domain again
        domain = self.central_service.get_domain(
            self.admin_context, domain.id)

        # Ensure the domain was updated correctly
        self.assertTrue(domain.serial > original_serial)
        self.assertEqual('info@example.net', domain.email)

        self.assertEqual(mock_notifier.call_count, 1)

        # Check that the object used in the notify is a Domain and the id
        # matches up
        notified_domain = mock_notifier.call_args[0][-1]
        self.assertIsInstance(notified_domain, objects.Domain)
        self.assertEqual(domain.id, notified_domain.id)

        mock_notifier.assert_called_once_with(
            self.admin_context, 'dns.domain.update', mock.ANY)

    def test_update_domain_without_id(self):
        # Create a domain
        domain = self.create_domain(email='info@example.org')

        # Update the object
        domain.email = 'info@example.net'
        domain.id = None
        # Perform the update
        with testtools.ExpectedException(Exception):
            self.central_service.update_domain(self.admin_context, domain)

    def test_update_domain_without_incrementing_serial(self):
        # Create a domain
        domain = self.create_domain(email='info@example.org')
        original_serial = domain.serial

        # Update the object
        domain.email = 'info@example.net'

        # Perform the update
        self.central_service.update_domain(
            self.admin_context, domain, increment_serial=False)

        # Fetch the domain again
        domain = self.central_service.get_domain(self.admin_context, domain.id)

        # Ensure the domain was updated correctly
        self.assertEqual(original_serial, domain.serial)
        self.assertEqual('info@example.net', domain.email)

    def test_update_domain_name_fail(self):
        # Create a domain
        domain = self.create_domain(name='example.org.')

        # Update the Object
        domain.name = 'example.net.'

        # Perform the update
        with testtools.ExpectedException(exceptions.BadRequest):
            self.central_service.update_domain(self.admin_context, domain)

    def test_update_domain_deadlock_retry(self):
        # Create a domain
        domain = self.create_domain(name='example.org.')
        original_serial = domain.serial

        # Update the Object
        domain.email = 'info@example.net'

        # Due to Python's scoping of i - we need to make it a mutable type
        # for the counter to work.. In Py3, we can use the nonlocal keyword.
        i = [False]

        def fail_once_then_pass():
            if i[0] is True:
                return self.central_service.storage.session.commit()
            else:
                i[0] = True
                raise db_exception.DBDeadlock()

        with mock.patch.object(self.central_service.storage, 'commit',
                          side_effect=fail_once_then_pass):
            # Perform the update
            domain = self.central_service.update_domain(
                self.admin_context, domain)

        # Ensure i[0] is True, indicating the side_effect code above was
        # triggered
        self.assertTrue(i[0])

        # Ensure the domain was updated correctly
        self.assertTrue(domain.serial > original_serial)
        self.assertEqual('info@example.net', domain.email)

    @mock.patch.object(notifier.Notifier, "info")
    def test_delete_domain(self, mock_notifier):
        # Create a domain
        domain = self.create_domain()

        mock_notifier.reset_mock()

        # Delete the domain
        self.central_service.delete_domain(self.admin_context, domain['id'])

        # Fetch the domain
        deleted_domain = self.central_service.get_domain(
            self.admin_context, domain['id'])

        # Ensure the domain is marked for deletion
        self.assertEqual(deleted_domain.id, domain.id)
        self.assertEqual(deleted_domain.name, domain.name)
        self.assertEqual(deleted_domain.email, domain.email)
        self.assertEqual(deleted_domain.status, 'PENDING')
        self.assertEqual(deleted_domain.tenant_id, domain.tenant_id)
        self.assertEqual(deleted_domain.parent_domain_id,
                         domain.parent_domain_id)
        self.assertEqual(deleted_domain.action, 'DELETE')
        self.assertEqual(deleted_domain.serial, domain.serial)
        self.assertEqual(deleted_domain.pool_id, domain.pool_id)

        self.assertEqual(mock_notifier.call_count, 1)

        # Check that the object used in the notify is a Domain and the id
        # matches up
        notified_domain = mock_notifier.call_args[0][-1]
        self.assertIsInstance(notified_domain, objects.Domain)
        self.assertEqual(deleted_domain.id, notified_domain.id)

        mock_notifier.assert_called_once_with(
            self.admin_context, 'dns.domain.delete', mock.ANY)

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

    def test_xfr_domain(self):
        # Create a domain
        fixture = self.get_domain_fixture('SECONDARY', 0)
        fixture['email'] = cfg.CONF['service:central'].managed_resource_email
        fixture['attributes'] = [{"key": "master", "value": "10.0.0.10"}]

        # Create a zone
        secondary = self.create_domain(**fixture)

        self.central_service.xfr_domain(self.admin_context, secondary.id)

    def test_xfr_domain_invalid_type(self):
        domain = self.create_domain()

        with testtools.ExpectedException(exceptions.BadRequest):
            self.central_service.xfr_domain(self.admin_context, domain.id)

    # RecordSet Tests
    def test_create_recordset(self):
        domain = self.create_domain()
        original_serial = domain.serial

        # Create the Object
        recordset = objects.RecordSet(name='www.%s' % domain.name, type='A')

        # Persist the Object
        recordset = self.central_service.create_recordset(
            self.admin_context, domain.id, recordset=recordset)

        # Get the zone again to check if serial increased
        updated_domain = self.central_service.get_domain(self.admin_context,
                                                         domain.id)
        new_serial = updated_domain.serial

        # Ensure all values have been set correctly
        self.assertIsNotNone(recordset.id)
        self.assertEqual('www.%s' % domain.name, recordset.name)
        self.assertEqual('A', recordset.type)

        self.assertIsNotNone(recordset.records)
        # The serial number does not get updated is there are no records
        # in the recordset
        self.assertEqual(new_serial, original_serial)

    def test_create_recordset_with_records(self):
        domain = self.create_domain()
        original_serial = domain.serial

        # Create the Object
        recordset = objects.RecordSet(
            name='www.%s' % domain.name,
            type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.3.3.15'),
                objects.Record(data='192.3.3.16'),
            ])
        )

        # Persist the Object
        recordset = self.central_service.create_recordset(
            self.admin_context, domain.id, recordset=recordset)

        # Get updated serial number
        updated_zone = self.central_service.get_domain(self.admin_context,
                                                       domain.id)
        new_serial = updated_zone.serial

        # Ensure all values have been set correctly
        self.assertIsNotNone(recordset.records)
        self.assertEqual(2, len(recordset.records))
        self.assertIsNotNone(recordset.records[0].id)
        self.assertIsNotNone(recordset.records[1].id)
        self.assertThat(new_serial, GreaterThan(original_serial))

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
                self.admin_context,
                domain['id'],
                recordset=objects.RecordSet.from_dict(values))

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
                self.admin_context,
                domain['id'],
                recordset=objects.RecordSet.from_dict(values))

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
                self.admin_context,
                domain['id'],
                recordset=objects.RecordSet.from_dict(values))

    def test_create_invalid_recordset_ttl(self):
        self.policy({'use_low_ttl': '!'})
        self.config(min_ttl="100",
                    group='service:central')
        domain = self.create_domain()

        values = dict(
            name='www.%s' % domain['name'],
            type='A',
            ttl=10
        )

        # Attempt to create a A record under the TTL
        with testtools.ExpectedException(exceptions.InvalidTTL):
            self.central_service.create_recordset(
                self.admin_context,
                domain['id'],
                recordset=objects.RecordSet.from_dict(values))

    def test_create_recordset_no_min_ttl(self):
        self.policy({'use_low_ttl': '!'})
        self.config(min_ttl="None",
                    group='service:central')
        domain = self.create_domain()

        values = dict(
            name='www.%s' % domain['name'],
            type='A',
            ttl=10
        )

        recordset = self.central_service.create_recordset(
            self.admin_context,
            domain['id'],
            recordset=objects.RecordSet.from_dict(values))
        self.assertEqual(recordset['ttl'], values['ttl'])

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

    def test_get_recordset_with_records(self):
        domain = self.create_domain()

        # Create a recordset and two records
        recordset = self.create_recordset(domain)
        self.create_record(domain, recordset)
        self.create_record(domain, recordset, fixture=1)

        # Retrieve it, and ensure it's the same
        recordset = self.central_service.get_recordset(
            self.admin_context, domain.id, recordset.id)

        self.assertEqual(2, len(recordset.records))
        self.assertIsNotNone(recordset.records[0].id)
        self.assertIsNotNone(recordset.records[1].id)

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

        # Ensure we have two recordsets to start with as SOA & NS
        # recordsets are created automatically
        recordsets = self.central_service.find_recordsets(
            self.admin_context, criterion)

        self.assertEqual(len(recordsets), 2)

        # Create a single recordset (using default values)
        self.create_recordset(domain, name='www.%s' % domain['name'])

        # Ensure we can retrieve the newly created recordset
        recordsets = self.central_service.find_recordsets(
            self.admin_context, criterion)

        self.assertEqual(len(recordsets), 3)
        self.assertEqual(recordsets[2]['name'], 'www.%s' % domain['name'])

        # Create a second recordset
        self.create_recordset(domain, name='mail.%s' % domain['name'])

        # Ensure we can retrieve both recordsets
        recordsets = self.central_service.find_recordsets(
            self.admin_context, criterion)

        self.assertEqual(len(recordsets), 4)
        self.assertEqual(recordsets[2]['name'], 'www.%s' % domain['name'])
        self.assertEqual(recordsets[3]['name'], 'mail.%s' % domain['name'])

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

    def test_find_recordset_with_records(self):
        domain = self.create_domain()

        # Create a recordset
        recordset = self.create_recordset(domain)
        self.create_record(domain, recordset)
        self.create_record(domain, recordset, fixture=1)

        # Retrieve it, and ensure it's the same
        criterion = {'domain_id': domain.id, 'name': recordset.name}

        recordset = self.central_service.find_recordset(
            self.admin_context, criterion)

        self.assertEqual(2, len(recordset.records))
        self.assertIsNotNone(recordset.records[0].id)
        self.assertIsNotNone(recordset.records[1].id)

    def test_update_recordset(self):
        # Create a domain
        domain = self.create_domain()
        original_serial = domain.serial

        # Create a recordset
        recordset = self.create_recordset(domain)

        # Update the recordset
        recordset.ttl = 1800

        # Perform the update
        self.central_service.update_recordset(self.admin_context, recordset)

        # Get domain again to verify that serial number was updated
        updated_domain = self.central_service.get_domain(self.admin_context,
                                                         domain.id)
        new_serial = updated_domain.serial

        # Fetch the resource again
        recordset = self.central_service.get_recordset(
            self.admin_context, recordset.domain_id, recordset.id)

        # Ensure the new value took
        self.assertEqual(recordset.ttl, 1800)
        self.assertThat(new_serial, GreaterThan(original_serial))

    def test_update_recordset_deadlock_retry(self):
        # Create a domain
        domain = self.create_domain()

        # Create a recordset
        recordset = self.create_recordset(domain)

        # Update the recordset
        recordset.ttl = 1800

        # Due to Python's scoping of i - we need to make it a mutable type
        # for the counter to work.. In Py3, we can use the nonlocal keyword.
        i = [False]

        def fail_once_then_pass():
            if i[0] is True:
                return self.central_service.storage.session.commit()
            else:
                i[0] = True
                raise db_exception.DBDeadlock()

        with mock.patch.object(self.central_service.storage, 'commit',
                          side_effect=fail_once_then_pass):
            # Perform the update
            recordset = self.central_service.update_recordset(
                self.admin_context, recordset)

        # Ensure i[0] is True, indicating the side_effect code above was
        # triggered
        self.assertTrue(i[0])

        # Ensure the recordset was updated correctly
        self.assertEqual(1800, recordset.ttl)

    def test_update_recordset_with_record_create(self):
        # Create a domain
        domain = self.create_domain()

        # Create a recordset
        recordset = self.create_recordset(domain)

        # Append two new Records
        recordset.records.append(objects.Record(data='192.0.2.1'))
        recordset.records.append(objects.Record(data='192.0.2.2'))

        # Perform the update
        self.central_service.update_recordset(self.admin_context, recordset)

        # Fetch the RecordSet again
        recordset = self.central_service.get_recordset(
            self.admin_context, domain.id, recordset.id)

        # Ensure two Records are attached to the RecordSet correctly
        self.assertEqual(2, len(recordset.records))
        self.assertIsNotNone(recordset.records[0].id)
        self.assertIsNotNone(recordset.records[1].id)

    def test_update_recordset_with_record_delete(self):
        # Create a domain
        domain = self.create_domain()
        original_serial = domain.serial

        # Create a recordset and two records
        recordset = self.create_recordset(domain)
        self.create_record(domain, recordset)
        self.create_record(domain, recordset, fixture=1)

        # Append two new Records
        recordset.records.append(objects.Record(data='192.0.2.1'))
        recordset.records.append(objects.Record(data='192.0.2.2'))

        # Remove one of the Records
        recordset.records.pop(0)

        # Perform the update
        self.central_service.update_recordset(self.admin_context, recordset)

        # Fetch the RecordSet again
        recordset = self.central_service.get_recordset(
            self.admin_context, domain.id, recordset.id)

        # Fetch the Domain again
        updated_domain = self.central_service.get_domain(self.admin_context,
                                                         domain.id)
        new_serial = updated_domain.serial

        # Ensure two Records are attached to the RecordSet correctly
        self.assertEqual(1, len(recordset.records))
        self.assertIsNotNone(recordset.records[0].id)
        self.assertThat(new_serial, GreaterThan(original_serial))

    def test_update_recordset_with_record_update(self):
        # Create a domain
        domain = self.create_domain()

        # Create a recordset and two records
        recordset = self.create_recordset(domain, 'A')
        self.create_record(domain, recordset)
        self.create_record(domain, recordset, fixture=1)

        # Fetch the RecordSet again
        recordset = self.central_service.get_recordset(
            self.admin_context, domain.id, recordset.id)

        # Update one of the Records
        updated_record_id = recordset.records[0].id
        recordset.records[0].data = '192.0.2.255'

        # Perform the update
        self.central_service.update_recordset(self.admin_context, recordset)

        # Fetch the RecordSet again
        recordset = self.central_service.get_recordset(
            self.admin_context, domain.id, recordset.id)

        # Ensure the Record has been updated
        for record in recordset.records:
            if record.id != updated_record_id:
                continue

            self.assertEqual('192.0.2.255', record.data)
            return  # Exits this test early as we succeeded

        raise Exception('Updated record not found')

    def test_update_recordset_without_incrementing_serial(self):
        domain = self.create_domain()

        # Create a recordset
        recordset = self.create_recordset(domain)

        # Fetch the domain so we have the latest serial number
        domain_before = self.central_service.get_domain(
            self.admin_context, domain.id)

        # Update the recordset
        recordset.ttl = 1800

        # Perform the update
        self.central_service.update_recordset(
            self.admin_context, recordset, increment_serial=False)

        # Fetch the resource again
        recordset = self.central_service.get_recordset(
            self.admin_context, recordset.domain_id, recordset.id)

        # Ensure the recordset was updated correctly
        self.assertEqual(recordset.ttl, 1800)

        # Ensure the domains serial number was not updated
        domain_after = self.central_service.get_domain(
            self.admin_context, domain.id)

        self.assertEqual(domain_before.serial, domain_after.serial)

    def test_update_recordset_immutable_domain_id(self):
        domain = self.create_domain()
        other_domain = self.create_domain(fixture=1)

        # Create a recordset
        recordset = self.create_recordset(domain)

        # Update the recordset
        recordset.ttl = 1800
        recordset.domain_id = other_domain.id

        # Ensure we get a BadRequest if we change the domain_id
        with testtools.ExpectedException(exceptions.BadRequest):
            self.central_service.update_recordset(
                self.admin_context, recordset)

    def test_update_recordset_immutable_tenant_id(self):
        domain = self.create_domain()

        # Create a recordset
        recordset = self.create_recordset(domain)

        # Update the recordset
        recordset.ttl = 1800
        recordset.tenant_id = 'other-tenant'

        # Ensure we get a BadRequest if we change the domain_id
        with testtools.ExpectedException(exceptions.BadRequest):
            self.central_service.update_recordset(
                self.admin_context, recordset)

    def test_update_recordset_immutable_type(self):
        domain = self.create_domain()

        # Create a recordset
        recordset = self.create_recordset(domain)
        cname_recordset = self.create_recordset(domain, type='CNAME')

        # Update the recordset
        recordset.ttl = 1800
        recordset.type = cname_recordset.type

        # Ensure we get a BadRequest if we change the domain_id
        with testtools.ExpectedException(exceptions.BadRequest):
            self.central_service.update_recordset(
                self.admin_context, recordset)

    def test_delete_recordset(self):
        domain = self.create_domain()
        original_serial = domain.serial

        # Create a recordset
        recordset = self.create_recordset(domain)

        # Delete the recordset
        self.central_service.delete_recordset(
            self.admin_context, domain['id'], recordset['id'])

        # Fetch the recordset again, ensuring an exception is raised
        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            self.central_service.get_recordset(
                self.admin_context, domain['id'], recordset['id'])

        # Fetch the domain again to verify serial number increased
        updated_domain = self.central_service.get_domain(self.admin_context,
                                                         domain.id)
        new_serial = updated_domain.serial
        self.assertThat(new_serial, GreaterThan(original_serial))

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

        # We should have 1 recordset now, plus SOA & NS recordsets
        recordsets = self.central_service.count_recordsets(self.admin_context)
        self.assertEqual(recordsets, 3)

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
            self.admin_context, domain['id'], recordset['id'],
            objects.Record.from_dict(values))

        # Ensure all values have been set correctly
        self.assertIsNotNone(record['id'])
        self.assertEqual(record['data'], values['data'])
        self.assertIn('status', record)

    def test_create_record_over_quota(self):
        self.config(quota_domain_records=3)

        # Creating the domain automatically creates SOA & NS records
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
            self.admin_context, domain['id'], recordset['id'],
            objects.Record.from_dict(values),
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
        record = self.create_record(domain, recordset)

        # Update the Object
        record.data = '192.0.2.255'

        # Perform the update
        self.central_service.update_record(self.admin_context, record)

        # Fetch the resource again
        record = self.central_service.get_record(
            self.admin_context, record.domain_id, record.recordset_id,
            record.id)

        # Ensure the new value took
        self.assertEqual('192.0.2.255', record.data)

    def test_update_record_without_incrementing_serial(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain, 'A')

        # Create a record
        record = self.create_record(domain, recordset)

        # Fetch the domain so we have the latest serial number
        domain_before = self.central_service.get_domain(
            self.admin_context, domain.id)

        # Update the Object
        record.data = '192.0.2.255'

        # Perform the update
        self.central_service.update_record(
            self.admin_context, record, increment_serial=False)

        # Fetch the resource again
        record = self.central_service.get_record(
            self.admin_context, record.domain_id, record.recordset_id,
            record.id)

        # Ensure the new value took
        self.assertEqual('192.0.2.255', record.data)

        # Ensure the domains serial number was not updated
        domain_after = self.central_service.get_domain(
            self.admin_context, domain.id)

        self.assertEqual(domain_before.serial, domain_after.serial)

    def test_update_record_immutable_domain_id(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)
        other_domain = self.create_domain(fixture=1)

        # Create a record
        record = self.create_record(domain, recordset)

        # Update the record
        record.domain_id = other_domain.id

        # Ensure we get a BadRequest if we change the domain_id
        with testtools.ExpectedException(exceptions.BadRequest):
            self.central_service.update_record(self.admin_context, record)

    def test_update_record_immutable_recordset_id(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)
        other_recordset = self.create_recordset(domain, fixture=1)

        # Create a record
        record = self.create_record(domain, recordset)

        # Update the record
        record.recordset_id = other_recordset.id

        # Ensure we get a BadRequest if we change the recordset_id
        with testtools.ExpectedException(exceptions.BadRequest):
            self.central_service.update_record(self.admin_context, record)

    def test_delete_record(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        # Create a record
        record = self.create_record(domain, recordset)

        # Fetch the domain serial number
        domain_serial = self.central_service.get_domain(
            self.admin_context, domain['id']).serial

        # Delete the record
        self.central_service.delete_record(
            self.admin_context, domain['id'], recordset['id'], record['id'])

        # Ensure the domain serial number was updated
        new_domain_serial = self.central_service.get_domain(
            self.admin_context, domain['id']).serial
        self.assertNotEqual(new_domain_serial, domain_serial)

        # Fetch the record
        deleted_record = self.central_service.get_record(
            self.admin_context, domain['id'], recordset['id'],
            record['id'])

        # Ensure the record is marked for deletion
        self.assertEqual(deleted_record.id, record.id)
        self.assertEqual(deleted_record.data, record.data)
        self.assertEqual(deleted_record.domain_id, record.domain_id)
        self.assertEqual(deleted_record.status, 'PENDING')
        self.assertEqual(deleted_record.tenant_id, record.tenant_id)
        self.assertEqual(deleted_record.recordset_id, record.recordset_id)
        self.assertEqual(deleted_record.action, 'DELETE')
        self.assertEqual(deleted_record.serial, new_domain_serial)

    def test_delete_record_without_incrementing_serial(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        # Create a record
        record = self.create_record(domain, recordset)

        # Fetch the domain serial number
        domain_serial = self.central_service.get_domain(
            self.admin_context, domain['id']).serial

        # Delete the record
        self.central_service.delete_record(
            self.admin_context, domain['id'], recordset['id'], record['id'],
            increment_serial=False)

        # Ensure the domains serial number was not updated
        new_domain_serial = self.central_service.get_domain(
            self.admin_context, domain['id'])['serial']
        self.assertEqual(new_domain_serial, domain_serial)

        # Fetch the record
        deleted_record = self.central_service.get_record(
            self.admin_context, domain['id'], recordset['id'],
            record['id'])

        # Ensure the record is marked for deletion
        self.assertEqual(deleted_record.id, record.id)
        self.assertEqual(deleted_record.data, record.data)
        self.assertEqual(deleted_record.domain_id, record.domain_id)
        self.assertEqual(deleted_record.status, 'PENDING')
        self.assertEqual(deleted_record.tenant_id, record.tenant_id)
        self.assertEqual(deleted_record.recordset_id, record.recordset_id)
        self.assertEqual(deleted_record.action, 'DELETE')
        self.assertEqual(deleted_record.serial, new_domain_serial)

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

        # we should have 1 record now, plus SOA & NS records
        records = self.central_service.count_records(self.admin_context)
        self.assertEqual(records, 3)

    def test_count_records_policy_check(self):
        # Set the policy to reject the authz
        self.policy({'count_records': '!'})

        with testtools.ExpectedException(exceptions.Forbidden):
            self.central_service.count_records(self.get_context())

    def test_get_floatingip_no_record(self):
        context = self.get_context(tenant='a')

        fip = self.network_api.fake.allocate_floatingip(context.tenant)

        fip_ptr = self.central_service.get_floatingip(
            context, fip['region'], fip['id'])

        self.assertEqual(fip['region'], fip_ptr['region'])
        self.assertEqual(fip['id'], fip_ptr['id'])
        self.assertEqual(fip['address'], fip_ptr['address'])
        self.assertEqual(None, fip_ptr['ptrdname'])

    def test_get_floatingip_with_record(self):
        context = self.get_context(tenant='a')

        fixture = self.get_ptr_fixture()

        fip = self.network_api.fake.allocate_floatingip(context.tenant)

        expected = self.central_service.update_floatingip(
            context, fip['region'], fip['id'], fixture)

        actual = self.central_service.get_floatingip(
            context, fip['region'], fip['id'])
        self.assertEqual(expected, actual)

        self.assertEqual(expected, actual)

    def test_get_floatingip_not_allocated(self):
        context = self.get_context(tenant='a')

        fip = self.network_api.fake.allocate_floatingip(context.tenant)
        self.network_api.fake.deallocate_floatingip(fip['id'])

        with testtools.ExpectedException(exceptions.NotFound):
            self.central_service.get_floatingip(
                context, fip['region'], fip['id'])

    def test_get_floatingip_deallocated_and_invalidate(self):
        context_a = self.get_context(tenant='a')
        elevated_a = context_a.elevated()
        elevated_a.all_tenants = True

        context_b = self.get_context(tenant='b')

        fixture = self.get_ptr_fixture()

        # First allocate and create a FIP as tenant a
        fip = self.network_api.fake.allocate_floatingip(context_a.tenant)

        self.central_service.update_floatingip(
            context_a, fip['region'], fip['id'], fixture)

        criterion = {
            'managed_resource_id': fip['id'],
            'managed_tenant_id': context_a.tenant}
        domain_id = self.central_service.find_record(
            elevated_a, criterion).domain_id

        # Simulate the update on the backend
        domain_serial = self.central_service.get_domain(
            elevated_a, domain_id).serial
        self.central_service.update_status(
            elevated_a, domain_id, "SUCCESS", domain_serial)

        self.network_api.fake.deallocate_floatingip(fip['id'])

        with testtools.ExpectedException(exceptions.NotFound):
            self.central_service.get_floatingip(
                context_a, fip['region'], fip['id'])

        # Ensure that the record is still in DB (No invalidation)
        self.central_service.find_record(elevated_a, criterion)

        # Now give the fip id to tenant 'b' and see that it get's deleted
        self.network_api.fake.allocate_floatingip(
            context_b.tenant, fip['id'])

        # There should be a fip returned with ptrdname of None
        fip_ptr = self.central_service.get_floatingip(
            context_b, fip['region'], fip['id'])
        self.assertEqual(None, fip_ptr['ptrdname'])

        # Simulate the invalidation on the backend
        domain_serial = self.central_service.get_domain(
            elevated_a, domain_id).serial
        self.central_service.update_status(
            elevated_a, domain_id, "SUCCESS", domain_serial)

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

        fip = self.network_api.fake.allocate_floatingip(context.tenant)

        fips = self.central_service.list_floatingips(context)

        self.assertEqual(1, len(fips))
        self.assertEqual(None, fips[0]['ptrdname'])
        self.assertEqual(fip['id'], fips[0]['id'])
        self.assertEqual(fip['region'], fips[0]['region'])
        self.assertEqual(fip['address'], fips[0]['address'])
        self.assertEqual(None, fips[0]['description'])

    def test_list_floatingips_with_record(self):
        context = self.get_context(tenant='a')

        fixture = self.get_ptr_fixture()

        fip = self.network_api.fake.allocate_floatingip(context.tenant)

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
        context_a = self.get_context(tenant='a')
        elevated_a = context_a.elevated()
        elevated_a.all_tenants = True

        context_b = self.get_context(tenant='b')

        fixture = self.get_ptr_fixture()

        # First allocate and create a FIP as tenant a
        fip = self.network_api.fake.allocate_floatingip(context_a.tenant)

        self.central_service.update_floatingip(
            context_a, fip['region'], fip['id'], fixture)

        criterion = {
            'managed_resource_id': fip['id'],
            'managed_tenant_id': context_a.tenant}
        domain_id = self.central_service.find_record(
            elevated_a, criterion).domain_id

        # Simulate the update on the backend
        domain_serial = self.central_service.get_domain(
            elevated_a, domain_id).serial
        self.central_service.update_status(
            elevated_a, domain_id, "SUCCESS", domain_serial)

        self.network_api.fake.deallocate_floatingip(fip['id'])

        fips = self.central_service.list_floatingips(context_a)
        assert(len(fips) == 0)

        # Ensure that the record is still in DB (No invalidation)
        self.central_service.find_record(elevated_a, criterion)

        # Now give the fip id to tenant 'b' and see that it get's deleted
        self.network_api.fake.allocate_floatingip(
            context_b.tenant, fip['id'])

        # There should be a fip returned with ptrdname of None
        fips = self.central_service.list_floatingips(context_b)
        self.assertEqual(1, len(fips))
        self.assertEqual(None, fips[0]['ptrdname'])

        # Simulate the invalidation on the backend
        domain_serial = self.central_service.get_domain(
            elevated_a, domain_id).serial
        self.central_service.update_status(
            elevated_a, domain_id, "SUCCESS", domain_serial)

        # Ensure that the old record for tenant a for the fip now owned by
        # tenant b is gone
        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.central_service.find_record(elevated_a, criterion)

    def test_set_floatingip(self):
        context = self.get_context(tenant='a')

        fixture = self.get_ptr_fixture()

        fip = self.network_api.fake.allocate_floatingip(context.tenant)

        fip_ptr = self.central_service.update_floatingip(
            context, fip['region'], fip['id'], fixture)

        self.assertEqual(fixture['ptrdname'], fip_ptr['ptrdname'])
        self.assertEqual(fip['address'], fip_ptr['address'])
        self.assertEqual(None, fip_ptr['description'])
        self.assertIsNotNone(fip_ptr['ttl'])

    def test_set_floatingip_no_managed_resource_tenant_id(self):
        context = self.get_context(tenant='a')

        fixture = self.get_ptr_fixture()

        fip = self.network_api.fake.allocate_floatingip(context.tenant)

        self.central_service.update_floatingip(
            context, fip['region'], fip['id'], fixture)

        tenant_id = "00000000-0000-0000-0000-000000000000"

        elevated_context = context.elevated()
        elevated_context.all_tenants = True

        # The domain created should have the default 0's uuid as owner
        domain = self.central_service.find_domain(
            elevated_context,
            {"tenant_id": tenant_id})
        self.assertEqual(tenant_id, domain.tenant_id)

    def test_set_floatingip_removes_old_record(self):
        context_a = self.get_context(tenant='a')
        elevated_a = context_a.elevated()
        elevated_a.all_tenants = True

        context_b = self.get_context(tenant='b')

        fixture = self.get_ptr_fixture()

        # Test that re-setting as tenant a an already set floatingip leaves
        # only 1 record
        fip = self.network_api.fake.allocate_floatingip(context_a.tenant)

        self.central_service.update_floatingip(
            context_a, fip['region'], fip['id'], fixture)

        criterion = {
            'managed_resource_id': fip['id'],
            'managed_tenant_id': context_a.tenant}
        domain_id = self.central_service.find_record(
            elevated_a, criterion).domain_id

        fixture2 = self.get_ptr_fixture(fixture=1)
        self.central_service.update_floatingip(
            context_a, fip['region'], fip['id'], fixture2)

        # Simulate the update on the backend
        domain_serial = self.central_service.get_domain(
            elevated_a, domain_id).serial
        self.central_service.update_status(
            elevated_a, domain_id, "SUCCESS", domain_serial)

        count = self.central_service.count_records(
            elevated_a, {'managed_resource_id': fip['id']})

        self.assertEqual(1, count)

        self.network_api.fake.deallocate_floatingip(fip['id'])

        # Now test that tenant b allocating the same fip and setting a ptr
        # deletes any records
        fip = self.network_api.fake.allocate_floatingip(
            context_b.tenant, fip['id'])

        self.central_service.update_floatingip(
            context_b, fip['region'], fip['id'], fixture)

        # Simulate the update on the backend
        domain_serial = self.central_service.get_domain(
            elevated_a, domain_id).serial
        self.central_service.update_status(
            elevated_a, domain_id, "SUCCESS", domain_serial)

        count = self.central_service.count_records(
            elevated_a, {'managed_resource_id': fip['id']})

        self.assertEqual(1, count)

    def test_set_floatingip_not_allocated(self):
        context = self.get_context(tenant='a')
        fixture = self.get_ptr_fixture()

        fip = self.network_api.fake.allocate_floatingip(context.tenant)
        self.network_api.fake.deallocate_floatingip(fip['id'])

        # If one attempts to assign a de-allocated FIP or not-owned it should
        # fail with BadRequest
        with testtools.ExpectedException(exceptions.NotFound):
            fixture = self.central_service.update_floatingip(
                context, fip['region'], fip['id'], fixture)

    def test_unset_floatingip(self):
        context = self.get_context(tenant='a')

        fixture = self.get_ptr_fixture()

        fip = self.network_api.fake.allocate_floatingip(context.tenant)

        fip_ptr = self.central_service.update_floatingip(
            context, fip['region'], fip['id'], fixture)

        self.assertEqual(fixture['ptrdname'], fip_ptr['ptrdname'])
        self.assertEqual(fip['address'], fip_ptr['address'])
        self.assertEqual(None, fip_ptr['description'])
        self.assertIsNotNone(fip_ptr['ttl'])

        self.central_service.update_floatingip(
            context, fip['region'], fip['id'],
            objects.FloatingIP().from_dict({'ptrdname': None}))

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
        # Create a blacklisted zone
        expected = self.create_blacklist(fixture=0)

        # Retrieve the newly created blacklist
        blacklist = self.central_service.find_blacklist(
            self.admin_context, {'id': expected['id']})

        self.assertEqual(blacklist['pattern'], expected['pattern'])
        self.assertEqual(blacklist['description'], expected['description'])

    def test_update_blacklist(self):
        # Create a blacklisted zone
        blacklist = self.create_blacklist(fixture=0)

        # Update the Object
        blacklist.description = "New Comment"

        # Perform the update
        self.central_service.update_blacklist(self.admin_context, blacklist)

        # Fetch the resource again
        blacklist = self.central_service.get_blacklist(self.admin_context,
                                                       blacklist.id)

        # Verify that the record was updated correctly
        self.assertEqual("New Comment", blacklist.description)

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

    # SOA recordset tests
    def test_create_SOA(self):
        # A SOA record should automatically be created each time
        # a zone is created
        # Create a zone
        zone = self.create_domain(name='example3.org.')

        # Retrieve SOA
        criterion = {'domain_id': zone['id'], 'type': 'SOA'}

        soa = self.central_service.find_recordset(self.admin_context,
                                                  criterion)

        # Split out the various soa values
        soa_record_values = soa.records[0].data.split()

        zone_email = zone['email'].replace("@", ".")
        zone_email += (".")

        # Ensure all values have been set correctly
        self.assertIsNotNone(soa.id)
        self.assertEqual('SOA', soa.type)
        self.assertIsNotNone(soa.records)
        self.assertEqual(int(soa_record_values[2]), zone['serial'])
        self.assertEqual(soa_record_values[1], zone_email)
        self.assertEqual(int(soa_record_values[3]), zone['refresh'])
        self.assertEqual(int(soa_record_values[4]), zone['retry'])
        self.assertEqual(int(soa_record_values[5]), zone['expire'])
        self.assertEqual(int(soa_record_values[6]), zone['minimum'])

    def test_update_soa(self):
        # Anytime the zone's serial number is incremented
        # the SOA recordset should automatically be updated
        zone = self.create_domain(email='info@example.org')

        # Update the object
        zone.email = 'info@example.net'

        # Perform the update
        self.central_service.update_domain(self.admin_context, zone)

        # Fetch the domain again
        updated_zone = self.central_service.get_domain(self.admin_context,
                                                       zone.id)

        # Retrieve SOA
        criterion = {'domain_id': zone['id'], 'type': 'SOA'}

        soa = self.central_service.find_recordset(self.admin_context,
                                                  criterion)

        # Split out the various soa values
        soa_record_values = soa.records[0].data.split()

        self.assertEqual(int(soa_record_values[2]), updated_zone['serial'])

    # Pool Tests
    def test_create_pool(self):
        # Get the values
        values = self.get_pool_fixture(fixture=0)
        # Create the pool using the values
        pool = self.central_service.create_pool(
            self.admin_context, objects.Pool.from_dict(values))

        # Verify that all the values were set correctly
        self.assertIsNotNone(pool['id'])
        self.assertIsNotNone(pool['created_at'])
        self.assertIsNotNone(pool['version'])
        self.assertIsNotNone(pool['tenant_id'])
        self.assertIsNone(pool['updated_at'])
        self.assertIsNotNone(pool['attributes'])
        self.assertIsNotNone(pool['ns_records'])

        self.assertEqual(pool['name'], values['name'])

        # Compare the actual values of attributes and ns_records
        for k in range(0, len(values['attributes'])):
            self.assertDictContainsSubset(
                values['attributes'][k],
                pool['attributes'][k].to_primitive()['designate_object.data']
            )

        for k in range(0, len(values['ns_records'])):
            self.assertDictContainsSubset(
                values['ns_records'][k],
                pool['ns_records'][k].to_primitive()['designate_object.data'])

    def test_get_pool(self):
        # Create a server pool
        expected = self.create_pool(fixture=0)

        # GET the pool and verify it is the same
        pool = self.central_service.get_pool(self.admin_context,
                                             expected['id'])

        self.assertEqual(pool['id'], expected['id'])
        self.assertEqual(pool['created_at'], expected['created_at'])
        self.assertEqual(pool['version'], expected['version'])
        self.assertEqual(pool['tenant_id'], expected['tenant_id'])
        self.assertEqual(pool['name'], expected['name'])

        # Compare the actual values of attributes and ns_records
        for k in range(0, len(expected['attributes'])):
            self.assertEqual(
                pool['attributes'][k].to_primitive()['designate_object.data'],
                expected['attributes'][k].to_primitive()
                ['designate_object.data'])

        for k in range(0, len(expected['ns_records'])):
            self.assertEqual(
                pool['ns_records'][k].to_primitive()['designate_object.data'],
                expected['ns_records'][k].to_primitive()
                ['designate_object.data'])

    def test_find_pools(self):
        # Verify no pools exist, except for default pool
        pools = self.central_service.find_pools(self.admin_context)

        self.assertEqual(len(pools), 1)

        # Create a pool
        self.create_pool(fixture=0)

        # Verify we can find the newly created pool
        pools = self.central_service.find_pools(self.admin_context)
        values = self.get_pool_fixture(fixture=0)

        self.assertEqual(len(pools), 2)
        self.assertEqual(pools[1]['name'], values['name'])

        # Compare the actual values of attributes and ns_records
        expected_attributes = values['attributes'][0]
        actual_attributes = \
            pools[1]['attributes'][0].to_primitive()['designate_object.data']
        for k in expected_attributes:
            self.assertEqual(actual_attributes[k], expected_attributes[k])

        expected_ns_records = values['ns_records'][0]
        actual_ns_records = \
            pools[1]['ns_records'][0].to_primitive()['designate_object.data']
        for k in expected_ns_records:
            self.assertEqual(actual_ns_records[k], expected_ns_records[k])

    def test_find_pool(self):
        # Create a server pool
        expected = self.create_pool(fixture=0)

        # Find the created pool
        pool = self.central_service.find_pool(self.admin_context,
                                              {'id': expected['id']})

        self.assertEqual(pool['name'], expected['name'])

        # Compare the actual values of attributes and ns_records
        for k in range(0, len(expected['attributes'])):
            self.assertEqual(
                pool['attributes'][k].to_primitive()['designate_object.data'],
                expected['attributes'][k].to_primitive()
                ['designate_object.data'])

        for k in range(0, len(expected['ns_records'])):
            self.assertEqual(
                pool['ns_records'][k].to_primitive()['designate_object.data'],
                expected['ns_records'][k].to_primitive()
                ['designate_object.data'])

    def test_update_pool(self):
        # Create a server pool
        pool = self.create_pool(fixture=0)

        # Update and save the pool
        pool.description = 'New Comment'
        self.central_service.update_pool(self.admin_context, pool)

        # Fetch the pool
        pool = self.central_service.get_pool(self.admin_context, pool.id)

        # Verify that the pool was updated correctly
        self.assertEqual("New Comment", pool.description)

    def test_update_pool_add_ns_record(self):
        # Create a server pool and domain
        pool = self.create_pool(fixture=0)
        domain = self.create_domain(pool_id=pool.id)

        ns_record_count = len(pool.ns_records)
        new_ns_record = objects.PoolNsRecord(
            priority=10,
            hostname='ns-new.example.org.')

        # Update and save the pool
        pool.ns_records.append(new_ns_record)
        self.central_service.update_pool(self.admin_context, pool)

        # Fetch the pool
        pool = self.central_service.get_pool(self.admin_context, pool.id)

        # Verify that the pool was updated correctly
        self.assertEqual(ns_record_count + 1, len(pool.ns_records))
        self.assertIn(new_ns_record.hostname,
                      [n.hostname for n in pool.ns_records])

        # Fetch the domains NS recordset
        ns_recordset = self.central_service.find_recordset(
            self.admin_context,
            criterion={'domain_id': domain.id, 'type': "NS"})

        # Verify that the doamins NS records ware updated correctly
        self.assertEqual(set([n.hostname for n in pool.ns_records]),
                         set([n.data for n in ns_recordset.records]))

    def test_update_pool_remove_ns_record(self):
        # Create a server pool and domain
        pool = self.create_pool(fixture=0)
        domain = self.create_domain(pool_id=pool.id)

        ns_record_count = len(pool.ns_records)

        # Update and save the pool
        removed_ns_record = pool.ns_records.pop(-1)
        self.central_service.update_pool(self.admin_context, pool)

        # Fetch the pool
        pool = self.central_service.get_pool(self.admin_context, pool.id)

        # Verify that the pool was updated correctly
        self.assertEqual(ns_record_count - 1, len(pool.ns_records))
        self.assertNotIn(removed_ns_record.hostname,
                         [n.hostname for n in pool.ns_records])

        # Fetch the domains NS recordset
        ns_recordset = self.central_service.find_recordset(
            self.admin_context,
            criterion={'domain_id': domain.id, 'type': "NS"})

        # Verify that the doamins NS records ware updated correctly
        self.assertEqual(set([n.hostname for n in pool.ns_records]),
                         set([n.data for n in ns_recordset.records]))

    def test_delete_pool(self):
        # Create a server pool
        pool = self.create_pool()

        # Delete the pool
        self.central_service.delete_pool(self.admin_context, pool['id'])

        # Verify that the pool has been deleted
        with testtools.ExpectedException(exceptions.PoolNotFound):
            self.central_service.get_pool(self.admin_context, pool['id'])

    def test_update_status_delete_domain(self):
        # Create a domain
        domain = self.create_domain()

        # Delete the domain
        self.central_service.delete_domain(self.admin_context, domain['id'])

        # Simulate the domain having been deleted on the backend
        domain_serial = self.central_service.get_domain(
            self.admin_context, domain['id']).serial
        self.central_service.update_status(
            self.admin_context, domain['id'], "SUCCESS", domain_serial)

        # Fetch the domain again, ensuring an exception is raised
        with testtools.ExpectedException(exceptions.DomainNotFound):
            self.central_service.get_domain(self.admin_context, domain['id'])

    def test_update_status_delete_last_record(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        # Create a record
        record = self.create_record(domain, recordset)

        # Delete the record
        self.central_service.delete_record(
            self.admin_context, domain['id'], recordset['id'], record['id'])

        # Simulate the record having been deleted on the backend
        domain_serial = self.central_service.get_domain(
            self.admin_context, domain['id']).serial
        self.central_service.update_status(
            self.admin_context, domain['id'], "SUCCESS", domain_serial)

        # Fetch the record again, ensuring an exception is raised
        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            self.central_service.get_record(
                self.admin_context, domain['id'], recordset['id'],
                record['id'])

    def test_update_status_delete_last_record_without_incrementing_serial(
            self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        # Create a record
        record = self.create_record(domain, recordset)

        # Fetch the domain serial number
        domain_serial = self.central_service.get_domain(
            self.admin_context, domain['id']).serial

        # Delete the record
        self.central_service.delete_record(
            self.admin_context, domain['id'], recordset['id'], record['id'],
            increment_serial=False)

        # Simulate the record having been deleted on the backend
        domain_serial = self.central_service.get_domain(
            self.admin_context, domain['id']).serial
        self.central_service.update_status(
            self.admin_context, domain['id'], "SUCCESS", domain_serial)

        # Fetch the record again, ensuring an exception is raised
        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            self.central_service.get_record(
                self.admin_context, domain['id'], recordset['id'],
                record['id'])

        # Ensure the domains serial number was not updated
        new_domain_serial = self.central_service.get_domain(
            self.admin_context, domain['id']).serial

        self.assertEqual(new_domain_serial, domain_serial)

    def test_create_zone_transfer_request(self):
        domain = self.create_domain()
        zone_transfer_request = self.create_zone_transfer_request(domain)

        # Verify all values have been set correctly
        self.assertIsNotNone(zone_transfer_request.id)
        self.assertIsNotNone(zone_transfer_request.tenant_id)
        self.assertIsNotNone(zone_transfer_request.key)
        self.assertEqual(zone_transfer_request.domain_id, domain.id)

    def test_create_zone_transfer_request_duplicate(self):
        domain = self.create_domain()
        self.create_zone_transfer_request(domain)
        with testtools.ExpectedException(
                exceptions.DuplicateZoneTransferRequest):
            self.create_zone_transfer_request(domain)

    def test_create_scoped_zone_transfer_request(self):
        domain = self.create_domain()
        values = self.get_zone_transfer_request_fixture(fixture=1)
        zone_transfer_request = self.create_zone_transfer_request(domain,
                                                                  fixture=1)

        # Verify all values have been set correctly
        self.assertIsNotNone(zone_transfer_request.id)
        self.assertIsNotNone(zone_transfer_request.tenant_id)
        self.assertEqual(zone_transfer_request.domain_id, domain.id)
        self.assertIsNotNone(zone_transfer_request.key)
        self.assertEqual(
            zone_transfer_request.target_tenant_id,
            values['target_tenant_id'])

    def test_get_zone_transfer_request(self):
        domain = self.create_domain()
        zt_request = self.create_zone_transfer_request(domain,
                                                       fixture=1)
        retrived_zt = self.central_service.get_zone_transfer_request(
            self.admin_context,
            zt_request.id)
        self.assertEqual(zt_request.domain_id, retrived_zt.domain_id)
        self.assertEqual(zt_request.key, retrived_zt.key)

    def test_get_zone_transfer_request_scoped(self):
        tenant_1_context = self.get_context(tenant=1)
        tenant_2_context = self.get_context(tenant=2)
        tenant_3_context = self.get_context(tenant=3)
        domain = self.create_domain(context=tenant_1_context)
        zt_request = self.create_zone_transfer_request(
            domain,
            context=tenant_1_context,
            target_tenant_id=2)

        self.central_service.get_zone_transfer_request(
            tenant_2_context, zt_request.id)

        self.central_service.get_zone_transfer_request(
            tenant_1_context, zt_request.id)

        with testtools.ExpectedException(exceptions.Forbidden):
            self.central_service.get_zone_transfer_request(
                tenant_3_context, zt_request.id)

    def test_update_zone_transfer_request(self):
        domain = self.create_domain()
        zone_transfer_request = self.create_zone_transfer_request(domain)

        zone_transfer_request.description = 'TEST'
        self.central_service.update_zone_transfer_request(
            self.admin_context, zone_transfer_request)

        # Verify all values have been set correctly
        self.assertIsNotNone(zone_transfer_request.id)
        self.assertIsNotNone(zone_transfer_request.tenant_id)
        self.assertIsNotNone(zone_transfer_request.key)
        self.assertEqual(zone_transfer_request.description, 'TEST')

    def test_delete_zone_transfer_request(self):
        domain = self.create_domain()
        zone_transfer_request = self.create_zone_transfer_request(domain)

        self.central_service.delete_zone_transfer_request(
            self.admin_context, zone_transfer_request.id)

        with testtools.ExpectedException(
                exceptions.ZoneTransferRequestNotFound):
                self.central_service.get_zone_transfer_request(
                    self.admin_context,
                    zone_transfer_request.id)

    def test_create_zone_transfer_accept(self):
        tenant_1_context = self.get_context(tenant=1)
        tenant_2_context = self.get_context(tenant=2)
        admin_context = self.get_admin_context()
        admin_context.all_tenants = True

        domain = self.create_domain(context=tenant_1_context)
        recordset = self.create_recordset(domain, context=tenant_1_context)
        record = self.create_record(
            domain, recordset, context=tenant_1_context)

        zone_transfer_request = self.create_zone_transfer_request(
            domain, context=tenant_1_context)

        zone_transfer_accept = objects.ZoneTransferAccept()
        zone_transfer_accept.zone_transfer_request_id =\
            zone_transfer_request.id

        zone_transfer_accept.key = zone_transfer_request.key
        zone_transfer_accept.domain_id = domain.id

        zone_transfer_accept = \
            self.central_service.create_zone_transfer_accept(
                tenant_2_context, zone_transfer_accept)

        result = {}
        result['domain'] = self.central_service.get_domain(
            admin_context, domain.id)

        result['recordset'] = self.central_service.get_recordset(
            admin_context, domain.id, recordset.id)

        result['record'] = self.central_service.get_record(
            admin_context, domain.id, recordset.id, record.id)

        result['zt_accept'] = self.central_service.get_zone_transfer_accept(
            admin_context, zone_transfer_accept.id)
        result['zt_request'] = self.central_service.get_zone_transfer_request(
            admin_context, zone_transfer_request.id)

        self.assertEqual(
            result['domain'].tenant_id, str(tenant_2_context.tenant))
        self.assertEqual(
            result['recordset'].tenant_id, str(tenant_2_context.tenant))
        self.assertEqual(
            result['record'].tenant_id, str(tenant_2_context.tenant))
        self.assertEqual(
            result['zt_accept'].status, 'COMPLETE')
        self.assertEqual(
            result['zt_request'].status, 'COMPLETE')

    def test_create_zone_transfer_accept_scoped(self):
        tenant_1_context = self.get_context(tenant=1)
        tenant_2_context = self.get_context(tenant=2)
        admin_context = self.get_admin_context()
        admin_context.all_tenants = True

        domain = self.create_domain(context=tenant_1_context)
        recordset = self.create_recordset(domain, context=tenant_1_context)
        record = self.create_record(
            domain, recordset, context=tenant_1_context)

        zone_transfer_request = self.create_zone_transfer_request(
            domain,
            context=tenant_1_context,
            target_tenant_id='2')

        zone_transfer_accept = objects.ZoneTransferAccept()
        zone_transfer_accept.zone_transfer_request_id =\
            zone_transfer_request.id

        zone_transfer_accept.key = zone_transfer_request.key
        zone_transfer_accept.domain_id = domain.id

        zone_transfer_accept = \
            self.central_service.create_zone_transfer_accept(
                tenant_2_context, zone_transfer_accept)

        result = {}
        result['domain'] = self.central_service.get_domain(
            admin_context, domain.id)

        result['recordset'] = self.central_service.get_recordset(
            admin_context, domain.id, recordset.id)

        result['record'] = self.central_service.get_record(
            admin_context, domain.id, recordset.id, record.id)

        result['zt_accept'] = self.central_service.get_zone_transfer_accept(
            admin_context, zone_transfer_accept.id)
        result['zt_request'] = self.central_service.get_zone_transfer_request(
            admin_context, zone_transfer_request.id)

        self.assertEqual(
            result['domain'].tenant_id, str(tenant_2_context.tenant))
        self.assertEqual(
            result['recordset'].tenant_id, str(tenant_2_context.tenant))
        self.assertEqual(
            result['record'].tenant_id, str(tenant_2_context.tenant))
        self.assertEqual(
            result['zt_accept'].status, 'COMPLETE')
        self.assertEqual(
            result['zt_request'].status, 'COMPLETE')

    def test_create_zone_transfer_accept_failed_key(self):
        tenant_1_context = self.get_context(tenant=1)
        tenant_2_context = self.get_context(tenant=2)
        admin_context = self.get_admin_context()
        admin_context.all_tenants = True

        domain = self.create_domain(context=tenant_1_context)

        zone_transfer_request = self.create_zone_transfer_request(
            domain,
            context=tenant_1_context,
            target_tenant_id=2)

        zone_transfer_accept = objects.ZoneTransferAccept()
        zone_transfer_accept.zone_transfer_request_id =\
            zone_transfer_request.id

        zone_transfer_accept.key = 'WRONG KEY'
        zone_transfer_accept.domain_id = domain.id

        with testtools.ExpectedException(exceptions.IncorrectZoneTransferKey):
            zone_transfer_accept = \
                self.central_service.create_zone_transfer_accept(
                    tenant_2_context, zone_transfer_accept)

    def test_create_zone_tarnsfer_accept_out_of_tenant_scope(self):
        tenant_1_context = self.get_context(tenant=1)
        tenant_3_context = self.get_context(tenant=3)
        admin_context = self.get_admin_context()
        admin_context.all_tenants = True

        domain = self.create_domain(context=tenant_1_context)

        zone_transfer_request = self.create_zone_transfer_request(
            domain,
            context=tenant_1_context,
            target_tenant_id=2)

        zone_transfer_accept = objects.ZoneTransferAccept()
        zone_transfer_accept.zone_transfer_request_id =\
            zone_transfer_request.id

        zone_transfer_accept.key = zone_transfer_request.key
        zone_transfer_accept.domain_id = domain.id

        with testtools.ExpectedException(exceptions.Forbidden):
            zone_transfer_accept = \
                self.central_service.create_zone_transfer_accept(
                    tenant_3_context, zone_transfer_accept)
