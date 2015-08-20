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
import uuid
import math

import mock
import testtools
from oslo_config import cfg
from oslo_log import log as logging

from designate import exceptions
from designate import objects
from designate.storage.base import Storage as StorageBase


LOG = logging.getLogger(__name__)


class StorageTestCase(object):
    def create_quota(self, **kwargs):
        """
        This create method has been kept in the StorageTestCase class as quotas
        are treated differently to other resources in Central.
        """

        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_quota_fixture(fixture=fixture, values=kwargs)

        if 'tenant_id' not in values:
            values['tenant_id'] = context.tenant

        return self.storage.create_quota(context, values)

    # Paging Tests
    def _ensure_paging(self, data, method):
        """
        Given an array of created items we iterate through them making sure
        they match up to things returned by paged results.
        """
        results = None
        item_number = 0

        for current_page in range(0, int(math.ceil(float(len(data)) / 2))):
            LOG.debug('Validating results on page %d', current_page)

            if results is not None:
                results = method(
                    self.admin_context, limit=2, marker=results[-1]['id'])
            else:
                results = method(self.admin_context, limit=2)

            LOG.critical('Results: %d', len(results))

            for result_number, result in enumerate(results):
                LOG.debug('Validating result %d on page %d', result_number,
                          current_page)
                self.assertEqual(
                    data[item_number]['id'], results[result_number]['id'])

                item_number += 1

    def test_paging_marker_not_found(self):
        with testtools.ExpectedException(exceptions.MarkerNotFound):
            self.storage.find_pool_attributes(
                self.admin_context, marker=str(uuid.uuid4()), limit=5)

    def test_paging_marker_invalid(self):
        with testtools.ExpectedException(exceptions.InvalidMarker):
            self.storage.find_pool_attributes(
                self.admin_context, marker='4')

    def test_paging_limit_invalid(self):
        with testtools.ExpectedException(exceptions.ValueError):
            self.storage.find_pool_attributes(
                self.admin_context, limit='z')

    def test_paging_sort_dir_invalid(self):
        with testtools.ExpectedException(exceptions.ValueError):
            self.storage.find_pool_attributes(
                self.admin_context, sort_dir='invalid_sort_dir')

    def test_paging_sort_key_invalid(self):
        with testtools.ExpectedException(exceptions.InvalidSortKey):
            self.storage.find_pool_attributes(
                self.admin_context, sort_key='invalid_sort_key')

    # Interface Tests
    def test_interface(self):
        self._ensure_interface(StorageBase, self.storage.__class__)

    # Quota Tests
    def test_create_quota(self):
        values = self.get_quota_fixture()
        values['tenant_id'] = self.admin_context.tenant

        result = self.storage.create_quota(self.admin_context, values)

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['tenant_id'], self.admin_context.tenant)
        self.assertEqual(result['resource'], values['resource'])
        self.assertEqual(result['hard_limit'], values['hard_limit'])

    def test_create_quota_duplicate(self):
        # Create the initial quota
        self.create_quota()

        with testtools.ExpectedException(exceptions.DuplicateQuota):
            self.create_quota()

    def test_find_quotas(self):
        actual = self.storage.find_quotas(self.admin_context)
        self.assertEqual(0, len(actual))

        # Create a single quota
        quota_one = self.create_quota()

        actual = self.storage.find_quotas(self.admin_context)
        self.assertEqual(1, len(actual))

        self.assertEqual(quota_one['tenant_id'], actual[0]['tenant_id'])
        self.assertEqual(quota_one['resource'], actual[0]['resource'])
        self.assertEqual(quota_one['hard_limit'], actual[0]['hard_limit'])

        # Create a second quota
        quota_two = self.create_quota(fixture=1)

        actual = self.storage.find_quotas(self.admin_context)
        self.assertEqual(2, len(actual))

        self.assertEqual(quota_two['tenant_id'], actual[1]['tenant_id'])
        self.assertEqual(quota_two['resource'], actual[1]['resource'])
        self.assertEqual(quota_two['hard_limit'], actual[1]['hard_limit'])

    def test_find_quotas_criterion(self):
        quota_one = self.create_quota()
        quota_two = self.create_quota(fixture=1)

        criterion = dict(
            tenant_id=quota_one['tenant_id'],
            resource=quota_one['resource']
        )

        results = self.storage.find_quotas(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['tenant_id'], quota_one['tenant_id'])
        self.assertEqual(results[0]['resource'], quota_one['resource'])
        self.assertEqual(results[0]['hard_limit'], quota_one['hard_limit'])

        criterion = dict(
            tenant_id=quota_two['tenant_id'],
            resource=quota_two['resource']
        )

        results = self.storage.find_quotas(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['tenant_id'], quota_two['tenant_id'])
        self.assertEqual(results[0]['resource'], quota_two['resource'])
        self.assertEqual(results[0]['hard_limit'], quota_two['hard_limit'])

    def test_get_quota(self):
        # Create a quota
        expected = self.create_quota()
        actual = self.storage.get_quota(self.admin_context, expected['id'])

        self.assertEqual(actual['tenant_id'], expected['tenant_id'])
        self.assertEqual(actual['resource'], expected['resource'])
        self.assertEqual(actual['hard_limit'], expected['hard_limit'])

    def test_get_quota_missing(self):
        with testtools.ExpectedException(exceptions.QuotaNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.get_quota(self.admin_context, uuid)

    def test_find_quota_criterion(self):
        quota_one = self.create_quota()
        quota_two = self.create_quota(fixture=1)

        criterion = dict(
            tenant_id=quota_one['tenant_id'],
            resource=quota_one['resource']
        )

        result = self.storage.find_quota(self.admin_context, criterion)

        self.assertEqual(result['tenant_id'], quota_one['tenant_id'])
        self.assertEqual(result['resource'], quota_one['resource'])
        self.assertEqual(result['hard_limit'], quota_one['hard_limit'])

        criterion = dict(
            tenant_id=quota_two['tenant_id'],
            resource=quota_two['resource']
        )

        result = self.storage.find_quota(self.admin_context, criterion)

        self.assertEqual(result['tenant_id'], quota_two['tenant_id'])
        self.assertEqual(result['resource'], quota_two['resource'])
        self.assertEqual(result['hard_limit'], quota_two['hard_limit'])

    def test_find_quota_criterion_missing(self):
        expected = self.create_quota()

        criterion = dict(
            tenant_id=expected['tenant_id'] + "NOT FOUND"
        )

        with testtools.ExpectedException(exceptions.QuotaNotFound):
            self.storage.find_quota(self.admin_context, criterion)

    def test_update_quota(self):
        # Create a quota
        quota = self.create_quota(fixture=1)

        # Update the Object
        quota.hard_limit = 5000

        # Perform the update
        quota = self.storage.update_quota(self.admin_context, quota)

        # Ensure the new value took
        self.assertEqual(5000, quota.hard_limit)

        # Ensure the version column was incremented
        self.assertEqual(2, quota.version)

    def test_update_quota_duplicate(self):
        # Create two quotas
        quota_one = self.create_quota(fixture=0)
        quota_two = self.create_quota(fixture=1)

        # Update the Q2 object to be a duplicate of Q1
        quota_two.resource = quota_one.resource

        with testtools.ExpectedException(exceptions.DuplicateQuota):
            self.storage.update_quota(self.admin_context, quota_two)

    def test_update_quota_missing(self):
        quota = objects.Quota(id='caf771fc-6b05-4891-bee1-c2a48621f57b')

        with testtools.ExpectedException(exceptions.QuotaNotFound):
            self.storage.update_quota(self.admin_context, quota)

    def test_delete_quota(self):
        quota = self.create_quota()

        self.storage.delete_quota(self.admin_context, quota['id'])

        with testtools.ExpectedException(exceptions.QuotaNotFound):
            self.storage.get_quota(self.admin_context, quota['id'])

    def test_delete_quota_missing(self):
        with testtools.ExpectedException(exceptions.QuotaNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.delete_quota(self.admin_context, uuid)

    # TSIG Key Tests
    def test_create_tsigkey(self):
        values = self.get_tsigkey_fixture()

        result = self.storage.create_tsigkey(
            self.admin_context, tsigkey=objects.TsigKey.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['name'], values['name'])
        self.assertEqual(result['algorithm'], values['algorithm'])
        self.assertEqual(result['secret'], values['secret'])
        self.assertEqual(result['scope'], values['scope'])

    def test_create_tsigkey_duplicate(self):
        # Create the Initial TsigKey
        tsigkey_one = self.create_tsigkey()

        values = self.get_tsigkey_fixture(1)
        values['name'] = tsigkey_one['name']

        with testtools.ExpectedException(exceptions.DuplicateTsigKey):
            self.create_tsigkey(**values)

    def test_find_tsigkeys(self):
        actual = self.storage.find_tsigkeys(self.admin_context)
        self.assertEqual(0, len(actual))

        # Create a single tsigkey
        tsig = self.create_tsigkey()

        actual = self.storage.find_tsigkeys(self.admin_context)
        self.assertEqual(1, len(actual))

        self.assertEqual(tsig['name'], actual[0]['name'])
        self.assertEqual(tsig['algorithm'], actual[0]['algorithm'])
        self.assertEqual(tsig['secret'], actual[0]['secret'])
        self.assertEqual(tsig['scope'], actual[0]['scope'])

    def test_find_tsigkeys_paging(self):
        # Create 10 TSIG Keys
        created = [self.create_tsigkey(name='tsig-%s' % i)
                   for i in range(10)]

        # Ensure we can page through the results.
        self._ensure_paging(created, self.storage.find_tsigkeys)

    def test_find_tsigkeys_criterion(self):
        tsigkey_one = self.create_tsigkey(fixture=0)
        tsigkey_two = self.create_tsigkey(fixture=1)

        criterion = dict(
            name=tsigkey_one['name']
        )

        results = self.storage.find_tsigkeys(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], tsigkey_one['name'])

        criterion = dict(
            name=tsigkey_two['name']
        )

        results = self.storage.find_tsigkeys(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], tsigkey_two['name'])

    def test_get_tsigkey(self):
        # Create a tsigkey
        expected = self.create_tsigkey()

        actual = self.storage.get_tsigkey(self.admin_context, expected['id'])

        self.assertEqual(actual['name'], expected['name'])
        self.assertEqual(actual['algorithm'], expected['algorithm'])
        self.assertEqual(actual['secret'], expected['secret'])
        self.assertEqual(actual['scope'], expected['scope'])

    def test_get_tsigkey_missing(self):
        with testtools.ExpectedException(exceptions.TsigKeyNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.get_tsigkey(self.admin_context, uuid)

    def test_update_tsigkey(self):
        # Create a tsigkey
        tsigkey = self.create_tsigkey(name='test-key')

        # Update the Object
        tsigkey.name = 'test-key-updated'

        # Perform the update
        tsigkey = self.storage.update_tsigkey(self.admin_context, tsigkey)

        # Ensure the new value took
        self.assertEqual('test-key-updated', tsigkey.name)

        # Ensure the version column was incremented
        self.assertEqual(2, tsigkey.version)

    def test_update_tsigkey_duplicate(self):
        # Create two tsigkeys
        tsigkey_one = self.create_tsigkey(fixture=0)
        tsigkey_two = self.create_tsigkey(fixture=1)

        # Update the T2 object to be a duplicate of T1
        tsigkey_two.name = tsigkey_one.name

        with testtools.ExpectedException(exceptions.DuplicateTsigKey):
            self.storage.update_tsigkey(self.admin_context, tsigkey_two)

    def test_update_tsigkey_missing(self):
        tsigkey = objects.TsigKey(id='caf771fc-6b05-4891-bee1-c2a48621f57b')

        with testtools.ExpectedException(exceptions.TsigKeyNotFound):
            self.storage.update_tsigkey(self.admin_context, tsigkey)

    def test_delete_tsigkey(self):
        tsigkey = self.create_tsigkey()

        self.storage.delete_tsigkey(self.admin_context, tsigkey['id'])

        with testtools.ExpectedException(exceptions.TsigKeyNotFound):
            self.storage.get_tsigkey(self.admin_context, tsigkey['id'])

    def test_delete_tsigkey_missing(self):
        with testtools.ExpectedException(exceptions.TsigKeyNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.delete_tsigkey(self.admin_context, uuid)

    # Tenant Tests
    def test_find_tenants(self):
        context = self.get_admin_context()
        one_context = context
        one_context.tenant = 'One'
        two_context = context
        two_context.tenant = 'Two'
        context.all_tenants = True

        # create 3 domains in 2 tenants
        self.create_domain(fixture=0, context=one_context, tenant_id='One')
        domain = self.create_domain(fixture=1, context=one_context,
                                    tenant_id='One')
        self.create_domain(fixture=2, context=two_context, tenant_id='Two')

        # Delete one of the domains.
        self.storage.delete_domain(context, domain['id'])

        # Ensure we get accurate results
        result = self.storage.find_tenants(context)
        result_dict = [dict(t) for t in result]

        expected = [{
            'id': 'One',
            'domain_count': 1,
        }, {
            'id': 'Two',
            'domain_count': 1,
        }]

        self.assertEqual(expected, result_dict)

    def test_get_tenant(self):
        context = self.get_admin_context()
        one_context = context
        one_context.tenant = 1
        context.all_tenants = True

        # create 2 domains in a tenant
        domain_1 = self.create_domain(fixture=0, context=one_context)
        domain_2 = self.create_domain(fixture=1, context=one_context)
        domain_3 = self.create_domain(fixture=2, context=one_context)

        # Delete one of the domains.
        self.storage.delete_domain(context, domain_3['id'])

        result = self.storage.get_tenant(context, 1)

        self.assertEqual(result['id'], 1)
        self.assertEqual(result['domain_count'], 2)
        self.assertEqual(sorted(result['domains']),
                         [domain_1['name'], domain_2['name']])

    def test_count_tenants(self):
        context = self.get_admin_context()
        one_context = context
        one_context.tenant = 1
        two_context = context
        two_context.tenant = 2
        context.all_tenants = True

        # in the beginning, there should be nothing
        tenants = self.storage.count_tenants(context)
        self.assertEqual(tenants, 0)

        # create 2 domains with 2 tenants
        self.create_domain(fixture=0, context=one_context, tenant_id=1)
        self.create_domain(fixture=1, context=two_context, tenant_id=2)
        domain = self.create_domain(fixture=2,
                                    context=two_context, tenant_id=2)

        # Delete one of the domains.
        self.storage.delete_domain(context, domain['id'])

        tenants = self.storage.count_tenants(context)
        self.assertEqual(tenants, 2)

    def test_count_tenants_none_result(self):
        rp = mock.Mock()
        rp.fetchone.return_value = None
        with mock.patch.object(self.storage.session, 'execute',
                               return_value=rp):
            tenants = self.storage.count_tenants(self.admin_context)
            self.assertEqual(tenants, 0)

    # Domain Tests
    def test_create_domain(self):
        pool_id = cfg.CONF['service:central'].default_pool_id
        values = {
            'tenant_id': self.admin_context.tenant,
            'name': 'example.net.',
            'email': 'example@example.net',
            'pool_id': pool_id
        }

        result = self.storage.create_domain(
            self.admin_context, domain=objects.Domain.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['tenant_id'], self.admin_context.tenant)
        self.assertEqual(result['name'], values['name'])
        self.assertEqual(result['email'], values['email'])
        self.assertEqual(result['pool_id'], pool_id)
        self.assertIn('status', result)

    def test_create_domain_duplicate(self):
        # Create the Initial Domain
        self.create_domain()

        with testtools.ExpectedException(exceptions.DuplicateDomain):
            self.create_domain()

    def test_find_domains(self):
        self.config(quota_domains=20)

        actual = self.storage.find_domains(self.admin_context)
        self.assertEqual(0, len(actual))

        # Create a single domain
        domain = self.create_domain()

        actual = self.storage.find_domains(self.admin_context)
        self.assertEqual(1, len(actual))

        self.assertEqual(domain['name'], actual[0]['name'])
        self.assertEqual(domain['email'], actual[0]['email'])

    def test_find_domains_paging(self):
        # Create 10 Domains
        created = [self.create_domain(name='example-%d.org.' % i)
                   for i in range(10)]

        # Ensure we can page through the results.
        self._ensure_paging(created, self.storage.find_domains)

    def test_find_domains_criterion(self):
        domain_one = self.create_domain()
        domain_two = self.create_domain(fixture=1)

        criterion = dict(
            name=domain_one['name']
        )

        results = self.storage.find_domains(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], domain_one['name'])
        self.assertEqual(results[0]['email'], domain_one['email'])
        self.assertIn('status', domain_one)

        criterion = dict(
            name=domain_two['name']
        )

        results = self.storage.find_domains(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], domain_two['name'])
        self.assertEqual(results[0]['email'], domain_two['email'])
        self.assertIn('status', domain_two)

    def test_find_domains_all_tenants(self):
        # Create two contexts with different tenant_id's
        one_context = self.get_admin_context()
        one_context.tenant = 1
        two_context = self.get_admin_context()
        two_context.tenant = 2

        # Create normal and all_tenants context objects
        nm_context = self.get_admin_context()
        at_context = self.get_admin_context()
        at_context.all_tenants = True

        # Create two domains in different tenants
        self.create_domain(fixture=0, context=one_context)
        self.create_domain(fixture=1, context=two_context)

        # Ensure the all_tenants context see's two domains
        results = self.storage.find_domains(at_context)
        self.assertEqual(2, len(results))

        # Ensure the normal context see's no domains
        results = self.storage.find_domains(nm_context)
        self.assertEqual(0, len(results))

        # Ensure the tenant 1 context see's 1 domain
        results = self.storage.find_domains(one_context)
        self.assertEqual(1, len(results))

        # Ensure the tenant 2 context see's 1 domain
        results = self.storage.find_domains(two_context)
        self.assertEqual(1, len(results))

    def test_get_domain(self):
        # Create a domain
        expected = self.create_domain()
        actual = self.storage.get_domain(self.admin_context, expected['id'])

        self.assertEqual(actual['name'], expected['name'])
        self.assertEqual(actual['email'], expected['email'])
        self.assertIn('status', actual)

    def test_get_domain_missing(self):
        with testtools.ExpectedException(exceptions.DomainNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.get_domain(self.admin_context, uuid)

    def test_get_deleted_domain(self):
        context = self.get_admin_context()
        context.show_deleted = True

        domain = self.create_domain(context=context)

        self.storage.delete_domain(context, domain['id'])
        self.storage.get_domain(context, domain['id'])

    def test_find_domain_criterion(self):
        domain_one = self.create_domain()
        domain_two = self.create_domain(fixture=1)

        criterion = dict(
            name=domain_one['name']
        )

        result = self.storage.find_domain(self.admin_context, criterion)

        self.assertEqual(result['name'], domain_one['name'])
        self.assertEqual(result['email'], domain_one['email'])
        self.assertIn('status', domain_one)

        criterion = dict(
            name=domain_two['name']
        )

        result = self.storage.find_domain(self.admin_context, criterion)

        self.assertEqual(result['name'], domain_two['name'])
        self.assertEqual(result['email'], domain_two['email'])
        self.assertIn('status', domain_one)
        self.assertIn('status', domain_two)

    def test_find_domain_criterion_missing(self):
        expected = self.create_domain()

        criterion = dict(
            name=expected['name'] + "NOT FOUND"
        )

        with testtools.ExpectedException(exceptions.DomainNotFound):
            self.storage.find_domain(self.admin_context, criterion)

    def test_find_domain_criterion_lessthan(self):
        domain = self.create_domain()

        # Test Finding No Results (serial is not < serial)
        criterion = dict(
            name=domain['name'],
            serial='<%s' % domain['serial'],
        )

        with testtools.ExpectedException(exceptions.DomainNotFound):
            self.storage.find_domain(self.admin_context, criterion)

        # Test Finding 1 Result (serial is < serial + 1)
        criterion = dict(
            name=domain['name'],
            serial='<%s' % (domain['serial'] + 1),
        )

        result = self.storage.find_domain(self.admin_context, criterion)

        self.assertEqual(result['name'], domain['name'])

    def test_find_domain_criterion_greaterthan(self):
        domain = self.create_domain()

        # Test Finding No Results (serial is not > serial)
        criterion = dict(
            name=domain['name'],
            serial='>%s' % domain['serial'],
        )

        with testtools.ExpectedException(exceptions.DomainNotFound):
            self.storage.find_domain(self.admin_context, criterion)

        # Test Finding 1 Result (serial is > serial - 1)
        criterion = dict(
            name=domain['name'],
            serial='>%s' % (domain['serial'] - 1),
        )

        result = self.storage.find_domain(self.admin_context, criterion)

        self.assertEqual(result['name'], domain['name'])

    def test_update_domain(self):
        # Create a domain
        domain = self.create_domain(name='example.org.')

        # Update the Object
        domain.name = 'example.net.'

        # Perform the update
        domain = self.storage.update_domain(self.admin_context, domain)

        # Ensure the new valie took
        self.assertEqual('example.net.', domain.name)

        # Ensure the version column was incremented
        self.assertEqual(2, domain.version)

    def test_update_domain_duplicate(self):
        # Create two domains
        domain_one = self.create_domain(fixture=0)
        domain_two = self.create_domain(fixture=1)

        # Update the D2 object to be a duplicate of D1
        domain_two.name = domain_one.name

        with testtools.ExpectedException(exceptions.DuplicateDomain):
            self.storage.update_domain(self.admin_context, domain_two)

    def test_update_domain_missing(self):
        domain = objects.Domain(id='caf771fc-6b05-4891-bee1-c2a48621f57b')
        with testtools.ExpectedException(exceptions.DomainNotFound):
            self.storage.update_domain(self.admin_context, domain)

    def test_delete_domain(self):
        domain = self.create_domain()

        self.storage.delete_domain(self.admin_context, domain['id'])

        with testtools.ExpectedException(exceptions.DomainNotFound):
            self.storage.get_domain(self.admin_context, domain['id'])

    def test_delete_domain_missing(self):
        with testtools.ExpectedException(exceptions.DomainNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.delete_domain(self.admin_context, uuid)

    def test_count_domains(self):
        # in the beginning, there should be nothing
        domains = self.storage.count_domains(self.admin_context)
        self.assertEqual(domains, 0)

        # Create a single domain
        self.create_domain()

        # count 'em up
        domains = self.storage.count_domains(self.admin_context)

        # well, did we get 1?
        self.assertEqual(domains, 1)

    def test_count_domains_none_result(self):
        rp = mock.Mock()
        rp.fetchone.return_value = None
        with mock.patch.object(self.storage.session, 'execute',
                               return_value=rp):
            domains = self.storage.count_domains(self.admin_context)
            self.assertEqual(domains, 0)

    def test_create_recordset(self):
        domain = self.create_domain()

        values = {
            'name': 'www.%s' % domain['name'],
            'type': 'A'
        }

        result = self.storage.create_recordset(
            self.admin_context,
            domain['id'],
            recordset=objects.RecordSet.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['name'], values['name'])
        self.assertEqual(result['type'], values['type'])

    def test_create_recordset_duplicate(self):
        domain = self.create_domain()

        # Create the First RecordSet
        self.create_recordset(domain)

        with testtools.ExpectedException(exceptions.DuplicateRecordSet):
            # Attempt to create the second/duplicate recordset
            self.create_recordset(domain)

    def test_create_recordset_with_records(self):
        domain = self.create_domain()

        recordset = objects.RecordSet(
            name='www.%s' % domain['name'],
            type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.1'),
                objects.Record(data='192.0.2.2'),
            ])
        )

        recordset = self.storage.create_recordset(
            self.admin_context, domain['id'], recordset)

        # Ensure recordset.records is a RecordList instance
        self.assertIsInstance(recordset.records, objects.RecordList)

        # Ensure two Records are attached to the RecordSet correctly
        self.assertEqual(2, len(recordset.records))
        self.assertIsInstance(recordset.records[0], objects.Record)
        self.assertIsInstance(recordset.records[1], objects.Record)

        # Ensure the Records have been saved by checking they have an ID
        self.assertIsNotNone(recordset.records[0].id)
        self.assertIsNotNone(recordset.records[1].id)

    def test_find_recordsets(self):
        domain = self.create_domain()

        criterion = {'domain_id': domain['id']}

        actual = self.storage.find_recordsets(self.admin_context, criterion)
        self.assertEqual(2, len(actual))

        # Create a single recordset
        recordset_one = self.create_recordset(domain)

        actual = self.storage.find_recordsets(self.admin_context, criterion)
        self.assertEqual(3, len(actual))

        self.assertEqual(recordset_one['name'], actual[2]['name'])
        self.assertEqual(recordset_one['type'], actual[2]['type'])

    def test_find_recordsets_paging(self):
        domain = self.create_domain(name='example.org.')

        # Create 10 RecordSets
        created = [self.create_recordset(domain, name='r-%d.example.org.' % i)
                   for i in range(10)]

        # Add in the SOA and NS recordsets that are automatically created
        soa = self.storage.find_recordset(self.admin_context,
                                          criterion={'domain_id': domain['id'],
                                                     'type': "SOA"})
        ns = self.storage.find_recordset(self.admin_context,
                                         criterion={'domain_id': domain['id'],
                                                    'type': "NS"})
        created.insert(0, ns)
        created.insert(0, soa)

        # Ensure we can page through the results.
        self._ensure_paging(created, self.storage.find_recordsets)

    def test_find_recordsets_criterion(self):
        domain = self.create_domain()

        recordset_one = self.create_recordset(domain, type='A', fixture=0)
        self.create_recordset(domain, fixture=1)

        criterion = dict(
            domain_id=domain['id'],
            name=recordset_one['name'],
        )

        results = self.storage.find_recordsets(self.admin_context,
                                               criterion)

        self.assertEqual(len(results), 1)

        criterion = dict(
            domain_id=domain['id'],
            type='A',
        )

        results = self.storage.find_recordsets(self.admin_context,
                                               criterion)

        self.assertEqual(len(results), 2)

    def test_find_recordsets_criterion_wildcard(self):
        domain = self.create_domain()

        values = {'name': 'one.%s' % domain['name']}

        self.create_recordset(domain, **values)

        criterion = dict(
            domain_id=domain['id'],
            name="%%%(name)s" % {"name": domain['name']},
        )

        results = self.storage.find_recordsets(self.admin_context, criterion)

        # Should be 3, as SOA and NS recordsets are automiatcally created
        self.assertEqual(len(results), 3)

    def test_find_recordsets_with_records(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        # Create two Records in the RecordSet
        self.create_record(domain, recordset)
        self.create_record(domain, recordset, fixture=1)

        criterion = dict(
            id=recordset.id,
        )

        # Find the RecordSet
        results = self.storage.find_recordsets(self.admin_context, criterion)

        # Ensure we only have one result
        self.assertEqual(1, len(results))

        recordset = results[0]

        # Ensure recordset.records is a RecordList instance
        self.assertIsInstance(recordset.records, objects.RecordList)

        # Ensure two Records are attached to the RecordSet correctly
        self.assertEqual(2, len(recordset.records))
        self.assertIsInstance(recordset.records[0], objects.Record)
        self.assertIsInstance(recordset.records[1], objects.Record)

    def test_get_recordset(self):
        domain = self.create_domain()
        expected = self.create_recordset(domain)

        actual = self.storage.get_recordset(self.admin_context, expected['id'])

        self.assertEqual(actual['name'], expected['name'])
        self.assertEqual(actual['type'], expected['type'])

    def test_get_recordset_with_records(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        # Create two Records in the RecordSet
        self.create_record(domain, recordset)
        self.create_record(domain, recordset, fixture=1)

        # Fetch the RecordSet again
        recordset = self.storage.get_recordset(
            self.admin_context, recordset.id)

        # Ensure recordset.records is a RecordList instance
        self.assertIsInstance(recordset.records, objects.RecordList)

        # Ensure two Records are attached to the RecordSet correctly
        self.assertEqual(2, len(recordset.records))
        self.assertIsInstance(recordset.records[0], objects.Record)
        self.assertIsInstance(recordset.records[1], objects.Record)

    def test_get_recordset_missing(self):
        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.get_recordset(self.admin_context, uuid)

    def test_find_recordset_criterion(self):
        domain = self.create_domain()
        expected = self.create_recordset(domain)

        criterion = dict(
            domain_id=domain['id'],
            name=expected['name'],
        )

        actual = self.storage.find_recordset(self.admin_context, criterion)

        self.assertEqual(actual['name'], expected['name'])
        self.assertEqual(actual['type'], expected['type'])

    def test_find_recordset_criterion_missing(self):
        domain = self.create_domain()
        expected = self.create_recordset(domain)

        criterion = dict(
            name=expected['name'] + "NOT FOUND"
        )

        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            self.storage.find_recordset(self.admin_context, criterion)

    def test_find_recordset_criterion_with_records(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        # Create two Records in the RecordSet
        self.create_record(domain, recordset)
        self.create_record(domain, recordset, fixture=1)

        criterion = dict(
            id=recordset.id,
        )

        # Fetch the RecordSet again
        recordset = self.storage.find_recordset(self.admin_context, criterion)

        # Ensure recordset.records is a RecordList instance
        self.assertIsInstance(recordset.records, objects.RecordList)

        # Ensure two Records are attached to the RecordSet correctly
        self.assertEqual(2, len(recordset.records))
        self.assertIsInstance(recordset.records[0], objects.Record)
        self.assertIsInstance(recordset.records[1], objects.Record)

    def test_update_recordset(self):
        domain = self.create_domain()

        # Create a recordset
        recordset = self.create_recordset(domain)

        # Update the Object
        recordset.ttl = 1800

        # Change records as well
        recordset.records.append(objects.Record(data="10.0.0.1"))

        # Perform the update
        recordset = self.storage.update_recordset(self.admin_context,
                                                  recordset)

        # Ensure the new value took
        self.assertEqual(1800, recordset.ttl)

        # Ensure the version column was incremented
        self.assertEqual(2, recordset.version)

    def test_update_recordset_duplicate(self):
        domain = self.create_domain()

        # Create two recordsets
        recordset_one = self.create_recordset(domain, type='A')
        recordset_two = self.create_recordset(domain, type='A', fixture=1)

        # Update the R2 object to be a duplicate of R1
        recordset_two.name = recordset_one.name

        with testtools.ExpectedException(exceptions.DuplicateRecordSet):
            self.storage.update_recordset(self.admin_context, recordset_two)

    def test_update_recordset_missing(self):
        recordset = objects.RecordSet(
            id='caf771fc-6b05-4891-bee1-c2a48621f57b')

        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            self.storage.update_recordset(self.admin_context, recordset)

    def test_update_recordset_with_record_create(self):
        domain = self.create_domain()

        # Create a RecordSet
        recordset = self.create_recordset(domain, 'A')

        # Append two new Records
        recordset.records.append(objects.Record(data='192.0.2.1'))
        recordset.records.append(objects.Record(data='192.0.2.2'))

        # Perform the update
        self.storage.update_recordset(self.admin_context, recordset)

        # Fetch the RecordSet again
        recordset = self.storage.get_recordset(
            self.admin_context, recordset.id)

        # Ensure two Records are attached to the RecordSet correctly
        self.assertEqual(2, len(recordset.records))
        self.assertIsInstance(recordset.records[0], objects.Record)
        self.assertIsInstance(recordset.records[1], objects.Record)

        # Ensure the Records have been saved by checking they have an ID
        self.assertIsNotNone(recordset.records[0].id)
        self.assertIsNotNone(recordset.records[1].id)

    def test_update_recordset_with_record_delete(self):
        domain = self.create_domain()

        # Create a RecordSet and two Records
        recordset = self.create_recordset(domain, 'A')
        self.create_record(domain, recordset)
        self.create_record(domain, recordset, fixture=1)

        # Fetch the RecordSet again
        recordset = self.storage.get_recordset(
            self.admin_context, recordset.id)

        # Remove one of the Records
        recordset.records.pop(0)

        # Ensure only one Record is attached to the RecordSet
        self.assertEqual(1, len(recordset.records))

        # Perform the update
        self.storage.update_recordset(self.admin_context, recordset)

        # Fetch the RecordSet again
        recordset = self.storage.get_recordset(
            self.admin_context, recordset.id)

        # Ensure only one Record is attached to the RecordSet
        self.assertEqual(1, len(recordset.records))
        self.assertIsInstance(recordset.records[0], objects.Record)

    def test_update_recordset_with_record_update(self):
        domain = self.create_domain()

        # Create a RecordSet and two Records
        recordset = self.create_recordset(domain, 'A')
        self.create_record(domain, recordset)
        self.create_record(domain, recordset, fixture=1)

        # Fetch the RecordSet again
        recordset = self.storage.get_recordset(
            self.admin_context, recordset.id)

        # Update one of the Records
        updated_record_id = recordset.records[0].id
        recordset.records[0].data = '192.0.2.255'

        # Perform the update
        self.storage.update_recordset(self.admin_context, recordset)

        # Fetch the RecordSet again
        recordset = self.storage.get_recordset(
            self.admin_context, recordset.id)

        # Ensure the Record has been updated
        for record in recordset.records:
            if record.id != updated_record_id:
                continue

            self.assertEqual('192.0.2.255', record.data)
            return  # Exits this test early as we succeeded

        raise Exception('Updated record not found')

    def test_delete_recordset(self):
        domain = self.create_domain()

        # Create a recordset
        recordset = self.create_recordset(domain)

        self.storage.delete_recordset(self.admin_context, recordset['id'])

        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            self.storage.get_recordset(self.admin_context, recordset['id'])

    def test_delete_recordset_missing(self):
        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.delete_recordset(self.admin_context, uuid)

    def test_count_recordsets(self):
        # in the beginning, there should be nothing
        recordsets = self.storage.count_recordsets(self.admin_context)
        self.assertEqual(recordsets, 0)

        # Create a single domain & recordset
        domain = self.create_domain()
        self.create_recordset(domain)

        # we should have 3 recordsets now, including SOA & NS
        recordsets = self.storage.count_recordsets(self.admin_context)
        self.assertEqual(recordsets, 3)

        # Delete the domain, we should be back to 0 recordsets
        self.storage.delete_domain(self.admin_context, domain.id)
        recordsets = self.storage.count_recordsets(self.admin_context)
        self.assertEqual(recordsets, 0)

    def test_count_recordsets_none_result(self):
        rp = mock.Mock()
        rp.fetchone.return_value = None
        with mock.patch.object(self.storage.session, 'execute',
                               return_value=rp):
            recordsets = self.storage.count_recordsets(self.admin_context)
            self.assertEqual(recordsets, 0)

    def test_create_record(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain, type='A')

        values = {
            'data': '192.0.2.1',
        }

        result = self.storage.create_record(
            self.admin_context, domain['id'], recordset['id'],
            objects.Record.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNotNone(result['hash'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['tenant_id'], self.admin_context.tenant)
        self.assertEqual(result['data'], values['data'])
        self.assertIn('status', result)

    def test_create_record_duplicate(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        # Create the First Record
        self.create_record(domain, recordset)

        with testtools.ExpectedException(exceptions.DuplicateRecord):
            # Attempt to create the second/duplicate record
            self.create_record(domain, recordset)

    def test_find_records(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        criterion = {
            'domain_id': domain['id'],
            'recordset_id': recordset['id']
        }

        actual = self.storage.find_records(self.admin_context, criterion)
        self.assertEqual(0, len(actual))

        # Create a single record
        record = self.create_record(domain, recordset)

        actual = self.storage.find_records(self.admin_context, criterion)
        self.assertEqual(1, len(actual))

        self.assertEqual(record['data'], actual[0]['data'])
        self.assertIn('status', record)

    def test_find_records_paging(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain, type='A')

        # Create 10 Records
        created = [self.create_record(domain, recordset, data='192.0.2.%d' % i)
                   for i in range(10)]

        # Add in the SOA and NS records that are automatically created
        soa = self.storage.find_recordset(self.admin_context,
                                          criterion={'domain_id': domain['id'],
                                                     'type': "SOA"})
        ns = self.storage.find_recordset(self.admin_context,
                                         criterion={'domain_id': domain['id'],
                                                    'type': "NS"})
        for r in ns['records']:
            created.insert(0, r)
        created.insert(0, soa['records'][0])

        # Ensure we can page through the results.
        self._ensure_paging(created, self.storage.find_records)

    def test_find_records_criterion(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain, type='A')

        record_one = self.create_record(domain, recordset)
        self.create_record(domain, recordset, fixture=1)

        criterion = dict(
            data=record_one['data'],
            domain_id=domain['id'],
            recordset_id=recordset['id'],
        )

        results = self.storage.find_records(self.admin_context, criterion)
        self.assertEqual(len(results), 1)

        criterion = dict(
            domain_id=domain['id'],
            recordset_id=recordset['id'],
        )

        results = self.storage.find_records(self.admin_context, criterion)

        self.assertEqual(len(results), 2)

    def test_find_records_criterion_wildcard(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain, type='A')

        values = {'data': '127.0.0.1'}

        self.create_record(domain, recordset, **values)

        criterion = dict(
            domain_id=domain['id'],
            recordset_id=recordset['id'],
            data="%.0.0.1",
        )

        results = self.storage.find_records(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

    def test_find_records_all_tenants(self):
        # Create two contexts with different tenant_id's
        one_context = self.get_admin_context()
        one_context.tenant = 1
        two_context = self.get_admin_context()
        two_context.tenant = 2

        # Create normal and all_tenants context objects
        nm_context = self.get_admin_context()
        at_context = self.get_admin_context()
        at_context.all_tenants = True

        # Create two domains in different tenants, and 1 record in each
        domain_one = self.create_domain(fixture=0, context=one_context)
        recordset_one = self.create_recordset(domain_one, fixture=0,
                                              context=one_context)
        self.create_record(domain_one, recordset_one, context=one_context)

        domain_two = self.create_domain(fixture=1, context=two_context)
        recordset_one = self.create_recordset(domain_two, fixture=1,
                                              context=two_context)

        self.create_record(domain_two, recordset_one, context=two_context)

        # Ensure the all_tenants context see's two records
        # Plus the SOA & NS in each of 2 domains = 6 records total
        results = self.storage.find_records(at_context)
        self.assertEqual(6, len(results))

        # Ensure the normal context see's no records
        results = self.storage.find_records(nm_context)
        self.assertEqual(0, len(results))

        # Ensure the tenant 1 context see's 1 record + SOA & NS
        results = self.storage.find_records(one_context)
        self.assertEqual(3, len(results))

        # Ensure the tenant 2 context see's 1 record + SOA & NS
        results = self.storage.find_records(two_context)
        self.assertEqual(3, len(results))

    def test_get_record(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        expected = self.create_record(domain, recordset)

        actual = self.storage.get_record(self.admin_context, expected['id'])

        self.assertEqual(actual['data'], expected['data'])
        self.assertIn('status', actual)

    def test_get_record_missing(self):
        with testtools.ExpectedException(exceptions.RecordNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.get_record(self.admin_context, uuid)

    def test_find_record_criterion(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        expected = self.create_record(domain, recordset)

        criterion = dict(
            domain_id=domain['id'],
            recordset_id=recordset['id'],
            data=expected['data'],
        )

        actual = self.storage.find_record(self.admin_context, criterion)

        self.assertEqual(actual['data'], expected['data'])
        self.assertIn('status', actual)

    def test_find_record_criterion_missing(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        expected = self.create_record(domain, recordset)

        criterion = dict(
            domain_id=domain['id'],
            data=expected['data'] + "NOT FOUND",
        )

        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.storage.find_record(self.admin_context, criterion)

    def test_update_record(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain, type='A')

        # Create a record
        record = self.create_record(domain, recordset)

        # Update the Object
        record.data = '192.0.2.255'

        # Perform the update
        record = self.storage.update_record(self.admin_context, record)

        # Ensure the new value took
        self.assertEqual('192.0.2.255', record.data)

        # Ensure the version column was incremented
        self.assertEqual(2, record.version)

    def test_update_record_duplicate(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        # Create two records
        record_one = self.create_record(domain, recordset)
        record_two = self.create_record(domain, recordset, fixture=1)

        # Update the R2 object to be a duplicate of R1
        record_two.data = record_one.data

        with testtools.ExpectedException(exceptions.DuplicateRecord):
            self.storage.update_record(self.admin_context, record_two)

    def test_update_record_missing(self):
        record = objects.Record(id='caf771fc-6b05-4891-bee1-c2a48621f57b')

        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.storage.update_record(self.admin_context, record)

    def test_delete_record(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        # Create a record
        record = self.create_record(domain, recordset)

        self.storage.delete_record(self.admin_context, record['id'])

        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.storage.get_record(self.admin_context, record['id'])

    def test_delete_record_missing(self):
        with testtools.ExpectedException(exceptions.RecordNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.delete_record(self.admin_context, uuid)

    def test_count_records(self):
        # in the beginning, there should be nothing
        records = self.storage.count_records(self.admin_context)
        self.assertEqual(records, 0)

        # Create a single domain & record
        domain = self.create_domain()
        recordset = self.create_recordset(domain)
        self.create_record(domain, recordset)

        # we should have 3 records now, including NS and SOA
        records = self.storage.count_records(self.admin_context)
        self.assertEqual(records, 3)

        # Delete the domain, we should be back to 0 records
        self.storage.delete_domain(self.admin_context, domain.id)
        records = self.storage.count_records(self.admin_context)
        self.assertEqual(records, 0)

    def test_count_records_none_result(self):
        rp = mock.Mock()
        rp.fetchone.return_value = None
        with mock.patch.object(self.storage.session, 'execute',
                               return_value=rp):
            records = self.storage.count_records(self.admin_context)
            self.assertEqual(records, 0)

    def test_ping(self):
        pong = self.storage.ping(self.admin_context)

        self.assertEqual(pong['status'], True)
        self.assertIsNotNone(pong['rtt'])

    def test_ping_fail(self):
        with mock.patch.object(self.storage.engine, "execute",
                               side_effect=Exception):
            result = self.storage.ping(self.admin_context)
            self.assertEqual(False, result['status'])
            self.assertIsNotNone(result['rtt'])

    # TLD Tests
    def test_create_tld(self):
        values = {
            'name': 'com',
            'description': 'This is a comment.'
        }

        result = self.storage.create_tld(
            self.admin_context, objects.Tld.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])
        self.assertIsNotNone(result['version'])
        self.assertEqual(result['name'], values['name'])
        self.assertEqual(result['description'], values['description'])

    def test_create_tld_with_duplicate(self):
        # Create the First Tld
        self.create_tld(fixture=0)

        with testtools.ExpectedException(exceptions.DuplicateTld):
            # Attempt to create the second/duplicate Tld
            self.create_tld(fixture=0)

    def test_find_tlds(self):

        actual = self.storage.find_tlds(self.admin_context)
        self.assertEqual(0, len(actual))

        # Create a single Tld
        tld = self.create_tld(fixture=0)

        actual = self.storage.find_tlds(self.admin_context)
        self.assertEqual(1, len(actual))

        self.assertEqual(tld['name'], actual[0]['name'])
        self.assertEqual(tld['description'], actual[0]['description'])

    def test_find_tlds_paging(self):
        # Create 10 Tlds
        created = [self.create_tld(name='org%d' % i)
                   for i in range(10)]

        # Ensure we can page through the results.
        self._ensure_paging(created, self.storage.find_tlds)

    def test_find_tlds_with_criterion(self):
        tld_one = self.create_tld(fixture=0)
        tld_two = self.create_tld(fixture=1)

        criterion_one = dict(name=tld_one['name'])

        results = self.storage.find_tlds(self.admin_context,
                                         criterion_one)
        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], tld_one['name'])

        criterion_two = dict(name=tld_two['name'])

        results = self.storage.find_tlds(self.admin_context,
                                         criterion_two)
        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], tld_two['name'])

    def test_get_tld(self):
        # Create a tld
        expected = self.create_tld()
        actual = self.storage.get_tld(self.admin_context, expected['id'])

        self.assertEqual(actual['name'], expected['name'])

    def test_get_tld_missing(self):
        with testtools.ExpectedException(exceptions.TldNotFound):
            uuid = '4c8e7f82-3519-4bf7-8940-a66a4480f223'
            self.storage.get_tld(self.admin_context, uuid)

    def test_find_tld_criterion(self):
        # Create two tlds
        tld_one = self.create_tld(fixture=0)
        tld_two = self.create_tld(fixture=1)

        criterion = dict(name=tld_one['name'])

        # Find tld_one using its name as criterion
        result = self.storage.find_tld(self.admin_context, criterion)

        # Assert names match
        self.assertEqual(result['name'], tld_one['name'])

        # Repeat with tld_two
        criterion = dict(name=tld_two['name'])

        result = self.storage.find_tld(self.admin_context, criterion)

        self.assertEqual(result['name'], tld_two['name'])

    def test_find_tld_criterion_missing(self):
        expected = self.create_tld()

        criterion = dict(name=expected['name'] + "NOT FOUND")

        with testtools.ExpectedException(exceptions.TldNotFound):
            self.storage.find_tld(self.admin_context, criterion)

    def test_update_tld(self):
        # Create a tld
        tld = self.create_tld(name='net')

        # Update the tld
        tld.name = 'org'

        # Update storage
        tld = self.storage.update_tld(self.admin_context, tld)

        # Verify the new value
        self.assertEqual('org', tld.name)

        # Ensure the version column was incremented
        self.assertEqual(2, tld.version)

    def test_update_tld_duplicate(self):
        # Create two tlds
        tld_one = self.create_tld(fixture=0)
        tld_two = self.create_tld(fixture=1)

        # Update tld_two to be a duplicate of tld_ond
        tld_two.name = tld_one.name

        with testtools.ExpectedException(exceptions.DuplicateTld):
            self.storage.update_tld(self.admin_context, tld_two)

    def test_update_tld_missing(self):
        tld = objects.Tld(id='486f9cbe-b8b6-4d8c-8275-1a6e47b13e00')
        with testtools.ExpectedException(exceptions.TldNotFound):
            self.storage.update_tld(self.admin_context, tld)

    def test_delete_tld(self):
        # Create a tld
        tld = self.create_tld()

        # Delete the tld
        self.storage.delete_tld(self.admin_context, tld['id'])

        # Verify that it's deleted
        with testtools.ExpectedException(exceptions.TldNotFound):
            self.storage.get_tld(self.admin_context, tld['id'])

    def test_delete_tld_missing(self):
        with testtools.ExpectedException(exceptions.TldNotFound):
            uuid = 'cac1fc02-79b2-4e62-a1a4-427b6790bbe6'
            self.storage.delete_tld(self.admin_context, uuid)

    # Blacklist tests
    def test_create_blacklist(self):
        values = {
            'pattern': "^([A-Za-z0-9_\\-]+\\.)*example\\.com\\.$",
            'description': "This is a comment."
        }

        result = self.storage.create_blacklist(
            self.admin_context, objects.Blacklist.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNotNone(result['version'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['pattern'], values['pattern'])
        self.assertEqual(result['description'], values['description'])

    def test_create_blacklist_duplicate(self):
        # Create the initial Blacklist
        self.create_blacklist(fixture=0)

        with testtools.ExpectedException(exceptions.DuplicateBlacklist):
            self.create_blacklist(fixture=0)

    def test_find_blacklists(self):
        # Verify that there are no blacklists created
        actual = self.storage.find_blacklists(self.admin_context)
        self.assertEqual(0, len(actual))

        # Create a Blacklist
        blacklist = self.create_blacklist(fixture=0)

        actual = self.storage.find_blacklists(self.admin_context)
        self.assertEqual(1, len(actual))

        self.assertEqual(blacklist['pattern'], actual[0]['pattern'])

    def test_find_blacklists_paging(self):
        # Create 10 Blacklists
        created = [self.create_blacklist(pattern='^example-%d.org.' % i)
                   for i in range(10)]

        # Ensure we can page through the results.
        self._ensure_paging(created, self.storage.find_blacklists)

    def test_find_blacklists_with_criterion(self):
        # Create two blacklists
        blacklist_one = self.create_blacklist(fixture=0)
        blacklist_two = self.create_blacklist(fixture=1)

        # Verify blacklist_one
        criterion = dict(pattern=blacklist_one['pattern'])

        results = self.storage.find_blacklists(self.admin_context,
                                               criterion)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['pattern'], blacklist_one['pattern'])

        # Verify blacklist_two
        criterion = dict(pattern=blacklist_two['pattern'])

        results = self.storage.find_blacklists(self.admin_context,
                                               criterion)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['pattern'], blacklist_two['pattern'])

    def test_get_blacklist(self):
        expected = self.create_blacklist(fixture=0)
        actual = self.storage.get_blacklist(self.admin_context, expected['id'])

        self.assertEqual(actual['pattern'], expected['pattern'])

    def test_get_blacklist_missing(self):
        with testtools.ExpectedException(exceptions.BlacklistNotFound):
            uuid = '2c102ffd-7146-4b4e-ad62-b530ee0873fb'
            self.storage.get_blacklist(self.admin_context, uuid)

    def test_find_blacklist_criterion(self):
        blacklist_one = self.create_blacklist(fixture=0)
        blacklist_two = self.create_blacklist(fixture=1)

        criterion = dict(pattern=blacklist_one['pattern'])

        result = self.storage.find_blacklist(self.admin_context, criterion)

        self.assertEqual(result['pattern'], blacklist_one['pattern'])

        criterion = dict(pattern=blacklist_two['pattern'])

        result = self.storage.find_blacklist(self.admin_context, criterion)

        self.assertEqual(result['pattern'], blacklist_two['pattern'])

    def test_find_blacklist_criterion_missing(self):
        expected = self.create_blacklist(fixture=0)

        criterion = dict(pattern=expected['pattern'] + "NOT FOUND")

        with testtools.ExpectedException(exceptions.BlacklistNotFound):
            self.storage.find_blacklist(self.admin_context, criterion)

    def test_update_blacklist(self):
        blacklist = self.create_blacklist(pattern='^example.uk.')

        # Update the blacklist
        blacklist.pattern = '^example.uk.co.'

        blacklist = self.storage.update_blacklist(self.admin_context,
                                                  blacklist)
        # Verify the new values
        self.assertEqual('^example.uk.co.', blacklist.pattern)

        # Ensure the version column was incremented
        self.assertEqual(2, blacklist.version)

    def test_update_blacklist_duplicate(self):
        # Create two blacklists
        blacklist_one = self.create_blacklist(fixture=0)
        blacklist_two = self.create_blacklist(fixture=1)

        # Update the second one to be a duplicate of the first
        blacklist_two.pattern = blacklist_one.pattern

        with testtools.ExpectedException(exceptions.DuplicateBlacklist):
            self.storage.update_blacklist(self.admin_context,
                                          blacklist_two)

    def test_update_blacklist_missing(self):
        blacklist = objects.Blacklist(
            id='e8cee063-3a26-42d6-b181-bdbdc2c99d08')

        with testtools.ExpectedException(exceptions.BlacklistNotFound):
            self.storage.update_blacklist(self.admin_context, blacklist)

    def test_delete_blacklist(self):
        blacklist = self.create_blacklist(fixture=0)

        self.storage.delete_blacklist(self.admin_context, blacklist['id'])

        with testtools.ExpectedException(exceptions.BlacklistNotFound):
            self.storage.get_blacklist(self.admin_context, blacklist['id'])

    def test_delete_blacklist_missing(self):
        with testtools.ExpectedException(exceptions.BlacklistNotFound):
            uuid = '97f57960-f41b-4e93-8e22-8fd6c7e2c183'
            self.storage.delete_blacklist(self.admin_context, uuid)

    # Pool Tests
    def test_create_pool(self):
        values = {
            'name': 'test1',
            'tenant_id': self.admin_context.tenant,
            'provisioner': 'UNMANAGED'
        }

        result = self.storage.create_pool(
            self.admin_context, objects.Pool.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['name'], values['name'])
        self.assertEqual(result['tenant_id'], values['tenant_id'])
        self.assertEqual(result['provisioner'], values['provisioner'])

    def test_create_pool_duplicate(self):
        # Create the first pool
        self.create_pool(fixture=0)

        # Create the second pool and should get exception
        with testtools.ExpectedException(exceptions.DuplicatePool):
            self.create_pool(fixture=0)

    def test_find_pools(self):
        # Verify that there are no pools, except for default pool
        actual = self.storage.find_pools(self.admin_context)
        self.assertEqual(1, len(actual))

        # Create a Pool
        pool = self.create_pool(fixture=0)

        actual = self.storage.find_pools(self.admin_context)
        self.assertEqual(2, len(actual))

        # Test against the second pool, since the first is the default pool
        self.assertEqual(pool['name'], actual[1]['name'])

    def test_find_pools_paging(self):
        # Get any pools that are already created, including default
        pools = self.storage.find_pools(self.admin_context)

        # Create 10 Pools
        created = [self.create_pool(name='test%d' % i)
            for i in range(10)]

        # Add in the existing pools

        for p in pools:
            created.insert(0, p)

        # Ensure we can page through the results
        self._ensure_paging(created, self.storage.find_pools)

    def test_find_pools_criterion(self):
        # Create two pools
        pool_one = self.create_pool(fixture=0)
        pool_two = self.create_pool(fixture=1)

        # Verify pool_one
        criterion = dict(name=pool_one['name'])

        results = self.storage.find_pools(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], pool_one['name'])
        self.assertEqual(results[0]['provisioner'], pool_one['provisioner'])

        criterion = dict(name=pool_two['name'])

        results = self.storage.find_pools(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], pool_two['name'])
        self.assertEqual(results[0]['provisioner'], pool_two['provisioner'])

    def test_get_pool(self):
        # Create a pool
        expected = self.create_pool()
        actual = self.storage.get_pool(self.admin_context, expected['id'])

        self.assertEqual(actual['name'], expected['name'])
        self.assertEqual(actual['provisioner'], expected['provisioner'])

    def test_get_pool_missing(self):
        with testtools.ExpectedException(exceptions.PoolNotFound):
            uuid = 'c28893e3-eb87-4562-aa29-1f0e835d749b'
            self.storage.get_pool(self.admin_context, uuid)

    def test_find_pool_criterion(self):
        pool_one = self.create_pool(fixture=0)
        pool_two = self.create_pool(fixture=1)

        criterion = dict(name=pool_one['name'])

        result = self.storage.find_pool(self.admin_context, criterion)

        self.assertEqual(result['name'], pool_one['name'])
        self.assertEqual(result['provisioner'], pool_one['provisioner'])

        criterion = dict(name=pool_two['name'])

        result = self.storage.find_pool(self.admin_context, criterion)

        self.assertEqual(result['name'], pool_two['name'])
        self.assertEqual(result['provisioner'], pool_two['provisioner'])

    def test_find_pool_criterion_missing(self):
        expected = self.create_pool()

        criterion = dict(name=expected['name'] + "NOT FOUND")

        with testtools.ExpectedException(exceptions.PoolNotFound):
            self.storage.find_pool(self.admin_context, criterion)

    def test_update_pool(self):
        # Create a pool
        pool = self.create_pool(name='test1')

        # Update the Pool
        pool.name = 'test3'

        # Perform the update
        pool = self.storage.update_pool(self.admin_context, pool)

        # Verify the new value is there
        self.assertEqual('test3', pool.name)

    def test_update_pool_duplicate(self):
        # Create two pools
        pool_one = self.create_pool(fixture=0)
        pool_two = self.create_pool(fixture=1)

        # Update pool_two to be a duplicate of pool_one
        pool_two.name = pool_one.name

        with testtools.ExpectedException(exceptions.DuplicatePool):
            self.storage.update_pool(self.admin_context, pool_two)

    def test_update_pool_missing(self):
        pool = objects.Pool(id='8806f871-5140-43f4-badd-2bbc5715b013')

        with testtools.ExpectedException(exceptions.PoolNotFound):
            self.storage.update_pool(self.admin_context, pool)

    def test_delete_pool(self):
        pool = self.create_pool()

        self.storage.delete_pool(self.admin_context, pool['id'])

        with testtools.ExpectedException(exceptions.PoolNotFound):
            self.storage.get_pool(self.admin_context, pool['id'])

    def test_delete_pool_missing(self):
        with testtools.ExpectedException(exceptions.PoolNotFound):
            uuid = '203ca44f-c7e7-4337-9a02-0d735833e6aa'
            self.storage.delete_pool(self.admin_context, uuid)

    def test_create_zone_transfer_request(self):
        domain = self.create_domain()

        values = {
            'tenant_id': self.admin_context.tenant,
            'domain_id': domain.id,
            'key': 'qwertyuiop'
        }

        result = self.storage.create_zone_transfer_request(
            self.admin_context, objects.ZoneTransferRequest.from_dict(values))

        self.assertEqual(result['tenant_id'], self.admin_context.tenant)
        self.assertIn('status', result)

    def test_create_zone_transfer_request_scoped(self):
        domain = self.create_domain()
        tenant_2_context = self.get_context(tenant='2')
        tenant_3_context = self.get_context(tenant='3')

        values = {
            'tenant_id': self.admin_context.tenant,
            'domain_id': domain.id,
            'key': 'qwertyuiop',
            'target_tenant_id': tenant_2_context.tenant,
        }

        result = self.storage.create_zone_transfer_request(
            self.admin_context, objects.ZoneTransferRequest.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['tenant_id'], self.admin_context.tenant)
        self.assertEqual(result['target_tenant_id'], tenant_2_context.tenant)
        self.assertIn('status', result)

        stored_ztr = self.storage.get_zone_transfer_request(
            tenant_2_context, result.id)

        self.assertEqual(stored_ztr['tenant_id'], self.admin_context.tenant)
        self.assertEqual(result['id'], stored_ztr['id'])

        with testtools.ExpectedException(
                exceptions.ZoneTransferRequestNotFound):
            self.storage.get_zone_transfer_request(
                tenant_3_context, result.id)

    def test_find_zone_transfer_requests(self):
        domain = self.create_domain()

        values = {
            'tenant_id': self.admin_context.tenant,
            'domain_id': domain.id,
            'key': 'qwertyuiop'
        }

        self.storage.create_zone_transfer_request(
            self.admin_context, objects.ZoneTransferRequest.from_dict(values))

        requests = self.storage.find_zone_transfer_requests(
            self.admin_context, {"tenant_id": self.admin_context.tenant})
        self.assertEqual(len(requests), 1)

    def test_delete_zone_transfer_request(self):
        domain = self.create_domain()
        zt_request = self.create_zone_transfer_request(domain)

        self.storage.delete_zone_transfer_request(
            self.admin_context, zt_request.id)

        with testtools.ExpectedException(
                exceptions.ZoneTransferRequestNotFound):
            self.storage.get_zone_transfer_request(
                self.admin_context, zt_request.id)

    def test_update_zone_transfer_request(self):
        domain = self.create_domain()
        zt_request = self.create_zone_transfer_request(domain)

        zt_request.description = 'New description'
        result = self.storage.update_zone_transfer_request(
            self.admin_context, zt_request)
        self.assertEqual(result.description, 'New description')

    def test_get_zone_transfer_request(self):
        domain = self.create_domain()
        zt_request = self.create_zone_transfer_request(domain)

        result = self.storage.get_zone_transfer_request(
            self.admin_context, zt_request.id)
        self.assertEqual(result.id, zt_request.id)
        self.assertEqual(result.domain_id, zt_request.domain_id)

    def test_create_zone_transfer_accept(self):
        domain = self.create_domain()
        zt_request = self.create_zone_transfer_request(domain)
        values = {
            'tenant_id': self.admin_context.tenant,
            'zone_transfer_request_id': zt_request.id,
            'domain_id': domain.id,
            'key': zt_request.key
        }

        result = self.storage.create_zone_transfer_accept(
            self.admin_context, objects.ZoneTransferAccept.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['tenant_id'], self.admin_context.tenant)
        self.assertIn('status', result)

    def test_find_zone_transfer_accepts(self):
        domain = self.create_domain()
        zt_request = self.create_zone_transfer_request(domain)
        values = {
            'tenant_id': self.admin_context.tenant,
            'zone_transfer_request_id': zt_request.id,
            'domain_id': domain.id,
            'key': zt_request.key
        }

        self.storage.create_zone_transfer_accept(
            self.admin_context, objects.ZoneTransferAccept.from_dict(values))

        accepts = self.storage.find_zone_transfer_accepts(
            self.admin_context, {"tenant_id": self.admin_context.tenant})
        self.assertEqual(len(accepts), 1)

    def test_find_zone_transfer_accept(self):
        domain = self.create_domain()
        zt_request = self.create_zone_transfer_request(domain)
        values = {
            'tenant_id': self.admin_context.tenant,
            'zone_transfer_request_id': zt_request.id,
            'domain_id': domain.id,
            'key': zt_request.key
        }

        result = self.storage.create_zone_transfer_accept(
            self.admin_context, objects.ZoneTransferAccept.from_dict(values))

        accept = self.storage.find_zone_transfer_accept(
            self.admin_context, {"id": result.id})
        self.assertEqual(accept.id, result.id)

    def test_transfer_zone_ownership(self):
        tenant_1_context = self.get_context(tenant='1')
        tenant_2_context = self.get_context(tenant='2')
        admin_context = self.get_admin_context()
        admin_context.all_tenants = True

        domain = self.create_domain(context=tenant_1_context)
        recordset = self.create_recordset(domain, context=tenant_1_context)
        record = self.create_record(
            domain, recordset, context=tenant_1_context)

        updated_domain = domain

        updated_domain.tenant_id = tenant_2_context.tenant

        self.storage.update_domain(
            admin_context, updated_domain)

        saved_domain = self.storage.get_domain(
            admin_context, domain.id)
        saved_recordset = self.storage.get_recordset(
            admin_context, recordset.id)
        saved_record = self.storage.get_record(
            admin_context, record.id)

        self.assertEqual(saved_domain.tenant_id, tenant_2_context.tenant)
        self.assertEqual(saved_recordset.tenant_id, tenant_2_context.tenant)
        self.assertEqual(saved_record.tenant_id, tenant_2_context.tenant)

    def test_delete_zone_transfer_accept(self):
        domain = self.create_domain()
        zt_request = self.create_zone_transfer_request(domain)
        zt_accept = self.create_zone_transfer_accept(zt_request)

        self.storage.delete_zone_transfer_accept(
            self.admin_context, zt_accept.id)

        with testtools.ExpectedException(
                exceptions.ZoneTransferAcceptNotFound):
            self.storage.get_zone_transfer_accept(
                self.admin_context, zt_accept.id)

    def test_update_zone_transfer_accept(self):
        domain = self.create_domain()
        zt_request = self.create_zone_transfer_request(domain)
        zt_accept = self.create_zone_transfer_accept(zt_request)

        zt_accept.status = 'COMPLETE'
        result = self.storage.update_zone_transfer_accept(
            self.admin_context, zt_accept)
        self.assertEqual(result.status, 'COMPLETE')

    def test_get_zone_transfer_accept(self):
        domain = self.create_domain()
        zt_request = self.create_zone_transfer_request(domain)
        zt_accept = self.create_zone_transfer_accept(zt_request)

        result = self.storage.get_zone_transfer_accept(
            self.admin_context, zt_accept.id)
        self.assertEqual(result.id, zt_accept.id)
        self.assertEqual(result.domain_id, zt_accept.domain_id)

    # PoolAttribute tests
    def test_create_pool_attribute(self):
        values = {
            'pool_id': "d5d10661-0312-4ae1-8664-31188a4310b7",
            'key': "test-attribute",
            'value': 'test-value'
        }

        result = self.storage.create_pool_attribute(
            self.admin_context, values['pool_id'],
            objects.PoolAttribute.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNotNone(result['version'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['pool_id'], values['pool_id'])
        self.assertEqual(result['key'], values['key'])
        self.assertEqual(result['value'], values['value'])

    def test_find_pool_attribute(self):
        # Verify that there are no Pool Attributes created
        actual = self.storage.find_pool_attributes(self.admin_context)
        self.assertEqual(0, len(actual))

        # Create a Pool Attribute
        pool_attribute = self.create_pool_attribute(fixture=0)

        actual = self.storage.find_pool_attributes(self.admin_context)
        self.assertEqual(1, len(actual))

        self.assertEqual(pool_attribute['pool_id'], actual[0]['pool_id'])
        self.assertEqual(pool_attribute['key'], actual[0]['key'])
        self.assertEqual(pool_attribute['value'], actual[0]['value'])

    def test_find_pool_attributes_paging(self):
        # Create 10 Pool Attributes
        created = [self.create_pool_attribute(value='^ns%d.example.com.' % i)
                   for i in range(10)]

        # Ensure we can page through the results.
        self._ensure_paging(created, self.storage.find_pool_attributes)

    def test_find_pool_attributes_with_criterion(self):
        # Create two pool attributes
        pool_attribute_one = self.create_pool_attribute(fixture=0)
        pool_attribute_two = self.create_pool_attribute(fixture=1)

        # Verify pool_attribute_one
        criterion = dict(key=pool_attribute_one['key'])

        results = self.storage.find_pool_attributes(self.admin_context,
                                                    criterion)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['pool_id'], pool_attribute_one['pool_id'])
        self.assertEqual(results[0]['key'], pool_attribute_one['key'])
        self.assertEqual(results[0]['value'], pool_attribute_one['value'])

        # Verify pool_attribute_two
        criterion = dict(key=pool_attribute_two['key'])
        LOG.debug("Criterion is %r " % criterion)

        results = self.storage.find_pool_attributes(self.admin_context,
                                                    criterion)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['pool_id'], pool_attribute_two['pool_id'])
        self.assertEqual(results[0]['key'], pool_attribute_two['key'])
        self.assertEqual(results[0]['value'], pool_attribute_two['value'])

    def test_get_pool_attribute(self):
        expected = self.create_pool_attribute(fixture=0)
        actual = self.storage.get_pool_attribute(self.admin_context,
                                                 expected['id'])

        self.assertEqual(actual['pool_id'], expected['pool_id'])
        self.assertEqual(actual['key'], expected['key'])
        self.assertEqual(actual['value'], expected['value'])

    def test_get_pool_attribute_missing(self):
        with testtools.ExpectedException(exceptions.PoolAttributeNotFound):
            uuid = '2c102ffd-7146-4b4e-ad62-b530ee0873fb'
            self.storage.get_pool_attribute(self.admin_context, uuid)

    def test_find_pool_attribute_criterion(self):
        pool_attribute_one = self.create_pool_attribute(fixture=0)
        pool_attribute_two = self.create_pool_attribute(fixture=1)

        criterion = dict(key=pool_attribute_one['key'])

        result = self.storage.find_pool_attribute(self.admin_context,
                                                  criterion)

        self.assertEqual(result['pool_id'], pool_attribute_one['pool_id'])
        self.assertEqual(result['key'], pool_attribute_one['key'])
        self.assertEqual(result['value'], pool_attribute_one['value'])

        criterion = dict(key=pool_attribute_two['key'])

        result = self.storage.find_pool_attribute(self.admin_context,
                                                  criterion)

        self.assertEqual(result['pool_id'], pool_attribute_two['pool_id'])
        self.assertEqual(result['key'], pool_attribute_two['key'])
        self.assertEqual(result['value'], pool_attribute_two['value'])

    def test_find_pool_attribute_criterion_missing(self):
        expected = self.create_pool_attribute(fixture=0)

        criterion = dict(key=expected['key'] + "NOT FOUND")

        with testtools.ExpectedException(exceptions.PoolAttributeNotFound):
            self.storage.find_pool_attribute(self.admin_context, criterion)

    def test_update_pool_attribute(self):
        pool_attribute = self.create_pool_attribute(value='ns1.example.org')

        # Update the Pool Attribute
        pool_attribute.value = 'ns5.example.org'

        pool_attribute = self.storage.update_pool_attribute(self.admin_context,
                                                            pool_attribute)
        # Verify the new values
        self.assertEqual('ns5.example.org', pool_attribute.value)

        # Ensure the version column was incremented
        self.assertEqual(2, pool_attribute.version)

    def test_update_pool_attribute_missing(self):
        pool_attribute = objects.PoolAttribute(
            id='728a329a-83b1-4573-82dc-45dceab435d4')

        with testtools.ExpectedException(exceptions.PoolAttributeNotFound):
            self.storage.update_pool_attribute(self.admin_context,
                                               pool_attribute)

    def test_update_pool_attribute_duplicate(self):
        # Create two PoolAttributes
        pool_attribute_one = self.create_pool_attribute(fixture=0)
        pool_attribute_two = self.create_pool_attribute(fixture=1)

        # Update the second one to be a duplicate of the first
        pool_attribute_two.pool_id = pool_attribute_one.pool_id
        pool_attribute_two.key = pool_attribute_one.key
        pool_attribute_two.value = pool_attribute_one.value

        with testtools.ExpectedException(exceptions.DuplicatePoolAttribute):
            self.storage.update_pool_attribute(self.admin_context,
                                               pool_attribute_two)

    def test_delete_pool_attribute(self):
        pool_attribute = self.create_pool_attribute(fixture=0)

        self.storage.delete_pool_attribute(self.admin_context,
                                           pool_attribute['id'])

        with testtools.ExpectedException(exceptions.PoolAttributeNotFound):
            self.storage.get_pool_attribute(self.admin_context,
                                            pool_attribute['id'])

    def test_delete_oool_attribute_missing(self):
        with testtools.ExpectedException(exceptions.PoolAttributeNotFound):
            uuid = '464e9250-4fe0-4267-9993-da639390bb04'
            self.storage.delete_pool_attribute(self.admin_context, uuid)

    def test_create_pool_attribute_duplicate(self):
        # Create the initial PoolAttribute
        self.create_pool_attribute(fixture=0)

        with testtools.ExpectedException(exceptions.DuplicatePoolAttribute):
            self.create_pool_attribute(fixture=0)

    # Zone Import Tests
    def test_create_zone_import(self):
        values = {
            'status': 'PENDING',
            'task_type': 'IMPORT'
        }

        result = self.storage.create_zone_import(
            self.admin_context, objects.ZoneImport.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])
        self.assertIsNotNone(result['version'])
        self.assertEqual(result['status'], values['status'])
        self.assertEqual(result['domain_id'], None)
        self.assertEqual(result['message'], None)

    def test_find_zone_imports(self):

        actual = self.storage.find_zone_imports(self.admin_context)
        self.assertEqual(0, len(actual))

        # Create a single ZoneImport
        zone_import = self.create_zone_import(fixture=0)

        actual = self.storage.find_zone_imports(self.admin_context)
        self.assertEqual(1, len(actual))

        self.assertEqual(zone_import['status'], actual[0]['status'])
        self.assertEqual(zone_import['message'], actual[0]['message'])
        self.assertEqual(zone_import['domain_id'], actual[0]['domain_id'])

    def test_find_zone_imports_paging(self):
        # Create 10 ZoneImports
        created = [self.create_zone_import() for i in range(10)]

        # Ensure we can page through the results.
        self._ensure_paging(created, self.storage.find_zone_imports)

    def test_find_zone_imports_with_criterion(self):
        zone_import_one = self.create_zone_import(fixture=0)
        zone_import_two = self.create_zone_import(fixture=1)

        criterion_one = dict(status=zone_import_one['status'])

        results = self.storage.find_zone_imports(self.admin_context,
                                         criterion_one)
        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['status'], zone_import_one['status'])

        criterion_two = dict(status=zone_import_two['status'])

        results = self.storage.find_zone_imports(self.admin_context,
                                         criterion_two)
        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['status'], zone_import_two['status'])

    def test_get_zone_import(self):
        # Create a zone_import
        expected = self.create_zone_import()
        actual = self.storage.get_zone_import(self.admin_context,
                                 expected['id'])

        self.assertEqual(actual['status'], expected['status'])

    def test_get_zone_import_missing(self):
        with testtools.ExpectedException(exceptions.ZoneImportNotFound):
            uuid = '4c8e7f82-3519-4bf7-8940-a66a4480f223'
            self.storage.get_zone_import(self.admin_context, uuid)

    def test_find_zone_import_criterion_missing(self):
        expected = self.create_zone_import()

        criterion = dict(status=expected['status'] + "NOT FOUND")

        with testtools.ExpectedException(exceptions.ZoneImportNotFound):
            self.storage.find_zone_import(self.admin_context, criterion)

    def test_update_zone_import(self):
        # Create a zone_import
        zone_import = self.create_zone_import(status='PENDING',
                                              task_type='IMPORT')

        # Update the zone_import
        zone_import.status = 'COMPLETE'

        # Update storage
        zone_import = self.storage.update_zone_import(self.admin_context,
                                                  zone_import)

        # Verify the new value
        self.assertEqual('COMPLETE', zone_import.status)

        # Ensure the version column was incremented
        self.assertEqual(2, zone_import.version)

    def test_update_zone_import_missing(self):
        zone_import = objects.ZoneImport(
                        id='486f9cbe-b8b6-4d8c-8275-1a6e47b13e00')
        with testtools.ExpectedException(exceptions.ZoneImportNotFound):
            self.storage.update_zone_import(self.admin_context, zone_import)

    def test_delete_zone_import(self):
        # Create a zone_import
        zone_import = self.create_zone_import()

        # Delete the zone_import
        self.storage.delete_zone_import(self.admin_context, zone_import['id'])

        # Verify that it's deleted
        with testtools.ExpectedException(exceptions.ZoneImportNotFound):
            self.storage.get_zone_import(self.admin_context, zone_import['id'])

    def test_delete_zone_import_missing(self):
        with testtools.ExpectedException(exceptions.ZoneImportNotFound):
            uuid = 'cac1fc02-79b2-4e62-a1a4-427b6790bbe6'
            self.storage.delete_zone_import(self.admin_context, uuid)
