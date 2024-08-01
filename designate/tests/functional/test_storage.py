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
from sqlalchemy import text
from unittest import mock

from oslo_log import log as logging
from oslo_messaging.rpc import dispatcher as rpc_dispatcher
from oslo_utils import uuidutils

import designate.conf
from designate.conf.mdns import DEFAULT_MDNS_PORT
from designate import exceptions
from designate import objects
from designate import storage
from designate.storage import sql
import designate.tests.functional


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class SqlalchemyStorageTest(designate.tests.functional.TestCase):
    def setUp(self):
        super().setUp()
        self.storage = storage.get_storage()

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
            values['tenant_id'] = context.project_id

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
        self.assertRaisesRegex(
            exceptions.MarkerNotFound,
            'Marker None could not be found',
            self.storage.find_pool_attributes, self.admin_context,
            marker=uuidutils.generate_uuid(), limit=5
        )

    def test_paging_marker_invalid(self):
        self.assertRaises(
            exceptions.InvalidMarker,
            self.storage.find_pool_attributes, self.admin_context,
            marker='4'
        )

    def test_paging_limit_invalid(self):
        self.assertRaisesRegex(
            exceptions.ValueError,
            r'invalid literal for int\(\) with base 10: \'z\'',
            self.storage.find_pool_attributes, self.admin_context,
            limit='z'
        )

    def test_paging_sort_dir_invalid(self):
        self.assertRaisesRegex(
            exceptions.ValueError,
            r'Unknown sort direction, must be \'desc\' or \'asc\'',
            self.storage.find_pool_attributes, self.admin_context,
            sort_dir='invalid_sort_dir'
        )

    def test_paging_sort_key_invalid(self):
        self.assertRaisesRegex(
            exceptions.InvalidSortKey,
            'Sort key supplied is invalid: None',
            self.storage.find_pool_attributes, self.admin_context,
            sort_key='invalid_sort_key'
        )

    # Quota Tests
    def test_create_quota(self):
        values = self.get_quota_fixture()
        values['tenant_id'] = self.admin_context.project_id

        result = self.storage.create_quota(self.admin_context, values)

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(self.admin_context.project_id, result['tenant_id'])
        self.assertEqual(values['resource'], result['resource'])
        self.assertEqual(values['hard_limit'], result['hard_limit'])

    def test_create_quota_duplicate(self):
        # Create the initial quota
        self.create_quota()

        self.assertRaisesRegex(
            exceptions.DuplicateQuota, 'Duplicate Quota',
            self.create_quota
        )

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
        uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'

        self.assertRaisesRegex(
            exceptions.QuotaNotFound, 'Could not find Quota',
            self.storage.get_quota, self.admin_context, uuid
        )

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
            tenant_id=expected['tenant_id'] + 'NOT FOUND'
        )

        self.assertRaisesRegex(
            exceptions.QuotaNotFound, 'Could not find Quota',
            self.storage.find_quota, self.admin_context, criterion
        )

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

        self.assertRaisesRegex(
            exceptions.DuplicateQuota, 'Duplicate Quota',
            self.storage.update_quota, self.admin_context, quota_two
        )

    def test_update_quota_missing(self):
        quota = objects.Quota(
            id='caf771fc-6b05-4891-bee1-c2a48621f57b'
        )

        self.assertRaisesRegex(
            exceptions.QuotaNotFound, 'Could not find Quota',
            self.storage.update_quota, self.admin_context, quota
        )

    def test_delete_quota(self):
        quota = self.create_quota()

        self.storage.delete_quota(self.admin_context, quota['id'])

        self.assertRaisesRegex(
            exceptions.QuotaNotFound, 'Could not find Quota',
            self.storage.get_quota, self.admin_context, quota['id']
        )

    def test_delete_quota_missing(self):
        uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'

        self.assertRaisesRegex(
            exceptions.QuotaNotFound, 'Could not find Quota',
            self.storage.delete_quota, self.admin_context, uuid
        )

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

        exc = self.assertRaises(rpc_dispatcher.ExpectedException,
                                self.create_tsigkey,
                                **values)

        self.assertEqual(exceptions.DuplicateTsigKey, exc.exc_info[0])

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

    def test_find_tsigkey(self):
        # Create a single tsigkey
        tsig = self.create_tsigkey()

        actual = self.storage.find_tsigkeys(self.admin_context)
        self.assertEqual(1, len(actual))
        name = actual[0].name

        actual = self.storage.find_tsigkey(self.admin_context,
                                           {'name': name})
        self.assertEqual(tsig['name'], actual['name'])
        self.assertEqual(tsig['algorithm'], actual['algorithm'])
        self.assertEqual(tsig['secret'], actual['secret'])
        self.assertEqual(tsig['scope'], actual['scope'])

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
        uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'

        self.assertRaisesRegex(
            exceptions.TsigKeyNotFound, 'Could not find TsigKey',
            self.storage.get_tsigkey, self.admin_context, uuid
        )

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

        self.assertRaisesRegex(
            exceptions.DuplicateTsigKey, 'Duplicate TsigKey',
            self.storage.update_tsigkey, self.admin_context, tsigkey_two
        )

    def test_update_tsigkey_missing(self):
        tsigkey = objects.TsigKey(
            id='caf771fc-6b05-4891-bee1-c2a48621f57b'
        )

        self.assertRaisesRegex(
            exceptions.TsigKeyNotFound, 'Could not find TsigKey',
            self.storage.update_tsigkey, self.admin_context, tsigkey
        )

    def test_delete_tsigkey(self):
        tsigkey = self.create_tsigkey()

        self.storage.delete_tsigkey(self.admin_context, tsigkey['id'])

        self.assertRaisesRegex(
            exceptions.TsigKeyNotFound, 'Could not find TsigKey',
            self.storage.get_tsigkey, self.admin_context, tsigkey['id']
        )

    def test_delete_tsigkey_missing(self):
        uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'

        self.assertRaisesRegex(
            exceptions.TsigKeyNotFound, 'Could not find TsigKey',
            self.storage.delete_tsigkey, self.admin_context, uuid
        )

    # Tenant Tests
    def test_find_tenants(self):
        context = self.get_admin_context()
        one_context = context
        one_context.project_id = 'One'
        two_context = context
        two_context.project_id = 'Two'
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
        one_context.project_id = 1
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
        one_context.project_id = 1
        two_context = context
        two_context.project_id = 2
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

    def test_count_tenants_no_results(self):
        tenants = self.storage.count_tenants(self.admin_context)
        self.assertEqual(0, tenants)

    @mock.patch('designate.storage.sql.get_read_session')
    def test_count_tenants_none_result(self, mock_read_session):
        mock_sql_execute = mock.Mock()
        mock_sql_fetchone = mock.Mock()

        mock_read_session().__enter__.return_value = mock_sql_execute
        mock_sql_execute.execute.return_value = mock_sql_fetchone
        mock_sql_fetchone.fetchone.return_value = None

        tenants = self.storage.count_tenants(self.admin_context)

        mock_read_session.assert_called()

        self.assertEqual(0, tenants)

    # Zone Tests
    def test_create_zone(self):
        pool_id = CONF['service:central'].default_pool_id
        values = {
            'tenant_id': self.admin_context.project_id,
            'name': 'example.net.',
            'email': 'example@example.net',
            'pool_id': pool_id
        }

        result = self.storage.create_zone(
            self.admin_context, zone=objects.Zone.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(self.admin_context.project_id, result['tenant_id'])
        self.assertEqual(values['name'], result['name'])
        self.assertEqual(values['email'], result['email'])
        self.assertEqual(pool_id, result['pool_id'])
        self.assertIn('status', result)

    def test_create_zone_duplicate(self):
        # Create the Initial Zone
        self.create_zone()

        exc = self.assertRaises(rpc_dispatcher.ExpectedException,
                                self.create_zone)

        self.assertEqual(exceptions.DuplicateZone, exc.exc_info[0])

    def test_create_zone_standard_ttl(self):
        values = self.get_zone_fixture()
        new_zone = self.storage.create_zone(
            self.admin_context, zone=objects.Zone.from_dict(values)
        )

        # default fallback ttl is 3600 when no ttl value is provided.
        self.assertEqual(3600, new_zone.ttl)

    def test_create_zone_custom_ttl(self):
        self.config(default_ttl=60)

        values = self.get_zone_fixture()
        values['ttl'] = 30
        new_zone = self.storage.create_zone(
            self.admin_context, zone=objects.Zone.from_dict(values)
        )

        self.assertEqual(30, new_zone.ttl)

    def test_create_zone_override_default_ttl(self):
        self.config(default_ttl=60)

        values = self.get_zone_fixture()
        new_zone = self.storage.create_zone(
            self.admin_context, zone=objects.Zone.from_dict(values)
        )

        self.assertEqual(60, new_zone.ttl)

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
        one_context.project_id = 1
        two_context = self.get_admin_context()
        two_context.project_id = 2

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

    def test_find_zones_shared(self):
        # Create an admin context
        admin_context = self.get_admin_context()

        # Create a zone in the admin context
        zone = self.create_zone(context=admin_context)

        # Share the zone with two other projects
        self.share_zone(
            zone_id=zone['id'], target_project_id=1, context=admin_context)
        self.share_zone(
            zone_id=zone['id'], target_project_id=2, context=admin_context)

        # Ensure that one zone record is returned from find_zones (LP 2025295)
        results = self.storage.find_zones(admin_context)
        self.assertEqual(1, len(results))

    def test_get_zone(self):
        # Create a zone
        expected = self.create_zone()
        actual = self.storage.get_zone(self.admin_context, expected['id'])

        self.assertEqual(expected['name'], actual['name'])
        self.assertEqual(expected['email'], actual['email'])
        self.assertIn('status', actual)

    def test_get_zone_missing(self):
        uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'

        self.assertRaisesRegex(
            exceptions.ZoneNotFound, 'Could not find Zone',
            self.storage.get_zone, self.admin_context, uuid
        )

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
            name=expected['name'] + 'NOT FOUND'
        )

        self.assertRaisesRegex(
            exceptions.ZoneNotFound, 'Could not find Zone',
            self.storage.find_zone, self.admin_context, criterion
        )

    def test_find_zone_criterion_lessthan(self):
        zone = self.create_zone()

        # Test Finding No Results (serial is not < serial)
        criterion = dict(
            name=zone['name'],
            serial='<%s' % zone['serial'],
        )

        self.assertRaisesRegex(
            exceptions.ZoneNotFound, 'Could not find Zone',
            self.storage.find_zone, self.admin_context, criterion
        )

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

        self.assertRaisesRegex(
            exceptions.ZoneNotFound, 'Could not find Zone',
            self.storage.find_zone, self.admin_context, criterion
        )

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
        zone.recordsets = objects.RecordSetList(objects=[])
        zone.attributes = objects.ZoneAttributeList(
            objects=[objects.ZoneAttribute(key='foo', value='bar')]
        )
        zone.masters = objects.ZoneMasterList(
            objects=[objects.ZoneMaster(host='192.0.2.1', port=80)]
        )

        # Perform the update
        zone = self.storage.update_zone(self.admin_context, zone)

        # Ensure the new valie took
        self.assertEqual('example.net.', zone.name)

        # Ensure the version column was incremented
        self.assertEqual(2, zone.version)

    def test_update_zone_secondary(self):
        # Create a zone
        fixture = self.get_zone_fixture('SECONDARY', 1)
        fixture['email'] = 'root@example.com'
        zone = self.create_zone(**fixture)

        # Update the Object
        zone.name = 'example.net.'
        zone.recordsets = objects.RecordSetList()

        # Perform the update
        zone = self.storage.update_zone(self.admin_context, zone)

        # Ensure the new valie took
        self.assertEqual('example.net.', zone.name)

        # Ensure the version column was incremented
        self.assertEqual(2, zone.version)

    def test_update_zone_new_recordset_with_existing(self):
        zone = self.create_zone(name='example.org.')
        recordset1 = self.create_recordset(zone)
        recordset2 = objects.RecordSet(
            name='www.example.org.', type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.1'),
            ])
        )

        zone.name = 'example.net.'
        zone.recordsets = objects.RecordSetList(
            objects=[recordset1, recordset2]
        )

        # Perform the update
        self.storage.update_zone(self.admin_context, zone)

        recordsets = self.storage.find_recordsets(
            self.admin_context, {'zone_id': zone['id']}
        )
        self.assertEqual(4, len(recordsets))

    def test_update_zone_new_recordset(self):
        zone = self.create_zone(name='example.org.')

        recordset = objects.RecordSet(
            name='www.example.org.', type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.1'),
            ])
        )

        zone.name = 'example.net.'
        zone.recordsets = objects.RecordSetList(objects=[recordset])

        # Perform the update
        self.storage.update_zone(self.admin_context, zone)

        recordsets = self.storage.find_recordsets(
            self.admin_context, {'zone_id': zone['id']}
        )
        self.assertEqual(3, len(recordsets))

    def test_update_zone_duplicate(self):
        # Create two zones
        zone_one = self.create_zone(fixture=0)
        zone_two = self.create_zone(fixture=1)

        # Update the D2 object to be a duplicate of D1
        zone_two.name = zone_one.name

        self.assertRaisesRegex(
            exceptions.DuplicateZone, 'Duplicate Zone',
            self.storage.update_zone, self.admin_context, zone_two
        )

    def test_update_zone_missing(self):
        zone = objects.Zone(
            id='caf771fc-6b05-4891-bee1-c2a48621f57b'
        )

        self.assertRaisesRegex(
            exceptions.ZoneNotFound, 'Could not find Zone',
            self.storage.update_zone, self.admin_context, zone
        )

    def test_delete_zone(self):
        zone = self.create_zone()

        self.storage.delete_zone(self.admin_context, zone['id'])

        self.assertRaisesRegex(
            exceptions.ZoneNotFound, 'Could not find Zone',
            self.storage.get_zone, self.admin_context, zone['id']
        )

    def test_delete_zone_missing(self):
        uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'

        self.assertRaisesRegex(
            exceptions.ZoneNotFound, 'Could not find Zone',
            self.storage.delete_zone, self.admin_context, uuid
        )

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

    @mock.patch('designate.storage.sql.get_read_session')
    def test_count_zones_none_result(self, mock_read_session):
        mock_sql_execute = mock.Mock()
        mock_sql_fetchone = mock.Mock()

        mock_read_session().__enter__.return_value = mock_sql_execute
        mock_sql_execute.execute.return_value = mock_sql_fetchone
        mock_sql_fetchone.fetchone.return_value = None

        zones = self.storage.count_zones(self.admin_context)

        mock_read_session.assert_called()

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

        exc = self.assertRaises(rpc_dispatcher.ExpectedException,
                                self.create_recordset,
                                zone)

        self.assertEqual(exceptions.DuplicateRecordSet, exc.exc_info[0])

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

    def test_find_recordsets_axfr(self):
        zone = self.create_zone()
        self.create_recordset(zone)

        result = self.storage.find_recordsets_axfr(
            self.admin_context, {'zone_id': zone['id']}
        )
        self.assertEqual(3, len(result))

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
                                                     'type': 'SOA'})
        ns = self.storage.find_recordset(self.admin_context,
                                         criterion={'zone_id': zone['id'],
                                                    'type': 'NS'})
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
            name='%%%(name)s' % {'name': zone['name']},
        )

        results = self.storage.find_recordsets(self.admin_context, criterion)

        # Should be 3, as SOA and NS recordsets are automiatcally created
        self.assertEqual(3, len(results))

    def test_find_recordsets_with_records(self):
        zone = self.create_zone()

        records = [
            objects.Record.from_dict({'data': '192.0.2.1'}),
            objects.Record.from_dict({'data': '192.0.2.2'}),
            objects.Record.from_dict({'data': '192.0.2.3'})
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
            name=expected['name'] + 'NOT FOUND'
        )

        self.assertRaisesRegex(
            exceptions.RecordSetNotFound, 'Could not find RecordSet',
            self.storage.find_recordset, self.admin_context, criterion
        )

    def test_find_recordset_criterion_with_records(self):
        zone = self.create_zone()

        records = [
            objects.Record.from_dict(self.get_record_fixture('A', fixture=0)),
            objects.Record.from_dict(self.get_record_fixture('A', fixture=1))
        ]
        recordset = self.create_recordset(zone, records=records)

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
        recordset.records.append(objects.Record(data='192.0.2.2'))

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

        self.assertRaisesRegex(
            exceptions.DuplicateRecordSet, 'Duplicate RecordSet',
            self.storage.update_recordset, self.admin_context, recordset_two
        )

    def test_update_recordset_missing(self):
        recordset = objects.RecordSet(
            id='caf771fc-6b05-4891-bee1-c2a48621f57b'
        )

        self.assertRaisesRegex(
            exceptions.RecordSetNotFound, 'Could not find RecordSet',
            self.storage.update_recordset, self.admin_context, recordset
        )

    def test_update_recordset_with_record_create(self):
        zone = self.create_zone()

        # Create a RecordSet
        recordset = self.create_recordset(zone, 'A', records=[])

        # Append two new Records
        recordset.records.append(objects.Record(data='192.0.2.1'))
        recordset.records.append(objects.Record(data='192.0.2.2'))

        # Perform the update
        self.storage.update_recordset(self.admin_context, recordset)

        # Fetch the RecordSet again
        recordset = self.storage.find_recordset(self.admin_context,
                                                {'id': recordset.id})

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
        records = [
            objects.Record.from_dict(self.get_record_fixture('A', fixture=0)),
            objects.Record.from_dict(self.get_record_fixture('A', fixture=1))
        ]
        recordset = self.create_recordset(zone, records=records)

        # Fetch the RecordSet again
        recordset = self.storage.find_recordset(self.admin_context,
                                                {'id': recordset.id})

        # Remove one of the Records
        recordset.records.pop(0)

        # Ensure only one Record is attached to the RecordSet
        self.assertEqual(1, len(recordset.records))

        # Perform the update
        self.storage.update_recordset(self.admin_context, recordset)

        # Fetch the RecordSet again
        recordset = self.storage.find_recordset(self.admin_context,
                                                {'id': recordset.id})

        # Ensure only one Record is attached to the RecordSet
        self.assertEqual(1, len(recordset.records))
        self.assertIsInstance(recordset.records[0], objects.Record)

    def test_update_recordset_with_record_update(self):
        zone = self.create_zone()

        # Create a RecordSet and two Records
        records = [
            objects.Record.from_dict(self.get_record_fixture('A', fixture=0)),
            objects.Record.from_dict(self.get_record_fixture('A', fixture=1))
        ]
        recordset = self.create_recordset(zone, records=records)

        # Fetch the RecordSet again
        recordset = self.storage.find_recordset(self.admin_context,
                                                {'id': recordset.id})

        # Update one of the Records
        updated_record_id = recordset.records[0].id
        recordset.records[0].data = '192.0.2.255'

        # Perform the update
        self.storage.update_recordset(self.admin_context, recordset)

        # Fetch the RecordSet again
        recordset = self.storage.find_recordset(self.admin_context,
                                                {'id': recordset.id})

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

        self.assertRaisesRegex(
            exceptions.RecordSetNotFound, 'Could not find RecordSet',
            self.storage.find_recordset, self.admin_context,
            criterion={'id': recordset['id']}
        )

    def test_delete_recordset_missing(self):
        uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'

        self.assertRaisesRegex(
            exceptions.RecordSetNotFound, 'Could not find RecordSet',
            self.storage.delete_recordset, self.admin_context, uuid
        )

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

    @mock.patch('designate.storage.sql.get_read_session')
    def test_count_recordsets_none_result(self, mock_read_session):
        mock_sql_execute = mock.Mock()
        mock_sql_fetchone = mock.Mock()

        mock_read_session().__enter__.return_value = mock_sql_execute
        mock_sql_execute.execute.return_value = mock_sql_fetchone
        mock_sql_fetchone.fetchone.return_value = None

        recordsets = self.storage.count_recordsets(self.admin_context)

        mock_read_session.assert_called()

        self.assertEqual(0, recordsets)

    def test_find_records(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone, records=[])

        criterion = {
            'zone_id': zone['id'],
            'recordset_id': recordset['id']
        }

        actual = self.storage.find_records(self.admin_context, criterion)
        self.assertEqual(0, len(actual))

        # Create a single record
        records = [
            objects.Record.from_dict(self.get_record_fixture('A', fixture=0)),
        ]
        recordset.records = records

        self.central_service.update_recordset(self.admin_context, recordset)

        recordset = self.central_service.get_recordset(
            self.admin_context, zone['id'], recordset['id']
        )
        record = recordset.records[0]

        actual = self.storage.find_records(self.admin_context, criterion)
        self.assertEqual(1, len(actual))

        self.assertEqual(record['data'], actual[0]['data'])

    def test_find_records_paging(self):
        zone = self.create_zone()

        records = []
        for i in range(10):
            records.append(
                objects.Record.from_dict({'data': '192.0.2.%d' % i})
            )

        self.create_recordset(zone, type='A', records=records)

        # Add in the SOA and NS records that are automatically created
        soa = self.storage.find_recordset(self.admin_context,
                                          criterion={'zone_id': zone['id'],
                                                     'type': 'SOA'})
        ns = self.storage.find_recordset(self.admin_context,
                                         criterion={'zone_id': zone['id'],
                                                    'type': 'NS'})
        for r in ns['records']:
            records.insert(0, r)
        records.insert(0, soa['records'][0])

        # Ensure we can page through the results.
        self._ensure_paging(records, self.storage.find_records)

    def test_find_records_criterion(self):
        zone = self.create_zone()
        record_one = objects.Record.from_dict(
            self.get_record_fixture('A', fixture=0)
        )
        records = [
            record_one,
            objects.Record.from_dict(self.get_record_fixture('A', fixture=1))
        ]
        recordset = self.create_recordset(zone, records=records)

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

        records = [objects.Record.from_dict({'data': '192.0.2.1'})]
        recordset = self.create_recordset(zone, type='A', records=records)

        criterion = dict(
            zone_id=zone['id'],
            recordset_id=recordset['id'],
            data='%.0.2.1',
        )

        results = self.storage.find_records(self.admin_context, criterion)

        self.assertEqual(1, len(results))

    def test_get_record(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)
        expected = recordset.records[0]

        actual = self.storage.get_record(self.admin_context, expected['id'])

        self.assertEqual(expected['data'], actual['data'])
        self.assertIn('status', actual)

    def test_get_record_missing(self):
        uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'

        self.assertRaisesRegex(
            exceptions.RecordNotFound, 'Could not find Record',
            self.storage.get_record, self.admin_context, uuid
        )

    def test_find_record_criterion(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)
        expected = recordset.records[0]

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
        expected = recordset.records[0]

        criterion = dict(
            zone_id=zone['id'],
            data=expected['data'] + 'NOT FOUND',
        )

        self.assertRaisesRegex(
            exceptions.RecordNotFound, 'Could not find Record',
            self.storage.find_record, self.admin_context, criterion
        )

    def test_update_record(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone, type='A')
        record = recordset.records[0]

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

        record_one = objects.Record.from_dict(
            self.get_record_fixture('A', fixture=0)
        )
        record_two = objects.Record.from_dict(
            self.get_record_fixture('A', fixture=1)
        )

        records = [
            record_one,
            record_two
        ]

        self.create_recordset(zone, records=records)

        # Update the R2 object to be a duplicate of R1
        record_two.data = record_one.data

        self.assertRaisesRegex(
            exceptions.DuplicateRecord, 'Duplicate Record',
            self.storage.update_record, self.admin_context, record_two
        )

    def test_update_record_missing(self):
        record = objects.Record(
            id='caf771fc-6b05-4891-bee1-c2a48621f57b'
        )

        self.assertRaisesRegex(
            exceptions.RecordNotFound, 'Could not find Record',
            self.storage.update_record, self.admin_context, record
        )

    def test_delete_record(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)
        record = recordset.records[0]

        self.storage.delete_record(self.admin_context, record['id'])

        self.assertRaisesRegex(
            exceptions.RecordNotFound, 'Could not find Record',
            self.storage.get_record, self.admin_context, record['id']
        )

    def test_delete_record_missing(self):
        uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'

        self.assertRaisesRegex(
            exceptions.RecordNotFound, 'Could not find Record',
            self.storage.delete_record, self.admin_context, uuid
        )

    def test_count_records(self):
        # in the beginning, there should be nothing
        records = self.storage.count_records(self.admin_context)
        self.assertEqual(0, records)

        # Create a single zone & record
        zone = self.create_zone()
        self.create_recordset(zone)

        # we should have 3 records now, including NS and SOA
        records = self.storage.count_records(self.admin_context)
        self.assertEqual(3, records)

        # Delete the zone, we should be back to 0 records
        self.storage.delete_zone(self.admin_context, zone.id)
        records = self.storage.count_records(self.admin_context)
        self.assertEqual(0, records)

    @mock.patch('designate.storage.sql.get_read_session')
    def test_count_records_none_result(self, mock_read_session):
        mock_sql_execute = mock.Mock()
        mock_sql_fetchone = mock.Mock()

        mock_read_session().__enter__.return_value = mock_sql_execute
        mock_sql_execute.execute.return_value = mock_sql_fetchone
        mock_sql_fetchone.fetchone.return_value = None

        records = self.storage.count_records(self.admin_context)

        mock_read_session.assert_called()

        self.assertEqual(0, records)

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
        self.assertEqual(values['name'], result['name'])
        self.assertEqual(values['description'], result['description'])

    def test_create_tld_with_duplicate(self):
        # Create the First Tld
        self.create_tld(fixture=0)

        exc = self.assertRaises(rpc_dispatcher.ExpectedException,
                                self.create_tld,
                                fixture=0)

        self.assertEqual(exceptions.DuplicateTld, exc.exc_info[0])

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
        uuid = '4c8e7f82-3519-4bf7-8940-a66a4480f223'

        self.assertRaisesRegex(
            exceptions.TldNotFound, 'Could not find Tld',
            self.storage.get_tld, self.admin_context, uuid
        )

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

        criterion = dict(name=expected['name'] + 'NOT FOUND')

        self.assertRaisesRegex(
            exceptions.TldNotFound, 'Could not find Tld',
            self.storage.find_tld, self.admin_context, criterion
        )

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

        self.assertRaisesRegex(
            exceptions.DuplicateTld, 'Duplicate Tld',
            self.storage.update_tld, self.admin_context, tld_two
        )

    def test_update_tld_missing(self):
        tld = objects.Tld(
            id='486f9cbe-b8b6-4d8c-8275-1a6e47b13e00'
        )

        self.assertRaisesRegex(
            exceptions.TldNotFound, 'Could not find Tld',
            self.storage.update_tld, self.admin_context, tld
        )

    def test_delete_tld(self):
        # Create a tld
        tld = self.create_tld()

        # Delete the tld
        self.storage.delete_tld(self.admin_context, tld['id'])

        # Verify that it's deleted
        self.assertRaisesRegex(
            exceptions.TldNotFound, 'Could not find Tld',
            self.storage.get_tld, self.admin_context, tld['id']
        )

    def test_delete_tld_missing(self):
        uuid = 'cac1fc02-79b2-4e62-a1a4-427b6790bbe6'

        self.assertRaisesRegex(
            exceptions.TldNotFound, 'Could not find Tld',
            self.storage.delete_tld, self.admin_context, uuid
        )

    # Blacklist tests
    def test_create_blacklist(self):
        values = {
            'pattern': '^([A-Za-z0-9_\\-]+\\.)*example\\.com\\.$',
            'description': 'This is a comment.'
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

        exc = self.assertRaises(rpc_dispatcher.ExpectedException,
                                self.create_blacklist,
                                fixture=0)

        self.assertEqual(exceptions.DuplicateBlacklist, exc.exc_info[0])

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
        uuid = '2c102ffd-7146-4b4e-ad62-b530ee0873fb'

        self.assertRaisesRegex(
            exceptions.BlacklistNotFound, 'Could not find Blacklist',
            self.storage.get_blacklist, self.admin_context, uuid
        )

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

        criterion = dict(pattern=expected['pattern'] + 'NOT FOUND')

        self.assertRaisesRegex(
            exceptions.BlacklistNotFound, 'Could not find Blacklist',
            self.storage.find_blacklist, self.admin_context, criterion
        )

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

        self.assertRaisesRegex(
            exceptions.DuplicateBlacklist, 'Duplicate Blacklist',
            self.storage.update_blacklist, self.admin_context, blacklist_two
        )

    def test_update_blacklist_missing(self):
        blacklist = objects.Blacklist(
            id='e8cee063-3a26-42d6-b181-bdbdc2c99d08'
        )

        self.assertRaisesRegex(
            exceptions.BlacklistNotFound, 'Could not find Blacklist',
            self.storage.update_blacklist, self.admin_context, blacklist
        )

    def test_delete_blacklist(self):
        blacklist = self.create_blacklist(fixture=0)

        self.storage.delete_blacklist(self.admin_context, blacklist['id'])

        self.assertRaisesRegex(
            exceptions.BlacklistNotFound, 'Could not find Blacklist',
            self.storage.get_blacklist, self.admin_context, blacklist['id']
        )

    def test_delete_blacklist_missing(self):
        uuid = '97f57960-f41b-4e93-8e22-8fd6c7e2c183'

        self.assertRaisesRegex(
            exceptions.BlacklistNotFound, 'Could not find Blacklist',
            self.storage.delete_blacklist, self.admin_context, uuid
        )

    # Pool Tests
    def test_create_pool(self):
        values = {
            'name': 'test1',
            'tenant_id': self.admin_context.project_id,
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
            'name': 'Pool',
            'description': 'Pool description',
            'attributes': [{'key': 'scope', 'value': 'public'}],
            'ns_records': [{'priority': 1, 'hostname': 'ns1.example.org.'}],
            'nameservers': [{'host': '192.0.2.1', 'port': 53}],
            'targets': [{
                'type': 'fake',
                'description': 'FooBar',
                'masters': [{'host': '192.0.2.2',
                             'port': DEFAULT_MDNS_PORT}],
                'options': [{'key': 'fake_option', 'value': 'fake_value'}],
            }],
            'also_notifies': [{'host': '192.0.2.3', 'port': 53}]
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
        exc = self.assertRaises(rpc_dispatcher.ExpectedException,
                                self.create_pool,
                                fixture=0)

        self.assertEqual(exceptions.DuplicatePool, exc.exc_info[0])

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
        uuid = 'c28893e3-eb87-4562-aa29-1f0e835d749b'

        self.assertRaisesRegex(
            exceptions.PoolNotFound, 'Could not find Pool',
            self.storage.get_pool, self.admin_context, uuid
        )

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

        criterion = dict(name=expected['name'] + 'NOT FOUND')

        self.assertRaisesRegex(
            exceptions.PoolNotFound, 'Could not find Pool',
            self.storage.find_pool, self.admin_context, criterion
        )

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

        self.assertRaisesRegex(
            exceptions.DuplicatePool, 'Duplicate Pool',
            self.storage.update_pool, self.admin_context, pool_two
        )

    def test_update_pool_missing(self):
        pool = objects.Pool(
            id='8806f871-5140-43f4-badd-2bbc5715b013'
        )

        self.assertRaisesRegex(
            exceptions.PoolNotFound, 'Could not find Pool',
            self.storage.update_pool, self.admin_context, pool
        )

    def test_update_pool_with_all_relations(self):
        values = {
            'name': 'Pool-A',
            'description': 'Pool-A description',
            'attributes': [{'key': 'scope', 'value': 'public'}],
            'ns_records': [{'priority': 1, 'hostname': 'ns1.example.org.'}],
            'nameservers': [{'host': '192.0.2.1', 'port': 53}],
            'targets': [{
                'type': 'fake',
                'description': 'FooBar',
                'masters': [{'host': '192.0.2.2',
                             'port': DEFAULT_MDNS_PORT}],
                'options': [{'key': 'fake_option', 'value': 'fake_value'}],
            }],
            'also_notifies': [{'host': '192.0.2.3', 'port': 53}]
        }

        # Create the Pool
        result = self.storage.create_pool(
            self.admin_context, objects.Pool.from_dict(values))

        created_pool_id = result.id

        # Prepare a new set of data for the Pool, copying over the ID so
        # we trigger an update rather than a create.
        values = {
            'id': created_pool_id,
            'name': 'Pool-B',
            'description': 'Pool-B description',
            'attributes': [{'key': 'scope', 'value': 'private'}],
            'ns_records': [{'priority': 1, 'hostname': 'ns2.example.org.'}],
            'nameservers': [{'host': '192.0.2.5', 'port': 53}],
            'targets': [{
                'type': 'fake',
                'description': 'NewFooBar',
                'masters': [{'host': '192.0.2.2',
                             'port': DEFAULT_MDNS_PORT}],
                'options': [{'key': 'fake_option', 'value': 'fake_value'}],
            }, {
                'type': 'fake',
                'description': 'FooBar2',
                'masters': [{'host': '192.0.2.7', 'port': 5355}],
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

        self.assertRaisesRegex(
            exceptions.PoolNotFound, 'Could not find Pool',
            self.storage.delete_pool, self.admin_context, pool['id']
        )

    @mock.patch.object(storage.sqlalchemy.SQLAlchemyStorage, 'delete_tsigkey')
    def test_delete_pool_catalog_zone_with_tsig(self, mock_delete_tsig):
        pool = self.create_pool(fixture=3)
        self.storage.delete_pool(self.admin_context, pool.id)

        mock_delete_tsig.assert_called()

        self.assertRaisesRegex(
            exceptions.PoolNotFound, 'Could not find Pool',
            self.storage.delete_pool, self.admin_context, pool.id
        )

    @mock.patch.object(storage.sqlalchemy.SQLAlchemyStorage, 'delete_tsigkey')
    def test_delete_pool_catalog_zone_without_tsig(self, mock_delete_tsig):
        pool = self.create_pool(fixture=2)
        self.storage.delete_pool(self.admin_context, pool.id)

        mock_delete_tsig.assert_not_called()

        self.assertRaisesRegex(
            exceptions.PoolNotFound, 'Could not find Pool',
            self.storage.delete_pool, self.admin_context, pool.id
        )

    def test_delete_pool_missing(self):
        uuid = '203ca44f-c7e7-4337-9a02-0d735833e6aa'

        self.assertRaisesRegex(
            exceptions.PoolNotFound, 'Could not find Pool',
            self.storage.delete_pool, self.admin_context, uuid
        )

    def test_create_pool_ns_record_duplicate(self):
        # Create a pool
        pool = self.create_pool(name='test1')

        ns = objects.PoolNsRecord(priority=1, hostname='ns.example.io.')
        self.storage.create_pool_ns_record(
            self.admin_context, pool.id, ns)

        ns2 = objects.PoolNsRecord(priority=2, hostname='ns.example.io.')

        self.assertRaisesRegex(
            exceptions.DuplicatePoolNsRecord, 'Duplicate PoolNsRecord',
            self.storage.create_pool_ns_record, self.admin_context, pool.id,
            ns2
        )

    def test_update_pool_ns_record_duplicate(self):
        # Create a pool
        pool = self.create_pool(name='test1')

        ns1 = objects.PoolNsRecord(priority=1, hostname='ns1.example.io.')
        self.storage.create_pool_ns_record(
            self.admin_context, pool.id, ns1)

        ns2 = objects.PoolNsRecord(priority=2, hostname='ns2.example.io.')
        self.storage.create_pool_ns_record(
            self.admin_context, pool.id, ns2)

        ns2.hostname = ns1.hostname
        self.assertRaisesRegex(
            exceptions.DuplicatePoolNsRecord, 'Duplicate PoolNsRecord',
            self.storage.update_pool_ns_record, self.admin_context, ns2
        )

    # PoolAttribute tests
    def test_create_pool_attribute(self):
        values = {
            'pool_id': 'd5d10661-0312-4ae1-8664-31188a4310b7',
            'key': 'test-attribute',
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
        LOG.debug('Criterion is %r ' % criterion)

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
        uuid = '2c102ffd-7146-4b4e-ad62-b530ee0873fb'

        self.assertRaisesRegex(
            exceptions.PoolAttributeNotFound, 'Could not find PoolAttribute',
            self.storage.get_pool_attribute, self.admin_context, uuid
        )

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

        criterion = dict(key=expected['key'] + 'NOT FOUND')

        self.assertRaisesRegex(
            exceptions.PoolAttributeNotFound, 'Could not find PoolAttribute',
            self.storage.find_pool_attribute, self.admin_context, criterion
        )

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
            id='728a329a-83b1-4573-82dc-45dceab435d4'
        )

        self.assertRaisesRegex(
            exceptions.PoolAttributeNotFound, 'Could not find PoolAttribute',
            self.storage.update_pool_attribute, self.admin_context,
            pool_attribute
        )

    def test_update_pool_attribute_duplicate(self):
        # Create two PoolAttributes
        pool_attribute_one = self.create_pool_attribute(fixture=0)
        pool_attribute_two = self.create_pool_attribute(fixture=1)

        # Update the second one to be a duplicate of the first
        pool_attribute_two.pool_id = pool_attribute_one.pool_id
        pool_attribute_two.key = pool_attribute_one.key
        pool_attribute_two.value = pool_attribute_one.value

        self.assertRaisesRegex(
            exceptions.DuplicatePoolAttribute, 'Duplicate PoolAttribute',
            self.storage.update_pool_attribute, self.admin_context,
            pool_attribute_two
        )

    def test_delete_pool_attribute(self):
        pool_attribute = self.create_pool_attribute(fixture=0)

        self.storage.delete_pool_attribute(self.admin_context,
                                           pool_attribute['id'])

        self.assertRaisesRegex(
            exceptions.PoolAttributeNotFound, 'Could not find PoolAttribute',
            self.storage.get_pool_attribute, self.admin_context,
            pool_attribute['id']
        )

    def test_delete_oool_attribute_missing(self):
        uuid = '464e9250-4fe0-4267-9993-da639390bb04'

        self.assertRaisesRegex(
            exceptions.PoolAttributeNotFound, 'Could not find PoolAttribute',
            self.storage.delete_pool_attribute, self.admin_context, uuid
        )

    def test_create_pool_attribute_duplicate(self):
        # Create the initial PoolAttribute
        self.create_pool_attribute(fixture=0)

        self.assertRaisesRegex(
            exceptions.DuplicatePoolAttribute, 'Duplicate PoolAttribute',
            self.create_pool_attribute, fixture=0
        )

    # PoolNameserver tests
    def test_create_pool_nameserver(self):
        pool = self.create_pool(fixture=0)

        values = {
            'pool_id': pool.id,
            'host': '192.0.2.1',
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

        self.assertRaisesRegex(
            exceptions.DuplicatePoolNameserver, 'Duplicate PoolNameserver',
            self.create_pool_nameserver, pool, fixture=0
        )

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
        uuid = '2c102ffd-7146-4b4e-ad62-b530ee0873fb'

        self.assertRaisesRegex(
            exceptions.PoolNameserverNotFound, 'Could not find PoolNameserver',
            self.storage.get_pool_nameserver, self.admin_context, uuid
        )

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

        criterion = dict(host=expected['host'] + 'NOT FOUND')

        self.assertRaisesRegex(
            exceptions.PoolNameserverNotFound, 'Could not find PoolNameserver',
            self.storage.find_pool_nameserver, self.admin_context, criterion
        )

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

        self.assertRaisesRegex(
            exceptions.DuplicatePoolNameserver, 'Duplicate PoolNameserver',
            self.storage.update_pool_nameserver, self.admin_context,
            pool_nameserver_two
        )

    def test_update_pool_nameserver_missing(self):
        pool_nameserver = objects.PoolNameserver(
            id='e8cee063-3a26-42d6-b181-bdbdc2c99d08'
        )

        self.assertRaisesRegex(
            exceptions.PoolNameserverNotFound, 'Could not find PoolNameserver',
            self.storage.update_pool_nameserver, self.admin_context,
            pool_nameserver
        )

    def test_delete_pool_nameserver(self):
        pool = self.create_pool(fixture=0)
        pool_nameserver = self.create_pool_nameserver(pool, fixture=0)

        self.storage.delete_pool_nameserver(
            self.admin_context, pool_nameserver['id'])

        self.assertRaisesRegex(
            exceptions.PoolNameserverNotFound, 'Could not find PoolNameserver',
            self.storage.get_pool_nameserver, self.admin_context,
            pool_nameserver['id']
        )

    def test_delete_pool_nameserver_missing(self):
        uuid = '97f57960-f41b-4e93-8e22-8fd6c7e2c183'

        self.assertRaisesRegex(
            exceptions.PoolNameserverNotFound, 'Could not find PoolNameserver',
            self.storage.delete_pool_nameserver, self.admin_context, uuid
        )

    # PoolTarget tests
    def test_create_pool_target(self):
        pool = self.create_pool(fixture=0)

        values = {
            'pool_id': pool.id,
            'type': 'fake'
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
        created = [self.create_pool_target(pool, description='Target %d' % i)
                   for i in range(10)]

        # Ensure we can page through the results.
        self._ensure_paging(created, self.storage.find_pool_targets,
                            criterion={'pool_id': pool.id})

    def test_find_pool_targets_with_criterion(self):
        pool = self.create_pool(fixture=0)

        # Create two pool_targets
        pool_target_one = self.create_pool_target(
            pool, fixture=0, description='One')
        pool_target_two = self.create_pool_target(
            pool, fixture=1, description='Two')

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
        uuid = '2c102ffd-7146-4b4e-ad62-b530ee0873fb'

        self.assertRaisesRegex(
            exceptions.PoolTargetNotFound, 'Could not find PoolTarget',
            self.storage.get_pool_target, self.admin_context, uuid
        )

    def test_find_pool_target_criterion(self):
        pool = self.create_pool(fixture=0)

        # Create two pool_targets
        pool_target_one = self.create_pool_target(
            pool, fixture=0, description='One')
        pool_target_two = self.create_pool_target(
            pool, fixture=1, description='Two')

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

        criterion = dict(description=expected['description'] + 'NOT FOUND')

        self.assertRaisesRegex(
            exceptions.PoolTargetNotFound, 'Could not find PoolTarget',
            self.storage.find_pool_target, self.admin_context, criterion
        )

    def test_update_pool_target(self):
        pool = self.create_pool(fixture=0)

        pool_target = self.create_pool_target(pool, description='One')

        # Update the pool_target
        pool_target.description = 'Two'
        pool_target.masters = objects.PoolTargetMasterList(
            objects=[objects.PoolTargetMaster(host='192.0.2.1', port=80)]
        )
        pool_target.options = objects.PoolTargetOptionList(
            objects=[objects.PoolTargetOption(key='foo', value='bar')]
        )

        pool_target = self.storage.update_pool_target(
            self.admin_context, pool_target)

        # Verify the new values
        self.assertEqual('Two', pool_target.description)

        # Ensure the version column was incremented
        self.assertEqual(2, pool_target.version)

    def test_update_pool_target_missing(self):
        pool_target = objects.PoolTarget(
            id='e8cee063-3a26-42d6-b181-bdbdc2c99d08'
        )

        self.assertRaisesRegex(
            exceptions.PoolTargetNotFound, 'Could not find PoolTarget',
            self.storage.update_pool_target, self.admin_context, pool_target
        )

    def test_delete_pool_target(self):
        pool = self.create_pool(fixture=0)
        pool_target = self.create_pool_target(pool, fixture=0)

        self.storage.delete_pool_target(
            self.admin_context, pool_target['id'])

        self.assertRaisesRegex(
            exceptions.PoolTargetNotFound, 'Could not find PoolTarget',
            self.storage.get_pool_target, self.admin_context, pool_target['id']
        )

    def test_delete_pool_target_missing(self):
        uuid = '97f57960-f41b-4e93-8e22-8fd6c7e2c183'

        self.assertRaisesRegex(
            exceptions.PoolTargetNotFound, 'Could not find PoolTarget',
            self.storage.delete_pool_target, self.admin_context, uuid
        )

    def test_create_pool_target_option(self):
        pool = self.create_pool(fixture=0)
        pool_target = self.create_pool_target(pool, fixture=0)

        target = self.storage.create_pool_target_option(
            self.admin_context, pool_target['id'],
            objects.PoolTargetOption(key='foo', value='bar')
        )

        result = self.storage._find_pool_target_options(
            self.admin_context, {'id': target['id']}
        )
        self.assertEqual(1, len(result))

    def test_update_pool_target_option(self):
        pool = self.create_pool(fixture=0)
        pool_target = self.create_pool_target(pool, fixture=0)

        target = self.storage.create_pool_target_option(
            self.admin_context, pool_target['id'],
            objects.PoolTargetOption(key='foo', value='bar')
        )

        target.value = 'baz'
        self.storage.update_pool_target_option(self.admin_context, target)

        result = self.storage._find_pool_target_options(
            self.admin_context, {'id': target['id']}
        )
        self.assertEqual('baz', result[0].value)

    def test_delete_pool_target_option(self):
        pool = self.create_pool(fixture=0)
        pool_target = self.create_pool_target(pool, fixture=0)

        target = self.storage.create_pool_target_option(
            self.admin_context, pool_target['id'],
            objects.PoolTargetOption(key='foo', value='bar')
        )

        self.storage.delete_pool_target_option(
            self.admin_context, target['id']
        )

        result = self.storage._find_pool_target_options(
            self.admin_context, {'id': target['id']}
        )
        self.assertEqual(0, len(result))

    def test_create_pool_target_master(self):
        pool = self.create_pool(fixture=0)
        pool_target = self.create_pool_target(pool, fixture=0)

        target = self.storage.create_pool_target_master(
            self.admin_context, pool_target['id'],
            objects.PoolTargetMaster(host='192.0.2.1', port=80)
        )

        result = self.storage._find_pool_target_masters(
            self.admin_context, {'id': target['id']}
        )
        self.assertEqual(1, len(result))

    def test_update_pool_target_master(self):
        pool = self.create_pool(fixture=0)
        pool_target = self.create_pool_target(pool, fixture=0)

        target = self.storage.create_pool_target_master(
            self.admin_context, pool_target['id'],
            objects.PoolTargetMaster(host='192.0.2.1', port=80)
        )

        target.port = 443
        self.storage.update_pool_target_master(self.admin_context, target)

        result = self.storage._find_pool_target_masters(
            self.admin_context, {'id': target['id']}
        )
        self.assertEqual(443, result[0].port)

    def test_delete_pool_target_master(self):
        pool = self.create_pool(fixture=0)
        pool_target = self.create_pool_target(pool, fixture=0)

        target = self.storage.create_pool_target_master(
            self.admin_context, pool_target['id'],
            objects.PoolTargetMaster(host='192.0.2.1', port=80)
        )

        self.storage.delete_pool_target_master(
            self.admin_context, target['id']
        )

        result = self.storage._find_pool_target_masters(
            self.admin_context, {'id': target['id']}
        )
        self.assertEqual(0, len(result))

    def test_create_zone_attribute(self):
        zone = self.create_zone()

        zone_attribute = self.storage.create_zone_attribute(
            self.admin_context, zone['id'],
            objects.ZoneAttribute(key='foo', value='bar')
        )

        result = self.storage.find_zone_attributes(
            self.admin_context, {'id': zone_attribute['id']}
        )
        self.assertEqual(1, len(result))

    def test_update_zone_attribute(self):
        zone = self.create_zone()

        zone_attribute = self.storage.create_zone_attribute(
            self.admin_context, zone['id'],
            objects.ZoneAttribute(key='foo', value='bar')
        )

        zone_attribute.value = 'baz'
        self.storage.update_zone_attribute(
            self.admin_context, zone_attribute
        )

        result = self.storage.get_zone_attributes(
            self.admin_context, zone_attribute['id']
        )
        self.assertEqual('baz', result.value)

    def test_delete_zone_attribute(self):
        zone = self.create_zone()

        zone_attribute = self.storage.create_zone_attribute(
            self.admin_context, zone['id'],
            objects.ZoneAttribute(key='foo', value='bar')
        )

        self.storage.delete_zone_attribute(
            self.admin_context, zone_attribute['id']
        )

        result = self.storage.find_zone_attributes(
            self.admin_context, {'id': zone_attribute['id']}
        )
        self.assertEqual(0, len(result))

    def test_create_zone_master(self):
        zone = self.create_zone()

        zone_master = self.storage.create_zone_master(
            self.admin_context, zone['id'],
            objects.ZoneMaster(host='192.0.2.1', port='80')
        )

        result = self.storage._find_zone_masters(
            self.admin_context, {'id': zone_master['id']}
        )
        self.assertEqual(1, len(result))

    def test_update_zone_master(self):
        zone = self.create_zone()

        zone_master = self.storage.create_zone_master(
            self.admin_context, zone['id'],
            objects.ZoneMaster(host='192.0.2.1', port='80')
        )

        zone_master.port = 443
        self.storage.update_zone_master(
            self.admin_context, zone_master
        )

        result = self.storage._find_zone_masters(
            self.admin_context, {'id': zone_master['id']}
        )
        self.assertEqual(443, result[0].port)

    def test_delete_zone_master(self):
        zone = self.create_zone()

        zone_master = self.storage.create_zone_master(
            self.admin_context, zone['id'],
            objects.ZoneMaster(host='192.0.2.1', port='80')
        )

        self.storage.delete_zone_master(
            self.admin_context, zone_master['id']
        )

        result = self.storage._find_zone_masters(
            self.admin_context, {'id': zone_master['id']}
        )
        self.assertEqual(0, len(result))

    def test_create_zone_export(self):
        zone_export = self.storage.create_zone_export(
            self.admin_context,
            objects.ZoneExport(status='ACTIVE', task_type='EXPORT')
        )

        result = self.storage.find_zone_exports(
            self.admin_context, {'id': zone_export['id']}
        )
        self.assertEqual(1, len(result))

    def test_find_zone_exports_with_no_criterion(self):
        self.storage.create_zone_export(
            self.admin_context,
            objects.ZoneExport(status='ACTIVE', task_type='EXPORT')
        )

        result = self.storage._find_zone_exports(
            self.admin_context, None
        )
        self.assertEqual(1, len(result))

    def test_update_zone_export(self):
        zone_export = self.storage.create_zone_export(
            self.admin_context,
            objects.ZoneExport(status='ACTIVE', task_type='EXPORT')
        )

        zone_export.message = 'foo'
        self.storage.update_zone_export(
            self.admin_context, zone_export
        )

        result = self.storage.find_zone_export(
            self.admin_context, {'id': zone_export['id']}
        )
        self.assertEqual('foo', result.message)

    def test_delete_zone_export(self):
        zone_export = self.storage.create_zone_export(
            self.admin_context,
            objects.ZoneExport(status='ACTIVE', task_type='EXPORT')
        )

        self.storage.delete_zone_export(
            self.admin_context, zone_export['id']
        )

        result = self.storage.find_zone_exports(
            self.admin_context, {'id': zone_export['id']}
        )
        self.assertEqual(0, len(result))

    # PoolAlsoNotify tests
    def test_create_pool_also_notify(self):
        pool = self.create_pool(fixture=0)

        values = {
            'pool_id': pool.id,
            'host': '192.0.2.1',
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

        self.assertRaisesRegex(
            exceptions.DuplicatePoolAlsoNotify, 'Duplicate PoolAlsoNotify',
            self.create_pool_also_notify, pool, fixture=0
        )

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
        uuid = '2c102ffd-7146-4b4e-ad62-b530ee0873fb'

        self.assertRaisesRegex(
            exceptions.PoolAlsoNotifyNotFound, 'Could not find PoolAlsoNotify',
            self.storage.get_pool_also_notify, self.admin_context, uuid
        )

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

        criterion = dict(host=expected['host'] + 'NOT FOUND')

        self.assertRaisesRegex(
            exceptions.PoolAlsoNotifyNotFound, 'Could not find PoolAlsoNotify',
            self.storage.find_pool_also_notify, self.admin_context, criterion
        )

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

        self.assertRaisesRegex(
            exceptions.DuplicatePoolAlsoNotify, 'Duplicate PoolAlsoNotify',
            self.storage.update_pool_also_notify, self.admin_context,
            pool_also_notify_two
        )

    def test_update_pool_also_notify_missing(self):
        pool_also_notify = objects.PoolAlsoNotify(
            id='e8cee063-3a26-42d6-b181-bdbdc2c99d08'
        )

        self.assertRaisesRegex(
            exceptions.PoolAlsoNotifyNotFound, 'Could not find PoolAlsoNotify',
            self.storage.update_pool_also_notify, self.admin_context,
            pool_also_notify
        )

    def test_delete_pool_also_notify(self):
        pool = self.create_pool(fixture=0)
        pool_also_notify = self.create_pool_also_notify(pool, fixture=0)

        self.storage.delete_pool_also_notify(
            self.admin_context, pool_also_notify['id'])

        self.assertRaisesRegex(
            exceptions.PoolAlsoNotifyNotFound, 'Could not find PoolAlsoNotify',
            self.storage.get_pool_also_notify, self.admin_context,
            pool_also_notify['id']
        )

    def test_delete_pool_also_notify_missing(self):
        uuid = '97f57960-f41b-4e93-8e22-8fd6c7e2c183'

        self.assertRaisesRegex(
            exceptions.PoolAlsoNotifyNotFound, 'Could not find PoolAlsoNotify',
            self.storage.delete_pool_also_notify, self.admin_context, uuid
        )

    def test_create_service_status_duplicate(self):
        values = self.get_service_status_fixture(fixture=0)

        self.storage.create_service_status(
            self.admin_context, objects.ServiceStatus.from_dict(values))

        self.assertRaisesRegex(
            exceptions.DuplicateServiceStatus, 'Duplicate ServiceStatus',
            self.storage.create_service_status, self.admin_context,
            objects.ServiceStatus.from_dict(values)
        )

    # Zone Transfer Accept tests
    def test_create_zone_transfer_request(self):
        zone = self.create_zone()

        values = {
            'tenant_id': self.admin_context.project_id,
            'zone_id': zone.id,
            'key': 'qwertyuiop'
        }

        result = self.storage.create_zone_transfer_request(
            self.admin_context, objects.ZoneTransferRequest.from_dict(values))

        self.assertEqual(self.admin_context.project_id, result['tenant_id'])
        self.assertIn('status', result)

    def test_create_zone_transfer_request_scoped(self):
        zone = self.create_zone()
        tenant_2_context = self.get_context(project_id='2')
        tenant_3_context = self.get_context(project_id='3')

        values = {
            'tenant_id': self.admin_context.project_id,
            'zone_id': zone.id,
            'key': 'qwertyuiop',
            'target_tenant_id': tenant_2_context.project_id,
        }

        result = self.storage.create_zone_transfer_request(
            self.admin_context, objects.ZoneTransferRequest.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(self.admin_context.project_id, result['tenant_id'])
        self.assertEqual(
            tenant_2_context.project_id, result['target_tenant_id']
        )
        self.assertIn('status', result)

        stored_ztr = self.storage.get_zone_transfer_request(
            tenant_2_context, result.id)

        self.assertEqual(
            self.admin_context.project_id, stored_ztr['tenant_id']
        )
        self.assertEqual(stored_ztr['id'], result['id'])

        self.assertRaisesRegex(
            exceptions.ZoneTransferRequestNotFound,
            'Could not find ZoneTransferRequest',
            self.storage.get_zone_transfer_request, tenant_3_context, result.id
        )

    def test_find_zone_transfer_requests(self):
        zone = self.create_zone()

        values = {
            'tenant_id': self.admin_context.project_id,
            'zone_id': zone.id,
            'key': 'qwertyuiop'
        }

        self.storage.create_zone_transfer_request(
            self.admin_context, objects.ZoneTransferRequest.from_dict(values))

        requests = self.storage.find_zone_transfer_requests(
            self.admin_context, {'tenant_id': self.admin_context.project_id})
        self.assertEqual(1, len(requests))

    def test_delete_zone_transfer_request(self):
        zone = self.create_zone()
        zt_request = self.create_zone_transfer_request(zone)

        self.storage.delete_zone_transfer_request(
            self.admin_context, zt_request.id)

        self.assertRaisesRegex(
            exceptions.ZoneTransferRequestNotFound,
            'Could not find ZoneTransferRequest',
            self.storage.get_zone_transfer_request, self.admin_context,
            zt_request.id
        )

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

    def test_get_zone_transfer_request_no_project_id(self):
        context1 = self.get_context(project_id='1',
                                    roles=['member', 'reader'])
        context2 = self.get_context(roles=['member', 'reader'])

        zone = self.create_zone(context=context1)
        zt_request = self.create_zone_transfer_request(zone, context=context1)

        result = self.storage.get_zone_transfer_request(context2,
                                                        zt_request.id)
        self.assertEqual(objects.ZoneTransferRequest(), result)

    def test_find_zone_transfer_requests_no_project_id(self):
        context1 = self.get_context(project_id='1',
                                    roles=['member', 'reader'])
        context2 = self.get_context(roles=['member', 'reader'])

        zone = self.create_zone(context=context1)
        zt_request = self.create_zone_transfer_request(zone, context=context1)

        result = self.storage.find_zone_transfer_requests(context2,
                                                          zt_request.id)
        self.assertEqual(objects.ZoneTransferRequestList(), result)
        self.assertEqual(0, len(result))

    # Zone Transfer Accept tests
    def test_create_zone_transfer_accept(self):
        zone = self.create_zone()
        zt_request = self.create_zone_transfer_request(zone)
        values = {
            'tenant_id': self.admin_context.project_id,
            'zone_transfer_request_id': zt_request.id,
            'zone_id': zone.id,
            'key': zt_request.key
        }

        result = self.storage.create_zone_transfer_accept(
            self.admin_context, objects.ZoneTransferAccept.from_dict(values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(self.admin_context.project_id, result['tenant_id'])
        self.assertIn('status', result)

    def test_find_zone_transfer_accepts(self):
        zone = self.create_zone()
        zt_request = self.create_zone_transfer_request(zone)
        values = {
            'tenant_id': self.admin_context.project_id,
            'zone_transfer_request_id': zt_request.id,
            'zone_id': zone.id,
            'key': zt_request.key
        }

        self.storage.create_zone_transfer_accept(
            self.admin_context, objects.ZoneTransferAccept.from_dict(values))

        accepts = self.storage.find_zone_transfer_accepts(
            self.admin_context, {'tenant_id': self.admin_context.project_id})
        self.assertEqual(1, len(accepts))

    def test_find_zone_transfer_accept(self):
        zone = self.create_zone()
        zt_request = self.create_zone_transfer_request(zone)
        values = {
            'tenant_id': self.admin_context.project_id,
            'zone_transfer_request_id': zt_request.id,
            'zone_id': zone.id,
            'key': zt_request.key
        }

        result = self.storage.create_zone_transfer_accept(
            self.admin_context, objects.ZoneTransferAccept.from_dict(values))

        accept = self.storage.find_zone_transfer_accept(
            self.admin_context, {'id': result.id})
        self.assertEqual(result.id, accept.id)

    def test_transfer_zone_ownership(self):
        tenant_1_context = self.get_context(project_id='1',
                                            roles=['member', 'reader'])
        tenant_2_context = self.get_context(project_id='2',
                                            roles=['member', 'reader'])
        admin_context = self.get_admin_context()
        admin_context.all_tenants = True

        zone = self.create_zone(context=tenant_1_context)
        recordset = self.create_recordset(zone, context=tenant_1_context)
        record = recordset.records[0]

        updated_zone = zone

        updated_zone.tenant_id = tenant_2_context.project_id

        self.storage.update_zone(
            admin_context, updated_zone)

        saved_zone = self.storage.get_zone(
            admin_context, zone.id)
        saved_recordset = self.storage.find_recordset(
            admin_context, criterion={'id': recordset.id})
        saved_record = self.storage.get_record(
            admin_context, record.id)

        self.assertEqual(tenant_2_context.project_id, saved_zone.tenant_id)
        self.assertEqual(
            tenant_2_context.project_id, saved_recordset.tenant_id
        )
        self.assertEqual(tenant_2_context.project_id, saved_record.tenant_id)

    def test_delete_zone_transfer_accept(self):
        zone = self.create_zone()
        zt_request = self.create_zone_transfer_request(zone)
        zt_accept = self.create_zone_transfer_accept(zt_request)

        self.storage.delete_zone_transfer_accept(
            self.admin_context, zt_accept.id)

        self.assertRaisesRegex(
            exceptions.ZoneTransferAcceptNotFound,
            'Could not find ZoneTransferAccept',
            self.storage.get_zone_transfer_accept, self.admin_context,
            zt_accept.id
        )

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

    @mock.patch('designate.storage.sql.get_read_session')
    def test_count_zone_tasks_none_result(self, mock_read_session):
        mock_sql_execute = mock.Mock()
        mock_sql_fetchone = mock.Mock()

        mock_read_session().__enter__.return_value = mock_sql_execute
        mock_sql_execute.execute.return_value = mock_sql_fetchone
        mock_sql_fetchone.fetchone.return_value = None

        zone_tasks = self.storage.count_zone_tasks(self.admin_context)

        mock_read_session.assert_called()

        self.assertEqual(0, zone_tasks)

    @mock.patch('designate.storage.sql.get_read_session')
    def test_count_zone_transfer_accept_none_result(self, mock_read_session):
        mock_sql_execute = mock.Mock()
        mock_sql_fetchone = mock.Mock()

        mock_read_session().__enter__.return_value = mock_sql_execute
        mock_sql_execute.execute.return_value = mock_sql_fetchone
        mock_sql_fetchone.fetchone.return_value = None

        zone_transfer_accepts = self.storage.count_zone_transfer_accept(
            self.admin_context
        )

        mock_read_session.assert_called()

        self.assertEqual(0, zone_transfer_accepts)

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
        uuid = '4c8e7f82-3519-4bf7-8940-a66a4480f223'

        self.assertRaisesRegex(
            exceptions.ZoneImportNotFound, 'Could not find ZoneImport',
            self.storage.get_zone_import, self.admin_context, uuid
        )

    def test_find_zone_import_criterion_missing(self):
        expected = self.create_zone_import()

        criterion = dict(status=expected['status'] + 'NOT FOUND')

        self.assertRaisesRegex(
            exceptions.ZoneImportNotFound, 'Could not find ZoneImport',
            self.storage.find_zone_import, self.admin_context, criterion
        )

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
            id='486f9cbe-b8b6-4d8c-8275-1a6e47b13e00'
        )

        self.assertRaisesRegex(
            exceptions.ZoneImportNotFound, 'Could not find ZoneImport',
            self.storage.update_zone_import, self.admin_context, zone_import
        )

    def test_delete_zone_import(self):
        # Create a zone_import
        zone_import = self.create_zone_import()

        # Delete the zone_import
        self.storage.delete_zone_import(self.admin_context, zone_import['id'])

        # Verify that it's deleted
        self.assertRaisesRegex(
            exceptions.ZoneImportNotFound, 'Could not find ZoneImport',
            self.storage.get_zone_import, self.admin_context, zone_import['id']
        )

    def test_delete_zone_import_missing(self):
        uuid = 'cac1fc02-79b2-4e62-a1a4-427b6790bbe6'

        self.assertRaisesRegex(
            exceptions.ZoneImportNotFound, 'Could not find ZoneImport',
            self.storage.delete_zone_import, self.admin_context, uuid
        )

    def test_schema_table_names(self):
        table_names = [
            'blacklists',
            'pool_also_notifies',
            'pool_attributes',
            'pool_nameservers',
            'pool_ns_records',
            'pool_target_masters',
            'pool_target_options',
            'pool_targets',
            'pools',
            'quotas',
            'records',
            'recordsets',
            'service_statuses',
            'shared_zones',
            'tlds',
            'tsigkeys',
            'zone_attributes',
            'zone_masters',
            'zone_tasks',
            'zone_transfer_accepts',
            'zone_transfer_requests',
            'zones'
        ]

        inspector = self.storage.get_inspector()

        actual_table_names = inspector.get_table_names()

        # We have transitioned database schema migration tools.
        # They use different tracking tables. Accomidate that one or both
        # may exist in this test.
        migration_table_found = False
        if ('migrate_version' in actual_table_names or
                'alembic_version' in actual_table_names):
            migration_table_found = True
        self.assertTrue(
            migration_table_found, 'A DB migration table was not found.'
        )
        try:
            actual_table_names.remove('migrate_version')
        except ValueError:
            pass
        try:
            actual_table_names.remove('alembic_version')
        except ValueError:
            pass

        self.assertEqual(table_names, actual_table_names)

    def test_schema_table_indexes(self):
        with sql.get_read_session() as session:
            indexes_t = session.execute(
                text("SELECT * FROM sqlite_master WHERE type = 'index';"))

            indexes = {}  # table name -> index names -> cmd
            for _, index_name, table_name, num, cmd in indexes_t:
                if index_name.startswith("sqlite_"):
                    continue  # ignore sqlite-specific indexes
                if table_name not in indexes:
                    indexes[table_name] = {}
                indexes[table_name][index_name] = cmd

        expected = {
            "records": {
                "record_created_at": "CREATE INDEX record_created_at ON records (created_at)",  # noqa
                "records_tenant": "CREATE INDEX records_tenant ON records (tenant_id)",  # noqa
                "update_status_index": "CREATE INDEX update_status_index ON records (status, zone_id, tenant_id, created_at, serial)",  # noqa
            },
            "recordsets": {
                "recordset_created_at": "CREATE INDEX recordset_created_at ON recordsets (created_at)",  # noqa
                "recordset_type_name": "CREATE INDEX recordset_type_name ON recordsets (type, name)",  # noqa
                "reverse_name_dom_id": "CREATE INDEX reverse_name_dom_id ON recordsets (reverse_name, zone_id)",  # noqa
                "rrset_type_domainid": "CREATE INDEX rrset_type_domainid ON recordsets (type, zone_id)",  # noqa
                "rrset_updated_at": "CREATE INDEX rrset_updated_at ON recordsets (updated_at)",  # noqa
                "rrset_zoneid": "CREATE INDEX rrset_zoneid ON recordsets (zone_id)",  # noqa
                "rrset_type": "CREATE INDEX rrset_type ON recordsets (type)",  # noqa
                "rrset_ttl": "CREATE INDEX rrset_ttl ON recordsets (ttl)",  # noqa
                "rrset_tenant_id": "CREATE INDEX rrset_tenant_id ON recordsets (tenant_id)",  # noqa
            },
            "zones": {
                "delayed_notify": "CREATE INDEX delayed_notify ON zones (delayed_notify)",  # noqa
                "increment_serial": "CREATE INDEX increment_serial ON zones (increment_serial)",  # noqa
                "reverse_name_deleted": "CREATE INDEX reverse_name_deleted ON zones (reverse_name, deleted)",  # noqa
                "zone_created_at": "CREATE INDEX zone_created_at ON zones (created_at)",  # noqa
                "zone_deleted": "CREATE INDEX zone_deleted ON zones (deleted)",
                "zone_tenant_deleted": "CREATE INDEX zone_tenant_deleted ON zones (tenant_id, deleted)",  # noqa
            }
        }
        self.assertDictEqual(expected, indexes)

    def test_create_catalog_zone(self):
        pool = self.create_pool(fixture=2)

        catalog_zone = self.storage._create_catalog_zone(pool)

        self.assertEqual("cat.example.org.", catalog_zone.name)
        self.assertEqual(60, catalog_zone.refresh)
        self.assertEqual(pool.id, catalog_zone.pool_id)
        self.assertEqual("CATALOG", catalog_zone.type)
        self.assertEqual(
            CONF['service:central'].managed_resource_email,
            catalog_zone.email)

    def test_get_catalog_zone(self):
        pool = self.create_pool(fixture=2)

        catalog_zone = self.storage.get_catalog_zone(
            self.admin_context, pool)
        self.assertEqual(pool.id, catalog_zone.pool_id)
        self.assertEqual("CATALOG", catalog_zone.type)

    def test_get_catalog_zone_records(self):
        pool = self.create_pool(fixture=2)
        self.storage._ensure_catalog_zone_config(self.admin_context, pool)
        member_zone = self.create_zone(
            attributes=[{'key': 'pool_id', 'value': pool.id}])

        catz_records = self.storage.get_catalog_zone_records(
            self.admin_context, pool)
        fqdn = pool.catalog_zone.catalog_zone_fqdn

        self.assertEqual(5, len(catz_records))
        self.assertEqual("SOA", catz_records[0].type)
        self.assertEqual(fqdn, catz_records[0].name)
        self.assertEqual("NS", catz_records[1].type)
        self.assertEqual(fqdn, catz_records[1].name)
        self.assertEqual("TXT", catz_records[2].type)
        self.assertEqual(f"version.{fqdn}", catz_records[2].name)
        self.assertEqual(
            f"{member_zone.id}.zones.{fqdn}", catz_records[3].name)
        self.assertEqual("SOA", catz_records[4].type)

    def test_ensure_catalog_zone_config_no_catalog_zone(self):
        pool = self.storage.find_pools(self.admin_context)[0]
        self.assertRaises(
            exceptions.ZoneNotFound, self.storage.get_catalog_zone,
            self.admin_context, pool)

        self.storage.get_catalog_zone = mock.Mock()
        self.storage._ensure_catalog_zone_config(
            self.admin_context, pool)
        self.storage.get_catalog_zone.assert_not_called()

    @mock.patch.object(storage.sqlalchemy.SQLAlchemyStorage, 'update_zone')
    @mock.patch.object(storage.sqlalchemy.SQLAlchemyStorage,
                       '_ensure_catalog_zone_consistent')
    def test_ensure_catalog_zone_config(
            self, mock_update_zone, mock_ensure_catalog_zone_consistent):
        self.create_pool(fixture=2)
        mock_update_zone.assert_called()

    @mock.patch.object(
        storage.sqlalchemy.SQLAlchemyStorage, 'get_catalog_zone')
    def test_ensure_catalog_zone_consistent_no_catalog_zone(
            self, mock_get_catalog_zone):
        pool = self.create_pool()
        self.storage._ensure_catalog_zone_consistent(self.admin_context, pool)
        mock_get_catalog_zone.assert_not_called()

    def test_ensure_catalog_zone_consistent(self):
        pool = self.create_pool(
            fixture=3)  # Pool with catalog zone and TSIG data
        self.storage._ensure_catalog_zone_config(self.admin_context, pool)
        catalog_zone = self.storage.get_catalog_zone(self.admin_context, pool)

        self.assertEqual(catalog_zone.attributes.get('catalog_zone_fqdn'),
                         pool.catalog_zone.catalog_zone_fqdn)

        self.assertEqual(int(
            catalog_zone.attributes.get('catalog_zone_refresh')),
            pool.catalog_zone.catalog_zone_refresh)

        # Check SOA
        catz_records = self.storage.get_catalog_zone_records(
            self.admin_context, pool)
        self.assertEqual(catz_records[-1].type, 'SOA')
        expected = (
            f'{pool.ns_records[0]["hostname"]} '
            f'{catalog_zone.attributes.get("catalog_zone_fqdn")} '
            f'{catalog_zone.serial} '
            f'{catalog_zone.attributes.get("catalog_zone_refresh")} '
            f'{catalog_zone.retry} '
            '2147483646 '
            f'{catalog_zone.minimum}'
        )
        self.assertEqual(expected, catz_records[-1].records[0].data)

        # Check TSIG
        tsigkey = self.storage.find_tsigkey(
            self.admin_context, criterion={'resource_id': catalog_zone.id})
        self.assertEqual(pool.catalog_zone.catalog_zone_tsig_key,
                         tsigkey.secret)
        self.assertEqual(pool.catalog_zone.catalog_zone_tsig_algorithm,
                         tsigkey.algorithm)

    def test_ensure_catalog_zone_consistent_no_tsig(self):
        pool = self.create_pool(fixture=2)
        catalog_zone = self.storage.get_catalog_zone(self.admin_context, pool)

        # Check no TSIG key created
        self.assertRaises(
            exceptions.TsigKeyNotFound, self.storage.find_tsigkey,
            self.admin_context, criterion={'resource_id': catalog_zone.id})

    def test_ensure_catalog_zone_consistent_invalid_tsig(self):
        # Check invalid TSIG data detected
        self.assertRaisesRegex(
            ValueError, 'Field value no-algorithm is invalid',
            self.create_pool, fixture=4)

    def test_ensure_catalog_zone_consistent_tsig_changed(self):
        pool = self.create_pool(
            fixture=3)  # Pool with catalog zone and TSIG data

        pool.catalog_zone.catalog_zone_tsig_key = 'SomeNewSecret'
        pool.catalog_zone.catalog_zone_tsig_algorithm = 'hmac-sha256'

        self.storage._ensure_catalog_zone_config(self.admin_context, pool)
        catalog_zone = self.storage.get_catalog_zone(self.admin_context, pool)

        # Check TSIG
        tsigkey = self.storage.find_tsigkey(
            self.admin_context, criterion={'resource_id': catalog_zone.id})
        self.assertEqual(pool.catalog_zone.catalog_zone_tsig_key,
                         tsigkey.secret)
        self.assertEqual(pool.catalog_zone.catalog_zone_tsig_algorithm,
                         tsigkey.algorithm)

    def test_ensure_catalog_zone_consistent_change_pool(self):
        pool = self.create_pool(fixture=2)  # Catalog zone without TSIG

        # Change pool attributes
        pool.catalog_zone.catalog_zone_fqdn = 'new.example.com.'
        pool.catalog_zone.catalog_zone_refresh = 3600

        self.storage._ensure_catalog_zone_consistent(self.admin_context, pool)
        catalog_zone = self.storage.get_catalog_zone(self.admin_context, pool)

        self.assertEqual(
            pool.catalog_zone.catalog_zone_fqdn,
            catalog_zone.attributes.get("catalog_zone_fqdn"))
        self.assertEqual(
            pool.catalog_zone.catalog_zone_refresh,
            int(catalog_zone.attributes.get("catalog_zone_refresh")))
