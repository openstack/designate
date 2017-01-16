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
import math

import mock
import testtools
from oslo_config import cfg
from oslo_log import log as logging

from designate import exceptions
from designate import objects
from designate.utils import generate_uuid
from designate.storage.base import Storage as StorageBase
from designate.utils import DEFAULT_MDNS_PORT


LOG = logging.getLogger(__name__)


class StorageTestCase(object):
    # TODO(kiall): Someone, Somewhere, could probably make use of a
    #              assertNestedDictContainsSubset(), cleanup and put somewhere
    #              better.
    def assertNestedDictContainsSubset(self, expected, actual):
        for key, value in expected.items():
            if isinstance(value, dict):
                self.assertNestedDictContainsSubset(value, actual.get(key, {}))

            elif isinstance(value, list):
                self.assertEqual(len(value), len(actual[key]))

                for index, item in enumerate(value):
                    self.assertNestedDictContainsSubset(
                        item, actual[key][index])

            else:
                self.assertEqual(value, actual[key])

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

    def create_pool_nameserver(self, pool, **kwargs):
        # NOTE(kiall): We add this method here, rather than in the base test
        #              case, as the base methods expect to make a central API
        #              call. If a central API method is exposed for this, we
        #              should remove this and add to the base.
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_pool_nameserver_fixture(
            fixture=fixture, values=kwargs)

        if 'pool_id' not in values:
            values['pool_id'] = pool.id

        return self.storage.create_pool_nameserver(
            context, pool.id, objects.PoolNameserver.from_dict(values))

    def create_pool_target(self, pool, **kwargs):
        # NOTE(kiall): We add this method here, rather than in the base test
        #              case, as the base methods expect to make a central API
        #              call. If a central API method is exposed for this, we
        #              should remove this and add to the base.
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_pool_target_fixture(
            fixture=fixture, values=kwargs)

        if 'pool_id' not in values:
            values['pool_id'] = pool.id

        return self.storage.create_pool_target(
            context, pool.id, objects.PoolTarget.from_dict(values))

    def create_pool_also_notify(self, pool, **kwargs):
        # NOTE(kiall): We add this method here, rather than in the base test
        #              case, as the base methods expect to make a central API
        #              call. If a central API method is exposed for this, we
        #              should remove this and add to the base.
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_pool_also_notify_fixture(
            fixture=fixture, values=kwargs)

        if 'pool_id' not in values:
            values['pool_id'] = pool.id

        return self.storage.create_pool_also_notify(
            context, pool.id, objects.PoolAlsoNotify.from_dict(values))

    # Paging Tests
    def _ensure_paging(self, data, method, criterion=None):
        """
        Given an array of created items we iterate through them making sure
        they match up to things returned by paged results.
        """
        results = None
        item_number = 0

        criterion = criterion or {}

        for current_page in range(0, int(math.ceil(float(len(data)) / 2))):
            LOG.critical('Validating results on page %d', current_page)

            if results is not None:
                results = method(
                    self.admin_context,
                    limit=2,
                    marker=results[-1]['id'],
                    criterion=criterion
                )
            else:
                results = method(self.admin_context, limit=2,
                                 criterion=criterion)

            LOG.critical('Results: %d', len(results))

            for result_number, result in enumerate(results):
                LOG.critical('Validating result %d on page %d', result_number,
                             current_page)
                self.assertEqual(
                    data[item_number]['id'], results[result_number]['id'])

                item_number += 1

    def test_paging_marker_not_found(self):
        with testtools.ExpectedException(exceptions.MarkerNotFound):
            self.storage.find_pool_attributes(
                self.admin_context, marker=generate_uuid(), limit=5)

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

        self.assertEqual(self.admin_context.tenant, result['tenant_id'])
        self.assertEqual(values['resource'], result['resource'])
        self.assertEqual(values['hard_limit'], result['hard_limit'])

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

        self.assertEqual(1, len(results))

        self.assertEqual(quota_one['tenant_id'], results[0]['tenant_id'])
        self.assertEqual(quota_one['resource'], results[0]['resource'])
        self.assertEqual(quota_one['hard_limit'], results[0]['hard_limit'])

        criterion = dict(
            tenant_id=quota_two['tenant_id'],
            resource=quota_two['resource']
        )

        results = self.storage.find_quotas(self.admin_context, criterion)

        self.assertEqual(1, len(results))

        self.assertEqual(quota_two['tenant_id'], results[0]['tenant_id'])
        self.assertEqual(quota_two['resource'], results[0]['resource'])
        self.assertEqual(quota_two['hard_limit'], results[0]['hard_limit'])

    def test_get_quota(self):
        # Create a quota
        expected = self.create_quota()
        actual = self.storage.get_quota(self.admin_context, expected['id'])

        self.assertEqual(expected['tenant_id'], actual['tenant_id'])
        self.assertEqual(expected['resource'], actual['resource'])
        self.assertEqual(expected['hard_limit'], actual['hard_limit'])

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

        self.assertEqual(quota_one['tenant_id'], result['tenant_id'])
        self.assertEqual(quota_one['resource'], result['resource'])
        self.assertEqual(quota_one['hard_limit'], result['hard_limit'])

        criterion = dict(
            tenant_id=quota_two['tenant_id'],
            resource=quota_two['resource']
        )

        result = self.storage.find_quota(self.admin_context, criterion)

        self.assertEqual(quota_two['tenant_id'], result['tenant_id'])
        self.assertEqual(quota_two['resource'], result['resource'])
        self.assertEqual(quota_two['hard_limit'], result['hard_limit'])

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

        self.assertEqual(values['name'], result['name'])
        self.assertEqual(values['algorithm'], result['algorithm'])
        self.assertEqual(values['secret'], result['secret'])
        self.assertEqual(values['scope'], result['scope'])

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

        self.assertEqual(1, len(results))

        self.assertEqual(tsigkey_one['name'], results[0]['name'])

        criterion = dict(
            name=tsigkey_two['name']
        )

        results = self.storage.find_tsigkeys(self.admin_context, criterion)

        self.assertEqual(1, len(results))

        self.assertEqual(tsigkey_two['name'], results[0]['name'])

    def test_get_tsigkey(self):
        # Create a tsigkey
        expected = self.create_tsigkey()

        actual = self.storage.get_tsigkey(self.admin_context, expected['id'])

        self.assertEqual(expected['name'], actual['name'])
        self.assertEqual(expected['algorithm'], actual['algorithm'])
        self.assertEqual(expected['secret'], actual['secret'])
        self.assertEqual(expected['scope'], actual['scope'])

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

        # create 3 zones in 2 tenants
        self.create_zone(fixture=0, context=one_context, tenant_id='One')
        zone = self.create_zone(fixture=1, context=one_context,
                                tenant_id='One')
        self.create_zone(fixture=2, context=two_context, tenant_id='Two')

        # Delete one of the zones.
        self.storage.delete_zone(context, zone['id'])

        # Ensure we get accurate results
        result = self.storage.find_tenants(context)
        result_dict = [dict(t) for t in result]

        expected = [{
            'id': 'One',
            'zone_count': 1,
        }, {
            'id': 'Two',
            'zone_count': 1,
        }]

        self.assertEqual(expected, result_dict)

    def test_get_tenant(self):
        context = self.get_admin_context()
        one_context = context
        one_context.tenant = 1
        context.all_tenants = True

        # create 2 zones in a tenant
        zone_1 = self.create_zone(fixture=0, context=one_context)
        zone_2 = self.create_zone(fixture=1, context=one_context)
        zone_3 = self.create_zone(fixture=2, context=one_context)

        # Delete one of the zones.
        self.storage.delete_zone(context, zone_3['id'])

        result = self.storage.get_tenant(context, 1)

        self.assertEqual(1, result['id'])
        self.assertEqual(2, result['zone_count'])
        self.assertEqual([zone_1['name'], zone_2['name']],
                         sorted(result['zones']))

    def test_count_tenants(self):
        context = self.get_admin_context()
        one_context = context
        one_context.tenant = 1
        two_context = context
        two_context.tenant = 2
        context.all_tenants = True

        # in the beginning, there should be nothing
        tenants = self.storage.count_tenants(context)
        self.assertEqual(0, tenants)

        # create 2 zones with 2 tenants
        self.create_zone(fixture=0, context=one_context, tenant_id=1)
        self.create_zone(fixture=1, context=two_context, tenant_id=2)
        zone = self.create_zone(fixture=2,
                                context=two_context, tenant_id=2)

        # Delete one of the zones.
        self.storage.delete_zone(context, zone['id'])

        tenants = self.storage.count_tenants(context)
        self.assertEqual(2, tenants)

    def test_count_tenants_none_result(self):
        rp = mock.Mock()
        rp.fetchone.return_value = None
        with mock.patch.object(self.storage.session, 'execute',
                               return_value=rp):
            tenants = self.storage.count_tenants(self.admin_context)
            self.assertEqual(0, tenants)

    # Zone Tests
    def test_create_zone(self):
        pool_id = cfg.CONF['service:central'].default_pool_id
        values = {
            'tenant_id': self.admin_context.tenant,
            'name': 'example.net.',
            'email': 'example@example.net',
            'pool_id': pool_id
        }

        result = self.storage.create_zone(
            self.admin_context, zone=objects.Zone.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(self.admin_context.tenant, result['tenant_id'])
        self.assertEqual(values['name'], result['name'])
        self.assertEqual(values['email'], result['email'])
        self.assertEqual(pool_id, result['pool_id'])
        self.assertIn('status', result)

    def test_create_zone_duplicate(self):
        # Create the Initial Zone
        self.create_zone()

        with testtools.ExpectedException(exceptions.DuplicateZone):
            self.create_zone()

    def test_find_zones(self):
        self.config(quota_zones=20)

        actual = self.storage.find_zones(self.admin_context)
        self.assertEqual(0, len(actual))

        # Create a single zone
        zone = self.create_zone()

        actual = self.storage.find_zones(self.admin_context)
        self.assertEqual(1, len(actual))

        self.assertEqual(zone['name'], actual[0]['name'])
        self.assertEqual(zone['email'], actual[0]['email'])

    def test_find_zones_paging(self):
        # Create 10 zones
        created = [self.create_zone(name='example-%d.org.' % i)
                   for i in range(10)]

        # Ensure we can page through the results.
        self._ensure_paging(created, self.storage.find_zones)

    def test_find_zones_criterion(self):
        zone_one = self.create_zone()
        zone_two = self.create_zone(fixture=1)

        criterion = dict(
            name=zone_one['name']
        )

        results = self.storage.find_zones(self.admin_context, criterion)

        self.assertEqual(1, len(results))

        self.assertEqual(zone_one['name'], results[0]['name'])
        self.assertEqual(zone_one['email'], results[0]['email'])
        self.assertIn('status', zone_one)

        criterion = dict(
            name=zone_two['name']
        )

        results = self.storage.find_zones(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(zone_two['name'], results[0]['name'])
        self.assertEqual(zone_two['email'], results[0]['email'])
        self.assertIn('status', zone_two)

    def test_find_zones_all_tenants(self):
        # Create two contexts with different tenant_id's
        one_context = self.get_admin_context()
        one_context.tenant = 1
        two_context = self.get_admin_context()
        two_context.tenant = 2

        # Create normal and all_tenants context objects
        nm_context = self.get_admin_context()
        at_context = self.get_admin_context()
        at_context.all_tenants = True

        # Create two zones in different tenants
        self.create_zone(fixture=0, context=one_context)
        self.create_zone(fixture=1, context=two_context)

        # Ensure the all_tenants context see's two zones
        results = self.storage.find_zones(at_context)
        self.assertEqual(2, len(results))

        # Ensure the normal context see's no zones
        results = self.storage.find_zones(nm_context)
        self.assertEqual(0, len(results))

        # Ensure the tenant 1 context see's 1 zone
        results = self.storage.find_zones(one_context)
        self.assertEqual(1, len(results))

        # Ensure the tenant 2 context see's 1 zone
        results = self.storage.find_zones(two_context)
        self.assertEqual(1, len(results))

    def test_get_zone(self):
        # Create a zone
        expected = self.create_zone()
        actual = self.storage.get_zone(self.admin_context, expected['id'])

        self.assertEqual(expected['name'], actual['name'])
        self.assertEqual(expected['email'], actual['email'])
        self.assertIn('status', actual)

    def test_get_zone_missing(self):
        with testtools.ExpectedException(exceptions.ZoneNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.get_zone(self.admin_context, uuid)

    def test_get_deleted_zone(self):
        context = self.get_admin_context()
        context.show_deleted = True

        zone = self.create_zone(context=context)

        self.storage.delete_zone(context, zone['id'])
        self.storage.get_zone(context, zone['id'])

    def test_find_zone_criterion(self):
        zone_one = self.create_zone()
        zone_two = self.create_zone(fixture=1)

        criterion = dict(
            name=zone_one['name']
        )

        result = self.storage.find_zone(self.admin_context, criterion)

        self.assertEqual(zone_one['name'], result['name'])
        self.assertEqual(zone_one['email'], result['email'])
        self.assertIn('status', zone_one)

        criterion = dict(
            name=zone_two['name']
        )

        result = self.storage.find_zone(self.admin_context, criterion)

        self.assertEqual(zone_two['name'], result['name'])
        self.assertEqual(zone_two['email'], result['email'])
        self.assertIn('status', zone_one)
        self.assertIn('status', zone_two)

    def test_find_zone_criterion_missing(self):
        expected = self.create_zone()

        criterion = dict(
            name=expected['name'] + "NOT FOUND"
        )

        with testtools.ExpectedException(exceptions.ZoneNotFound):
            self.storage.find_zone(self.admin_context, criterion)

    def test_find_zone_criterion_lessthan(self):
        zone = self.create_zone()

        # Test Finding No Results (serial is not < serial)
        criterion = dict(
            name=zone['name'],
            serial='<%s' % zone['serial'],
        )

        with testtools.ExpectedException(exceptions.ZoneNotFound):
            self.storage.find_zone(self.admin_context, criterion)

        # Test Finding 1 Result (serial is < serial + 1)
        criterion = dict(
            name=zone['name'],
            serial='<%s' % (zone['serial'] + 1),
        )

        result = self.storage.find_zone(self.admin_context, criterion)

        self.assertEqual(zone['name'], result['name'])

    def test_find_zone_criterion_greaterthan(self):
        zone = self.create_zone()

        # Test Finding No Results (serial is not > serial)
        criterion = dict(
            name=zone['name'],
            serial='>%s' % zone['serial'],
        )

        with testtools.ExpectedException(exceptions.ZoneNotFound):
            self.storage.find_zone(self.admin_context, criterion)

        # Test Finding 1 Result (serial is > serial - 1)
        criterion = dict(
            name=zone['name'],
            serial='>%s' % (zone['serial'] - 1),
        )

        result = self.storage.find_zone(self.admin_context, criterion)

        self.assertEqual(zone['name'], result['name'])

    def test_update_zone(self):
        # Create a zone
        zone = self.create_zone(name='example.org.')

        # Update the Object
        zone.name = 'example.net.'

        # Perform the update
        zone = self.storage.update_zone(self.admin_context, zone)

        # Ensure the new valie took
        self.assertEqual('example.net.', zone.name)

        # Ensure the version column was incremented
        self.assertEqual(2, zone.version)

    def test_update_zone_duplicate(self):
        # Create two zones
        zone_one = self.create_zone(fixture=0)
        zone_two = self.create_zone(fixture=1)

        # Update the D2 object to be a duplicate of D1
        zone_two.name = zone_one.name

        with testtools.ExpectedException(exceptions.DuplicateZone):
            self.storage.update_zone(self.admin_context, zone_two)

    def test_update_zone_missing(self):
        zone = objects.Zone(id='caf771fc-6b05-4891-bee1-c2a48621f57b')
        with testtools.ExpectedException(exceptions.ZoneNotFound):
            self.storage.update_zone(self.admin_context, zone)

    def test_delete_zone(self):
        zone = self.create_zone()

        self.storage.delete_zone(self.admin_context, zone['id'])

        with testtools.ExpectedException(exceptions.ZoneNotFound):
            self.storage.get_zone(self.admin_context, zone['id'])

    def test_delete_zone_missing(self):
        with testtools.ExpectedException(exceptions.ZoneNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.delete_zone(self.admin_context, uuid)

    def test_count_zones(self):
        # in the beginning, there should be nothing
        zones = self.storage.count_zones(self.admin_context)
        self.assertEqual(0, zones)

        # Create a single zone
        self.create_zone()

        # count 'em up
        zones = self.storage.count_zones(self.admin_context)

        # well, did we get 1?
        self.assertEqual(1, zones)

    def test_count_zones_none_result(self):
        rp = mock.Mock()
        rp.fetchone.return_value = None
        with mock.patch.object(self.storage.session, 'execute',
                               return_value=rp):
            zones = self.storage.count_zones(self.admin_context)
            self.assertEqual(0, zones)

    def test_create_recordset(self):
        zone = self.create_zone()

        values = {
            'name': 'www.%s' % zone['name'],
            'type': 'A'
        }

        result = self.storage.create_recordset(
            self.admin_context,
            zone['id'],
            recordset=objects.RecordSet.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(values['name'], result['name'])
        self.assertEqual(values['type'], result['type'])

    def test_create_recordset_duplicate(self):
        zone = self.create_zone()

        # Create the First RecordSet
        self.create_recordset(zone)

        with testtools.ExpectedException(exceptions.DuplicateRecordSet):
            # Attempt to create the second/duplicate recordset
            self.create_recordset(zone)

    def test_create_recordset_with_records(self):
        zone = self.create_zone()

        recordset = objects.RecordSet(
            name='www.%s' % zone['name'],
            type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.1'),
                objects.Record(data='192.0.2.2'),
            ])
        )

        recordset = self.storage.create_recordset(
            self.admin_context, zone['id'], recordset)

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
        zone = self.create_zone()

        criterion = {'zone_id': zone['id']}

        actual = self.storage.find_recordsets(self.admin_context, criterion)
        self.assertEqual(2, len(actual))

        # Create a single recordset
        recordset_one = self.create_recordset(zone)

        actual = self.storage.find_recordsets(self.admin_context, criterion)
        self.assertEqual(3, len(actual))

        self.assertEqual(recordset_one['name'], actual[2]['name'])
        self.assertEqual(recordset_one['type'], actual[2]['type'])

    def test_find_recordsets_paging(self):
        zone = self.create_zone(name='example.org.')

        # Create 10 RecordSets
        created = [self.create_recordset(zone, name='r-%d.example.org.' % i)
                   for i in range(10)]

        # Add in the SOA and NS recordsets that are automatically created
        soa = self.storage.find_recordset(self.admin_context,
                                          criterion={'zone_id': zone['id'],
                                                     'type': "SOA"})
        ns = self.storage.find_recordset(self.admin_context,
                                         criterion={'zone_id': zone['id'],
                                                    'type': "NS"})
        created.insert(0, ns)
        created.insert(0, soa)

        # Ensure we can page through the results.
        self._ensure_paging(created, self.storage.find_recordsets)

    def test_find_recordsets_criterion(self):
        zone = self.create_zone()

        recordset_one = self.create_recordset(zone, type='A', fixture=0)
        self.create_recordset(zone, fixture=1)

        criterion = dict(
            zone_id=zone['id'],
            name=recordset_one['name'],
        )

        results = self.storage.find_recordsets(self.admin_context,
                                               criterion)

        self.assertEqual(1, len(results))

        criterion = dict(
            zone_id=zone['id'],
            type='A',
        )

        results = self.storage.find_recordsets(self.admin_context,
                                               criterion)

        self.assertEqual(2, len(results))

    def test_find_recordsets_criterion_wildcard(self):
        zone = self.create_zone()

        values = {'name': 'one.%s' % zone['name']}

        self.create_recordset(zone, **values)

        criterion = dict(
            zone_id=zone['id'],
            name="%%%(name)s" % {"name": zone['name']},
        )

        results = self.storage.find_recordsets(self.admin_context, criterion)

        # Should be 3, as SOA and NS recordsets are automiatcally created
        self.assertEqual(3, len(results))

    def test_find_recordsets_with_records(self):
        zone = self.create_zone()

        records = [
            {"data": "10.0.0.1"},
            {"data": "10.0.0.2"},
            {"data": "10.0.0.3"}
        ]

        recordset = self.create_recordset(zone, records=records)

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
        self.assertEqual(3, len(recordset.records))

        records = []
        for record in recordset.records:
            self.assertIsInstance(record, objects.Record)
            self.assertNotIn(record, records)
            records.append(record)

    def test_get_recordset(self):
        zone = self.create_zone()
        expected = self.create_recordset(zone)

        actual = self.storage.get_recordset(self.admin_context, expected['id'])

        self.assertEqual(expected['name'], actual['name'])
        self.assertEqual(expected['type'], actual['type'])

    def test_get_recordset_with_records(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)

        # Create two Records in the RecordSet
        self.create_record(zone, recordset)
        self.create_record(zone, recordset, fixture=1)

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
        zone = self.create_zone()
        expected = self.create_recordset(zone)

        criterion = dict(
            zone_id=zone['id'],
            name=expected['name'],
        )

        actual = self.storage.find_recordset(self.admin_context, criterion)

        self.assertEqual(expected['name'], actual['name'])
        self.assertEqual(expected['type'], actual['type'])

    def test_find_recordset_criterion_missing(self):
        zone = self.create_zone()
        expected = self.create_recordset(zone)

        criterion = dict(
            name=expected['name'] + "NOT FOUND"
        )

        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            self.storage.find_recordset(self.admin_context, criterion)

    def test_find_recordset_criterion_with_records(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)

        # Create two Records in the RecordSet
        self.create_record(zone, recordset)
        self.create_record(zone, recordset, fixture=1)

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
        zone = self.create_zone()

        # Create a recordset
        recordset = self.create_recordset(zone)

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
        zone = self.create_zone()

        # Create two recordsets
        recordset_one = self.create_recordset(zone, type='A')
        recordset_two = self.create_recordset(zone, type='A', fixture=1)

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
        zone = self.create_zone()

        # Create a RecordSet
        recordset = self.create_recordset(zone, 'A')

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
        zone = self.create_zone()

        # Create a RecordSet and two Records
        recordset = self.create_recordset(zone, 'A')
        self.create_record(zone, recordset)
        self.create_record(zone, recordset, fixture=1)

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
        zone = self.create_zone()

        # Create a RecordSet and two Records
        recordset = self.create_recordset(zone, 'A')
        self.create_record(zone, recordset)
        self.create_record(zone, recordset, fixture=1)

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
        zone = self.create_zone()

        # Create a recordset
        recordset = self.create_recordset(zone)

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
        self.assertEqual(0, recordsets)

        # Create a single zone & recordset
        zone = self.create_zone()
        self.create_recordset(zone)

        # we should have 3 recordsets now, including SOA & NS
        recordsets = self.storage.count_recordsets(self.admin_context)
        self.assertEqual(3, recordsets)

        # Delete the zone, we should be back to 0 recordsets
        self.storage.delete_zone(self.admin_context, zone.id)
        recordsets = self.storage.count_recordsets(self.admin_context)
        self.assertEqual(0, recordsets)

    def test_count_recordsets_none_result(self):
        rp = mock.Mock()
        rp.fetchone.return_value = None
        with mock.patch.object(self.storage.session, 'execute',
                               return_value=rp):
            recordsets = self.storage.count_recordsets(self.admin_context)
            self.assertEqual(0, recordsets)

    def test_create_record(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone, type='A')

        values = {
            'data': '192.0.2.1',
        }

        result = self.storage.create_record(
            self.admin_context, zone['id'], recordset['id'],
            objects.Record.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNotNone(result['hash'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(self.admin_context.tenant, result['tenant_id'])
        self.assertEqual(values['data'], result['data'])
        self.assertIn('status', result)

    def test_create_record_duplicate(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)

        # Create the First Record
        self.create_record(zone, recordset)

        with testtools.ExpectedException(exceptions.DuplicateRecord):
            # Attempt to create the second/duplicate record
            self.create_record(zone, recordset)

    def test_find_records(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)

        criterion = {
            'zone_id': zone['id'],
            'recordset_id': recordset['id']
        }

        actual = self.storage.find_records(self.admin_context, criterion)
        self.assertEqual(0, len(actual))

        # Create a single record
        record = self.create_record(zone, recordset)

        actual = self.storage.find_records(self.admin_context, criterion)
        self.assertEqual(1, len(actual))

        self.assertEqual(record['data'], actual[0]['data'])
        self.assertIn('status', record)

    def test_find_records_paging(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone, type='A')

        # Create 10 Records
        created = [self.create_record(zone, recordset, data='192.0.2.%d' % i)
                   for i in range(10)]

        # Add in the SOA and NS records that are automatically created
        soa = self.storage.find_recordset(self.admin_context,
                                          criterion={'zone_id': zone['id'],
                                                     'type': "SOA"})
        ns = self.storage.find_recordset(self.admin_context,
                                         criterion={'zone_id': zone['id'],
                                                    'type': "NS"})
        for r in ns['records']:
            created.insert(0, r)
        created.insert(0, soa['records'][0])

        # Ensure we can page through the results.
        self._ensure_paging(created, self.storage.find_records)

    def test_find_records_criterion(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone, type='A')

        record_one = self.create_record(zone, recordset)
        self.create_record(zone, recordset, fixture=1)

        criterion = dict(
            data=record_one['data'],
            zone_id=zone['id'],
            recordset_id=recordset['id'],
        )

        results = self.storage.find_records(self.admin_context, criterion)
        self.assertEqual(1, len(results))

        criterion = dict(
            zone_id=zone['id'],
            recordset_id=recordset['id'],
        )

        results = self.storage.find_records(self.admin_context, criterion)

        self.assertEqual(2, len(results))

    def test_find_records_criterion_wildcard(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone, type='A')

        values = {'data': '127.0.0.1'}

        self.create_record(zone, recordset, **values)

        criterion = dict(
            zone_id=zone['id'],
            recordset_id=recordset['id'],
            data="%.0.0.1",
        )

        results = self.storage.find_records(self.admin_context, criterion)

        self.assertEqual(1, len(results))

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

        # Create two zones in different tenants, and 1 record in each
        zone_one = self.create_zone(fixture=0, context=one_context)
        recordset_one = self.create_recordset(zone_one, fixture=0,
                                              context=one_context)
        self.create_record(zone_one, recordset_one, context=one_context)

        zone_two = self.create_zone(fixture=1, context=two_context)
        recordset_one = self.create_recordset(zone_two, fixture=1,
                                              context=two_context)

        self.create_record(zone_two, recordset_one, context=two_context)

        # Ensure the all_tenants context see's two records
        # Plus the SOA & NS in each of 2 zones = 6 records total
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
        zone = self.create_zone()
        recordset = self.create_recordset(zone)

        expected = self.create_record(zone, recordset)

        actual = self.storage.get_record(self.admin_context, expected['id'])

        self.assertEqual(expected['data'], actual['data'])
        self.assertIn('status', actual)

    def test_get_record_missing(self):
        with testtools.ExpectedException(exceptions.RecordNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.get_record(self.admin_context, uuid)

    def test_find_record_criterion(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)

        expected = self.create_record(zone, recordset)

        criterion = dict(
            zone_id=zone['id'],
            recordset_id=recordset['id'],
            data=expected['data'],
        )

        actual = self.storage.find_record(self.admin_context, criterion)

        self.assertEqual(expected['data'], actual['data'])
        self.assertIn('status', actual)

    def test_find_record_criterion_missing(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)

        expected = self.create_record(zone, recordset)

        criterion = dict(
            zone_id=zone['id'],
            data=expected['data'] + "NOT FOUND",
        )

        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.storage.find_record(self.admin_context, criterion)

    def test_update_record(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone, type='A')

        # Create a record
        record = self.create_record(zone, recordset)

        # Update the Object
        record.data = '192.0.2.255'

        # Perform the update
        record = self.storage.update_record(self.admin_context, record)

        # Ensure the new value took
        self.assertEqual('192.0.2.255', record.data)

        # Ensure the version column was incremented
        self.assertEqual(2, record.version)

    def test_update_record_duplicate(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)

        # Create two records
        record_one = self.create_record(zone, recordset)
        record_two = self.create_record(zone, recordset, fixture=1)

        # Update the R2 object to be a duplicate of R1
        record_two.data = record_one.data

        with testtools.ExpectedException(exceptions.DuplicateRecord):
            self.storage.update_record(self.admin_context, record_two)

    def test_update_record_missing(self):
        record = objects.Record(id='caf771fc-6b05-4891-bee1-c2a48621f57b')

        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.storage.update_record(self.admin_context, record)

    def test_delete_record(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)

        # Create a record
        record = self.create_record(zone, recordset)

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
        self.assertEqual(0, records)

        # Create a single zone & record
        zone = self.create_zone()
        recordset = self.create_recordset(zone)
        self.create_record(zone, recordset)

        # we should have 3 records now, including NS and SOA
        records = self.storage.count_records(self.admin_context)
        self.assertEqual(3, records)

        # Delete the zone, we should be back to 0 records
        self.storage.delete_zone(self.admin_context, zone.id)
        records = self.storage.count_records(self.admin_context)
        self.assertEqual(0, records)

    def test_count_records_none_result(self):
        rp = mock.Mock()
        rp.fetchone.return_value = None
        with mock.patch.object(self.storage.session, 'execute',
                               return_value=rp):
            records = self.storage.count_records(self.admin_context)
            self.assertEqual(0, records)

    def test_ping(self):
        pong = self.storage.ping(self.admin_context)

        self.assertTrue(pong['status'])
        self.assertIsNotNone(pong['rtt'])

    def test_ping_fail(self):
        with mock.patch.object(self.storage.engine, "execute",
                               side_effect=Exception):
            result = self.storage.ping(self.admin_context)
            self.assertFalse(result['status'])
            self.assertIsNotNone(result['rtt'])

    # TLD Tests
    def test_create_tld(self):
        values = {
            'name': 'com',
            'description': u'This is a comment.'
        }

        result = self.storage.create_tld(
            self.admin_context, objects.Tld.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])
        self.assertIsNotNone(result['version'])
        self.assertEqual(values['name'], result['name'])
        self.assertEqual(values['description'], result['description'])

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
        self.assertEqual(1, len(results))

        self.assertEqual(tld_one['name'], results[0]['name'])

        criterion_two = dict(name=tld_two['name'])

        results = self.storage.find_tlds(self.admin_context,
                                         criterion_two)
        self.assertEqual(len(results), 1)

        self.assertEqual(tld_two['name'], results[0]['name'])

    def test_get_tld(self):
        # Create a tld
        expected = self.create_tld()
        actual = self.storage.get_tld(self.admin_context, expected['id'])

        self.assertEqual(expected['name'], actual['name'])

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
        self.assertEqual(tld_one['name'], result['name'])

        # Repeat with tld_two
        criterion = dict(name=tld_two['name'])

        result = self.storage.find_tld(self.admin_context, criterion)

        self.assertEqual(tld_two['name'], result['name'])

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
            'description': u"This is a comment."
        }

        result = self.storage.create_blacklist(
            self.admin_context, objects.Blacklist.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNotNone(result['version'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(values['pattern'], result['pattern'])
        self.assertEqual(values['description'], result['description'])

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
        self.assertEqual(1, len(results))
        self.assertEqual(blacklist_one['pattern'], results[0]['pattern'])

        # Verify blacklist_two
        criterion = dict(pattern=blacklist_two['pattern'])

        results = self.storage.find_blacklists(self.admin_context,
                                               criterion)
        self.assertEqual(1, len(results))
        self.assertEqual(blacklist_two['pattern'], results[0]['pattern'])

    def test_get_blacklist(self):
        expected = self.create_blacklist(fixture=0)
        actual = self.storage.get_blacklist(self.admin_context, expected['id'])

        self.assertEqual(expected['pattern'], actual['pattern'])

    def test_get_blacklist_missing(self):
        with testtools.ExpectedException(exceptions.BlacklistNotFound):
            uuid = '2c102ffd-7146-4b4e-ad62-b530ee0873fb'
            self.storage.get_blacklist(self.admin_context, uuid)

    def test_find_blacklist_criterion(self):
        blacklist_one = self.create_blacklist(fixture=0)
        blacklist_two = self.create_blacklist(fixture=1)

        criterion = dict(pattern=blacklist_one['pattern'])

        result = self.storage.find_blacklist(self.admin_context, criterion)

        self.assertEqual(blacklist_one['pattern'], result['pattern'])

        criterion = dict(pattern=blacklist_two['pattern'])

        result = self.storage.find_blacklist(self.admin_context, criterion)

        self.assertEqual(blacklist_two['pattern'], result['pattern'])

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

        self.assertEqual(values['name'], result['name'])
        self.assertEqual(values['tenant_id'], result['tenant_id'])
        self.assertEqual(values['provisioner'], result['provisioner'])

    def test_create_pool_with_all_relations(self):
        values = {
            'name': u'Pool',
            'description': u'Pool description',
            'attributes': [{'key': 'scope', 'value': 'public'}],
            'ns_records': [{'priority': 1, 'hostname': 'ns1.example.org.'}],
            'nameservers': [{'host': "192.0.2.1", 'port': 53}],
            'targets': [{
                'type': "fake",
                'description': u"FooBar",
                'masters': [{'host': "192.0.2.2",
                             'port': DEFAULT_MDNS_PORT}],
                'options': [{'key': 'fake_option', 'value': 'fake_value'}],
            }],
            'also_notifies': [{'host': "192.0.2.3", 'port': 53}]
        }

        # Create the Pool, and check all values are OK
        result = self.storage.create_pool(
            self.admin_context, objects.Pool.from_dict(values))
        self.assertNestedDictContainsSubset(values, result.to_dict())

        # Re-Fetch the pool, and check everything is still OK
        result = self.storage.get_pool(self.admin_context, result.id)
        self.assertNestedDictContainsSubset(values, result.to_dict())

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

        self.assertEqual(1, len(results))

        self.assertEqual(pool_one['name'], results[0]['name'])
        self.assertEqual(pool_one['provisioner'], results[0]['provisioner'])

        criterion = dict(name=pool_two['name'])

        results = self.storage.find_pools(self.admin_context, criterion)

        self.assertEqual(1, len(results))

        self.assertEqual(pool_two['name'], results[0]['name'])
        self.assertEqual(pool_two['provisioner'], results[0]['provisioner'])

    def test_get_pool(self):
        # Create a pool
        expected = self.create_pool()
        actual = self.storage.get_pool(self.admin_context, expected['id'])

        self.assertEqual(expected['name'], actual['name'])
        self.assertEqual(expected['provisioner'], actual['provisioner'])

    def test_get_pool_missing(self):
        with testtools.ExpectedException(exceptions.PoolNotFound):
            uuid = 'c28893e3-eb87-4562-aa29-1f0e835d749b'
            self.storage.get_pool(self.admin_context, uuid)

    def test_find_pool_criterion(self):
        pool_one = self.create_pool(fixture=0)
        pool_two = self.create_pool(fixture=1)

        criterion = dict(name=pool_one['name'])

        result = self.storage.find_pool(self.admin_context, criterion)

        self.assertEqual(pool_one['name'], result['name'])
        self.assertEqual(pool_one['provisioner'], result['provisioner'])

        criterion = dict(name=pool_two['name'])

        result = self.storage.find_pool(self.admin_context, criterion)

        self.assertEqual(pool_two['name'], result['name'])
        self.assertEqual(pool_two['provisioner'], result['provisioner'])

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

    def test_update_pool_with_all_relations(self):
        values = {
            'name': u'Pool-A',
            'description': u'Pool-A description',
            'attributes': [{'key': 'scope', 'value': 'public'}],
            'ns_records': [{'priority': 1, 'hostname': 'ns1.example.org.'}],
            'nameservers': [{'host': "192.0.2.1", 'port': 53}],
            'targets': [{
                'type': "fake",
                'description': u"FooBar",
                'masters': [{'host': "192.0.2.2",
                             'port': DEFAULT_MDNS_PORT}],
                'options': [{'key': 'fake_option', 'value': 'fake_value'}],
            }],
            'also_notifies': [{'host': "192.0.2.3", 'port': 53}]
        }

        # Create the Pool
        result = self.storage.create_pool(
            self.admin_context, objects.Pool.from_dict(values))

        created_pool_id = result.id

        # Prepare a new set of data for the Pool, copying over the ID so
        # we trigger an update rather than a create.
        values = {
            'id': created_pool_id,
            'name': u'Pool-B',
            'description': u'Pool-B description',
            'attributes': [{'key': 'scope', 'value': 'private'}],
            'ns_records': [{'priority': 1, 'hostname': 'ns2.example.org.'}],
            'nameservers': [{'host': "192.0.2.5", 'port': 53}],
            'targets': [{
                'type': "fake",
                'description': u"NewFooBar",
                'masters': [{'host': "192.0.2.2",
                             'port': DEFAULT_MDNS_PORT}],
                'options': [{'key': 'fake_option', 'value': 'fake_value'}],
            }, {
                'type': "fake",
                'description': u"FooBar2",
                'masters': [{'host': "192.0.2.7", 'port': 5355}],
                'options': [{'key': 'fake_option', 'value': 'new_fake_value'}],
            }],
            'also_notifies': []
        }

        # Update the pool, and check everything is OK
        result = self.storage.update_pool(
            self.admin_context, objects.Pool.from_dict(values))
        self.assertNestedDictContainsSubset(values, result.to_dict())

        # Re-Fetch the pool, and check everything is still OK
        result = self.storage.get_pool(self.admin_context, created_pool_id)
        self.assertNestedDictContainsSubset(values, result.to_dict())

    def test_delete_pool(self):
        pool = self.create_pool()

        self.storage.delete_pool(self.admin_context, pool['id'])

        with testtools.ExpectedException(exceptions.PoolNotFound):
            self.storage.get_pool(self.admin_context, pool['id'])

    def test_delete_pool_missing(self):
        with testtools.ExpectedException(exceptions.PoolNotFound):
            uuid = '203ca44f-c7e7-4337-9a02-0d735833e6aa'
            self.storage.delete_pool(self.admin_context, uuid)

    def test_create_pool_ns_record_duplicate(self):
        # Create a pool
        pool = self.create_pool(name='test1')

        ns = objects.PoolNsRecord(priority=1, hostname="ns.example.io.")
        self.storage.create_pool_ns_record(
            self.admin_context, pool.id, ns)

        ns2 = objects.PoolNsRecord(priority=2, hostname="ns.example.io.")
        with testtools.ExpectedException(exceptions.DuplicatePoolNsRecord):
            self.storage.create_pool_ns_record(
                self.admin_context, pool.id, ns2)

    def test_update_pool_ns_record_duplicate(self):
        # Create a pool
        pool = self.create_pool(name='test1')

        ns1 = objects.PoolNsRecord(priority=1, hostname="ns1.example.io.")
        self.storage.create_pool_ns_record(
            self.admin_context, pool.id, ns1)

        ns2 = objects.PoolNsRecord(priority=2, hostname="ns2.example.io.")
        self.storage.create_pool_ns_record(
            self.admin_context, pool.id, ns2)

        with testtools.ExpectedException(exceptions.DuplicatePoolNsRecord):
            ns2.hostname = ns1.hostname
            self.storage.update_pool_ns_record(
                self.admin_context, ns2)

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

        self.assertEqual(values['pool_id'], result['pool_id'])
        self.assertEqual(values['key'], result['key'])
        self.assertEqual(values['value'], result['value'])

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
        self.assertEqual(1, len(results))
        self.assertEqual(pool_attribute_one['pool_id'], results[0]['pool_id'])
        self.assertEqual(pool_attribute_one['key'], results[0]['key'])
        self.assertEqual(pool_attribute_one['value'], results[0]['value'])

        # Verify pool_attribute_two
        criterion = dict(key=pool_attribute_two['key'])
        LOG.debug("Criterion is %r " % criterion)

        results = self.storage.find_pool_attributes(self.admin_context,
                                                    criterion)
        self.assertEqual(1, len(results))
        self.assertEqual(pool_attribute_two['pool_id'], results[0]['pool_id'])
        self.assertEqual(pool_attribute_two['key'], results[0]['key'])
        self.assertEqual(pool_attribute_two['value'], results[0]['value'])

    def test_get_pool_attribute(self):
        expected = self.create_pool_attribute(fixture=0)
        actual = self.storage.get_pool_attribute(self.admin_context,
                                                 expected['id'])

        self.assertEqual(expected['pool_id'], actual['pool_id'])
        self.assertEqual(expected['key'], actual['key'])
        self.assertEqual(expected['value'], actual['value'])

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

        self.assertEqual(pool_attribute_one['pool_id'], result['pool_id'])
        self.assertEqual(pool_attribute_one['key'], result['key'])
        self.assertEqual(pool_attribute_one['value'], result['value'])

        criterion = dict(key=pool_attribute_two['key'])

        result = self.storage.find_pool_attribute(self.admin_context,
                                                  criterion)

        self.assertEqual(pool_attribute_two['pool_id'], result['pool_id'])
        self.assertEqual(pool_attribute_two['key'], result['key'])
        self.assertEqual(pool_attribute_two['value'], result['value'])

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

    # PoolNameserver tests
    def test_create_pool_nameserver(self):
        pool = self.create_pool(fixture=0)

        values = {
            'pool_id': pool.id,
            'host': "192.0.2.1",
            'port': 53
        }

        result = self.storage.create_pool_nameserver(
            self.admin_context,
            pool.id,
            objects.PoolNameserver.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNotNone(result['version'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(values['pool_id'], result['pool_id'])
        self.assertEqual(values['host'], result['host'])
        self.assertEqual(values['port'], result['port'])

    def test_create_pool_nameserver_duplicate(self):
        pool = self.create_pool(fixture=0)

        # Create the initial PoolNameserver
        self.create_pool_nameserver(pool, fixture=0)

        with testtools.ExpectedException(exceptions.DuplicatePoolNameserver):
            self.create_pool_nameserver(pool, fixture=0)

    def test_find_pool_nameservers(self):
        pool = self.create_pool(fixture=0)

        # Verify that there are no pool_nameservers created
        actual = self.storage.find_pool_nameservers(self.admin_context)
        self.assertEqual(0, len(actual))

        # Create a PoolNameserver
        pool_nameserver = self.create_pool_nameserver(pool, fixture=0)

        # Fetch the PoolNameservers and ensure only 1 exists
        actual = self.storage.find_pool_nameservers(self.admin_context)
        self.assertEqual(1, len(actual))

        self.assertEqual(pool_nameserver['pool_id'], actual[0]['pool_id'])
        self.assertEqual(pool_nameserver['host'], actual[0]['host'])
        self.assertEqual(pool_nameserver['port'], actual[0]['port'])

    def test_find_pool_nameservers_paging(self):
        pool = self.create_pool(fixture=0)

        # Create 10 PoolNameservers
        created = [self.create_pool_nameserver(pool, host='192.0.2.%d' % i)
                   for i in range(10)]

        # Ensure we can page through the results.
        self._ensure_paging(created, self.storage.find_pool_nameservers)

    def test_find_pool_nameservers_with_criterion(self):
        pool = self.create_pool(fixture=0)

        # Create two pool_nameservers
        pool_nameserver_one = self.create_pool_nameserver(pool, fixture=0)
        pool_nameserver_two = self.create_pool_nameserver(pool, fixture=1)

        # Verify pool_nameserver_one
        criterion = dict(host=pool_nameserver_one['host'])

        results = self.storage.find_pool_nameservers(
            self.admin_context, criterion)

        self.assertEqual(1, len(results))
        self.assertEqual(pool_nameserver_one['host'], results[0]['host'])

        # Verify pool_nameserver_two
        criterion = dict(host=pool_nameserver_two['host'])

        results = self.storage.find_pool_nameservers(self.admin_context,
                                                     criterion)
        self.assertEqual(1, len(results))
        self.assertEqual(pool_nameserver_two['host'], results[0]['host'])

    def test_get_pool_nameserver(self):
        pool = self.create_pool(fixture=0)

        expected = self.create_pool_nameserver(pool, fixture=0)
        actual = self.storage.get_pool_nameserver(
            self.admin_context, expected['id'])

        self.assertEqual(expected['host'], actual['host'])

    def test_get_pool_nameserver_missing(self):
        with testtools.ExpectedException(exceptions.PoolNameserverNotFound):
            uuid = '2c102ffd-7146-4b4e-ad62-b530ee0873fb'
            self.storage.get_pool_nameserver(self.admin_context, uuid)

    def test_find_pool_nameserver_criterion(self):
        pool = self.create_pool(fixture=0)

        # Create two pool_nameservers
        pool_nameserver_one = self.create_pool_nameserver(pool, fixture=0)
        pool_nameserver_two = self.create_pool_nameserver(pool, fixture=1)

        # Verify pool_nameserver_one
        criterion = dict(host=pool_nameserver_one['host'])

        result = self.storage.find_pool_nameserver(
            self.admin_context, criterion)

        self.assertEqual(pool_nameserver_one['host'], result['host'])

        # Verify pool_nameserver_two
        criterion = dict(host=pool_nameserver_two['host'])

        result = self.storage.find_pool_nameserver(
            self.admin_context, criterion)

        self.assertEqual(pool_nameserver_two['host'], result['host'])

    def test_find_pool_nameserver_criterion_missing(self):
        pool = self.create_pool(fixture=0)

        expected = self.create_pool_nameserver(pool, fixture=0)

        criterion = dict(host=expected['host'] + "NOT FOUND")

        with testtools.ExpectedException(exceptions.PoolNameserverNotFound):
            self.storage.find_pool_nameserver(self.admin_context, criterion)

    def test_update_pool_nameserver(self):
        pool = self.create_pool(fixture=0)

        pool_nameserver = self.create_pool_nameserver(pool, host='192.0.2.1')

        # Update the pool_nameserver
        pool_nameserver.host = '192.0.2.2'

        pool_nameserver = self.storage.update_pool_nameserver(
            self.admin_context, pool_nameserver)

        # Verify the new values
        self.assertEqual('192.0.2.2', pool_nameserver.host)

        # Ensure the version column was incremented
        self.assertEqual(2, pool_nameserver.version)

    def test_update_pool_nameserver_duplicate(self):
        pool = self.create_pool(fixture=0)

        # Create two pool_nameservers
        pool_nameserver_one = self.create_pool_nameserver(
            pool, fixture=0, host='192.0.2.1')
        pool_nameserver_two = self.create_pool_nameserver(
            pool, fixture=0, host='192.0.2.2')

        # Update the second one to be a duplicate of the first
        pool_nameserver_two.host = pool_nameserver_one.host

        with testtools.ExpectedException(exceptions.DuplicatePoolNameserver):
            self.storage.update_pool_nameserver(
                self.admin_context, pool_nameserver_two)

    def test_update_pool_nameserver_missing(self):
        pool_nameserver = objects.PoolNameserver(
            id='e8cee063-3a26-42d6-b181-bdbdc2c99d08')

        with testtools.ExpectedException(exceptions.PoolNameserverNotFound):
            self.storage.update_pool_nameserver(
                self.admin_context, pool_nameserver)

    def test_delete_pool_nameserver(self):
        pool = self.create_pool(fixture=0)
        pool_nameserver = self.create_pool_nameserver(pool, fixture=0)

        self.storage.delete_pool_nameserver(
            self.admin_context, pool_nameserver['id'])

        with testtools.ExpectedException(exceptions.PoolNameserverNotFound):
            self.storage.get_pool_nameserver(
                self.admin_context, pool_nameserver['id'])

    def test_delete_pool_nameserver_missing(self):
        with testtools.ExpectedException(exceptions.PoolNameserverNotFound):
            uuid = '97f57960-f41b-4e93-8e22-8fd6c7e2c183'
            self.storage.delete_pool_nameserver(self.admin_context, uuid)

    # PoolTarget tests
    def test_create_pool_target(self):
        pool = self.create_pool(fixture=0)

        values = {
            'pool_id': pool.id,
            'type': "fake"
        }

        result = self.storage.create_pool_target(
            self.admin_context,
            pool.id,
            objects.PoolTarget.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNotNone(result['version'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(values['pool_id'], result['pool_id'])
        self.assertEqual(values['type'], result['type'])

    def test_find_pool_targets(self):
        pool = self.create_pool(fixture=0)

        # Verify that there are no new pool_targets created
        actual = self.storage.find_pool_targets(
            self.admin_context,
            criterion={'pool_id': pool.id})
        self.assertEqual(0, len(actual))

        # Create a PoolTarget
        pool_target = self.create_pool_target(pool, fixture=0)

        # Fetch the PoolTargets and ensure only 2 exist
        actual = self.storage.find_pool_targets(
            self.admin_context,
            criterion={'pool_id': pool.id})
        self.assertEqual(1, len(actual))

        self.assertEqual(pool_target['pool_id'], actual[0]['pool_id'])
        self.assertEqual(pool_target['type'], actual[0]['type'])

    def test_find_pool_targets_paging(self):
        pool = self.create_pool(fixture=0)

        # Create 10 PoolTargets
        created = [self.create_pool_target(pool, description=u'Target %d' % i)
                   for i in range(10)]

        # Ensure we can page through the results.
        self._ensure_paging(created, self.storage.find_pool_targets,
                            criterion={'pool_id': pool.id})

    def test_find_pool_targets_with_criterion(self):
        pool = self.create_pool(fixture=0)

        # Create two pool_targets
        pool_target_one = self.create_pool_target(
            pool, fixture=0, description=u'One')
        pool_target_two = self.create_pool_target(
            pool, fixture=1, description=u'Two')

        # Verify pool_target_one
        criterion = dict(description=pool_target_one['description'])

        results = self.storage.find_pool_targets(
            self.admin_context, criterion)

        self.assertEqual(1, len(results))
        self.assertEqual(
            pool_target_one['description'], results[0]['description'])

        # Verify pool_target_two
        criterion = dict(description=pool_target_two['description'])

        results = self.storage.find_pool_targets(self.admin_context,
                                                 criterion)
        self.assertEqual(1, len(results))
        self.assertEqual(
            pool_target_two['description'], results[0]['description'])

    def test_get_pool_target(self):
        pool = self.create_pool(fixture=0)

        expected = self.create_pool_target(pool, fixture=0)
        actual = self.storage.get_pool_target(
            self.admin_context, expected['id'])

        self.assertEqual(expected['type'], actual['type'])

    def test_get_pool_target_missing(self):
        with testtools.ExpectedException(exceptions.PoolTargetNotFound):
            uuid = '2c102ffd-7146-4b4e-ad62-b530ee0873fb'
            self.storage.get_pool_target(self.admin_context, uuid)

    def test_find_pool_target_criterion(self):
        pool = self.create_pool(fixture=0)

        # Create two pool_targets
        pool_target_one = self.create_pool_target(
            pool, fixture=0, description=u'One')
        pool_target_two = self.create_pool_target(
            pool, fixture=1, description=u'Two')

        # Verify pool_target_one
        criterion = dict(description=pool_target_one['description'])

        result = self.storage.find_pool_target(
            self.admin_context, criterion)

        self.assertEqual(pool_target_one['description'], result['description'])

        # Verify pool_target_two
        criterion = dict(description=pool_target_two['description'])

        result = self.storage.find_pool_target(
            self.admin_context, criterion)

        self.assertEqual(pool_target_two['description'], result['description'])

    def test_find_pool_target_criterion_missing(self):
        pool = self.create_pool(fixture=0)

        expected = self.create_pool_target(pool, fixture=0)

        criterion = dict(description=expected['description'] + u"NOT FOUND")

        with testtools.ExpectedException(exceptions.PoolTargetNotFound):
            self.storage.find_pool_target(self.admin_context, criterion)

    def test_update_pool_target(self):
        pool = self.create_pool(fixture=0)

        pool_target = self.create_pool_target(pool, description=u'One')

        # Update the pool_target
        pool_target.description = u'Two'

        pool_target = self.storage.update_pool_target(
            self.admin_context, pool_target)

        # Verify the new values
        self.assertEqual(u'Two', pool_target.description)

        # Ensure the version column was incremented
        self.assertEqual(2, pool_target.version)

    def test_update_pool_target_missing(self):
        pool_target = objects.PoolTarget(
            id='e8cee063-3a26-42d6-b181-bdbdc2c99d08')

        with testtools.ExpectedException(exceptions.PoolTargetNotFound):
            self.storage.update_pool_target(
                self.admin_context, pool_target)

    def test_delete_pool_target(self):
        pool = self.create_pool(fixture=0)
        pool_target = self.create_pool_target(pool, fixture=0)

        self.storage.delete_pool_target(
            self.admin_context, pool_target['id'])

        with testtools.ExpectedException(exceptions.PoolTargetNotFound):
            self.storage.get_pool_target(
                self.admin_context, pool_target['id'])

    def test_delete_pool_target_missing(self):
        with testtools.ExpectedException(exceptions.PoolTargetNotFound):
            uuid = '97f57960-f41b-4e93-8e22-8fd6c7e2c183'
            self.storage.delete_pool_target(self.admin_context, uuid)

    # PoolAlsoNotify tests
    def test_create_pool_also_notify(self):
        pool = self.create_pool(fixture=0)

        values = {
            'pool_id': pool.id,
            'host': "192.0.2.1",
            'port': 53
        }

        result = self.storage.create_pool_also_notify(
            self.admin_context,
            pool.id,
            objects.PoolAlsoNotify.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNotNone(result['version'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(values['pool_id'], result['pool_id'])
        self.assertEqual(values['host'], result['host'])
        self.assertEqual(values['port'], result['port'])

    def test_create_pool_also_notify_duplicate(self):
        pool = self.create_pool(fixture=0)

        # Create the initial PoolAlsoNotify
        self.create_pool_also_notify(pool, fixture=0)

        with testtools.ExpectedException(exceptions.DuplicatePoolAlsoNotify):
            self.create_pool_also_notify(pool, fixture=0)

    def test_find_pool_also_notifies(self):
        pool = self.create_pool(fixture=0)

        # Verify that there are no pool_also_notifies created
        actual = self.storage.find_pool_also_notifies(self.admin_context)
        self.assertEqual(0, len(actual))

        # Create a PoolAlsoNotify
        pool_also_notify = self.create_pool_also_notify(pool, fixture=0)

        # Fetch the PoolAlsoNotifies and ensure only 1 exists
        actual = self.storage.find_pool_also_notifies(self.admin_context)
        self.assertEqual(1, len(actual))

        self.assertEqual(pool_also_notify['pool_id'], actual[0]['pool_id'])
        self.assertEqual(pool_also_notify['host'], actual[0]['host'])
        self.assertEqual(pool_also_notify['port'], actual[0]['port'])

    def test_find_pool_also_notifies_paging(self):
        pool = self.create_pool(fixture=0)

        # Create 10 PoolAlsoNotifies
        created = [self.create_pool_also_notify(pool, host='192.0.2.%d' % i)
                   for i in range(10)]

        # Ensure we can page through the results.
        self._ensure_paging(created, self.storage.find_pool_also_notifies)

    def test_find_pool_also_notifies_with_criterion(self):
        pool = self.create_pool(fixture=0)

        # Create two pool_also_notifies
        pool_also_notify_one = self.create_pool_also_notify(pool, fixture=0)
        pool_also_notify_two = self.create_pool_also_notify(pool, fixture=1)

        # Verify pool_also_notify_one
        criterion = dict(host=pool_also_notify_one['host'])

        results = self.storage.find_pool_also_notifies(
            self.admin_context, criterion)

        self.assertEqual(1, len(results))
        self.assertEqual(pool_also_notify_one['host'], results[0]['host'])

        # Verify pool_also_notify_two
        criterion = dict(host=pool_also_notify_two['host'])

        results = self.storage.find_pool_also_notifies(self.admin_context,
                                               criterion)
        self.assertEqual(1, len(results))
        self.assertEqual(pool_also_notify_two['host'], results[0]['host'])

    def test_get_pool_also_notify(self):
        pool = self.create_pool(fixture=0)

        expected = self.create_pool_also_notify(pool, fixture=0)
        actual = self.storage.get_pool_also_notify(
            self.admin_context, expected['id'])

        self.assertEqual(expected['host'], actual['host'])

    def test_get_pool_also_notify_missing(self):
        with testtools.ExpectedException(exceptions.PoolAlsoNotifyNotFound):
            uuid = '2c102ffd-7146-4b4e-ad62-b530ee0873fb'
            self.storage.get_pool_also_notify(self.admin_context, uuid)

    def test_find_pool_also_notify_criterion(self):
        pool = self.create_pool(fixture=0)

        # Create two pool_also_notifies
        pool_also_notify_one = self.create_pool_also_notify(pool, fixture=0)
        pool_also_notify_two = self.create_pool_also_notify(pool, fixture=1)

        # Verify pool_also_notify_one
        criterion = dict(host=pool_also_notify_one['host'])

        result = self.storage.find_pool_also_notify(
            self.admin_context, criterion)

        self.assertEqual(pool_also_notify_one['host'], result['host'])

        # Verify pool_also_notify_two
        criterion = dict(host=pool_also_notify_two['host'])

        result = self.storage.find_pool_also_notify(
            self.admin_context, criterion)

        self.assertEqual(pool_also_notify_two['host'], result['host'])

    def test_find_pool_also_notify_criterion_missing(self):
        pool = self.create_pool(fixture=0)

        expected = self.create_pool_also_notify(pool, fixture=0)

        criterion = dict(host=expected['host'] + "NOT FOUND")

        with testtools.ExpectedException(exceptions.PoolAlsoNotifyNotFound):
            self.storage.find_pool_also_notify(self.admin_context, criterion)

    def test_update_pool_also_notify(self):
        pool = self.create_pool(fixture=0)

        pool_also_notify = self.create_pool_also_notify(pool, host='192.0.2.1')

        # Update the pool_also_notify
        pool_also_notify.host = '192.0.2.2'

        pool_also_notify = self.storage.update_pool_also_notify(
            self.admin_context, pool_also_notify)

        # Verify the new values
        self.assertEqual('192.0.2.2', pool_also_notify.host)

        # Ensure the version column was incremented
        self.assertEqual(2, pool_also_notify.version)

    def test_update_pool_also_notify_duplicate(self):
        pool = self.create_pool(fixture=0)

        # Create two pool_also_notifies
        pool_also_notify_one = self.create_pool_also_notify(
            pool, fixture=0, host='192.0.2.1')
        pool_also_notify_two = self.create_pool_also_notify(
            pool, fixture=0, host='192.0.2.2')

        # Update the second one to be a duplicate of the first
        pool_also_notify_two.host = pool_also_notify_one.host

        with testtools.ExpectedException(exceptions.DuplicatePoolAlsoNotify):
            self.storage.update_pool_also_notify(
                self.admin_context, pool_also_notify_two)

    def test_update_pool_also_notify_missing(self):
        pool_also_notify = objects.PoolAlsoNotify(
            id='e8cee063-3a26-42d6-b181-bdbdc2c99d08')

        with testtools.ExpectedException(exceptions.PoolAlsoNotifyNotFound):
            self.storage.update_pool_also_notify(
                self.admin_context, pool_also_notify)

    def test_delete_pool_also_notify(self):
        pool = self.create_pool(fixture=0)
        pool_also_notify = self.create_pool_also_notify(pool, fixture=0)

        self.storage.delete_pool_also_notify(
            self.admin_context, pool_also_notify['id'])

        with testtools.ExpectedException(exceptions.PoolAlsoNotifyNotFound):
            self.storage.get_pool_also_notify(
                self.admin_context, pool_also_notify['id'])

    def test_delete_pool_also_notify_missing(self):
        with testtools.ExpectedException(exceptions.PoolAlsoNotifyNotFound):
            uuid = '97f57960-f41b-4e93-8e22-8fd6c7e2c183'
            self.storage.delete_pool_also_notify(self.admin_context, uuid)

    # Zone Transfer Accept tests
    def test_create_zone_transfer_request(self):
        zone = self.create_zone()

        values = {
            'tenant_id': self.admin_context.tenant,
            'zone_id': zone.id,
            'key': 'qwertyuiop'
        }

        result = self.storage.create_zone_transfer_request(
            self.admin_context, objects.ZoneTransferRequest.from_dict(values))

        self.assertEqual(self.admin_context.tenant, result['tenant_id'])
        self.assertIn('status', result)

    def test_create_zone_transfer_request_scoped(self):
        zone = self.create_zone()
        tenant_2_context = self.get_context(tenant='2')
        tenant_3_context = self.get_context(tenant='3')

        values = {
            'tenant_id': self.admin_context.tenant,
            'zone_id': zone.id,
            'key': 'qwertyuiop',
            'target_tenant_id': tenant_2_context.tenant,
        }

        result = self.storage.create_zone_transfer_request(
            self.admin_context, objects.ZoneTransferRequest.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(self.admin_context.tenant, result['tenant_id'])
        self.assertEqual(tenant_2_context.tenant, result['target_tenant_id'])
        self.assertIn('status', result)

        stored_ztr = self.storage.get_zone_transfer_request(
            tenant_2_context, result.id)

        self.assertEqual(self.admin_context.tenant, stored_ztr['tenant_id'])
        self.assertEqual(stored_ztr['id'], result['id'])

        with testtools.ExpectedException(
                exceptions.ZoneTransferRequestNotFound):
            self.storage.get_zone_transfer_request(
                tenant_3_context, result.id)

    def test_find_zone_transfer_requests(self):
        zone = self.create_zone()

        values = {
            'tenant_id': self.admin_context.tenant,
            'zone_id': zone.id,
            'key': 'qwertyuiop'
        }

        self.storage.create_zone_transfer_request(
            self.admin_context, objects.ZoneTransferRequest.from_dict(values))

        requests = self.storage.find_zone_transfer_requests(
            self.admin_context, {"tenant_id": self.admin_context.tenant})
        self.assertEqual(1, len(requests))

    def test_delete_zone_transfer_request(self):
        zone = self.create_zone()
        zt_request = self.create_zone_transfer_request(zone)

        self.storage.delete_zone_transfer_request(
            self.admin_context, zt_request.id)

        with testtools.ExpectedException(
                exceptions.ZoneTransferRequestNotFound):
            self.storage.get_zone_transfer_request(
                self.admin_context, zt_request.id)

    def test_update_zone_transfer_request(self):
        zone = self.create_zone()
        zt_request = self.create_zone_transfer_request(zone)

        zt_request.description = 'New description'
        result = self.storage.update_zone_transfer_request(
            self.admin_context, zt_request)
        self.assertEqual('New description', result.description)

    def test_get_zone_transfer_request(self):
        zone = self.create_zone()
        zt_request = self.create_zone_transfer_request(zone)

        result = self.storage.get_zone_transfer_request(
            self.admin_context, zt_request.id)
        self.assertEqual(zt_request.id, result.id)
        self.assertEqual(zt_request.zone_id, result.zone_id)

    # Zone Transfer Accept tests
    def test_create_zone_transfer_accept(self):
        zone = self.create_zone()
        zt_request = self.create_zone_transfer_request(zone)
        values = {
            'tenant_id': self.admin_context.tenant,
            'zone_transfer_request_id': zt_request.id,
            'zone_id': zone.id,
            'key': zt_request.key
        }

        result = self.storage.create_zone_transfer_accept(
            self.admin_context, objects.ZoneTransferAccept.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(self.admin_context.tenant, result['tenant_id'])
        self.assertIn('status', result)

    def test_find_zone_transfer_accepts(self):
        zone = self.create_zone()
        zt_request = self.create_zone_transfer_request(zone)
        values = {
            'tenant_id': self.admin_context.tenant,
            'zone_transfer_request_id': zt_request.id,
            'zone_id': zone.id,
            'key': zt_request.key
        }

        self.storage.create_zone_transfer_accept(
            self.admin_context, objects.ZoneTransferAccept.from_dict(values))

        accepts = self.storage.find_zone_transfer_accepts(
            self.admin_context, {"tenant_id": self.admin_context.tenant})
        self.assertEqual(1, len(accepts))

    def test_find_zone_transfer_accept(self):
        zone = self.create_zone()
        zt_request = self.create_zone_transfer_request(zone)
        values = {
            'tenant_id': self.admin_context.tenant,
            'zone_transfer_request_id': zt_request.id,
            'zone_id': zone.id,
            'key': zt_request.key
        }

        result = self.storage.create_zone_transfer_accept(
            self.admin_context, objects.ZoneTransferAccept.from_dict(values))

        accept = self.storage.find_zone_transfer_accept(
            self.admin_context, {"id": result.id})
        self.assertEqual(result.id, accept.id)

    def test_transfer_zone_ownership(self):
        tenant_1_context = self.get_context(tenant='1')
        tenant_2_context = self.get_context(tenant='2')
        admin_context = self.get_admin_context()
        admin_context.all_tenants = True

        zone = self.create_zone(context=tenant_1_context)
        recordset = self.create_recordset(zone, context=tenant_1_context)
        record = self.create_record(
            zone, recordset, context=tenant_1_context)

        updated_zone = zone

        updated_zone.tenant_id = tenant_2_context.tenant

        self.storage.update_zone(
            admin_context, updated_zone)

        saved_zone = self.storage.get_zone(
            admin_context, zone.id)
        saved_recordset = self.storage.get_recordset(
            admin_context, recordset.id)
        saved_record = self.storage.get_record(
            admin_context, record.id)

        self.assertEqual(tenant_2_context.tenant, saved_zone.tenant_id)
        self.assertEqual(tenant_2_context.tenant, saved_recordset.tenant_id)
        self.assertEqual(tenant_2_context.tenant, saved_record.tenant_id)

    def test_delete_zone_transfer_accept(self):
        zone = self.create_zone()
        zt_request = self.create_zone_transfer_request(zone)
        zt_accept = self.create_zone_transfer_accept(zt_request)

        self.storage.delete_zone_transfer_accept(
            self.admin_context, zt_accept.id)

        with testtools.ExpectedException(
                exceptions.ZoneTransferAcceptNotFound):
            self.storage.get_zone_transfer_accept(
                self.admin_context, zt_accept.id)

    def test_update_zone_transfer_accept(self):
        zone = self.create_zone()
        zt_request = self.create_zone_transfer_request(zone)
        zt_accept = self.create_zone_transfer_accept(zt_request)

        zt_accept.status = 'COMPLETE'
        result = self.storage.update_zone_transfer_accept(
            self.admin_context, zt_accept)
        self.assertEqual('COMPLETE', result.status)

    def test_get_zone_transfer_accept(self):
        zone = self.create_zone()
        zt_request = self.create_zone_transfer_request(zone)
        zt_accept = self.create_zone_transfer_accept(zt_request)

        result = self.storage.get_zone_transfer_accept(
            self.admin_context, zt_accept.id)
        self.assertEqual(zt_accept.id, result.id)
        self.assertEqual(zt_accept.zone_id, result.zone_id)

    def test_count_zone_tasks(self):
        # in the beginning, there should be nothing
        zones = self.storage.count_zone_tasks(self.admin_context)
        self.assertEqual(0, zones)

        values = {
            'status': 'PENDING',
            'task_type': 'IMPORT'
        }

        self.storage.create_zone_import(
            self.admin_context, objects.ZoneImport.from_dict(values))

        # count imported zones
        zones = self.storage.count_zone_tasks(self.admin_context)

        # well, did we get 1?
        self.assertEqual(1, zones)

    def test_count_zone_tasks_none_result(self):
        rp = mock.Mock()
        rp.fetchone.return_value = None
        with mock.patch.object(self.storage.session, 'execute',
                               return_value=rp):
            zones = self.storage.count_zone_tasks(self.admin_context)
            self.assertEqual(0, zones)

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
        self.assertEqual(values['status'], result['status'])
        self.assertIsNone(result['zone_id'])
        self.assertIsNone(result['message'])

    def test_find_zone_imports(self):

        actual = self.storage.find_zone_imports(self.admin_context)
        self.assertEqual(0, len(actual))

        # Create a single ZoneImport
        zone_import = self.create_zone_import(fixture=0)

        actual = self.storage.find_zone_imports(self.admin_context)
        self.assertEqual(1, len(actual))

        self.assertEqual(zone_import['status'], actual[0]['status'])
        self.assertEqual(zone_import['message'], actual[0]['message'])
        self.assertEqual(zone_import['zone_id'], actual[0]['zone_id'])

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
        self.assertEqual(1, len(results))

        self.assertEqual(zone_import_one['status'], results[0]['status'])

        criterion_two = dict(status=zone_import_two['status'])

        results = self.storage.find_zone_imports(self.admin_context,
                                         criterion_two)
        self.assertEqual(1, len(results))

        self.assertEqual(zone_import_two['status'], results[0]['status'])

    def test_get_zone_import(self):
        # Create a zone_import
        expected = self.create_zone_import()
        actual = self.storage.get_zone_import(self.admin_context,
                                 expected['id'])

        self.assertEqual(expected['status'], actual['status'])

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
