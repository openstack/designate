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
import testtools

from designate.openstack.common import log as logging
from designate import exceptions

LOG = logging.getLogger(__name__)


class StorageTestCase(object):
    def create_quota(self, fixture=0, values={}):
        fixture = self.get_quota_fixture(fixture, values)
        return fixture, self.storage.create_quota(self.admin_context, fixture)

    def create_server(self, fixture=0, values={}):
        fixture = self.get_server_fixture(fixture, values)
        return fixture, self.storage.create_server(self.admin_context, fixture)

    def create_tsigkey(self, fixture=0, values={}):
        fixture = self.get_tsigkey_fixture(fixture, values)
        return fixture, self.storage.create_tsigkey(self.admin_context,
                                                    fixture)

    def create_domain(self, fixture=0, values={}):
        fixture = self.get_domain_fixture(fixture, values)

        if 'tenant_id' not in values:
            fixture['tenant_id'] = self.admin_context.tenant_id

        return fixture, self.storage.create_domain(self.admin_context,
                                                   fixture)

    def create_record(self, domain, fixture=0, values={}):
        fixture = self.get_record_fixture(domain['name'], fixture, values)
        return fixture, self.storage.create_record(self.admin_context,
                                                   domain['id'],
                                                   fixture)

    # Quota Tests
    def test_create_quota(self):
        values = self.get_quota_fixture()

        result = self.storage.create_quota(self.admin_context, values=values)

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['tenant_id'], values['tenant_id'])
        self.assertEqual(result['resource'], values['resource'])
        self.assertEqual(result['hard_limit'], values['hard_limit'])

    def test_create_quota_duplicate(self):
        # Create the initial quota
        self.create_quota()

        with testtools.ExpectedException(exceptions.DuplicateQuota):
            self.create_quota()

    def test_find_quotas(self):
        actual = self.storage.find_quotas(self.admin_context)
        self.assertEqual(actual, [])

        # Create a single quota
        _, quota_one = self.create_quota()

        actual = self.storage.find_quotas(self.admin_context)
        self.assertEqual(len(actual), 1)

        self.assertEqual(actual[0]['tenant_id'], quota_one['tenant_id'])
        self.assertEqual(actual[0]['resource'], quota_one['resource'])
        self.assertEqual(actual[0]['hard_limit'], quota_one['hard_limit'])

        # Create a second quota
        _, quota_two = self.create_quota(fixture=1)

        actual = self.storage.find_quotas(self.admin_context)
        self.assertEqual(len(actual), 2)

        self.assertEqual(actual[1]['tenant_id'], quota_two['tenant_id'])
        self.assertEqual(actual[1]['resource'], quota_two['resource'])
        self.assertEqual(actual[1]['hard_limit'], quota_two['hard_limit'])

    def test_find_quotas_criterion(self):
        _, quota_one = self.create_quota(0)
        _, quota_two = self.create_quota(1)

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
        _, expected = self.create_quota()
        actual = self.storage.get_quota(self.admin_context, expected['id'])

        self.assertEqual(actual['tenant_id'], expected['tenant_id'])
        self.assertEqual(actual['resource'], expected['resource'])
        self.assertEqual(actual['hard_limit'], expected['hard_limit'])

    def test_get_quota_missing(self):
        with testtools.ExpectedException(exceptions.QuotaNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.get_quota(self.admin_context, uuid)

    def test_find_quota_criterion(self):
        _, quota_one = self.create_quota(0)
        _, quota_two = self.create_quota(1)

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
        _, expected = self.create_quota(0)

        criterion = dict(
            tenant_id=expected['tenant_id'] + "NOT FOUND"
        )

        with testtools.ExpectedException(exceptions.QuotaNotFound):
            self.storage.find_quota(self.admin_context, criterion)

    def test_update_quota(self):
        # Create a quota
        fixture, quota = self.create_quota()

        updated = self.storage.update_quota(self.admin_context, quota['id'],
                                            fixture)

        self.assertEqual(updated['tenant_id'], fixture['tenant_id'])
        self.assertEqual(updated['resource'], fixture['resource'])
        self.assertEqual(updated['hard_limit'], fixture['hard_limit'])

    def test_update_quota_duplicate(self):
        # Create two quotas
        self.create_quota(fixture=0)
        _, quota = self.create_quota(fixture=1)

        values = self.quota_fixtures[0]

        with testtools.ExpectedException(exceptions.DuplicateQuota):
            self.storage.update_quota(self.admin_context, quota['id'],
                                      values)

    def test_update_quota_missing(self):
        with testtools.ExpectedException(exceptions.QuotaNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.update_quota(self.admin_context, uuid, {})

    def test_delete_quota(self):
        quota_fixture, quota = self.create_quota()

        self.storage.delete_quota(self.admin_context, quota['id'])

        with testtools.ExpectedException(exceptions.QuotaNotFound):
            self.storage.get_quota(self.admin_context, quota['id'])

    def test_delete_quota_missing(self):
        with testtools.ExpectedException(exceptions.QuotaNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.delete_quota(self.admin_context, uuid)

    # Server Tests
    def test_create_server(self):
        values = {
            'name': 'ns1.example.org.'
        }

        result = self.storage.create_server(self.admin_context, values=values)

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['name'], values['name'])

    def test_create_server_duplicate(self):
        # Create the Initial Server
        self.create_server()

        with testtools.ExpectedException(exceptions.DuplicateServer):
            self.create_server()

    def test_find_servers(self):
        actual = self.storage.find_servers(self.admin_context)
        self.assertEqual(actual, [])

        # Create a single server
        _, server_one = self.create_server()

        actual = self.storage.find_servers(self.admin_context)
        self.assertEqual(len(actual), 1)

        self.assertEqual(str(actual[0]['name']), str(server_one['name']))

        # Create a second server
        _, server_two = self.create_server(fixture=1)

        actual = self.storage.find_servers(self.admin_context)
        self.assertEqual(len(actual), 2)

        self.assertEqual(str(actual[1]['name']), str(server_two['name']))

    def test_find_servers_criterion(self):
        _, server_one = self.create_server(0)
        _, server_two = self.create_server(1)

        criterion = dict(
            name=server_one['name']
        )

        results = self.storage.find_servers(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], server_one['name'])

        criterion = dict(
            name=server_two['name']
        )

        results = self.storage.find_servers(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], server_two['name'])

    def test_get_server(self):
        # Create a server
        _, expected = self.create_server()
        actual = self.storage.get_server(self.admin_context, expected['id'])

        self.assertEqual(str(actual['name']), str(expected['name']))

    def test_get_server_missing(self):
        with testtools.ExpectedException(exceptions.ServerNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.get_server(self.admin_context, uuid)

    def test_update_server(self):
        # Create a server
        fixture, server = self.create_server()

        updated = self.storage.update_server(self.admin_context, server['id'],
                                             fixture)

        self.assertEqual(str(updated['name']), str(fixture['name']))

    def test_update_server_duplicate(self):
        # Create two servers
        self.create_server(fixture=0)
        _, server = self.create_server(fixture=1)

        values = self.server_fixtures[0]

        with testtools.ExpectedException(exceptions.DuplicateServer):
            self.storage.update_server(self.admin_context, server['id'],
                                       values)

    def test_update_server_missing(self):
        with testtools.ExpectedException(exceptions.ServerNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.update_server(self.admin_context, uuid, {})

    def test_delete_server(self):
        server_fixture, server = self.create_server()

        self.storage.delete_server(self.admin_context, server['id'])

        with testtools.ExpectedException(exceptions.ServerNotFound):
            self.storage.get_server(self.admin_context, server['id'])

    def test_delete_server_missing(self):
        with testtools.ExpectedException(exceptions.ServerNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.delete_server(self.admin_context, uuid)

    # TSIG Key Tests
    def test_create_tsigkey(self):
        values = self.get_tsigkey_fixture()

        result = self.storage.create_tsigkey(self.admin_context, values=values)

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['name'], values['name'])
        self.assertEqual(result['algorithm'], values['algorithm'])
        self.assertEqual(result['secret'], values['secret'])

    def test_create_tsigkey_duplicate(self):
        # Create the Initial TsigKey
        _, tsigkey_one = self.create_tsigkey()

        values = self.get_tsigkey_fixture(1)
        values['name'] = tsigkey_one['name']

        with testtools.ExpectedException(exceptions.DuplicateTsigKey):
            self.create_tsigkey(values=values)

    def test_find_tsigkeys(self):
        actual = self.storage.find_tsigkeys(self.admin_context)
        self.assertEqual(actual, [])

        # Create a single tsigkey
        _, tsigkey_one = self.create_tsigkey()

        actual = self.storage.find_tsigkeys(self.admin_context)
        self.assertEqual(len(actual), 1)

        self.assertEqual(actual[0]['name'], tsigkey_one['name'])
        self.assertEqual(actual[0]['algorithm'], tsigkey_one['algorithm'])
        self.assertEqual(actual[0]['secret'], tsigkey_one['secret'])

        # Create a second tsigkey
        _, tsigkey_two = self.create_tsigkey(fixture=1)

        actual = self.storage.find_tsigkeys(self.admin_context)
        self.assertEqual(len(actual), 2)

        self.assertEqual(actual[1]['name'], tsigkey_two['name'])
        self.assertEqual(actual[1]['algorithm'], tsigkey_two['algorithm'])
        self.assertEqual(actual[1]['secret'], tsigkey_two['secret'])

    def test_find_tsigkeys_criterion(self):
        _, tsigkey_one = self.create_tsigkey(fixture=0)
        _, tsigkey_two = self.create_tsigkey(fixture=1)

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
        _, expected = self.create_tsigkey()

        actual = self.storage.get_tsigkey(self.admin_context, expected['id'])

        self.assertEqual(actual['name'], expected['name'])
        self.assertEqual(actual['algorithm'], expected['algorithm'])
        self.assertEqual(actual['secret'], expected['secret'])

    def test_get_tsigkey_missing(self):
        with testtools.ExpectedException(exceptions.TsigKeyNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.get_tsigkey(self.admin_context, uuid)

    def test_update_tsigkey(self):
        # Create a tsigkey
        fixture, tsigkey = self.create_tsigkey()

        updated = self.storage.update_tsigkey(self.admin_context,
                                              tsigkey['id'],
                                              fixture)

        self.assertEqual(updated['name'], fixture['name'])
        self.assertEqual(updated['algorithm'], fixture['algorithm'])
        self.assertEqual(updated['secret'], fixture['secret'])

    def test_update_tsigkey_duplicate(self):
        # Create two tsigkeys
        self.create_tsigkey(fixture=0)
        _, tsigkey = self.create_tsigkey(fixture=1)

        values = self.tsigkey_fixtures[0]

        with testtools.ExpectedException(exceptions.DuplicateTsigKey):
            self.storage.update_tsigkey(self.admin_context, tsigkey['id'],
                                        values)

    def test_update_tsigkey_missing(self):
        with testtools.ExpectedException(exceptions.TsigKeyNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.update_tsigkey(self.admin_context, uuid, {})

    def test_delete_tsigkey(self):
        tsigkey_fixture, tsigkey = self.create_tsigkey()

        self.storage.delete_tsigkey(self.admin_context, tsigkey['id'])

        with testtools.ExpectedException(exceptions.TsigKeyNotFound):
            self.storage.get_tsigkey(self.admin_context, tsigkey['id'])

    def test_delete_tsigkey_missing(self):
        with testtools.ExpectedException(exceptions.TsigKeyNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.delete_tsigkey(self.admin_context, uuid)

    # Tenant Tests
    def test_find_tenants(self):
        # create 3 domains in 2 tenants
        self.create_domain(fixture=0, values={'tenant_id': 'One'})
        _, domain = self.create_domain(fixture=1, values={'tenant_id': 'One'})
        self.create_domain(fixture=2, values={'tenant_id': 'Two'})

        # Delete one of the domains.
        self.storage.delete_domain(self.admin_context, domain['id'])

        # Ensure we get accurate results
        result = self.storage.find_tenants(self.admin_context)

        expected = [{
            'id': 'One',
            'domain_count': 1
        }, {
            'id': 'Two',
            'domain_count': 1
        }]

        self.assertEqual(result, expected)

    def test_get_tenant(self):
        # create 2 domains in a tenant
        _, domain_1 = self.create_domain(fixture=0, values={'tenant_id': 1})
        _, domain_2 = self.create_domain(fixture=1, values={'tenant_id': 1})
        _, domain_3 = self.create_domain(fixture=2, values={'tenant_id': 1})

        # Delete one of the domains.
        self.storage.delete_domain(self.admin_context, domain_3['id'])

        result = self.storage.get_tenant(self.admin_context, 1)

        self.assertEqual(result['id'], 1)
        self.assertEqual(result['domain_count'], 2)
        self.assertEqual(sorted(result['domains']),
                         [domain_1['name'], domain_2['name']])

    def test_count_tenants(self):
        # in the beginning, there should be nothing
        tenants = self.storage.count_tenants(self.admin_context)
        self.assertEqual(tenants, 0)

        # create 2 domains with 2 tenants
        self.create_domain(fixture=0, values={'tenant_id': 1})
        self.create_domain(fixture=1, values={'tenant_id': 2})
        _, domain = self.create_domain(fixture=2, values={'tenant_id': 2})

        # Delete one of the domains.
        self.storage.delete_domain(self.admin_context, domain['id'])

        tenants = self.storage.count_tenants(self.admin_context)
        self.assertEqual(tenants, 2)

    # Domain Tests
    def test_create_domain(self):
        values = {
            'tenant_id': self.admin_context.tenant_id,
            'name': 'example.net.',
            'email': 'example@example.net'
        }

        result = self.storage.create_domain(self.admin_context, values=values)

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['tenant_id'], self.admin_context.tenant_id)
        self.assertEqual(result['name'], values['name'])
        self.assertEqual(result['email'], values['email'])
        self.assertIn('status', result)

    def test_create_domain_duplicate(self):
        # Create the Initial Domain
        self.create_domain()

        with testtools.ExpectedException(exceptions.DuplicateDomain):
            self.create_domain()

    def test_find_domains(self):
        actual = self.storage.find_domains(self.admin_context)
        self.assertEqual(actual, [])

        # Create a single domain
        fixture_one, domain_one = self.create_domain()

        actual = self.storage.find_domains(self.admin_context)
        self.assertEqual(len(actual), 1)

        self.assertEqual(actual[0]['name'], domain_one['name'])
        self.assertEqual(actual[0]['email'], domain_one['email'])

        # Create a second domain
        self.create_domain(fixture=1)

        actual = self.storage.find_domains(self.admin_context)
        self.assertEqual(len(actual), 2)

    def test_find_domains_criterion(self):
        _, domain_one = self.create_domain(0)
        _, domain_two = self.create_domain(1)

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

    def test_get_domain(self):
        # Create a domain
        fixture, expected = self.create_domain()
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

        _, domain = self.create_domain()

        self.storage.delete_domain(context, domain['id'])
        self.storage.get_domain(context, domain['id'])

    def test_find_domain_criterion(self):
        _, domain_one = self.create_domain(0)
        _, domain_two = self.create_domain(1)

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
        _, expected = self.create_domain(0)

        criterion = dict(
            name=expected['name'] + "NOT FOUND"
        )

        with testtools.ExpectedException(exceptions.DomainNotFound):
            self.storage.find_domain(self.admin_context, criterion)

    def test_update_domain(self):
        # Create a domain
        fixture, domain = self.create_domain()

        updated = self.storage.update_domain(self.admin_context, domain['id'],
                                             fixture)

        self.assertEqual(updated['name'], fixture['name'])
        self.assertEqual(updated['email'], fixture['email'])
        self.assertIn('status', updated)

    def test_update_domain_duplicate(self):
        # Create two domains
        fixture_one, domain_one = self.create_domain(fixture=0)
        _, domain_two = self.create_domain(fixture=1)

        with testtools.ExpectedException(exceptions.DuplicateDomain):
            self.storage.update_domain(self.admin_context, domain_two['id'],
                                       fixture_one)

    def test_update_domain_missing(self):
        with testtools.ExpectedException(exceptions.DomainNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.update_domain(self.admin_context, uuid, {})

    def test_delete_domain(self):
        domain_fixture, domain = self.create_domain()

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

    def test_create_record(self):
        domain_fixture, domain = self.create_domain()

        values = {
            'name': 'www.%s' % domain['name'],
            'type': 'A',
            'data': '192.0.2.1',
        }

        result = self.storage.create_record(self.admin_context, domain['id'],
                                            values=values)

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNotNone(result['hash'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['tenant_id'], self.admin_context.tenant_id)
        self.assertEqual(result['name'], values['name'])
        self.assertEqual(result['type'], values['type'])
        self.assertEqual(result['data'], values['data'])
        self.assertIn('status', result)

    def test_create_record_duplicate(self):
        _, domain = self.create_domain()

        # Create the First Record
        self.create_record(domain)

        with testtools.ExpectedException(exceptions.DuplicateRecord):
            # Attempt to create the second/duplicate record
            self.create_record(domain)

    def test_find_records(self):
        _, domain = self.create_domain()
        actual = self.storage.find_records(
            self.admin_context,
            criterion={'domain_id': domain['id']})
        self.assertEqual(actual, [])

        # Create a single record
        _, record_one = self.create_record(domain, fixture=0)

        actual = self.storage.find_records(
            self.admin_context,
            criterion={'domain_id': domain['id']})
        self.assertEqual(len(actual), 1)

        self.assertEqual(actual[0]['name'], record_one['name'])
        self.assertEqual(actual[0]['type'], record_one['type'])
        self.assertEqual(actual[0]['data'], record_one['data'])
        self.assertIn('status', record_one)

        # Create a second record
        _, record_two = self.create_record(domain, fixture=1)

        actual = self.storage.find_records(
            self.admin_context,
            criterion={'domain_id': domain['id']})
        self.assertEqual(len(actual), 2)

        self.assertEqual(actual[1]['name'], record_two['name'])
        self.assertEqual(actual[1]['type'], record_two['type'])
        self.assertEqual(actual[1]['data'], record_two['data'])
        self.assertIn('status', record_two)

    def test_find_records_criterion(self):
        _, domain = self.create_domain()

        _, record_one = self.create_record(domain, fixture=0)
        self.create_record(domain, fixture=1)

        criterion = dict(
            data=record_one['data'],
            domain_id=domain['id']
        )

        results = self.storage.find_records(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        criterion = dict(
            type='A',
            domain_id=domain['id']
        )

        results = self.storage.find_records(self.admin_context, criterion)

        self.assertEqual(len(results), 2)

    def test_find_records_criterion_wildcard(self):
        _, domain = self.create_domain()

        values = {'name': 'one.%s' % domain['name']}

        self.create_record(domain, fixture=0, values=values)
        criterion = dict(
            name="%%%s" % domain['name'],
            domain_id=domain['id']
        )

        results = self.storage.find_records(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

    def test_get_record(self):
        _, domain = self.create_domain()

        _, expected = self.create_record(domain)

        actual = self.storage.get_record(self.admin_context, expected['id'])

        self.assertEqual(actual['name'], expected['name'])
        self.assertEqual(actual['type'], expected['type'])
        self.assertEqual(actual['data'], expected['data'])
        self.assertIn('status', actual)

    def test_get_record_missing(self):
        with testtools.ExpectedException(exceptions.RecordNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.get_record(self.admin_context, uuid)

    def test_find_record_criterion(self):
        _, domain = self.create_domain(0)
        _, expected = self.create_record(domain)

        criterion = dict(
            name=expected['name'],
            domain_id=domain['id']
        )

        actual = self.storage.find_record(self.admin_context, criterion)

        self.assertEqual(actual['name'], expected['name'])
        self.assertEqual(actual['type'], expected['type'])
        self.assertEqual(actual['data'], expected['data'])
        self.assertIn('status', actual)

    def test_find_record_criterion_missing(self):
        _, domain = self.create_domain(0)
        _, expected = self.create_record(domain)

        criterion = dict(
            name=expected['name'] + "NOT FOUND",
            domain_id=domain['id']
        )

        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.storage.find_record(self.admin_context, criterion)

    def test_update_record(self):
        domain_fixture, domain = self.create_domain()

        # Create a record
        _, record = self.create_record(domain)

        # Get some different values to test the update with
        record_fixture = self.get_record_fixture(domain['name'], fixture=1)

        # Update the record with the new values...
        updated = self.storage.update_record(self.admin_context, record['id'],
                                             record_fixture)

        # Ensure the update succeeded
        self.assertEqual(updated['id'], record['id'])
        self.assertEqual(updated['name'], record_fixture['name'])
        self.assertEqual(updated['type'], record_fixture['type'])
        self.assertEqual(updated['data'], record_fixture['data'])
        self.assertNotEqual(updated['hash'], record['hash'])
        self.assertIn('status', updated)

    def test_update_record_duplicate(self):
        _, domain = self.create_domain()

        # Create the first two records
        record_one_fixture, _ = self.create_record(domain, fixture=0)
        _, record_two = self.create_record(domain, fixture=1)

        with testtools.ExpectedException(exceptions.DuplicateRecord):
            # Attempt to update the second record, making it a duplicate record
            self.storage.update_record(self.admin_context, record_two['id'],
                                       record_one_fixture)

    def test_update_record_missing(self):
        with testtools.ExpectedException(exceptions.RecordNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.update_record(self.admin_context, uuid, {})

    def test_delete_record(self):
        _, domain = self.create_domain()

        # Create a record
        _, record = self.create_record(domain)

        self.storage.delete_record(self.admin_context, record['id'])

        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.storage.get_record(self.admin_context, record['id'])

    def test_delete_record_missing(self):
        with testtools.ExpectedException(exceptions.RecordNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.delete_record(self.admin_context, uuid)

    def test_ping(self):
        pong = self.storage.ping(self.admin_context)

        self.assertEqual(pong['status'], True)
        self.assertIsNotNone(pong['rtt'])

    def test_count_records(self):
        # in the beginning, there should be nothing
        records = self.storage.count_records(self.admin_context)
        self.assertEqual(records, 0)

        # Create a single domain & record
        _, domain = self.create_domain()
        self.create_record(domain)

        # we should have 1 record now
        records = self.storage.count_domains(self.admin_context)
        self.assertEqual(records, 1)
