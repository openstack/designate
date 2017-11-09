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

import datetime
import copy
import random
from collections import namedtuple

import mock
import testtools
from testtools.matchers import GreaterThan
from oslo_config import cfg
from oslo_log import log as logging
from oslo_db import exception as db_exception
from oslo_messaging.notify import notifier

from designate import exceptions
from designate import objects
from designate.mdns import rpcapi as mdns_api
from designate.tests.test_central import CentralTestCase
from designate.storage.impl_sqlalchemy import tables

LOG = logging.getLogger(__name__)


class CentralServiceTest(CentralTestCase):
    def test_stop(self):
        # Test stopping the service
        self.central_service.stop()

    def test_is_valid_zone_name(self):
        self.config(max_zone_name_len=10,
                    group='service:central')

        context = self.get_context()

        self.central_service._is_valid_zone_name(context, 'valid.org.')

        with testtools.ExpectedException(exceptions.InvalidZoneName):
            self.central_service._is_valid_zone_name(context, 'example.org.')

        with testtools.ExpectedException(exceptions.InvalidZoneName):
            self.central_service._is_valid_zone_name(context, 'example.tld.')

        with testtools.ExpectedException(exceptions.InvalidZoneName):
            self.central_service._is_valid_zone_name(context, 'tld.')

    def test_is_valid_zone_name_with_tlds(self):
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
            with testtools.ExpectedException(exceptions.InvalidZoneName):
                self.central_service._is_valid_zone_name(context, 'biz.')

    def test_is_valid_recordset_name(self):
        self.config(max_recordset_name_len=18,
                    group='service:central')

        context = self.get_context()

        zone = self.create_zone(name='example.org.')

        self.central_service._is_valid_recordset_name(
            context, zone, 'valid.example.org.')

        with testtools.ExpectedException(exceptions.InvalidRecordSetName):
            self.central_service._is_valid_recordset_name(
                context, zone, 'toolong.example.org.')

        with testtools.ExpectedException(ValueError):
            self.central_service._is_valid_recordset_name(
                context, zone, 'invalidtld.example.org')

        with testtools.ExpectedException(exceptions.InvalidRecordSetLocation):
            self.central_service._is_valid_recordset_name(
                context, zone, 'a.example.COM.')

        with testtools.ExpectedException(exceptions.InvalidRecordSetLocation):
            # Ensure names ending in the zone name, but
            # not contained in it fail
            self.central_service._is_valid_recordset_name(
                context, zone, 'aexample.org.')

    def test_is_blacklisted_zone_name(self):
        # Create blacklisted zones with specific names
        self.create_blacklist(pattern='example.org.')
        self.create_blacklist(pattern='example.net.')
        self.create_blacklist(pattern='^blacklisted.org.$')
        self.create_blacklist(pattern='com.$')

        # Set the policy to reject the authz
        self.policy({'use_blacklisted_zone': '!'})

        context = self.get_context()

        result = self.central_service._is_blacklisted_zone_name(
            context, 'org.')
        self.assertFalse(result)

        # subzones should not be allowed from a blacklisted zone
        result = self.central_service._is_blacklisted_zone_name(
            context, 'www.example.org.')
        self.assertTrue(result)

        result = self.central_service._is_blacklisted_zone_name(
            context, 'example.org.')
        self.assertTrue(result)

        # Check for blacklisted zones containing regexps
        result = self.central_service._is_blacklisted_zone_name(
            context, 'example.net.')
        self.assertTrue(result)

        result = self.central_service._is_blacklisted_zone_name(
            context, 'example.com.')
        self.assertTrue(result)

        result = self.central_service._is_blacklisted_zone_name(
            context, 'blacklisted.org.')

        self.assertTrue(result)

    def test_is_blacklisted_zone_name_evil(self):
        evil_regex = "(([a-z])+.)+[A-Z]([a-z])+$"
        evil_zone_name = ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                          "aaaaaaaa.com.")

        blacklists = objects.BlacklistList(
            objects=[objects.Blacklist(pattern=evil_regex)])

        context = self.get_context()

        with mock.patch.object(self.central_service.storage,
                               'find_blacklists',
                               return_value=blacklists):

            result = self.central_service._is_blacklisted_zone_name(
                context, evil_zone_name)
            self.assertTrue(result)

    def test_is_subzone(self):
        context = self.get_context()

        # Create a zone (using the specified zone name)
        zone = self.create_zone(name='example.org.')

        result = self.central_service._is_subzone(
            context, 'org.', zone.pool_id)
        self.assertFalse(result)

        result = self.central_service._is_subzone(
            context, 'www.example.net.', zone.pool_id)
        self.assertFalse(result)

        result = self.central_service._is_subzone(
            context, 'example.org.', zone.pool_id)
        self.assertFalse(result)

        result = self.central_service._is_subzone(
            context, 'www.example.org.', zone.pool_id)
        self.assertTrue(result)

    def test_is_superzone(self):
        context = self.get_context()

        # Create a zone (using the specified zone name)
        zone = self.create_zone(name='example.org.')

        LOG.debug("Testing 'org.'")
        result = self.central_service._is_superzone(
            context, 'org.', zone.pool_id)
        self.assertTrue(result)

        LOG.debug("Testing 'www.example.net.'")
        result = self.central_service._is_superzone(
            context, 'www.example.net.', zone.pool_id)
        self.assertFalse(result)

        LOG.debug("Testing 'www.example.org.'")
        result = self.central_service._is_superzone(
            context, 'www.example.org.', zone.pool_id)
        self.assertFalse(result)

    def test_is_valid_recordset_placement_subzone(self):
        context = self.get_context()

        # Create a zone (using the specified zone name)
        zone = self.create_zone(name='example.org.')
        sub_zone = self.create_zone(name='sub.example.org.')

        def _fail(zone_, name):
            with testtools.ExpectedException(
                    exceptions.InvalidRecordSetLocation):
                self.central_service._is_valid_recordset_placement_subzone(
                    context, zone_, name)

        def _ok(zone_, name):
            self.central_service._is_valid_recordset_placement_subzone(
                context, zone_, name)

        _fail(zone, 'record.sub.example.org.')
        _fail(zone, 'sub.example.org.')
        _ok(zone, 'example.org.')
        _ok(zone, 'record.example.org.')

        _ok(sub_zone, 'record.example.org.')

    def test_is_valid_ttl(self):
        self.policy({'use_low_ttl': '!'})
        self.config(min_ttl=100,
                    group='service:central')
        context = self.get_context()

        values = self.get_zone_fixture(fixture=1)
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
        self.assertEqual(self.get_tld_fixture(fixture=0)['name'], tld['name'])

        # Create a TLD with more than one label
        tld = self.create_tld(fixture=1)

        # Ensure all values have been set correctly
        self.assertIsNotNone(tld['id'])
        self.assertEqual(self.get_tld_fixture(fixture=1)['name'], tld['name'])

    def test_find_tlds(self):
        # Ensure we have no tlds to start with.
        tlds = self.central_service.find_tlds(self.admin_context)
        self.assertEqual(0, len(tlds))

        # Create a single tld
        self.create_tld(fixture=0)
        # Ensure we can retrieve the newly created tld
        tlds = self.central_service.find_tlds(self.admin_context)
        self.assertEqual(1, len(tlds))
        self.assertEqual(self.get_tld_fixture(fixture=0)['name'],
                         tlds[0]['name'])

        # Create a second tld
        self.create_tld(fixture=1)

        # Ensure we can retrieve both tlds
        tlds = self.central_service.find_tlds(self.admin_context)
        self.assertEqual(2, len(tlds))
        self.assertEqual(self.get_tld_fixture(fixture=0)['name'],
                         tlds[0]['name'])
        self.assertEqual(self.get_tld_fixture(fixture=1)['name'],
                         tlds[1]['name'])

    def test_get_tld(self):
        # Create a tld
        tld_name = 'ns%d.co.uk' % random.randint(10, 1000)
        expected_tld = self.create_tld(name=tld_name)

        # Retrieve it, and ensure it's the same
        tld = self.central_service.get_tld(
            self.admin_context, expected_tld['id'])

        self.assertEqual(expected_tld['id'], tld['id'])
        self.assertEqual(expected_tld['name'], tld['name'])

    def test_update_tld(self):
        # Create a tld
        tld = self.create_tld(name='org')

        # Update the Object
        tld.name = 'net'

        # Perform the update
        self.central_service.update_tld(self.admin_context, tld)

        # Fetch the tld again
        tld = self.central_service.get_tld(self.admin_context, tld.id)

        # Ensure the tld was updated correctly
        self.assertEqual('net', tld.name)

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
        self.assertEqual(values['name'], tsigkey['name'])
        self.assertEqual(values['algorithm'], tsigkey['algorithm'])
        self.assertEqual(values['secret'], tsigkey['secret'])

    def test_find_tsigkeys(self):
        # Ensure we have no tsigkeys to start with.
        tsigkeys = self.central_service.find_tsigkeys(self.admin_context)
        self.assertEqual(0, len(tsigkeys))

        # Create a single tsigkey (using default values)
        tsigkey_one = self.create_tsigkey()

        # Ensure we can retrieve the newly created tsigkey
        tsigkeys = self.central_service.find_tsigkeys(self.admin_context)
        self.assertEqual(1, len(tsigkeys))
        self.assertEqual(tsigkey_one['name'], tsigkeys[0]['name'])

        # Create a second tsigkey
        tsigkey_two = self.create_tsigkey(fixture=1)

        # Ensure we can retrieve both tsigkeys
        tsigkeys = self.central_service.find_tsigkeys(self.admin_context)
        self.assertEqual(2, len(tsigkeys))
        self.assertEqual(tsigkey_one['name'], tsigkeys[0]['name'])
        self.assertEqual(tsigkey_two['name'], tsigkeys[1]['name'])

    def test_get_tsigkey(self):
        # Create a tsigkey
        expected = self.create_tsigkey()

        # Retrieve it, and ensure it's the same
        tsigkey = self.central_service.get_tsigkey(
            self.admin_context, expected['id'])

        self.assertEqual(expected['id'], tsigkey['id'])
        self.assertEqual(expected['name'], tsigkey['name'])
        self.assertEqual(expected['algorithm'], tsigkey['algorithm'])
        self.assertEqual(expected['secret'], tsigkey['secret'])

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
        self.assertEqual(0, tenants)

        # Explicitly set a tenant_id
        self.create_zone(fixture=0, context=tenant_one_context)
        self.create_zone(fixture=1, context=tenant_two_context)

        tenants = self.central_service.count_tenants(admin_context)
        self.assertEqual(2, tenants)

    def test_count_tenants_policy_check(self):
        # Set the policy to reject the authz
        self.policy({'count_tenants': '!'})

        with testtools.ExpectedException(exceptions.Forbidden):
            self.central_service.count_tenants(self.get_context())

    # Zone Tests
    @mock.patch.object(notifier.Notifier, "info")
    def _test_create_zone(self, values, mock_notifier):
        # Reset the mock to avoid the calls from the create_nameserver() call
        mock_notifier.reset_mock()

        # Create a zone
        zone = self.central_service.create_zone(
            self.admin_context, zone=objects.Zone.from_dict(values))

        # Ensure all values have been set correctly
        self.assertIsNotNone(zone['id'])
        self.assertEqual(values['name'], zone['name'])
        self.assertEqual(values['email'], zone['email'])
        self.assertIn('status', zone)

        self.assertEqual(2, mock_notifier.call_count)

        # Ensure the correct NS Records are in place
        pool = self.central_service.get_pool(
            self.admin_context, zone.pool_id)

        ns_recordset = self.central_service.find_recordset(
            self.admin_context,
            criterion={'zone_id': zone.id, 'type': "NS"})

        self.assertIsNotNone(ns_recordset.id)
        self.assertEqual('NS', ns_recordset.type)
        self.assertIsNotNone(ns_recordset.records)
        self.assertEqual(set([n.hostname for n in pool.ns_records]),
                         set([n.data for n in ns_recordset.records]))

        return zone

    def test_create_zone_duplicate_different_pools(self):
        fixture = self.get_zone_fixture()

        # Create first zone that's placed in default pool
        self.create_zone(**fixture)

        # Create a secondary pool
        second_pool = self.create_pool()
        fixture["attributes"] = {}
        fixture["attributes"]["pool_id"] = second_pool.id

        self.create_zone(**fixture)

    def test_create_zone_over_tld(self):
        values = dict(
            name='example.com.',
            email='info@example.com',
            type='PRIMARY'
        )
        self._test_create_zone(values)

    def test_idn_create_zone_over_tld(self):
        values = dict(
            name='xn--3e0b707e'
        )

        # Create the appropriate TLD
        self.central_service.create_tld(
            self.admin_context, objects.Tld.from_dict(values))

        # Test creation of a zone in 한국 (kr)
        values = dict(
            name='example.xn--3e0b707e.',
            email='info@example.xn--3e0b707e',
            type='PRIMARY'
        )
        self._test_create_zone(values)

    def test_create_zone_over_quota(self):
        self.config(quota_zones=1)

        self.create_zone()

        with testtools.ExpectedException(exceptions.OverQuota):
            self.create_zone()

    def test_create_subzone(self):
        # Create the Parent Zone using fixture 0
        parent_zone = self.create_zone(fixture=0)

        # Prepare values for the subzone using fixture 1 as a base
        values = self.get_zone_fixture(fixture=1)
        values['name'] = 'www.%s' % parent_zone['name']

        # Create the subzone
        zone = self.central_service.create_zone(
            self.admin_context, objects.Zone.from_dict(values))

        # Ensure all values have been set correctly
        self.assertIsNotNone(zone['id'])
        self.assertEqual(parent_zone['id'], zone['parent_zone_id'])

    def test_create_subzone_different_pools(self):
        fixture = self.get_zone_fixture()

        # Create first zone that's placed in default pool
        zone = self.create_zone(**fixture)

        # Create a secondary pool
        second_pool = self.create_pool()
        fixture["attributes"] = {}
        fixture["attributes"]["pool_id"] = second_pool.id
        fixture["name"] = "sub.%s" % fixture["name"]
        subzone = self.create_zone(**fixture)

        if subzone.pool_id is not zone.pool_id:
            self.assertIsNone(subzone.parent_zone_id)
        else:
            raise Exception("Foo")

    def test_create_superzone(self):
        # Prepare values for the zone and subzone
        # using fixture 1 as a base
        zone_values = self.get_zone_fixture(fixture=1)

        subzone_values = copy.deepcopy(zone_values)
        subzone_values['name'] = 'www.%s' % zone_values['name']
        subzone_values['context'] = self.admin_context

        LOG.debug("zone_values: {0}".format(zone_values))
        LOG.debug("subzone_values: {0}".format(subzone_values))

        # Create the subzone
        subzone = self.create_zone(**subzone_values)

        # Create the Parent Zone using fixture 1
        parent_zone = self.central_service.create_zone(
            self.admin_context, objects.Zone.from_dict(zone_values))

        # Get updated subzone values
        subzone = self.central_service.get_zone(self.admin_context,
                                                subzone.id)

        # Ensure all values have been set correctly
        self.assertIsNotNone(parent_zone['id'])
        self.assertEqual(parent_zone['id'], subzone['parent_zone_id'])

    def test_create_subzone_failure(self):
        context = self.get_admin_context()

        # Explicitly set a tenant_id
        context.tenant = '1'

        # Create the Parent Zone using fixture 0
        parent_zone = self.create_zone(fixture=0, context=context)

        context = self.get_admin_context()

        # Explicitly use a different tenant_id
        context.tenant = '2'

        # Prepare values for the subzone using fixture 1 as a base
        values = self.get_zone_fixture(fixture=1)
        values['name'] = 'www.%s' % parent_zone['name']

        # Attempt to create the subzone
        with testtools.ExpectedException(exceptions.IllegalChildZone):
            self.central_service.create_zone(
                context, objects.Zone.from_dict(values))

    def test_create_superzone_failure(self):
        context = self.get_admin_context()

        # Explicitly set a tenant_id
        context.tenant = '1'

        # Set up zone and subzone values
        zone_values = self.get_zone_fixture(fixture=1)
        zone_name = zone_values['name']

        subzone_values = copy.deepcopy(zone_values)
        subzone_values['name'] = 'www.%s' % zone_name
        subzone_values['context'] = context

        # Create sub zone
        self.create_zone(**subzone_values)

        context = self.get_admin_context()

        # Explicitly use a different tenant_id
        context.tenant = '2'

        # Attempt to create the zone
        with testtools.ExpectedException(exceptions.IllegalParentZone):
            self.central_service.create_zone(
                context, objects.Zone.from_dict(zone_values))

    def test_create_blacklisted_zone_success(self):
        # Create blacklisted zone using default values
        self.create_blacklist()

        # Set the policy to accept the authz
        self.policy({'use_blacklisted_zone': '@'})

        values = dict(
            name='blacklisted.com.',
            email='info@blacklisted.com'
        )

        # Create a zone that is blacklisted
        zone = self.central_service.create_zone(
            self.admin_context, objects.Zone.from_dict(values))

        # Ensure all values have been set correctly
        self.assertIsNotNone(zone['id'])
        self.assertEqual(zone['name'], values['name'])
        self.assertEqual(zone['email'], values['email'])

    def test_create_blacklisted_zone_fail(self):
        self.create_blacklist()

        # Set the policy to reject the authz
        self.policy({'use_blacklisted_zone': '!'})

        values = dict(
            name='blacklisted.com.',
            email='info@blacklisted.com'
        )

        with testtools.ExpectedException(exceptions.InvalidZoneName):
            # Create a zone
            self.central_service.create_zone(
                self.admin_context, objects.Zone.from_dict(values))

    def _test_create_zone_fail(self, values, exception):

        with testtools.ExpectedException(exception):
            # Create an invalid zone
            self.central_service.create_zone(
                self.admin_context, objects.Zone.from_dict(values))

    def test_create_zone_invalid_tld_fail(self):
        # add a tld for com
        self.create_tld(fixture=0)

        values = dict(
            name='example.com.',
            email='info@example.com'
        )

        # Create a valid zone
        self.central_service.create_zone(
            self.admin_context, objects.Zone.from_dict(values))

        values = dict(
            name='example.net.',
            email='info@example.net'
        )

        # There is no TLD for net so it should fail
        with testtools.ExpectedException(exceptions.InvalidZoneName):
            # Create an invalid zone
            self.central_service.create_zone(
                self.admin_context, objects.Zone.from_dict(values))

    def test_create_zone_invalid_ttl_fail(self):
        self.policy({'use_low_ttl': '!'})
        self.config(min_ttl=100,
                    group='service:central')
        context = self.get_context()

        values = self.get_zone_fixture(fixture=1)
        values['ttl'] = 0

        with testtools.ExpectedException(exceptions.InvalidTTL):
                    self.central_service.create_zone(
                        context, objects.Zone.from_dict(values))

    def test_create_zone_below_zero_ttl(self):
        self.policy({'use_low_ttl': '!'})
        self.config(min_ttl=1,
                    group='service:central')
        context = self.get_context()

        values = self.get_zone_fixture(fixture=1)
        values['ttl'] = -100

        with testtools.ExpectedException(exceptions.InvalidTTL):
            self.central_service.create_zone(
                context, objects.Zone.from_dict(values))

    def test_create_zone_no_min_ttl(self):
        self.policy({'use_low_ttl': '!'})
        self.config(min_ttl=None,
                    group='service:central')
        values = self.get_zone_fixture(fixture=1)
        values['ttl'] = 10

        # Create zone with random TTL
        zone = self.central_service.create_zone(
            self.admin_context, objects.Zone.from_dict(values))

        # Ensure all values have been set correctly
        self.assertEqual(values['ttl'], zone['ttl'])

    def test_find_zones(self):
        # Ensure we have no zones to start with.
        zones = self.central_service.find_zones(self.admin_context)
        self.assertEqual(0, len(zones))

        # Create a single zone (using default values)
        self.create_zone()

        # Ensure we can retrieve the newly created zone
        zones = self.central_service.find_zones(self.admin_context)
        self.assertEqual(1, len(zones))
        self.assertEqual('example.com.', zones[0]['name'])

        # Create a second zone
        self.create_zone(name='example.net.')

        # Ensure we can retrieve both zone
        zones = self.central_service.find_zones(self.admin_context)
        self.assertEqual(2, len(zones))
        self.assertEqual('example.com.', zones[0]['name'])
        self.assertEqual('example.net.', zones[1]['name'])

    def test_find_zones_criteria(self):
        # Create a zone
        zone_name = '%d.example.com.' % random.randint(10, 1000)
        expected_zone = self.create_zone(name=zone_name)

        # Retrieve it, and ensure it's the same
        criterion = {'name': zone_name}

        zones = self.central_service.find_zones(
            self.admin_context, criterion)

        self.assertEqual(expected_zone['id'], zones[0]['id'])
        self.assertEqual(expected_zone['name'], zones[0]['name'])
        self.assertEqual(expected_zone['email'], zones[0]['email'])

    def test_find_zones_tenant_restrictions(self):
        admin_context = self.get_admin_context()
        admin_context.all_tenants = True

        tenant_one_context = self.get_context(tenant=1)
        tenant_two_context = self.get_context(tenant=2)

        # Ensure we have no zones to start with.
        zones = self.central_service.find_zones(admin_context)
        self.assertEqual(0, len(zones))

        # Create a single zone (using default values)
        zone = self.create_zone(context=tenant_one_context)

        # Ensure admins can retrieve the newly created zone
        zones = self.central_service.find_zones(admin_context)
        self.assertEqual(1, len(zones))
        self.assertEqual(zone['name'], zones[0]['name'])

        # Ensure tenant=1 can retrieve the newly created zone
        zones = self.central_service.find_zones(tenant_one_context)
        self.assertEqual(1, len(zones))
        self.assertEqual(zone['name'], zones[0]['name'])

        # Ensure tenant=2 can NOT retrieve the newly created zone
        zones = self.central_service.find_zones(tenant_two_context)
        self.assertEqual(0, len(zones))

    def test_get_zone(self):
        # Create a zone
        zone_name = '%d.example.com.' % random.randint(10, 1000)
        expected_zone = self.create_zone(name=zone_name)

        # Retrieve it, and ensure it's the same
        zone = self.central_service.get_zone(
            self.admin_context, expected_zone['id'])

        self.assertEqual(expected_zone['id'], zone['id'])
        self.assertEqual(expected_zone['name'], zone['name'])
        self.assertEqual(expected_zone['email'], zone['email'])

    def test_get_zone_servers(self):
        # Create a zone
        zone = self.create_zone()

        # Retrieve the servers list
        servers = self.central_service.get_zone_ns_records(
            self.admin_context, zone['id'])

        self.assertGreater(len(servers), 0)

    def test_find_zone(self):
        # Create a zone
        zone_name = '%d.example.com.' % random.randint(10, 1000)
        expected_zone = self.create_zone(name=zone_name)

        # Retrieve it, and ensure it's the same
        criterion = {'name': zone_name}

        zone = self.central_service.find_zone(
            self.admin_context, criterion)

        self.assertEqual(expected_zone['id'], zone['id'])
        self.assertEqual(expected_zone['name'], zone['name'])
        self.assertEqual(expected_zone['email'], zone['email'])
        self.assertIn('status', zone)

    @mock.patch.object(notifier.Notifier, "info")
    def test_update_zone(self, mock_notifier):
        # Create a zone
        zone = self.create_zone(email='info@example.org')
        original_serial = zone.serial

        # Update the object
        zone.email = 'info@example.net'

        # Reset the mock to avoid the calls from the create_zone() call
        mock_notifier.reset_mock()

        # Perform the update
        self.central_service.update_zone(self.admin_context, zone)

        # Fetch the zone again
        zone = self.central_service.get_zone(
            self.admin_context, zone.id)

        # Ensure the zone was updated correctly
        self.assertGreater(zone.serial, original_serial)
        self.assertEqual('info@example.net', zone.email)

        self.assertEqual(2, mock_notifier.call_count)

        # Check that the object used in the notify is a Zone and the id
        # matches up
        notified_zone = mock_notifier.call_args[0][-1]
        self.assertIsInstance(notified_zone, objects.Zone)
        self.assertEqual(zone.id, notified_zone.id)

    def test_update_zone_without_id(self):
        # Create a zone
        zone = self.create_zone(email='info@example.org')

        # Update the object
        zone.email = 'info@example.net'
        zone.id = None
        # Perform the update
        with testtools.ExpectedException(Exception):
            self.central_service.update_zone(self.admin_context, zone)

    def test_update_zone_without_incrementing_serial(self):
        # Create a zone
        zone = self.create_zone(email='info@example.org')
        original_serial = zone.serial

        # Update the object
        zone.email = 'info@example.net'

        # Perform the update
        self.central_service.update_zone(
            self.admin_context, zone, increment_serial=False)

        # Fetch the zone again
        zone = self.central_service.get_zone(self.admin_context, zone.id)

        # Ensure the zone was updated correctly
        self.assertEqual(original_serial, zone.serial)
        self.assertEqual('info@example.net', zone.email)

    def test_update_zone_name_fail(self):
        # Create a zone
        zone = self.create_zone(name='example.org.')

        # Update the Object
        zone.name = 'example.net.'

        # Perform the update
        with testtools.ExpectedException(exceptions.BadRequest):
            self.central_service.update_zone(self.admin_context, zone)

    def test_update_zone_deadlock_retry(self):
        # Create a zone
        zone = self.create_zone(name='example.org.')
        original_serial = zone.serial

        # Update the Object
        zone.email = 'info@example.net'

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
            zone = self.central_service.update_zone(
                self.admin_context, zone)

        # Ensure i[0] is True, indicating the side_effect code above was
        # triggered
        self.assertTrue(i[0])

        # Ensure the zone was updated correctly
        self.assertGreater(zone.serial, original_serial)
        self.assertEqual('info@example.net', zone.email)

    @mock.patch.object(notifier.Notifier, "info")
    def test_delete_zone(self, mock_notifier):
        # Create a zone
        zone = self.create_zone()

        mock_notifier.reset_mock()

        # Delete the zone
        self.central_service.delete_zone(self.admin_context, zone['id'])

        # Fetch the zone
        deleted_zone = self.central_service.get_zone(
            self.admin_context, zone['id'])

        # Ensure the zone is marked for deletion
        self.assertEqual(zone.id, deleted_zone.id)
        self.assertEqual(zone.name, deleted_zone.name)
        self.assertEqual(zone.email, deleted_zone.email)
        self.assertEqual('PENDING', deleted_zone.status)
        self.assertEqual(zone.tenant_id, deleted_zone.tenant_id)
        self.assertEqual(zone.parent_zone_id,
                         deleted_zone.parent_zone_id)
        self.assertEqual('DELETE', deleted_zone.action)
        self.assertEqual(zone.serial, deleted_zone.serial)
        self.assertEqual(zone.pool_id, deleted_zone.pool_id)

        self.assertEqual(2, mock_notifier.call_count)

        # Check that the object used in the notify is a Zone and the id
        # matches up
        notified_zone = mock_notifier.call_args[0][-1]
        self.assertIsInstance(notified_zone, objects.Zone)
        self.assertEqual(deleted_zone.id, notified_zone.id)

    def test_delete_parent_zone(self):
        # Create the Parent Zone using fixture 0
        parent_zone = self.create_zone(fixture=0)

        # Create the subzone
        self.create_zone(fixture=1, name='www.%s' % parent_zone['name'])

        # Attempt to delete the parent zone
        with testtools.ExpectedException(exceptions.ZoneHasSubZone):
            self.central_service.delete_zone(
                self.admin_context, parent_zone['id'])

    def test_count_zones(self):
        # in the beginning, there should be nothing
        zones = self.central_service.count_zones(self.admin_context)
        self.assertEqual(0, zones)

        # Create a single zone
        self.create_zone()

        # count 'em up
        zones = self.central_service.count_zones(self.admin_context)

        # well, did we get 1?
        self.assertEqual(1, zones)

    def test_count_zones_policy_check(self):
        # Set the policy to reject the authz
        self.policy({'count_zones': '!'})

        with testtools.ExpectedException(exceptions.Forbidden):
            self.central_service.count_zones(self.get_context())

    def _fetch_all_zones(self):
        """Fetch all zones including deleted ones
        """
        query = tables.zones.select()
        return self.central_service.storage.session.execute(query).fetchall()

    def _log_all_zones(self, zones, msg=None):
        """Log out a summary of zones
        """
        if msg:
            LOG.debug("--- %s ---" % msg)
        cols = ('name', 'status', 'action', 'deleted', 'deleted_at',
                'parent_zone_id')
        tpl = "%-35s | %-11s | %-11s | %-32s | %-20s | %s"
        LOG.debug(tpl % cols)
        for z in zones:
            LOG.debug(tpl % tuple(z[k] for k in cols))

    def _assert_count_all_zones(self, n):
        """Assert count ALL zones including deleted ones
        """
        zones = self._fetch_all_zones()
        if len(zones) == n:
            return

        msg = "failed: %d zones expected, %d found" % (n, len(zones))
        self._log_all_zones(zones, msg=msg)
        raise Exception("Unexpected number of zones")

    def _create_deleted_zone(self, name, mock_deletion_time):
        # Create a zone and set it as deleted
        zone = self.create_zone(name=name)
        self._delete_zone(zone, mock_deletion_time)
        return zone

    def _delete_zone(self, zone, mock_deletion_time):
        # Set a zone as deleted
        zid = zone.id.replace('-', '')
        query = tables.zones.update().\
            where(tables.zones.c.id == zid).\
            values(
                action='NONE',
                deleted=zid,
                deleted_at=mock_deletion_time,
                status='DELETED',
        )

        pxy = self.central_service.storage.session.execute(query)
        self.assertEqual(1, pxy.rowcount)
        return zone

    @mock.patch.object(notifier.Notifier, "info")
    def test_purge_zones_nothing_to_purge(self, mock_notifier):
        # Create a zone
        self.create_zone()
        mock_notifier.reset_mock()
        self._assert_count_all_zones(1)

        now = datetime.datetime(2015, 7, 31, 0, 0)
        self.central_service.purge_zones(
            self.admin_context,
            {
                'status': 'DELETED',
                'deleted': '!0',
                'deleted_at': "<=%s" % now
            },
            limit=100
        )
        self._assert_count_all_zones(1)

    @mock.patch.object(notifier.Notifier, "info")
    def test_purge_zones_one_to_purge(self, mock_notifier):
        self.create_zone()
        new = datetime.datetime(2015, 7, 30, 0, 0)
        now = datetime.datetime(2015, 7, 31, 0, 0)
        self._create_deleted_zone('example2.org.', new)
        mock_notifier.reset_mock()
        self._assert_count_all_zones(2)

        self.central_service.purge_zones(
            self.admin_context,
            {
                'deleted': '!0',
                'deleted_at': "<=%s" % now
            },
            limit=100,
        )
        self._assert_count_all_zones(1)

    @mock.patch.object(notifier.Notifier, "info")
    def test_purge_zones_one_to_purge_out_of_three(self, mock_notifier):
        self.create_zone()
        old = datetime.datetime(2015, 7, 20, 0, 0)
        time_threshold = datetime.datetime(2015, 7, 25, 0, 0)
        new = datetime.datetime(2015, 7, 30, 0, 0)
        self._create_deleted_zone('old.org.', old)
        self._create_deleted_zone('new.org.', new)
        mock_notifier.reset_mock()
        self._assert_count_all_zones(3)

        purge_cnt = self.central_service.purge_zones(
            self.admin_context,
            {
                'deleted': '!0',
                'deleted_at': "<=%s" % time_threshold
            },
            limit=100,
        )
        self._assert_count_all_zones(2)
        self.assertEqual(1, purge_cnt)

    @mock.patch.object(notifier.Notifier, "info")
    def test_purge_zones_without_time_threshold(self, mock_notifier):
        self.create_zone()
        old = datetime.datetime(2015, 7, 20, 0, 0)
        new = datetime.datetime(2015, 7, 30, 0, 0)
        self._create_deleted_zone('old.org.', old)
        self._create_deleted_zone('new.org.', new)
        mock_notifier.reset_mock()
        self._assert_count_all_zones(3)

        purge_cnt = self.central_service.purge_zones(
            self.admin_context,
            {
                'deleted': '!0',
            },
            limit=100,
        )
        self._assert_count_all_zones(1)
        self.assertEqual(2, purge_cnt)

    @mock.patch.object(notifier.Notifier, "info")
    def test_purge_zones_without_deleted_criterion(self, mock_notifier):
        self.create_zone()
        old = datetime.datetime(2015, 7, 20, 0, 0)
        time_threshold = datetime.datetime(2015, 7, 25, 0, 0)
        new = datetime.datetime(2015, 7, 30, 0, 0)
        self._create_deleted_zone('old.org.', old)
        self._create_deleted_zone('new.org.', new)
        mock_notifier.reset_mock()
        self._assert_count_all_zones(3)

        # Nothing should be purged
        purge_cnt = self.central_service.purge_zones(
            self.admin_context,
            {
                'deleted_at': "<=%s" % time_threshold
            },
            limit=100,
        )
        self._assert_count_all_zones(3)
        self.assertIsNone(purge_cnt)

    @mock.patch.object(notifier.Notifier, "info")
    def test_purge_zones_by_name(self, mock_notifier):
        self.create_zone()

        # The zone is purged (even if it was not deleted)
        purge_cnt = self.central_service.purge_zones(
            self.admin_context,
            {
                'name': 'example.com.'
            },
            limit=100,
        )
        self._assert_count_all_zones(0)
        self.assertEqual(1, purge_cnt)

    @mock.patch.object(notifier.Notifier, "info")
    def test_purge_zones_without_any_criterion(self, mock_notifier):
        with testtools.ExpectedException(TypeError):
            self.central_service.purge_zones(
                self.admin_context,
                limit=100,
            )

    @mock.patch.object(notifier.Notifier, "info")
    def test_purge_zones_with_sharding(self, mock_notifier):
        old = datetime.datetime(2015, 7, 20, 0, 0)
        time_threshold = datetime.datetime(2015, 7, 25, 0, 0)
        zone = self._create_deleted_zone('old.org.', old)
        mock_notifier.reset_mock()

        # purge zones in an empty shard
        self.central_service.purge_zones(
            self.admin_context,
            {
                'deleted': '!0',
                'deleted_at': "<=%s" % time_threshold,
                'shard': 'BETWEEN 99998, 99999',
            },
            limit=100,
        )
        n_zones = self.central_service.count_zones(self.admin_context)
        self.assertEqual(1, n_zones)

        # purge zones in a shard that contains the zone created above
        self.central_service.purge_zones(
            self.admin_context,
            {
                'deleted': '!0',
                'deleted_at': "<=%s" % time_threshold,
                'shard': 'BETWEEN 0, %d' % zone.shard,
            },
            limit=100,
        )
        n_zones = self.central_service.count_zones(self.admin_context)
        self.assertEqual(0, n_zones)

    def test_purge_zones_walk_up_zones(self):
        Zone = namedtuple('Zone', 'id parent_zone_id')
        zones = [Zone(x + 1, x) for x in range(1234, 1237)]

        zones_by_id = {z.id: z for z in zones}
        sid = self.central_service.storage._walk_up_zones(
            zones[0], zones_by_id)
        self.assertEqual(1234, sid)

        sid = self.central_service.storage._walk_up_zones(
            zones[-1], zones_by_id)
        self.assertEqual(1234, sid)

    def test_purge_zones_walk_up_zones_loop(self):
        Zone = namedtuple('Zone', 'id parent_zone_id')
        zones = [Zone(2, 1), Zone(3, 2), Zone(1, 3)]
        zones_by_id = {z.id: z for z in zones}
        with testtools.ExpectedException(exceptions.IllegalParentZone):
            self.central_service.storage._walk_up_zones(
                zones[0], zones_by_id)

    @mock.patch.object(notifier.Notifier, "info")
    def test_purge_zones_with_orphans(self, mock_notifier):
        old = datetime.datetime(2015, 7, 20, 0, 0)
        time_threshold = datetime.datetime(2015, 7, 25, 0, 0)

        # Create a tree of alive and deleted [sub]zones
        z1 = self.create_zone(name='alive.org.')
        z2 = self.create_zone(name='deleted.alive.org.')
        z3 = self.create_zone(name='del2.deleted.alive.org.')
        z4 = self.create_zone(name='del3.del2.deleted.alive.org.')
        z5 = self.create_zone(name='alive2.del3.del2.deleted.alive.org.')

        self._delete_zone(z2, old)
        self._delete_zone(z3, old)
        self._delete_zone(z4, old)

        self.assertEqual(z1.id, z2['parent_zone_id'])
        self.assertEqual(z2.id, z3['parent_zone_id'])
        self.assertEqual(z3.id, z4['parent_zone_id'])
        self.assertEqual(z4.id, z5['parent_zone_id'])

        self._assert_count_all_zones(5)
        mock_notifier.reset_mock()

        zones = self._fetch_all_zones()
        self._log_all_zones(zones)
        self.central_service.purge_zones(
            self.admin_context,
            {
                'deleted': '!0',
                'deleted_at': "<=%s" % time_threshold
            },
            limit=100,
        )
        self._assert_count_all_zones(2)
        zones = self._fetch_all_zones()
        self._log_all_zones(zones)
        for z in zones:
            if z.name == 'alive.org.':
                self.assertIsNone(z.parent_zone_id)
            elif z.name == 'alive2.del3.del2.deleted.alive.org.':
                # alive2.del2.deleted.alive.org is to be reparented under
                # alive.org
                self.assertEqual(z1.id, z.parent_zone_id)
            else:
                raise Exception("Unexpected zone %r" % z)

    def test_touch_zone(self):
        # Create a zone
        expected_zone = self.create_zone()

        # Touch the zone
        self.central_service.touch_zone(
            self.admin_context, expected_zone['id'])

        # Fetch the zone again
        zone = self.central_service.get_zone(
            self.admin_context, expected_zone['id'])

        # Ensure the serial was incremented
        self.assertGreater(zone['serial'], expected_zone['serial'])

    def test_xfr_zone(self):
        # Create a zone
        fixture = self.get_zone_fixture('SECONDARY', 0)
        fixture['email'] = cfg.CONF['service:central'].managed_resource_email
        fixture['masters'] = [{"host": "10.0.0.10", "port": 53}]

        # Create a zone
        secondary = self.create_zone(**fixture)

        mdns = mock.Mock()
        with mock.patch.object(mdns_api.MdnsAPI, 'get_instance') as get_mdns:
            get_mdns.return_value = mdns
            mdns.get_serial_number.return_value = ('SUCCESS', 10, 1, )
            self.central_service.xfr_zone(self.admin_context, secondary.id)

        self.assertTrue(mdns.perform_zone_xfr.called)

    def test_xfr_zone_same_serial(self):
        # Create a zone
        fixture = self.get_zone_fixture('SECONDARY', 0)
        fixture['email'] = cfg.CONF['service:central'].managed_resource_email
        fixture['masters'] = [{"host": "10.0.0.10", "port": 53}]

        # Create a zone
        secondary = self.create_zone(**fixture)

        mdns = mock.Mock()
        with mock.patch.object(mdns_api.MdnsAPI, 'get_instance') as get_mdns:
            get_mdns.return_value = mdns
            mdns.get_serial_number.return_value = ('SUCCESS', 1, 1, )
            self.central_service.xfr_zone(self.admin_context, secondary.id)

        self.assertFalse(mdns.perform_zone_xfr.called)

    def test_xfr_zone_lower_serial(self):
        # Create a zone
        fixture = self.get_zone_fixture('SECONDARY', 0)
        fixture['email'] = cfg.CONF['service:central'].managed_resource_email
        fixture['masters'] = [{"host": "10.0.0.10", "port": 53}]
        fixture['serial'] = 10

        # Create a zone
        secondary = self.create_zone(**fixture)
        secondary.serial

        mdns = mock.Mock()
        with mock.patch.object(mdns_api.MdnsAPI, 'get_instance') as get_mdns:
            get_mdns.return_value = mdns
            mdns.get_serial_number.return_value = ('SUCCESS', 0, 1, )
            self.central_service.xfr_zone(self.admin_context, secondary.id)

        self.assertFalse(mdns.perform_zone_xfr.called)

    def test_xfr_zone_invalid_type(self):
        zone = self.create_zone()

        with testtools.ExpectedException(exceptions.BadRequest):
            self.central_service.xfr_zone(self.admin_context, zone.id)

    # RecordSet Tests
    def test_create_recordset(self):
        zone = self.create_zone()
        original_serial = zone.serial

        # Create the Object
        recordset = objects.RecordSet(name='www.%s' % zone.name, type='A')

        # Persist the Object
        recordset = self.central_service.create_recordset(
            self.admin_context, zone.id, recordset=recordset)

        # Get the zone again to check if serial increased
        updated_zone = self.central_service.get_zone(self.admin_context,
                                                     zone.id)
        new_serial = updated_zone.serial

        # Ensure all values have been set correctly
        self.assertIsNotNone(recordset.id)
        self.assertEqual('www.%s' % zone.name, recordset.name)
        self.assertEqual('A', recordset.type)

        self.assertIsNotNone(recordset.records)
        # The serial number does not get updated is there are no records
        # in the recordset
        self.assertEqual(original_serial, new_serial)

    def test_create_recordset_with_records(self):
        zone = self.create_zone()
        original_serial = zone.serial

        # Create the Object
        recordset = objects.RecordSet(
            name='www.%s' % zone.name,
            type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.3.3.15'),
                objects.Record(data='192.3.3.16'),
            ])
        )

        # Persist the Object
        recordset = self.central_service.create_recordset(
            self.admin_context, zone.id, recordset=recordset)

        # Get updated serial number
        updated_zone = self.central_service.get_zone(self.admin_context,
                                                     zone.id)
        new_serial = updated_zone.serial

        # Ensure all values have been set correctly
        self.assertIsNotNone(recordset.records)
        self.assertEqual(2, len(recordset.records))
        self.assertIsNotNone(recordset.records[0].id)
        self.assertIsNotNone(recordset.records[1].id)
        self.assertThat(new_serial, GreaterThan(original_serial))

    def test_create_recordset_over_quota(self):
        # SOA, NS recordsets exist by default.
        self.config(quota_zone_recordsets=3)

        zone = self.create_zone()

        self.create_recordset(zone)

        with testtools.ExpectedException(exceptions.OverQuota):
            self.create_recordset(zone)

    def test_create_invalid_recordset_location_cname_at_apex(self):
        zone = self.create_zone()

        values = dict(
            name=zone['name'],
            type='CNAME'
        )

        # Attempt to create a CNAME record at the apex
        with testtools.ExpectedException(exceptions.InvalidRecordSetLocation):
            self.central_service.create_recordset(
                self.admin_context,
                zone['id'],
                recordset=objects.RecordSet.from_dict(values))

    def test_create_invalid_recordset_location_cname_sharing(self):
        zone = self.create_zone()
        expected = self.create_recordset(zone)

        values = dict(
            name=expected['name'],
            type='CNAME'
        )

        # Attempt to create a CNAME record alongside another record
        with testtools.ExpectedException(exceptions.InvalidRecordSetLocation):
            self.central_service.create_recordset(
                self.admin_context,
                zone['id'],
                recordset=objects.RecordSet.from_dict(values))

    def test_create_invalid_recordset_location_wrong_zone(self):
        zone = self.create_zone()
        other_zone = self.create_zone(fixture=1)

        values = dict(
            name=other_zone['name'],
            type='A'
        )

        # Attempt to create a record in the incorrect zone
        with testtools.ExpectedException(exceptions.InvalidRecordSetLocation):
            self.central_service.create_recordset(
                self.admin_context,
                zone['id'],
                recordset=objects.RecordSet.from_dict(values))

    def test_create_invalid_recordset_ttl(self):
        self.policy({'use_low_ttl': '!'})
        self.config(min_ttl=100,
                    group='service:central')
        zone = self.create_zone()

        values = dict(
            name='www.%s' % zone['name'],
            type='A',
            ttl=10
        )

        # Attempt to create a A record under the TTL
        with testtools.ExpectedException(exceptions.InvalidTTL):
            self.central_service.create_recordset(
                self.admin_context,
                zone['id'],
                recordset=objects.RecordSet.from_dict(values))

    def test_create_recordset_no_min_ttl(self):
        self.policy({'use_low_ttl': '!'})
        self.config(min_ttl=None,
                    group='service:central')
        zone = self.create_zone()

        values = dict(
            name='www.%s' % zone['name'],
            type='A',
            ttl=10
        )

        recordset = self.central_service.create_recordset(
            self.admin_context,
            zone['id'],
            recordset=objects.RecordSet.from_dict(values))
        self.assertEqual(values['ttl'], recordset['ttl'])

    def test_get_recordset(self):
        zone = self.create_zone()

        # Create a recordset
        expected = self.create_recordset(zone)

        # Retrieve it, and ensure it's the same
        recordset = self.central_service.get_recordset(
            self.admin_context, zone['id'], expected['id'])

        self.assertEqual(expected['id'], recordset['id'])
        self.assertEqual(expected['name'], recordset['name'])
        self.assertEqual(expected['type'], recordset['type'])

    def test_get_recordset_with_records(self):
        zone = self.create_zone()

        # Create a recordset and two records
        recordset = self.create_recordset(zone)
        self.create_record(zone, recordset)
        self.create_record(zone, recordset, fixture=1)

        # Retrieve it, and ensure it's the same
        recordset = self.central_service.get_recordset(
            self.admin_context, zone.id, recordset.id)

        self.assertEqual(2, len(recordset.records))
        self.assertIsNotNone(recordset.records[0].id)
        self.assertIsNotNone(recordset.records[1].id)

    def test_get_recordset_incorrect_zone_id(self):
        zone = self.create_zone()
        other_zone = self.create_zone(fixture=1)

        # Create a recordset
        expected = self.create_recordset(zone)

        # Ensure we get a 404 if we use the incorrect zone_id
        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            self.central_service.get_recordset(
                self.admin_context, other_zone['id'], expected['id'])

    def test_find_recordsets(self):
        zone = self.create_zone()

        criterion = {'zone_id': zone['id']}

        # Ensure we have two recordsets to start with as SOA & NS
        # recordsets are created automatically
        recordsets = self.central_service.find_recordsets(
            self.admin_context, criterion)

        self.assertEqual(2, len(recordsets))

        # Create a single recordset (using default values)
        self.create_recordset(zone, name='www.%s' % zone['name'])

        # Ensure we can retrieve the newly created recordset
        recordsets = self.central_service.find_recordsets(
            self.admin_context, criterion)

        self.assertEqual(3, len(recordsets))
        self.assertEqual('www.%s' % zone['name'], recordsets[2]['name'])

        # Create a second recordset
        self.create_recordset(zone, name='mail.%s' % zone['name'])

        # Ensure we can retrieve both recordsets
        recordsets = self.central_service.find_recordsets(
            self.admin_context, criterion)

        self.assertEqual(4, len(recordsets))
        self.assertEqual('www.%s' % zone['name'], recordsets[2]['name'])
        self.assertEqual('mail.%s' % zone['name'], recordsets[3]['name'])

    def test_find_recordset(self):
        zone = self.create_zone()

        # Create a recordset
        expected = self.create_recordset(zone)

        # Retrieve it, and ensure it's the same
        criterion = {'zone_id': zone['id'], 'name': expected['name']}

        recordset = self.central_service.find_recordset(
            self.admin_context, criterion)

        self.assertEqual(expected['id'], recordset['id'], expected['id'])
        self.assertEqual(expected['name'], recordset['name'])

    def test_find_recordset_with_records(self):
        zone = self.create_zone()

        # Create a recordset
        recordset = self.create_recordset(zone)
        self.create_record(zone, recordset)
        self.create_record(zone, recordset, fixture=1)

        # Retrieve it, and ensure it's the same
        criterion = {'zone_id': zone.id, 'name': recordset.name}

        recordset = self.central_service.find_recordset(
            self.admin_context, criterion)

        self.assertEqual(2, len(recordset.records))
        self.assertIsNotNone(recordset.records[0].id)
        self.assertIsNotNone(recordset.records[1].id)

    def test_update_recordset(self):
        # Create a zone
        zone = self.create_zone()
        original_serial = zone.serial

        # Create a recordset
        recordset = self.create_recordset(zone)

        # Update the recordset
        recordset.ttl = 1800

        # Perform the update
        self.central_service.update_recordset(self.admin_context, recordset)

        # Get zone again to verify that serial number was updated
        updated_zone = self.central_service.get_zone(self.admin_context,
                                                     zone.id)
        new_serial = updated_zone.serial

        # Fetch the resource again
        recordset = self.central_service.get_recordset(
            self.admin_context, recordset.zone_id, recordset.id)

        # Ensure the new value took
        self.assertEqual(1800, recordset.ttl)
        self.assertThat(new_serial, GreaterThan(original_serial))

    def test_update_recordset_deadlock_retry(self):
        # Create a zone
        zone = self.create_zone()

        # Create a recordset
        recordset = self.create_recordset(zone)

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
        # Create a zone
        zone = self.create_zone()

        # Create a recordset
        recordset = self.create_recordset(zone)

        # Append two new Records
        recordset.records.append(objects.Record(data='192.0.2.1'))
        recordset.records.append(objects.Record(data='192.0.2.2'))

        # Perform the update
        self.central_service.update_recordset(self.admin_context, recordset)

        # Fetch the RecordSet again
        recordset = self.central_service.get_recordset(
            self.admin_context, zone.id, recordset.id)

        # Ensure two Records are attached to the RecordSet correctly
        self.assertEqual(2, len(recordset.records))
        self.assertIsNotNone(recordset.records[0].id)
        self.assertIsNotNone(recordset.records[1].id)

    def test_update_recordset_with_record_delete(self):
        # Create a zone
        zone = self.create_zone()
        original_serial = zone.serial

        # Create a recordset and two records
        recordset = self.create_recordset(zone)
        self.create_record(zone, recordset)
        self.create_record(zone, recordset, fixture=1)

        # Append two new Records
        recordset.records.append(objects.Record(data='192.0.2.1'))
        recordset.records.append(objects.Record(data='192.0.2.2'))

        # Remove one of the Records
        recordset.records.pop(0)

        # Perform the update
        self.central_service.update_recordset(self.admin_context, recordset)

        # Fetch the RecordSet again
        recordset = self.central_service.get_recordset(
            self.admin_context, zone.id, recordset.id)

        # Fetch the Zone again
        updated_zone = self.central_service.get_zone(self.admin_context,
                                                     zone.id)
        new_serial = updated_zone.serial

        # Ensure two Records are attached to the RecordSet correctly
        self.assertEqual(1, len(recordset.records))
        self.assertIsNotNone(recordset.records[0].id)
        self.assertThat(new_serial, GreaterThan(original_serial))

    def test_update_recordset_with_record_update(self):
        # Create a zone
        zone = self.create_zone()

        # Create a recordset and two records
        recordset = self.create_recordset(zone, 'A')
        self.create_record(zone, recordset)
        self.create_record(zone, recordset, fixture=1)

        # Fetch the RecordSet again
        recordset = self.central_service.get_recordset(
            self.admin_context, zone.id, recordset.id)

        # Update one of the Records
        updated_record_id = recordset.records[0].id
        recordset.records[0].data = '192.0.2.255'

        # Perform the update
        self.central_service.update_recordset(self.admin_context, recordset)

        # Fetch the RecordSet again
        recordset = self.central_service.get_recordset(
            self.admin_context, zone.id, recordset.id)

        # Ensure the Record has been updated
        for record in recordset.records:
            if record.id != updated_record_id:
                continue

            self.assertEqual('192.0.2.255', record.data)
            return  # Exits this test early as we succeeded

        raise Exception('Updated record not found')

    def test_update_recordset_without_incrementing_serial(self):
        zone = self.create_zone()

        # Create a recordset
        recordset = self.create_recordset(zone)

        # Fetch the zone so we have the latest serial number
        zone_before = self.central_service.get_zone(
            self.admin_context, zone.id)

        # Update the recordset
        recordset.ttl = 1800

        # Perform the update
        self.central_service.update_recordset(
            self.admin_context, recordset, increment_serial=False)

        # Fetch the resource again
        recordset = self.central_service.get_recordset(
            self.admin_context, recordset.zone_id, recordset.id)

        # Ensure the recordset was updated correctly
        self.assertEqual(1800, recordset.ttl)

        # Ensure the zones serial number was not updated
        zone_after = self.central_service.get_zone(
            self.admin_context, zone.id)

        self.assertEqual(zone_before.serial, zone_after.serial)

    def test_update_recordset_immutable_zone_id(self):
        zone = self.create_zone()
        other_zone = self.create_zone(fixture=1)

        # Create a recordset
        recordset = self.create_recordset(zone)

        # Update the recordset
        recordset.ttl = 1800
        recordset.zone_id = other_zone.id

        # Ensure we get a BadRequest if we change the zone_id
        with testtools.ExpectedException(exceptions.BadRequest):
            self.central_service.update_recordset(
                self.admin_context, recordset)

    def test_update_recordset_immutable_tenant_id(self):
        zone = self.create_zone()

        # Create a recordset
        recordset = self.create_recordset(zone)

        # Update the recordset
        recordset.ttl = 1800
        recordset.tenant_id = 'other-tenant'

        # Ensure we get a BadRequest if we change the zone_id
        with testtools.ExpectedException(exceptions.BadRequest):
            self.central_service.update_recordset(
                self.admin_context, recordset)

    def test_update_recordset_immutable_type(self):
        zone = self.create_zone()

        # Create a recordset
        recordset = self.create_recordset(zone)
        cname_recordset = self.create_recordset(zone, type='CNAME')

        # Update the recordset
        recordset.ttl = 1800
        recordset.type = cname_recordset.type

        # Ensure we get a BadRequest if we change the zone_id
        with testtools.ExpectedException(exceptions.BadRequest):
            self.central_service.update_recordset(
                self.admin_context, recordset)

    def test_delete_recordset(self):
        zone = self.create_zone()
        original_serial = zone.serial

        # Create a recordset
        recordset = self.create_recordset(zone)

        # Delete the recordset
        self.central_service.delete_recordset(
            self.admin_context, zone['id'], recordset['id'])

        # Fetch the recordset again, ensuring an exception is raised
        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            self.central_service.get_recordset(
                self.admin_context, zone['id'], recordset['id'])

        # Fetch the zone again to verify serial number increased
        updated_zone = self.central_service.get_zone(self.admin_context,
                                                     zone.id)
        new_serial = updated_zone.serial
        self.assertThat(new_serial, GreaterThan(original_serial))

    def test_delete_recordset_without_incrementing_serial(self):
        zone = self.create_zone()

        # Create a recordset
        recordset = self.create_recordset(zone)

        # Fetch the zone so we have the latest serial number
        zone_before = self.central_service.get_zone(
            self.admin_context, zone['id'])

        # Delete the recordset
        self.central_service.delete_recordset(
            self.admin_context, zone['id'], recordset['id'],
            increment_serial=False)

        # Fetch the record again, ensuring an exception is raised
        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            self.central_service.get_recordset(
                self.admin_context, zone['id'], recordset['id'])

        # Ensure the zones serial number was not updated
        zone_after = self.central_service.get_zone(
            self.admin_context, zone['id'])

        self.assertEqual(zone_before['serial'], zone_after['serial'])

    def test_delete_recordset_incorrect_zone_id(self):
        zone = self.create_zone()
        other_zone = self.create_zone(fixture=1)

        # Create a recordset
        recordset = self.create_recordset(zone)

        # Ensure we get a 404 if we use the incorrect zone_id
        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            self.central_service.delete_recordset(
                self.admin_context, other_zone['id'], recordset['id'])

    def test_count_recordsets(self):
        # in the beginning, there should be nothing
        recordsets = self.central_service.count_recordsets(self.admin_context)
        self.assertEqual(0, recordsets)

        # Create a zone to put our recordset in
        zone = self.create_zone()

        # Create a recordset
        self.create_recordset(zone)

        # We should have 1 recordset now, plus SOA & NS recordsets
        recordsets = self.central_service.count_recordsets(self.admin_context)
        self.assertEqual(3, recordsets)

    def test_count_recordsets_policy_check(self):
        # Set the policy to reject the authz
        self.policy({'count_recordsets': '!'})

        with testtools.ExpectedException(exceptions.Forbidden):
            self.central_service.count_recordsets(self.get_context())

    # Record Tests
    def test_create_record(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone, type='A')

        values = dict(
            data='127.0.0.1'
        )

        # Create a record
        record = self.central_service.create_record(
            self.admin_context, zone['id'], recordset['id'],
            objects.Record.from_dict(values))

        # Ensure all values have been set correctly
        self.assertIsNotNone(record['id'])
        self.assertEqual(values['data'], record['data'])
        self.assertIn('status', record)

    def test_create_record_and_update_over_zone_quota(self):
        # SOA and NS Records exist
        self.config(quota_zone_records=1)

        # Creating the zone automatically creates SOA & NS records
        zone = self.create_zone()
        recordset = self.create_recordset(zone)

        self.create_record(zone, recordset)

        with testtools.ExpectedException(exceptions.OverQuota):
            self.create_record(zone, recordset)

    def test_create_record_over_zone_quota(self):
        self.config(quota_zone_records=1)

        # Creating the zone automatically creates SOA & NS records
        zone = self.create_zone()

        recordset = objects.RecordSet(
            name='www.%s' % zone.name,
            type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.3.3.15'),
                objects.Record(data='192.3.3.16'),
            ])
        )

        with testtools.ExpectedException(exceptions.OverQuota):
            # Persist the Object
            recordset = self.central_service.create_recordset(
                self.admin_context, zone.id, recordset=recordset)

    def test_create_record_over_recordset_quota(self):
        self.config(quota_recordset_records=1)

        # Creating the zone automatically creates SOA & NS records
        zone = self.create_zone()
        recordset = self.create_recordset(zone)

        self.create_record(zone, recordset)

        with testtools.ExpectedException(exceptions.OverQuota):
            self.create_record(zone, recordset)

    def test_create_record_without_incrementing_serial(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone, type='A')

        values = dict(
            data='127.0.0.1'
        )

        # Create a record
        self.central_service.create_record(
            self.admin_context, zone['id'], recordset['id'],
            objects.Record.from_dict(values),
            increment_serial=False)

        # Ensure the zones serial number was not updated
        updated_zone = self.central_service.get_zone(
            self.admin_context, zone['id'])

        self.assertEqual(zone['serial'], updated_zone['serial'])

    def test_get_record(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)

        # Create a record
        expected = self.create_record(zone, recordset)

        # Retrieve it, and ensure it's the same
        record = self.central_service.get_record(
            self.admin_context, zone['id'], recordset['id'], expected['id'])

        self.assertEqual(expected['id'], record['id'])
        self.assertEqual(expected['data'], record['data'])
        self.assertIn('status', record)

    def test_get_record_incorrect_zone_id(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)
        other_zone = self.create_zone(fixture=1)

        # Create a record
        expected = self.create_record(zone, recordset)

        # Ensure we get a 404 if we use the incorrect zone_id
        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.central_service.get_record(
                self.admin_context, other_zone['id'], recordset['id'],
                expected['id'])

    def test_get_record_incorrect_recordset_id(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)
        other_recordset = self.create_recordset(zone, fixture=1)

        # Create a record
        expected = self.create_record(zone, recordset)

        # Ensure we get a 404 if we use the incorrect recordset_id
        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.central_service.get_record(
                self.admin_context, zone['id'], other_recordset['id'],
                expected['id'])

    def test_find_records(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)

        criterion = {
            'zone_id': zone['id'],
            'recordset_id': recordset['id']
        }

        # Ensure we have no records to start with.
        records = self.central_service.find_records(
            self.admin_context, criterion)

        self.assertEqual(0, len(records))

        # Create a single record (using default values)
        expected_one = self.create_record(zone, recordset)

        # Ensure we can retrieve the newly created record
        records = self.central_service.find_records(
            self.admin_context, criterion)

        self.assertEqual(1, len(records))
        self.assertEqual(expected_one['data'], records[0]['data'])

        # Create a second record
        expected_two = self.create_record(zone, recordset, fixture=1)

        # Ensure we can retrieve both records
        records = self.central_service.find_records(
            self.admin_context, criterion)

        self.assertEqual(2, len(records))
        self.assertEqual(expected_one['data'], records[0]['data'])
        self.assertEqual(expected_two['data'], records[1]['data'])

    def test_find_record(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)

        # Create a record
        expected = self.create_record(zone, recordset)

        # Retrieve it, and ensure it's the same
        criterion = {
            'zone_id': zone['id'],
            'recordset_id': recordset['id'],
            'data': expected['data']
        }

        record = self.central_service.find_record(
            self.admin_context, criterion)

        self.assertEqual(expected['id'], record['id'])
        self.assertEqual(expected['data'], record['data'])
        self.assertIn('status', record)

    def test_update_record(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone, 'A')

        # Create a record
        record = self.create_record(zone, recordset)

        # Update the Object
        record.data = '192.0.2.255'

        # Perform the update
        self.central_service.update_record(self.admin_context, record)

        # Fetch the resource again
        record = self.central_service.get_record(
            self.admin_context, record.zone_id, record.recordset_id,
            record.id)

        # Ensure the new value took
        self.assertEqual('192.0.2.255', record.data)

    def test_update_record_without_incrementing_serial(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone, 'A')

        # Create a record
        record = self.create_record(zone, recordset)

        # Fetch the zone so we have the latest serial number
        zone_before = self.central_service.get_zone(
            self.admin_context, zone.id)

        # Update the Object
        record.data = '192.0.2.255'

        # Perform the update
        self.central_service.update_record(
            self.admin_context, record, increment_serial=False)

        # Fetch the resource again
        record = self.central_service.get_record(
            self.admin_context, record.zone_id, record.recordset_id,
            record.id)

        # Ensure the new value took
        self.assertEqual('192.0.2.255', record.data)

        # Ensure the zones serial number was not updated
        zone_after = self.central_service.get_zone(
            self.admin_context, zone.id)

        self.assertEqual(zone_before.serial, zone_after.serial)

    def test_update_record_immutable_zone_id(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)
        other_zone = self.create_zone(fixture=1)

        # Create a record
        record = self.create_record(zone, recordset)

        # Update the record
        record.zone_id = other_zone.id

        # Ensure we get a BadRequest if we change the zone_id
        with testtools.ExpectedException(exceptions.BadRequest):
            self.central_service.update_record(self.admin_context, record)

    def test_update_record_immutable_recordset_id(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)
        other_recordset = self.create_recordset(zone, fixture=1)

        # Create a record
        record = self.create_record(zone, recordset)

        # Update the record
        record.recordset_id = other_recordset.id

        # Ensure we get a BadRequest if we change the recordset_id
        with testtools.ExpectedException(exceptions.BadRequest):
            self.central_service.update_record(self.admin_context, record)

    def test_delete_record(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)

        # Create a record
        record = self.create_record(zone, recordset)

        # Fetch the zone serial number
        zone_serial = self.central_service.get_zone(
            self.admin_context, zone['id']).serial

        # Delete the record
        self.central_service.delete_record(
            self.admin_context, zone['id'], recordset['id'], record['id'])

        # Ensure the zone serial number was updated
        new_zone_serial = self.central_service.get_zone(
            self.admin_context, zone['id']).serial
        self.assertNotEqual(new_zone_serial, zone_serial)

        # Fetch the record
        deleted_record = self.central_service.get_record(
            self.admin_context, zone['id'], recordset['id'],
            record['id'])

        # Ensure the record is marked for deletion
        self.assertEqual(record.id, deleted_record.id)
        self.assertEqual(record.data, deleted_record.data)
        self.assertEqual(record.zone_id, deleted_record.zone_id)
        self.assertEqual('PENDING', deleted_record.status)
        self.assertEqual(record.tenant_id, deleted_record.tenant_id)
        self.assertEqual(record.recordset_id, deleted_record.recordset_id)
        self.assertEqual('DELETE', deleted_record.action)
        self.assertEqual(new_zone_serial, deleted_record.serial)

    def test_delete_record_without_incrementing_serial(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)

        # Create a record
        record = self.create_record(zone, recordset)

        # Fetch the zone serial number
        zone_serial = self.central_service.get_zone(
            self.admin_context, zone['id']).serial

        # Delete the record
        self.central_service.delete_record(
            self.admin_context, zone['id'], recordset['id'], record['id'],
            increment_serial=False)

        # Ensure the zones serial number was not updated
        new_zone_serial = self.central_service.get_zone(
            self.admin_context, zone['id'])['serial']
        self.assertEqual(zone_serial, new_zone_serial)

        # Fetch the record
        deleted_record = self.central_service.get_record(
            self.admin_context, zone['id'], recordset['id'],
            record['id'])

        # Ensure the record is marked for deletion
        self.assertEqual(record.id, deleted_record.id)
        self.assertEqual(record.data, deleted_record.data)
        self.assertEqual(record.zone_id, deleted_record.zone_id)
        self.assertEqual('PENDING', deleted_record.status)
        self.assertEqual(record.tenant_id, deleted_record.tenant_id)
        self.assertEqual(record.recordset_id, deleted_record.recordset_id)
        self.assertEqual('DELETE', deleted_record.action)
        self.assertEqual(new_zone_serial, deleted_record.serial)

    def test_delete_record_incorrect_zone_id(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)
        other_zone = self.create_zone(fixture=1)

        # Create a record
        record = self.create_record(zone, recordset)

        # Ensure we get a 404 if we use the incorrect zone_id
        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.central_service.delete_record(
                self.admin_context, other_zone['id'], recordset['id'],
                record['id'])

    def test_delete_record_incorrect_recordset_id(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)
        other_recordset = self.create_recordset(zone, fixture=1)

        # Create a record
        record = self.create_record(zone, recordset)

        # Ensure we get a 404 if we use the incorrect recordset_id
        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.central_service.delete_record(
                self.admin_context, zone['id'], other_recordset['id'],
                record['id'])

    def test_count_records(self):
        # in the beginning, there should be nothing
        records = self.central_service.count_records(self.admin_context)
        self.assertEqual(0, records)

        # Create a zone and recordset to put our record in
        zone = self.create_zone()
        recordset = self.create_recordset(zone)

        # Create a record
        self.create_record(zone, recordset)

        # we should have 1 record now, plus SOA & NS records
        records = self.central_service.count_records(self.admin_context)
        self.assertEqual(3, records)

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
        self.assertIsNone(fip_ptr['ptrdname'])

    def test_get_floatingip_dual_no_record(self):
        context = self.get_context(tenant='a')

        self.network_api.fake.allocate_floatingip(context.tenant)
        fip = self.network_api.fake.allocate_floatingip(context.tenant)

        fip_ptr = self.central_service.get_floatingip(
            context, fip['region'], fip['id'])

        self.assertEqual(fip['region'], fip_ptr['region'])
        self.assertEqual(fip['id'], fip_ptr['id'])
        self.assertEqual(fip['address'], fip_ptr['address'])
        self.assertIsNone(fip_ptr['ptrdname'])

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
        zone_id = self.central_service.find_record(
            elevated_a, criterion).zone_id

        # Simulate the update on the backend
        zone_serial = self.central_service.get_zone(
            elevated_a, zone_id).serial
        self.central_service.update_status(
            elevated_a, zone_id, "SUCCESS", zone_serial)

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
        self.assertIsNone(fip_ptr['ptrdname'])

        # Simulate the invalidation on the backend
        zone_serial = self.central_service.get_zone(
            elevated_a, zone_id).serial
        self.central_service.update_status(
            elevated_a, zone_id, "SUCCESS", zone_serial)

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
        self.assertIsNone(fips[0]['ptrdname'])
        self.assertEqual(fip['id'], fips[0]['id'])
        self.assertEqual(fip['region'], fips[0]['region'])
        self.assertEqual(fip['address'], fips[0]['address'])
        self.assertIsNone(fips[0]['description'])

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
        zone_id = self.central_service.find_record(
            elevated_a, criterion).zone_id

        # Simulate the update on the backend
        zone_serial = self.central_service.get_zone(
            elevated_a, zone_id).serial
        self.central_service.update_status(
            elevated_a, zone_id, "SUCCESS", zone_serial)

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
        self.assertIsNone(fips[0]['ptrdname'])

        # Simulate the invalidation on the backend
        zone_serial = self.central_service.get_zone(
            elevated_a, zone_id).serial
        self.central_service.update_status(
            elevated_a, zone_id, "SUCCESS", zone_serial)

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
        self.assertIsNone(fip_ptr['description'])
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

        # The zone created should have the default 0's uuid as owner
        zone = self.central_service.find_zone(
            elevated_context,
            {"tenant_id": tenant_id})
        self.assertEqual(tenant_id, zone.tenant_id)

    def test_set_floatingip_removes_old_record(self):
        context_a = self.get_context(tenant='a')
        elevated_a = context_a.elevated()
        elevated_a.all_tenants = True

        context_b = self.get_context(tenant='b')

        fixture = self.get_ptr_fixture()

        # Test that re-setting as tenant 'a' an already set floatingip leaves
        # only 1 record
        fip = self.network_api.fake.allocate_floatingip(context_a.tenant)

        self.central_service.update_floatingip(
            context_a, fip['region'], fip['id'], fixture)

        criterion = {
            'managed_resource_id': fip['id'],
            'managed_tenant_id': context_a.tenant}
        zone_id = self.central_service.find_record(
            elevated_a, criterion).zone_id

        fixture2 = self.get_ptr_fixture(fixture=1)
        self.central_service.update_floatingip(
            context_a, fip['region'], fip['id'], fixture2)

        # Simulate the update on the backend
        zone_serial = self.central_service.get_zone(
            elevated_a, zone_id).serial
        self.central_service.update_status(
            elevated_a, zone_id, "SUCCESS", zone_serial)

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
        zone_serial = self.central_service.get_zone(
            elevated_a, zone_id).serial
        self.central_service.update_status(
            elevated_a, zone_id, "SUCCESS", zone_serial)

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
        self.assertIsNone(fip_ptr['description'])
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
        self.assertEqual(values['pattern'], blacklist['pattern'])
        self.assertEqual(values['description'], blacklist['description'])

    def test_get_blacklist(self):
        # Create a blacklisted zone
        expected = self.create_blacklist(fixture=0)

        # Retrieve it, and verify it is the same
        blacklist = self.central_service.get_blacklist(
            self.admin_context, expected['id'])

        self.assertEqual(expected['id'], blacklist['id'])
        self.assertEqual(expected['pattern'], blacklist['pattern'])
        self.assertEqual(expected['description'], blacklist['description'])

    def test_find_blacklists(self):
        # Verify there are no blacklisted zones to start with
        blacklists = self.central_service.find_blacklists(
            self.admin_context)

        self.assertEqual(0, len(blacklists))

        # Create a single blacklisted zone
        self.create_blacklist()

        # Verify we can retrieve the newly created blacklist
        blacklists = self.central_service.find_blacklists(
            self.admin_context)
        values1 = self.get_blacklist_fixture(fixture=0)

        self.assertEqual(1, len(blacklists))
        self.assertEqual(values1['pattern'], blacklists[0]['pattern'])

        # Create a second blacklisted zone
        self.create_blacklist(fixture=1)

        # Verify we can retrieve both blacklisted zones
        blacklists = self.central_service.find_blacklists(
            self.admin_context)

        values2 = self.get_blacklist_fixture(fixture=1)

        self.assertEqual(2, len(blacklists))
        self.assertEqual(values1['pattern'], blacklists[0]['pattern'])
        self.assertEqual(values2['pattern'], blacklists[1]['pattern'])

    def test_find_blacklist(self):
        # Create a blacklisted zone
        expected = self.create_blacklist(fixture=0)

        # Retrieve the newly created blacklist
        blacklist = self.central_service.find_blacklist(
            self.admin_context, {'id': expected['id']})

        self.assertEqual(expected['pattern'], blacklist['pattern'])
        self.assertEqual(expected['description'], blacklist['description'])

    def test_update_blacklist(self):
        # Create a blacklisted zone
        blacklist = self.create_blacklist(fixture=0)

        # Update the Object
        blacklist.description = u"New Comment"

        # Perform the update
        self.central_service.update_blacklist(self.admin_context, blacklist)

        # Fetch the resource again
        blacklist = self.central_service.get_blacklist(self.admin_context,
                                                       blacklist.id)

        # Verify that the record was updated correctly
        self.assertEqual(u"New Comment", blacklist.description)

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
        zone = self.create_zone(name='example3.org.')

        # Retrieve SOA
        criterion = {'zone_id': zone['id'], 'type': 'SOA'}

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
        self.assertEqual(zone['serial'], int(soa_record_values[2]))
        self.assertEqual(zone_email, soa_record_values[1])
        self.assertEqual(zone['refresh'], int(soa_record_values[3]))
        self.assertEqual(zone['retry'], int(soa_record_values[4]))
        self.assertEqual(zone['expire'], int(soa_record_values[5]))
        self.assertEqual(zone['minimum'], int(soa_record_values[6]))

    def test_update_soa(self):
        # Anytime the zone's serial number is incremented
        # the SOA recordset should automatically be updated
        zone = self.create_zone(email='info@example.org')

        # Update the object
        zone.email = 'info@example.net'

        # Perform the update
        self.central_service.update_zone(self.admin_context, zone)

        # Fetch the zone again
        updated_zone = self.central_service.get_zone(self.admin_context,
                                                     zone.id)

        # Retrieve SOA
        criterion = {'zone_id': zone['id'], 'type': 'SOA'}

        soa = self.central_service.find_recordset(self.admin_context,
                                                  criterion)

        # Split out the various soa values
        soa_record_values = soa.records[0].data.split()

        self.assertEqual(updated_zone['serial'], int(soa_record_values[2]))

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

        self.assertEqual(values['name'], pool['name'])

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

        self.assertEqual(expected['id'], pool['id'])
        self.assertEqual(expected['created_at'], pool['created_at'])
        self.assertEqual(expected['version'], pool['version'])
        self.assertEqual(expected['tenant_id'], pool['tenant_id'])
        self.assertEqual(expected['name'], pool['name'])

        # Compare the actual values of attributes and ns_records
        for k in range(0, len(expected['attributes'])):
            self.assertEqual(
                expected['attributes'][k].to_primitive()
                ['designate_object.data'],
                pool['attributes'][k].to_primitive()['designate_object.data'])

        for k in range(0, len(expected['ns_records'])):
            self.assertEqual(
                expected['ns_records'][k].to_primitive()
                ['designate_object.data'],
                pool['ns_records'][k].to_primitive()['designate_object.data'])

    def test_find_pools(self):
        # Verify no pools exist, except for default pool
        pools = self.central_service.find_pools(self.admin_context)

        self.assertEqual(1, len(pools))

        # Create a pool
        self.create_pool(fixture=0)

        # Verify we can find the newly created pool
        pools = self.central_service.find_pools(self.admin_context)
        values = self.get_pool_fixture(fixture=0)

        self.assertEqual(2, len(pools))
        self.assertEqual(values['name'], pools[1]['name'])

        # Compare the actual values of attributes and ns_records
        expected_attributes = values['attributes'][0]
        actual_attributes = \
            pools[1]['attributes'][0].to_primitive()['designate_object.data']
        for k in expected_attributes:
            self.assertEqual(expected_attributes[k], actual_attributes[k])

        expected_ns_records = values['ns_records'][0]
        actual_ns_records = \
            pools[1]['ns_records'][0].to_primitive()['designate_object.data']
        for k in expected_ns_records:
            self.assertEqual(expected_ns_records[k], actual_ns_records[k])

    def test_find_pool(self):
        # Create a server pool
        expected = self.create_pool(fixture=0)

        # Find the created pool
        pool = self.central_service.find_pool(self.admin_context,
                                              {'id': expected['id']})

        self.assertEqual(expected['name'], pool['name'])

        # Compare the actual values of attributes and ns_records
        for k in range(0, len(expected['attributes'])):
            self.assertEqual(
                expected['attributes'][k].to_primitive()
                ['designate_object.data'],
                pool['attributes'][k].to_primitive()['designate_object.data'])

        for k in range(0, len(expected['ns_records'])):
            self.assertEqual(
                expected['ns_records'][k].to_primitive()
                ['designate_object.data'],
                pool['ns_records'][k].to_primitive()['designate_object.data'])

    def test_update_pool(self):
        # Create a server pool
        pool = self.create_pool(fixture=0)

        # Update and save the pool
        pool.description = u'New Comment'
        self.central_service.update_pool(self.admin_context, pool)

        # Fetch the pool
        pool = self.central_service.get_pool(self.admin_context, pool.id)

        # Verify that the pool was updated correctly
        self.assertEqual(u"New Comment", pool.description)

    def test_update_pool_add_ns_record(self):
        # Create a server pool and 3 zones
        pool = self.create_pool(fixture=0)
        zone = self.create_zone(
            attributes=[{'key': 'pool_id', 'value': pool.id}])
        self.create_zone(
            fixture=1,
            attributes=[{'key': 'pool_id', 'value': pool.id}])
        self.create_zone(
            fixture=2,
            attributes=[{'key': 'pool_id', 'value': pool.id}])

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

        # Fetch the zones NS recordset
        ns_recordset = self.central_service.find_recordset(
            self.admin_context,
            criterion={'zone_id': zone.id, 'type': "NS"})

        # Verify that the doamins NS records were updated correctly
        self.assertEqual(set([n.hostname for n in pool.ns_records]),
                         set([n.data for n in ns_recordset.records]))

        # Verify that the 3 zones are in the database and that
        # the delayed_notify flag is set
        zones = self._fetch_all_zones()
        self.assertEqual(3, len(zones))
        for z in zones:
            self.assertTrue(z.delayed_notify)

    def test_update_pool_add_ns_record_without_priority(self):
        pool = self.create_pool(fixture=0)
        self.create_zone(pool_id=pool.id)
        new_ns_record = objects.PoolNsRecord(hostname='ns-new.example.org.')
        pool.ns_records.append(new_ns_record)
        # PoolNsRecord without "priority" triggers a DB exception
        with testtools.ExpectedException(db_exception.DBError):
            self.central_service.update_pool(self.admin_context, pool)

    def test_update_pool_remove_ns_record(self):
        # Create a server pool and zone
        pool = self.create_pool(fixture=0)
        zone = self.create_zone(
            attributes=[{'key': 'pool_id', 'value': pool.id}])

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

        # Fetch the zones NS recordset
        ns_recordset = self.central_service.find_recordset(
            self.admin_context,
            criterion={'zone_id': zone.id, 'type': "NS"})

        # Verify that the doamins NS records ware updated correctly
        self.assertEqual(set([n.hostname for n in pool.ns_records]),
                         set([n.data for n in ns_recordset.records]))

        zones = self._fetch_all_zones()
        self.assertEqual(1, len(zones))
        self.assertTrue(zones[0].delayed_notify)

    def test_delete_pool(self):
        # Create a server pool
        pool = self.create_pool()

        # Delete the pool
        self.central_service.delete_pool(self.admin_context, pool['id'])

        # Verify that the pool has been deleted
        with testtools.ExpectedException(exceptions.PoolNotFound):
            self.central_service.get_pool(self.admin_context, pool['id'])

    def test_update_status_delete_zone(self):
        # Create a zone
        zone = self.create_zone()

        # Delete the zone (flag it for purging)
        self.central_service.delete_zone(self.admin_context, zone['id'])

        # The domain should be still there, albeit flagged for purging
        self.central_service.get_zone(self.admin_context, zone['id'])

        zones = self.central_service.find_zones(self.admin_context)
        self.assertEqual(1, len(zones))

        # Simulate the zone having been deleted on the backend
        zone_serial = self.central_service.get_zone(
            self.admin_context, zone['id']).serial

        self.central_service.update_status(
            self.admin_context, zone['id'], "SUCCESS", zone_serial)

        # Fetch the zone again, ensuring an exception is raised
        with testtools.ExpectedException(exceptions.ZoneNotFound):
            self.central_service.get_zone(self.admin_context, zone['id'])

    def test_update_status_delete_last_record(self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)

        # Create a record
        record = self.create_record(zone, recordset)

        # Delete the record
        self.central_service.delete_record(
            self.admin_context, zone['id'], recordset['id'], record['id'])

        # Simulate the record having been deleted on the backend
        zone_serial = self.central_service.get_zone(
            self.admin_context, zone['id']).serial
        self.central_service.update_status(
            self.admin_context, zone['id'], "SUCCESS", zone_serial)

        # Fetch the record again, ensuring an exception is raised
        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            self.central_service.get_record(
                self.admin_context, zone['id'], recordset['id'],
                record['id'])

    @mock.patch.object(notifier.Notifier, "info")
    def test_update_status_send_notification(self, mock_notifier):

        # Create zone and ensure that two zone/domain create notifications
        # have been sent - status is PENDING
        zone = self.create_zone(email='info@example.org')
        self.assertEqual(2, mock_notifier.call_count)

        notify_string, notified_zone = mock_notifier.call_args_list[0][0][1:]
        self.assertEqual('dns.domain.create', notify_string)
        self.assertEqual('example.com.', notified_zone.name)
        self.assertEqual('PENDING', notified_zone.status)

        notify_string, notified_zone = mock_notifier.call_args_list[1][0][1:]
        self.assertEqual('dns.zone.create', notify_string)
        self.assertEqual('example.com.', notified_zone.name)
        self.assertEqual('PENDING', notified_zone.status)

        # Perform an update; ensure that zone/domain update notifications
        # have been sent and the zone is now in ACTIVE status
        mock_notifier.reset_mock()
        self.central_service.update_status(
            self.admin_context, zone['id'], "SUCCESS", zone.serial)

        self.assertEqual(2, mock_notifier.call_count)
        notify_string, notified_zone = mock_notifier.call_args_list[0][0][1:]
        self.assertEqual('dns.domain.update', notify_string)
        self.assertEqual('example.com.', notified_zone.name)
        self.assertEqual('ACTIVE', notified_zone.status)

        notify_string, notified_zone = mock_notifier.call_args_list[1][0][1:]
        self.assertEqual('dns.zone.update', notify_string)
        self.assertEqual('example.com.', notified_zone.name)
        self.assertEqual('ACTIVE', notified_zone.status)

    def test_update_status_delete_last_record_without_incrementing_serial(
            self):
        zone = self.create_zone()
        recordset = self.create_recordset(zone)

        # Create a record
        record = self.create_record(zone, recordset)

        # Fetch the zone serial number
        zone_serial = self.central_service.get_zone(
            self.admin_context, zone['id']).serial

        # Delete the record
        self.central_service.delete_record(
            self.admin_context, zone['id'], recordset['id'], record['id'],
            increment_serial=False)

        # Simulate the record having been deleted on the backend
        zone_serial = self.central_service.get_zone(
            self.admin_context, zone['id']).serial
        self.central_service.update_status(
            self.admin_context, zone['id'], "SUCCESS", zone_serial)

        # Fetch the record again, ensuring an exception is raised
        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            self.central_service.get_record(
                self.admin_context, zone['id'], recordset['id'],
                record['id'])

        # Ensure the zones serial number was not updated
        new_zone_serial = self.central_service.get_zone(
            self.admin_context, zone['id']).serial

        self.assertEqual(zone_serial, new_zone_serial)

    def test_create_zone_transfer_request(self):
        zone = self.create_zone()
        zone_transfer_request = self.create_zone_transfer_request(zone)

        # Verify all values have been set correctly
        self.assertIsNotNone(zone_transfer_request.id)
        self.assertIsNotNone(zone_transfer_request.tenant_id)
        self.assertIsNotNone(zone_transfer_request.key)
        self.assertEqual(zone.id, zone_transfer_request.zone_id)

    def test_create_zone_transfer_request_duplicate(self):
        zone = self.create_zone()
        self.create_zone_transfer_request(zone)
        with testtools.ExpectedException(
                exceptions.DuplicateZoneTransferRequest):
            self.create_zone_transfer_request(zone)

    def test_create_scoped_zone_transfer_request(self):
        zone = self.create_zone()
        values = self.get_zone_transfer_request_fixture(fixture=1)
        zone_transfer_request = self.create_zone_transfer_request(zone,
                                                                  fixture=1)

        # Verify all values have been set correctly
        self.assertIsNotNone(zone_transfer_request.id)
        self.assertIsNotNone(zone_transfer_request.tenant_id)
        self.assertEqual(zone.id, zone_transfer_request.zone_id)
        self.assertIsNotNone(zone_transfer_request.key)
        self.assertEqual(
            values['target_tenant_id'],
            zone_transfer_request.target_tenant_id)

    def test_get_zone_transfer_request(self):
        zone = self.create_zone()
        zt_request = self.create_zone_transfer_request(zone,
                                                       fixture=1)
        retrived_zt = self.central_service.get_zone_transfer_request(
            self.admin_context,
            zt_request.id)
        self.assertEqual(zt_request.zone_id, retrived_zt.zone_id)
        self.assertEqual(zt_request.key, retrived_zt.key)

    def test_get_zone_transfer_request_scoped(self):
        tenant_1_context = self.get_context(tenant=1)
        tenant_2_context = self.get_context(tenant=2)
        tenant_3_context = self.get_context(tenant=3)
        zone = self.create_zone(context=tenant_1_context)
        zt_request = self.create_zone_transfer_request(
            zone,
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
        zone = self.create_zone()
        zone_transfer_request = self.create_zone_transfer_request(zone)

        zone_transfer_request.description = 'TEST'
        self.central_service.update_zone_transfer_request(
            self.admin_context, zone_transfer_request)

        # Verify all values have been set correctly
        self.assertIsNotNone(zone_transfer_request.id)
        self.assertIsNotNone(zone_transfer_request.tenant_id)
        self.assertIsNotNone(zone_transfer_request.key)
        self.assertEqual('TEST', zone_transfer_request.description)

    def test_delete_zone_transfer_request(self):
        zone = self.create_zone()
        zone_transfer_request = self.create_zone_transfer_request(zone)

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

        zone = self.create_zone(context=tenant_1_context)
        recordset = self.create_recordset(zone, context=tenant_1_context)
        record = self.create_record(
            zone, recordset, context=tenant_1_context)

        zone_transfer_request = self.create_zone_transfer_request(
            zone, context=tenant_1_context)

        zone_transfer_accept = objects.ZoneTransferAccept()
        zone_transfer_accept.zone_transfer_request_id =\
            zone_transfer_request.id

        zone_transfer_accept.key = zone_transfer_request.key
        zone_transfer_accept.zone_id = zone.id

        zone_transfer_accept = \
            self.central_service.create_zone_transfer_accept(
                tenant_2_context, zone_transfer_accept)

        result = {}
        result['zone'] = self.central_service.get_zone(
            admin_context, zone.id)

        result['recordset'] = self.central_service.get_recordset(
            admin_context, zone.id, recordset.id)

        result['record'] = self.central_service.get_record(
            admin_context, zone.id, recordset.id, record.id)

        result['zt_accept'] = self.central_service.get_zone_transfer_accept(
            admin_context, zone_transfer_accept.id)
        result['zt_request'] = self.central_service.get_zone_transfer_request(
            admin_context, zone_transfer_request.id)

        self.assertEqual(
            str(tenant_2_context.tenant), result['zone'].tenant_id)
        self.assertEqual(
            str(tenant_2_context.tenant), result['recordset'].tenant_id)
        self.assertEqual(
            str(tenant_2_context.tenant), result['record'].tenant_id)
        self.assertEqual(
            'COMPLETE', result['zt_accept'].status)
        self.assertEqual(
            'COMPLETE', result['zt_request'].status)

    def test_create_zone_transfer_accept_scoped(self):
        tenant_1_context = self.get_context(tenant=1)
        tenant_2_context = self.get_context(tenant=2)
        admin_context = self.get_admin_context()
        admin_context.all_tenants = True

        zone = self.create_zone(context=tenant_1_context)
        recordset = self.create_recordset(zone, context=tenant_1_context)
        record = self.create_record(
            zone, recordset, context=tenant_1_context)

        zone_transfer_request = self.create_zone_transfer_request(
            zone,
            context=tenant_1_context,
            target_tenant_id='2')

        zone_transfer_accept = objects.ZoneTransferAccept()
        zone_transfer_accept.zone_transfer_request_id =\
            zone_transfer_request.id

        zone_transfer_accept.key = zone_transfer_request.key
        zone_transfer_accept.zone_id = zone.id

        zone_transfer_accept = \
            self.central_service.create_zone_transfer_accept(
                tenant_2_context, zone_transfer_accept)

        result = {}
        result['zone'] = self.central_service.get_zone(
            admin_context, zone.id)

        result['recordset'] = self.central_service.get_recordset(
            admin_context, zone.id, recordset.id)

        result['record'] = self.central_service.get_record(
            admin_context, zone.id, recordset.id, record.id)

        result['zt_accept'] = self.central_service.get_zone_transfer_accept(
            admin_context, zone_transfer_accept.id)
        result['zt_request'] = self.central_service.get_zone_transfer_request(
            admin_context, zone_transfer_request.id)

        self.assertEqual(
            str(tenant_2_context.tenant), result['zone'].tenant_id)
        self.assertEqual(
            str(tenant_2_context.tenant), result['recordset'].tenant_id)
        self.assertEqual(
            str(tenant_2_context.tenant), result['record'].tenant_id)
        self.assertEqual(
            'COMPLETE', result['zt_accept'].status)
        self.assertEqual(
            'COMPLETE', result['zt_request'].status)

    def test_create_zone_transfer_accept_failed_key(self):
        tenant_1_context = self.get_context(tenant=1)
        tenant_2_context = self.get_context(tenant=2)
        admin_context = self.get_admin_context()
        admin_context.all_tenants = True

        zone = self.create_zone(context=tenant_1_context)

        zone_transfer_request = self.create_zone_transfer_request(
            zone,
            context=tenant_1_context,
            target_tenant_id=2)

        zone_transfer_accept = objects.ZoneTransferAccept()
        zone_transfer_accept.zone_transfer_request_id =\
            zone_transfer_request.id

        zone_transfer_accept.key = 'WRONG KEY'
        zone_transfer_accept.zone_id = zone.id

        with testtools.ExpectedException(exceptions.IncorrectZoneTransferKey):
            zone_transfer_accept = \
                self.central_service.create_zone_transfer_accept(
                    tenant_2_context, zone_transfer_accept)

    def test_create_zone_tarnsfer_accept_out_of_tenant_scope(self):
        tenant_1_context = self.get_context(tenant=1)
        tenant_3_context = self.get_context(tenant=3)
        admin_context = self.get_admin_context()
        admin_context.all_tenants = True

        zone = self.create_zone(context=tenant_1_context)

        zone_transfer_request = self.create_zone_transfer_request(
            zone,
            context=tenant_1_context,
            target_tenant_id=2)

        zone_transfer_accept = objects.ZoneTransferAccept()
        zone_transfer_accept.zone_transfer_request_id =\
            zone_transfer_request.id

        zone_transfer_accept.key = zone_transfer_request.key
        zone_transfer_accept.zone_id = zone.id

        with testtools.ExpectedException(exceptions.Forbidden):
            zone_transfer_accept = \
                self.central_service.create_zone_transfer_accept(
                    tenant_3_context, zone_transfer_accept)

    # Zone Import Tests
    def test_create_zone_import(self):
        # Create a Zone Import
        context = self.get_context()
        request_body = self.get_zonefile_fixture()
        zone_import = self.central_service.create_zone_import(context,
                                                              request_body)

        # Ensure all values have been set correctly
        self.assertIsNotNone(zone_import['id'])
        self.assertEqual('PENDING', zone_import.status)
        self.assertIsNone(zone_import.message)
        self.assertIsNone(zone_import.zone_id)

        self.wait_for_import(zone_import.id)

    def test_find_zone_imports(self):
        context = self.get_context()

        # Ensure we have no zone_imports to start with.
        zone_imports = self.central_service.find_zone_imports(
                         self.admin_context)
        self.assertEqual(0, len(zone_imports))

        # Create a single zone_import
        request_body = self.get_zonefile_fixture()
        zone_import_one = self.central_service.create_zone_import(
            context, request_body)

        # Wait for the import to complete
        self.wait_for_import(zone_import_one.id)

        # Ensure we can retrieve the newly created zone_import
        zone_imports = self.central_service.find_zone_imports(
                         self.admin_context)
        self.assertEqual(1, len(zone_imports))

        # Create a second zone_import
        request_body = self.get_zonefile_fixture(variant="two")
        zone_import_two = self.central_service.create_zone_import(
            context, request_body)

        # Wait for the imports to complete
        self.wait_for_import(zone_import_two.id)

        # Ensure we can retrieve both zone_imports
        zone_imports = self.central_service.find_zone_imports(
                         self.admin_context)
        self.assertEqual(2, len(zone_imports))
        self.assertEqual('COMPLETE', zone_imports[0].status)
        self.assertEqual('COMPLETE', zone_imports[1].status)

    def test_get_zone_import(self):
        # Create a Zone Import
        context = self.get_context()
        request_body = self.get_zonefile_fixture()
        zone_import = self.central_service.create_zone_import(
                    context, request_body)

        # Wait for the import to complete
        self.wait_for_import(zone_import.id)

        # Retrieve it, and ensure it's the same
        zone_import = self.central_service.get_zone_import(
            self.admin_context, zone_import.id)

        self.assertEqual(zone_import.id, zone_import['id'])
        self.assertEqual(zone_import.status, zone_import['status'])
        self.assertEqual('COMPLETE', zone_import.status)

    def test_update_zone_import(self):
        # Create a Zone Import
        context = self.get_context()
        request_body = self.get_zonefile_fixture()
        zone_import = self.central_service.create_zone_import(
                    context, request_body)

        self.wait_for_import(zone_import.id)

        # Update the Object
        zone_import.message = 'test message'

        # Perform the update
        zone_import = self.central_service.update_zone_import(
                self.admin_context, zone_import)

        # Fetch the zone_import again
        zone_import = self.central_service.get_zone_import(context,
                                                           zone_import.id)

        # Ensure the zone_import was updated correctly
        self.assertEqual('test message', zone_import.message)

    def test_delete_zone_import(self):
        # Create a Zone Import
        context = self.get_context()
        request_body = self.get_zonefile_fixture()
        zone_import = self.central_service.create_zone_import(
                    context, request_body)

        self.wait_for_import(zone_import.id)

        # Delete the zone_import
        self.central_service.delete_zone_import(context,
                                                zone_import['id'])

        # Fetch the zone_import again, ensuring an exception is raised
        self.assertRaises(
            exceptions.ZoneImportNotFound,
            self.central_service.get_zone_import,
            context, zone_import['id'])
