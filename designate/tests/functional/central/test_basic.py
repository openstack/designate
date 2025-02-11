# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Federico Ceratto <federico.ceratto@hpe.com>
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


from unittest import mock

import fixtures
from oslo_log import log as logging
from oslo_messaging.rpc import dispatcher as rpc_dispatcher

from designate.central import service
import designate.conf
from designate import exceptions
from designate import objects
from designate import policy
from designate import quota
from designate import storage
from designate.storage import sqlalchemy
from designate.tests.base_fixtures import random_seed
import designate.tests.functional
from designate.tests import unit
from designate.worker import rpcapi as worker_rpcapi


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class MockZone:
    id = 1
    name = 'example.org'
    pool_id = 1
    tenant_id = 3
    ttl = 1
    type = 'PRIMARY'
    serial = 123
    shared = False

    def obj_attr_is_set(self, n):
        if n == 'recordsets':
            return False
        raise NotImplementedError()

    def __getitem__(self, k):
        items = {
            'id': 3,
            'email': 'foo@example.org',
            'serial': 123,
            'refresh': 20,
            'retry': 33,
            'expire': 9999,
            'minimum': 2,
            'name': 'example.org.',
        }
        try:
            return items[k]
        except KeyError:
            raise NotImplementedError(k)


class MockRecordSet:
    id = 1
    name = 'example.org.'
    pool_id = 1
    tenant_id = 3
    ttl = 1
    type = 'PRIMARY'
    serial = 123
    records = []

    def obj_attr_is_set(self, n):
        if n == 'records':
            return False
        raise NotImplementedError()


class MockRecord:
    hostname = 'bar'

    def __getitem__(self, n):
        assert n == 'hostname'
        return 'bar'


class MockPool:
    ns_records = [MockRecord(), ]


# Fixtures
fx_worker = fixtures.MockPatch(
    'designate.central.service.worker_rpcapi.WorkerAPI.get_instance',
    mock.MagicMock(spec_set=[
        'create_zone',
        'update_zone',
        'delete_zone'
    ])
)


class CentralBasic(designate.tests.functional.TestCase):
    def setUp(self):
        super().setUp()

        pool_list = objects.PoolList.from_list(
            [
                {'id': '794ccc2c-d751-44fe-b57f-8894c9f5c842'}
            ]
        )
        attrs = {
            'count_zones.return_value': 0,
            'find_zone.return_value': MockZone(),
            'get_zone.return_value': MockZone(),
            'get_pool.return_value': MockPool(),
            'find_pools.return_value': pool_list,
        }

        self.mock_policy = mock.NonCallableMock(spec_set=[
            'reset',
            'set_rules',
            'init',
            'check',
            'enforce_new_defaults',
        ])

        self.mock_storage = mock.Mock(spec=sqlalchemy.SQLAlchemyStorage)
        self.worker_api = mock.Mock()
        self.quota = mock.Mock()
        self.mock_storage.configure_mock(**attrs)

        mock.patch.object(
            worker_rpcapi.WorkerAPI, 'get_instance',
            return_value=self.worker_api).start()
        mock.patch.object(
            policy, 'reset', return_value=mock.Mock()).start()
        mock.patch.object(
            policy, 'set_rules', return_value=mock.Mock()).start()
        mock.patch.object(
            policy, 'init', return_value=mock.Mock()).start()
        self.mock_policy_check = mock.patch.object(
            policy, 'check', return_value=mock.Mock()).start()
        self.mock_get_quota = mock.patch.object(
            quota, 'get_quota', return_value=self.quota).start()
        self.mock_get_storage = mock.patch.object(
            storage, 'get_storage', return_value=self.mock_storage).start()

        self.service = service.Service()
        self.service.check_for_tlds = True
        self.service.notifier = mock.Mock()

        self.context = mock.NonCallableMock(spec_set=[
            'elevated',
            'sudo',
            'abandon',
            'all_tenants',
            'hard_delete',
            'project_id'
        ])


class CentralServiceTestCase(CentralBasic):
    def test_conf_fixture(self):
        self.assertIn('service:central', CONF)

    def test_init(self):
        self.assertTrue(self.service.check_for_tlds)

        # Ensure these attributes are lazy
        self.mock_get_storage.assert_not_called()
        self.mock_get_quota.assert_not_called()

    def test_storage_loads_lazily(self):
        self.assertTrue(self.service.storage)
        self.mock_get_storage.assert_called_once()

    def test_quota_loads_lazily(self):
        self.assertTrue(self.service.quota)
        self.mock_get_quota.assert_called_once()

    def test_is_valid_ttl(self):
        self.CONF.set_override('min_ttl', 10, 'service:central')
        self.service._is_valid_ttl(self.context, 20)

        # policy.check() not to raise: the user is allowed to create low TTLs
        self.service._is_valid_ttl(self.context, None)
        self.service._is_valid_ttl(self.context, 1)

        # policy.check() to raise
        self.mock_policy_check.side_effect = exceptions.Forbidden

        self.assertRaisesRegex(
            exceptions.InvalidTTL,
            'TTL is below the minimum: 10',
            self.service._is_valid_ttl, self.context, 3
        )

    def test_update_soa_secondary(self):
        ctx = mock.Mock()
        mock_zone = unit.RoObject(type='SECONDARY')

        self.service._update_soa(ctx, mock_zone)
        self.assertFalse(ctx.elevated.called)

    def test_update_soa(self):
        class MockRecord:
            data = None

        mock_soa = unit.RoObject(records=[MockRecord()])

        self.context.elevated = mock.Mock()
        self.service._update_zone_in_storage = mock.Mock()
        self.service.storage.get_pool = mock.Mock(
            return_value=MockPool())
        self.service.find_recordset = mock.Mock(return_value=mock_soa)
        self.service._build_soa_record = mock.Mock()
        self.service._update_recordset_in_storage = mock.Mock()

        self.service._update_soa(self.context, MockZone())

        self.assertTrue(
            self.service._update_recordset_in_storage.called)
        self.assertTrue(self.context.elevated.called)

    def test_count_zones(self):
        self.service.count_zones(self.context)
        self.service.storage.count_zones.assert_called_once_with(
            self.context, {}
        )

    def test_count_zones_criterion(self):
        self.service.count_zones(self.context, criterion={'a': 1})
        self.service.storage.count_zones.assert_called_once_with(
            self.context, {'a': 1}
        )

    def test_validate_new_recordset(self):
        central_service = self.central_service

        central_service._is_valid_recordset_name = mock.Mock()
        central_service._is_valid_recordset_placement = mock.Mock()
        central_service._is_valid_recordset_placement_subzone = mock.Mock()
        central_service._is_valid_ttl = mock.Mock()

        MockRecordSet.id = None

        central_service._validate_recordset(
            self.context, MockZone, MockRecordSet
        )

        self.assertTrue(central_service._is_valid_recordset_name.called)
        self.assertTrue(central_service._is_valid_recordset_placement.called)
        self.assertTrue(
            central_service._is_valid_recordset_placement_subzone.called)
        self.assertTrue(central_service._is_valid_ttl.called)

    def test_validate_existing_recordset(self):
        central_service = self.central_service

        central_service._is_valid_recordset_name = mock.Mock()
        central_service._is_valid_recordset_placement = mock.Mock()
        central_service._is_valid_recordset_placement_subzone = mock.Mock()
        central_service._is_valid_ttl = mock.Mock()

        MockRecordSet.obj_get_changes = mock.Mock(return_value={'ttl': 3600})

        central_service._validate_recordset(
            self.context, MockZone, MockRecordSet
        )

        self.assertTrue(central_service._is_valid_recordset_name.called)
        self.assertTrue(central_service._is_valid_recordset_placement.called)
        self.assertTrue(
            central_service._is_valid_recordset_placement_subzone.called)
        self.assertTrue(central_service._is_valid_ttl.called)

    def test_create_recordset_in_storage(self):
        self.service._enforce_recordset_quota = mock.Mock()
        self.service._validate_recordset = mock.Mock(spec=objects.RecordSet)

        self.service.storage.create_recordset = mock.Mock(return_value='rs')
        self.service._update_zone_in_storage = mock.Mock()

        rs, zone = self.service._create_recordset_in_storage(
            self.context, MockZone(), MockRecordSet()
        )
        self.assertEqual(rs, 'rs')
        self.assertFalse(self.service._update_zone_in_storage.called)

    def test_create_recordset_with_records_in_storage(self):
        central_service = self.central_service

        central_service._enforce_recordset_quota = mock.Mock()
        central_service._enforce_record_quota = mock.Mock()
        central_service._is_valid_recordset_name = mock.Mock()
        central_service._is_valid_recordset_placement = mock.Mock()
        central_service._is_valid_recordset_placement_subzone = mock.Mock()
        central_service._is_valid_ttl = mock.Mock()

        central_service.storage.create_recordset = mock.Mock(return_value='rs')
        central_service._update_zone_in_storage = mock.Mock(
            return_value=MockZone()
        )
        recordset = mock.Mock(spec=objects.RecordSet)
        recordset.obj_attr_is_set.return_value = True
        recordset.records = [MockRecord()]

        central_service._create_recordset_in_storage(
            self.context, MockZone(), recordset
        )

        self.assertTrue(central_service._enforce_record_quota.called)
        self.assertTrue(central_service._update_zone_in_storage.called)

    def test_create_recordset_checking_DBDeadLock(self):
        self.service._enforce_recordset_quota = mock.Mock()
        self.service._enforce_record_quota = mock.Mock()
        self.service._is_valid_recordset_name = mock.Mock()
        self.service._is_valid_recordset_placement = mock.Mock()
        self.service._is_valid_recordset_placement_subzone = mock.Mock()
        self.service._is_valid_ttl = mock.Mock()

        self.service.storage._retry_on_deadlock = mock.Mock()
        self.service.storage.create_recordset = mock.Mock(return_value='rs')
        self.service._update_zone_in_storage = mock.Mock(
            return_value=MockZone()
        )

        # NOTE(thirose): Since this is a race condition we assume that
        #  we will hit it if we try to do the operations in a loop 100 times.
        for num in range(100):
            recordset = mock.Mock(spec=objects.RecordSet)
            recordset.name = f'b{num}'
            recordset.obj_attr_is_set.return_value = True
            recordset.records = [MockRecord()]

            self.service._create_recordset_in_storage(
                self.context, MockZone(), recordset
            )

            self.service.storage._retry_on_deadlock.assert_not_called()
            self.service._update_zone_in_storage.assert_called()
            self.service.storage.create_recordset.assert_called()

    def test_create_soa(self):
        self.central_service._create_recordset_in_storage = mock.Mock(
            return_value=(None, None)
        )
        self.central_service._build_soa_record = mock.Mock(
            return_value='example.org. foo.bar 1 60 5 999 1'
        )
        zone = MockZone()
        self.central_service._create_soa(self.context, zone)

        rset = (
            self.central_service._create_recordset_in_storage.call_args[0][2]
        )

        self.assertEqual('example.org.', rset.name)
        self.assertEqual('SOA', rset.type)
        self.assertEqual('SOA', rset.type)
        self.assertEqual(1, len(rset.records.objects))
        self.assertTrue(rset.records.objects[0].managed)

    def test_create_zone_in_storage(self):
        self.service._create_soa = mock.Mock()
        self.service._create_ns = mock.Mock()
        self.service.get_zone_ns_records = mock.Mock(
            return_value=[unit.RoObject(hostname='host_foo')]
        )
        self.service._ensure_catalog_zone_serial_increment = mock.Mock()

        def create_zone(ctx, zone):
            return zone

        self.service.storage.create_zone = create_zone

        zone = self.service._create_zone_in_storage(
            self.context, MockZone()
        )
        self.assertEqual('PENDING', zone.status)
        self.assertEqual('CREATE', zone.action)
        ctx, zone, hostnames = self.service._create_ns.call_args[0]
        self.assertEqual(['host_foo'], hostnames)


class CentralZoneTestCase(CentralBasic):
    zone_id = '1c85d9b0-1e9d-4e99-aede-a06664f1af2e'
    zone_id_2 = '7c85d9b0-1e9d-4e99-aede-a06664f1af2e'
    record_id = 'b81ebcfb-6236-4424-b77f-2dd0179fa041'
    record_id_2 = 'c81ebcfb-6236-4424-b77f-2dd0179fa041'
    pool_id = '769ca3fc-5924-4a44-8c1f-7efbe52fbd59'
    recordset_id = '9c85d9b0-1e9d-4e99-aede-a06664f1af2e'
    recordset_id_2 = 'dc85d9b0-1e9d-4e99-aede-a06664f1af2e'
    recordset_id_3 = '2a94a9fe-30d1-4a15-9071-0bb21996d971'
    zone_export_id = 'e887597f-9697-47dd-a202-7a2711f8669c'
    zone_shared = False

    def setUp(self):
        super().setUp()

        def storage_find_tld(c, d):
            if d['name'] not in ('org',):
                raise exceptions.TldNotFound

        def storage_find_tlds(c):
            return objects.TldList.from_list(
                [objects.Tld.from_dict({'name': 'org'})]
            )

        self.service.storage.find_tlds = storage_find_tlds
        self.service.storage.find_tld = storage_find_tld

    def test_is_valid_zone_name_valid(self):
        self.service._is_blacklisted_zone_name = mock.Mock()
        self.service._is_valid_zone_name(self.context, 'valid.org.')

    def test_is_valid_zone_name_invalid(self):
        self.service._is_blacklisted_zone_name = mock.Mock()
        self.assertRaisesRegex(
            exceptions.InvalidZoneName,
            'More than one label is required',
            self.service._is_valid_zone_name, self.context, 'example^org.'
        )

    def test_is_valid_zone_name_invalid_2(self):
        self.service._is_blacklisted_zone_name = mock.Mock()
        self.assertRaisesRegex(
            exceptions.InvalidZoneName,
            'Invalid TLD',
            self.service._is_valid_zone_name, self.context, 'example.tld.'
        )

    def test_is_valid_zone_name_invalid_same_as_tld(self):
        self.service._is_blacklisted_zone_name = mock.Mock()
        self.assertRaisesRegex(
            exceptions.InvalidZoneName,
            'Invalid TLD',
            self.service._is_valid_zone_name, self.context, 'com.com.'
        )

    def test_is_valid_zone_name_invalid_tld(self):
        self.service._is_blacklisted_zone_name = mock.Mock()
        self.assertRaisesRegex(
            exceptions.InvalidZoneName,
            'More than one label is required',
            self.service._is_valid_zone_name, self.context, 'tld.'
        )

    def test_is_valid_zone_name_blacklisted(self):
        self.service._is_blacklisted_zone_name = mock.Mock(
            side_effect=exceptions.InvalidZoneName)
        self.assertRaisesRegex(
            exceptions.InvalidZoneName,
            'Invalid TLD',
            self.service._is_valid_zone_name, self.context, 'valid.com.'
        )

    def test_is_blacklisted_zone_name(self):
        self.service.storage.find_blacklists.return_value = [
            unit.RoObject(pattern='a'), unit.RoObject(pattern='b')
        ]
        blacklist_tests = (
            ('example.org', True),
            ('example.net', True),
            ('hi', False),
            ('', False)
        )
        for zone, expected in blacklist_tests:
            self.assertEqual(
                self.service._is_blacklisted_zone_name(self.context, zone),
                expected
            )

    def test_is_valid_recordset_name(self):
        zone = unit.RoObject(name='example.org.')
        self.service._is_valid_recordset_name(self.context, zone,
                                              'foo..example.org.')

    def test_is_valid_recordset_name_no_dot(self):
        zone = unit.RoObject(name='example.org.')
        self.assertRaisesRegex(
            ValueError,
            'Please supply a FQDN',
            self.service._is_valid_recordset_name,
            self.context, zone, 'foo.example.org',
        )

    def test_is_valid_recordset_name_too_long(self):
        zone = unit.RoObject(name='example.org.')
        CONF['service:central'].max_recordset_name_len = 255
        rs_name = 'a' * 255 + '.org.'
        self.assertRaisesRegex(
            exceptions.InvalidRecordSetName,
            'Name too long',
            self.service._is_valid_recordset_name,
            self.context, zone, rs_name,
        )

    def test_is_valid_recordset_name_wrong_zone(self):
        zone = unit.RoObject(name='example.org.')
        self.assertRaisesRegex(
            exceptions.InvalidRecordSetLocation,
            'RecordSet is not contained within it\'s parent zone',
            self.service._is_valid_recordset_name,
            self.context, zone, 'foo.example.com.',
        )

    def test_is_valid_recordset_placement_cname(self):
        zone = unit.RoObject(name='example.org.')
        self.assertRaisesRegex(
            exceptions.InvalidRecordSetLocation,
            'CNAME recordsets may not be created at the zone apex',
            self.service._is_valid_recordset_placement,
            self.context, zone, 'example.org.', 'CNAME',
        )

    def test_is_valid_recordset_placement_failing(self):
        zone = unit.RoObject(
            name='example.org.', id=CentralZoneTestCase.zone_id
        )
        self.service.storage.find_recordsets.return_value = [
            unit.RoObject(id=CentralZoneTestCase.recordset_id)
        ]
        self.assertRaisesRegex(
            exceptions.InvalidRecordSetLocation,
            'CNAME recordsets may not share a name with any other records',
            self.service._is_valid_recordset_placement,
            self.context, zone, 'example.org.', 'A',
        )

    def test_is_valid_recordset_placement_failing_2(self):
        zone = unit.RoObject(
            name='example.org.', id=CentralZoneTestCase.zone_id
        )
        self.service.storage.find_recordsets.return_value = [
            unit.RoObject(),
            unit.RoObject()
        ]
        self.assertRaisesRegex(
            exceptions.InvalidRecordSetLocation,
            'CNAME recordsets may not share a name with any other records',
            self.service._is_valid_recordset_placement,
            self.context, zone, 'example.org.', 'A',
        )

    def test_is_valid_recordset_placement(self):
        zone = unit.RoObject(
            name='example.org.', id=CentralZoneTestCase.zone_id
        )
        self.service.storage.find_recordsets.return_value = []
        ret = self.service._is_valid_recordset_placement(
            self.context,
            zone,
            'example.org.',
            'A',
        )
        self.assertTrue(ret)

    def test_is_valid_recordset_placement_subzone(self):
        zone = unit.RoObject(
            name='example.org.', id=CentralZoneTestCase.zone_id
        )
        self.service._is_valid_recordset_placement_subzone(
            self.context,
            zone,
            'example.org.'
        )

    def test_is_valid_recordset_placement_subzone_2(self):
        zone = unit.RoObject(
            name='example.org.', id=CentralZoneTestCase.zone_id
        )
        self.service._is_valid_recordset_name = mock.Mock(
            side_effect=Exception)
        self.service.storage.find_zones.return_value = [
            unit.RoObject(name='foo.example.org.')
        ]
        self.service._is_valid_recordset_placement_subzone(
            self.context,
            zone,
            'bar.example.org.'
        )

    def test_is_valid_recordset_placement_subzone_failing(self):
        zone = unit.RoObject(
            name='example.org.', id=CentralZoneTestCase.zone_id
        )
        self.service._is_valid_recordset_name = mock.Mock()
        self.service.storage.find_zones.return_value = [
            unit.RoObject(name='foo.example.org.')
        ]

        self.assertRaisesRegex(
            exceptions.InvalidRecordSetLocation,
            'RecordSet belongs in a child zone: foo.example.org.',
            self.service._is_valid_recordset_placement_subzone,
            self.context, zone, 'bar.example.org.'
        )

    def test_is_valid_recordset_records(self):
        recordset = unit.RoObject(
            records=[
                'ww1.example.com.',
                'ww2.example.com.'
            ],
            type='CNAME'
        )
        self.assertRaisesRegex(
            exceptions.BadRequest,
            'CNAME recordsets may not have more than 1 record',
            self.service._is_valid_recordset_records, recordset
        )

    def test_is_superzone(self):
        central_service = self.central_service

        central_service.storage.find_zones = mock.Mock()
        central_service._is_superzone(self.context, 'example.org.', '1')
        _, crit = self.service.storage.find_zones.call_args[0]
        self.assertEqual({'name': '%.example.org.', 'pool_id': '1'}, crit)

    def test_create_ns(self):
        self.service._create_recordset_in_storage = mock.Mock(
            return_value=(0, 0))
        self.service._create_ns(
            self.context,
            unit.RoObject(type='PRIMARY', name='example.org.'),
            [unit.RoObject(), unit.RoObject(), unit.RoObject()]
        )
        ctx, zone, rset = (
            self.service._create_recordset_in_storage.call_args[0])

        self.assertEqual('example.org.', rset.name)
        self.assertEqual('NS', rset.type)
        self.assertEqual(3, len(rset.records))
        self.assertTrue(rset.records[0].managed)

    def test_create_ns_skip(self):
        self.service._create_recordset_in_storage = mock.Mock()
        self.service._create_ns(
            self.context,
            unit.RoObject(type='SECONDARY', name='example.org.'),
            [],
        )
        self.assertFalse(
            self.service._create_recordset_in_storage.called)

    def test_add_ns_creation(self):
        self.service._create_ns = mock.Mock()

        self.service.find_recordset = mock.Mock(
            side_effect=exceptions.RecordSetNotFound()
        )

        self.service._add_ns(
            self.context,
            unit.RoObject(name='foo', id=CentralZoneTestCase.zone_id),
            unit.RoObject(name='bar')
        )
        ctx, zone, records = self.service._create_ns.call_args[0]
        self.assertTrue(len(records), 1)

    def test_add_ns(self):
        self.service._update_recordset_in_storage = mock.Mock()

        self.service.find_recordset = mock.Mock(
            return_value=unit.RoObject(
                records=objects.RecordList.from_list([]), managed=True
            )
        )

        self.service._add_ns(
            self.context,
            unit.RoObject(name='foo', id=CentralZoneTestCase.zone_id),
            unit.RoObject(name='bar')
        )
        ctx, zone, rset = (
            self.service._update_recordset_in_storage.call_args[0])
        self.assertEqual(len(rset.records), 1)
        self.assertTrue(rset.records[0].managed)
        self.assertEqual('bar', rset.records[0].data.name)

    def test_create_zone_no_servers(self):
        self.service._enforce_zone_quota = mock.Mock()
        self.service._is_valid_zone_name = mock.Mock()
        self.service._is_valid_ttl = mock.Mock()
        self.service._is_subzone = mock.Mock(
            return_value=False
        )
        self.service._is_superzone = mock.Mock(
            return_value=[]
        )
        self.service.storage.get_pool.return_value = unit.RoObject(
            ns_records=[]
        )

        self.useFixture(
            fixtures.MockPatchObject(
                self.service.storage,
                'find_pools',
                return_value=objects.PoolList.from_list(
                    [
                        {'id': '94ccc2c1-d751-44fe-b57f-8894c9f5c842'}
                    ]
                )
            )
        )

        z = objects.Zone(tenant_id='1',
                         name='example.com.', ttl=60,
                         pool_id=CentralZoneTestCase.pool_id)

        self.assertRaises(exceptions.NoServersConfigured,
                          self.service.create_zone,
                          self.context, z)

    def test_create_zone(self):
        self.service._enforce_zone_quota = mock.Mock()
        self.service._create_zone_in_storage = mock.Mock(
            return_value=objects.Zone(
                name='example.com.',
                type='PRIMARY',
            )
        )
        self.service._is_valid_zone_name = mock.Mock()
        self.service._is_valid_ttl = mock.Mock()
        self.service._is_subzone = mock.Mock(
            return_value=False
        )
        self.service._is_superzone = mock.Mock(
            return_value=[]
        )
        self.service.storage.get_pool.return_value = unit.RoObject(
            ns_records=[unit.RoObject()]
        )
        self.useFixture(
            fixtures.MockPatchObject(
                self.service.storage,
                'find_pools',
                return_value=objects.PoolList.from_list(
                    [
                        {'id': '94ccc2c1-d751-44fe-b57f-8894c9f5c842'}
                    ]
                )
            )
        )
        self.service.storage.get_catalog_zone = mock.Mock(
            side_effect=exceptions.ZoneNotFound)

        out = self.service.create_zone(
            self.context,
            objects.Zone(
                tenant_id='1',
                name='example.com.',
                ttl=60,
                pool_id=CentralZoneTestCase.pool_id,
                refresh=0,
                type='PRIMARY'
            )
        )
        self.assertEqual('example.com.', out.name)

    def test_get_zone(self):
        self.service.storage.get_zone.return_value = unit.RoObject(
            name='foo',
            tenant_id='2',
            shared=self.zone_shared,
        )
        self.service.get_zone(self.context,
                              CentralZoneTestCase.zone_id)

        self.mock_policy_check.assert_called_with(
            'get_zone', mock.ANY,
            {
                'zone_id': CentralZoneTestCase.zone_id,
                'zone_name': 'foo',
                'zone_shared': False,
                'project_id': '2',
                'tenant_id': '2'
            }
        )

    def test_get_zone_servers(self):
        self.service.storage.get_zone.return_value = unit.RoObject(
            name='foo',
            tenant_id='2',
            pool_id=CentralZoneTestCase.pool_id,
        )

        self.service.get_zone_ns_records(
            self.context,
            zone_id=CentralZoneTestCase.zone_id
        )

        ctx, pool_id = self.service.storage.get_pool.call_args[0]
        self.assertEqual(CentralZoneTestCase.pool_id, pool_id)

    def test_find_zones(self):
        self.context = unit.RoObject(project_id='t', roles=[])
        self.service.storage.find_zones = mock.Mock()
        self.service.find_zones(self.context)
        self.assertTrue(self.service.storage.find_zones.called)

        self.mock_policy_check.assert_called_with(
            'find_zones', mock.ANY, {'project_id': 't', 'tenant_id': 't'}
        )

    def test_delete_zone_has_subzone(self):
        self.context.abandon = False
        self.context.hard_delete = False
        self.service.storage.get_zone.return_value = unit.RoObject(
            name='foo',
            tenant_id='2',
            shared=self.zone_shared,
            type='PRIMARY',
        )
        self.service.storage.count_zones.return_value = 2

        self.assertRaises(exceptions.ZoneHasSubZone,
                          self.service.delete_zone,
                          self.context,
                          CentralZoneTestCase.zone_id)

        self.mock_policy_check.assert_called_with(
            'delete_zone', mock.ANY, {
                'zone_id': CentralZoneTestCase.zone_id,
                'zone_name': 'foo',
                'project_id': '2',
                'tenant_id': '2'
            }
        )

    @mock.patch.object(designate.central.service.Service,
                       '_ensure_catalog_zone_serial_increment')
    def test_delete_zone_abandon(
            self, mock_ensure_catalog_zone_serial_increment):
        self.service.storage.get_zone.return_value = unit.RoObject(
            name='foo',
            tenant_id='2',
            id=CentralZoneTestCase.zone_id_2,
            shared=self.zone_shared,
            type='PRIMARY',
        )
        self.context.abandon = True
        self.service.storage.count_zones.return_value = 0
        self.service.delete_zone(self.context,
                                 CentralZoneTestCase.zone_id)
        self.assertTrue(self.service.storage.delete_zone.called)
        self.assertFalse(self.service.worker_api.delete_zone.called)

        self.mock_policy_check.assert_called_with(
            'abandon_zone', mock.ANY, {
                'zone_id': CentralZoneTestCase.zone_id,
                'zone_name': 'foo',
                'project_id': '2',
                'tenant_id': '2'
            }
        )

    # RoObject not compatible with _ensure_catalog_zone_serial_increment
    @mock.patch.object(designate.central.service.Service,
                       '_ensure_catalog_zone_serial_increment')
    def test_delete_zone(self, mock_ensure_catalog_zone_serial_increment):
        self.context.abandon = False
        self.context.hard_delete = False
        self.service.storage.get_zone.return_value = unit.RoObject(
            name='foo',
            tenant_id='2',
            shared=self.zone_shared,
            type='PRIMARY',
        )
        self.service._delete_zone_in_storage = mock.Mock(
            return_value=unit.RoObject(
                name='foo'
            )
        )
        self.service.storage.count_zones.return_value = 0
        out = self.service.delete_zone(self.context,
                                       CentralZoneTestCase.zone_id)
        self.assertFalse(self.service.storage.delete_zone.called)
        self.assertTrue(self.service.worker_api.delete_zone.called)

        self.mock_policy_check.assert_called()
        ctx, deleted_dom = self.service.worker_api.delete_zone.call_args[0]

        self.assertEqual('foo', deleted_dom.name)
        self.assertEqual('foo', out.name)
        self.mock_policy_check.assert_called_with(
            'delete_zone', mock.ANY, {
                'zone_id': CentralZoneTestCase.zone_id,
                'zone_name': 'foo',
                'project_id': '2',
                'tenant_id': '2'
            }
        )

    # RoObject not compatible with _ensure_catalog_zone_serial_increment
    @mock.patch.object(designate.central.service.Service,
                       '_ensure_catalog_zone_serial_increment')
    def test_delete_zone_hard_delete(
            self, mock_ensure_catalog_zone_serial_increment):
        self.context.abandon = False
        self.context.hard_delete = True
        self.service.storage.get_zone.return_value = unit.RoObject(
            name='foo',
            tenant_id='2',
            shared=False,
            type='PRIMARY',
        )
        self.service._delete_zone_in_storage = mock.Mock(
            return_value=unit.RoObject(
                name='foo'
            )
        )
        self.service.storage.count_zones.return_value = 0
        out = self.service.delete_zone(self.context,
                                       CentralZoneTestCase.zone_id)
        self.assertFalse(self.service.storage.delete_zone.called)
        self.assertTrue(self.service.worker_api.delete_zone.called)
        self.mock_policy_check.assert_called()
        ctx, deleted_dom = (
            self.service.worker_api.delete_zone.call_args[0])

        self.assertEqual('foo', deleted_dom.name)
        self.assertEqual('foo', out.name)
        self.mock_policy_check.assert_called_with(
            'delete_zone', mock.ANY, {
                'zone_id': CentralZoneTestCase.zone_id,
                'zone_name': 'foo',
                'project_id': '2',
                'tenant_id': '2'
            }
        )

    def test_delete_zone_in_storage(self):
        self.service._ensure_catalog_zone_serial_increment = mock.Mock()
        self.service._delete_zone_in_storage(
            self.context,
            unit.RwObject(action='', status=''),
        )
        d = self.service.storage.update_zone.call_args[0][1]
        self.assertEqual('DELETE', d.action)
        self.assertEqual('PENDING', d.status)

    def test_xfr_zone_secondary(self):
        self.service.storage.get_zone.return_value = unit.RoObject(
            name='example.org.',
            tenant_id='2',
            type='SECONDARY',
            masters=[unit.RoObject(host='192.0.2.1', port=53)],
            serial=1,
        )
        with fx_worker:
            self.service.worker_api.get_serial_number.return_value = (
                'SUCCESS', 2
            )
            self.service.xfr_zone(
                self.context, CentralZoneTestCase.zone_id)
            self.assertTrue(
                self.service.worker_api.perform_zone_xfr.called)

            self.mock_policy_check.assert_called()
        self.mock_policy_check.assert_called_with(
            'xfr_zone', mock.ANY, {
                'zone_id': CentralZoneTestCase.zone_id,
                'zone_name': 'example.org.',
                'project_id': '2',
                'tenant_id': '2'
            }
        )

    def test_xfr_zone_not_secondary(self):
        self.service.storage.get_zone.return_value = unit.RoObject(
            name='example.org.',
            tenant_id='2',
            type='PRIMARY',
        )

        exc = self.assertRaises(rpc_dispatcher.ExpectedException,
                                self.service.xfr_zone,
                                self.context,
                                CentralZoneTestCase.zone_id)

        self.assertEqual(exceptions.BadRequest, exc.exc_info[0])

    def test_count_report(self):
        self.service.count_zones = mock.Mock(return_value=1)
        self.service.count_records = mock.Mock(return_value=2)
        self.service.count_tenants = mock.Mock(return_value=3)
        reports = self.service.count_report(
            self.context,
            criterion=None
        )
        self.assertEqual([{'zones': 1, 'records': 2, 'tenants': 3}], reports)

    def test_count_report_zones(self):
        self.service.count_zones = mock.Mock(return_value=1)
        self.service.count_records = mock.Mock(return_value=2)
        self.service.count_tenants = mock.Mock(return_value=3)
        reports = self.service.count_report(
            self.context,
            criterion='zones'
        )
        self.assertEqual([{'zones': 1}], reports)

    def test_count_report_records(self):
        self.service.count_zones = mock.Mock(return_value=1)
        self.service.count_records = mock.Mock(return_value=2)
        self.service.count_tenants = mock.Mock(return_value=3)
        reports = self.service.count_report(
            self.context,
            criterion='records'
        )
        self.assertEqual([{'records': 2}], reports)

    def test_count_report_tenants(self):
        self.service.count_zones = mock.Mock(return_value=1)
        self.service.count_records = mock.Mock(return_value=2)
        self.service.count_tenants = mock.Mock(return_value=3)
        reports = self.service.count_report(
            self.context,
            criterion='tenants'
        )
        self.assertEqual([{'tenants': 3}], reports)

    def test_count_report_not_found(self):
        self.service.count_zones = mock.Mock(return_value=1)
        self.service.count_records = mock.Mock(return_value=2)
        self.service.count_tenants = mock.Mock(return_value=3)

        exc = self.assertRaises(rpc_dispatcher.ExpectedException,
                                self.service.count_report,
                                self.context,
                                criterion='bogus')

        self.assertEqual(exceptions.ReportNotFound, exc.exc_info[0])

    def test_get_recordset_not_found(self):
        zone = MockZone()
        zone.id = CentralZoneTestCase.zone_id
        self.service.storage.get_zone.return_value = zone
        self.service.storage.find_recordset.return_value = unit.RoObject(
            zone_id=CentralZoneTestCase.zone_id_2
        )

        exc = self.assertRaises(rpc_dispatcher.ExpectedException,
                                self.service.get_recordset,
                                self.context,
                                CentralZoneTestCase.zone_id,
                                CentralZoneTestCase.recordset_id)

        self.assertEqual(exceptions.RecordSetNotFound, exc.exc_info[0])

    def test_get_recordset(self):
        self.service.storage.get_zone.return_value = unit.RoObject(
            id=CentralZoneTestCase.zone_id_2,
            name='example.org.',
            tenant_id='2',
            shared=self.zone_shared,
        )
        recordset = objects.RecordSet(
            zone_id=CentralZoneTestCase.zone_id_2,
            zone_name='example.org.',
            id=CentralZoneTestCase.recordset_id
        )

        self.service.storage.find_recordset.return_value = recordset

        self.service.get_recordset(
            self.context,
            CentralZoneTestCase.zone_id_2,
            CentralZoneTestCase.recordset_id,
        )

        self.mock_policy_check.assert_called_with(
            'get_recordset', mock.ANY, {
                'zone_id': CentralZoneTestCase.zone_id_2,
                'zone_name': 'example.org.',
                'zone_shared': False,
                'recordset_id': CentralZoneTestCase.recordset_id,
                'project_id': '2',
                'tenant_id': '2'
            }
        )

    def test_get_recordset_no_zone_id(self):
        self.service.storage.get_zone.return_value = unit.RoObject(
            id=CentralZoneTestCase.zone_id_2,
            name='example.org.',
            tenant_id='2',
            shared=self.zone_shared,
        )
        recordset = objects.RecordSet(
            zone_id=CentralZoneTestCase.zone_id_2,
            zone_name='example.org.',
            id=CentralZoneTestCase.recordset_id
        )

        self.service.storage.find_recordset.return_value = recordset

        # Set the zone_id value to false
        self.service.get_recordset(
            self.context,
            False,
            CentralZoneTestCase.recordset_id,
        )

        self.mock_policy_check.assert_called_with(
            'get_recordset', mock.ANY, {
                'zone_id': CentralZoneTestCase.zone_id_2,
                'zone_name': 'example.org.',
                'zone_shared': False,
                'recordset_id': CentralZoneTestCase.recordset_id,
                'project_id': '2',
                'tenant_id': '2'
            }
        )

    def test_find_recordsets(self):
        self.context = mock.Mock()
        self.context.project_id = 't'
        self.service.find_recordsets(self.context)
        self.assertTrue(self.service.storage.find_recordsets.called)

        self.mock_policy_check.assert_called_with(
            'find_recordsets', mock.ANY, {'project_id': 't', 'tenant_id': 't'}
        )

    def test_find_recordset(self):
        self.context = mock.Mock()
        self.context.project_id = 't'
        self.service.storage.get_zone.return_value = MockZone()
        self.service.find_recordset(self.context)
        self.assertTrue(self.service.storage.find_recordset.called)
        self.mock_policy_check.assert_called_with(
            'find_recordset', mock.ANY, {'project_id': 't', 'tenant_id': 't'}
        )

    def test_update_recordset_fail_on_changes(self):
        self.service.storage.get_zone.return_value = unit.RoObject()
        recordset = mock.Mock(spec=objects.RecordSet)
        recordset.obj_get_original_value.return_value = '1'

        recordset.obj_get_changes.return_value = ['tenant_id', 'foo']
        exc = self.assertRaises(rpc_dispatcher.ExpectedException,
                                self.service.update_recordset,
                                self.context,
                                recordset)

        self.assertEqual(exceptions.BadRequest, exc.exc_info[0])

        recordset.obj_get_changes.return_value = ['zone_id', 'foo']
        exc = self.assertRaises(rpc_dispatcher.ExpectedException,
                                self.service.update_recordset,
                                self.context,
                                recordset)

        self.assertEqual(exceptions.BadRequest, exc.exc_info[0])

        recordset.obj_get_changes.return_value = ['type', 'foo']
        exc = self.assertRaises(rpc_dispatcher.ExpectedException,
                                self.service.update_recordset,
                                self.context,
                                recordset)

        self.assertEqual(exceptions.BadRequest, exc.exc_info[0])

    def test_update_recordset_action_delete(self):
        self.service.storage.get_zone.return_value = unit.RoObject(
            action='DELETE', tenant_id='', type='PRIMARY'
        )
        recordset = mock.Mock(spec=objects.RecordSet)
        recordset.obj_get_changes.return_value = ['foo']

        exc = self.assertRaises(rpc_dispatcher.ExpectedException,
                                self.service.update_recordset,
                                self.context,
                                recordset)

        self.assertEqual(exceptions.BadRequest, exc.exc_info[0])

    def test_update_recordset_action_fail_on_managed(self):
        self.service.storage.get_zone.return_value = unit.RoObject(
            type='foo',
            name='example.org.',
            tenant_id='2',
            action='bogus',
            shared=self.zone_shared,
        )
        recordset = mock.Mock(spec=objects.RecordSet)
        recordset.obj_get_changes.return_value = ['foo']
        recordset.managed = True
        self.context = mock.Mock()
        self.context.edit_managed_records = False

        exc = self.assertRaises(rpc_dispatcher.ExpectedException,
                                self.service.update_recordset,
                                self.context,
                                recordset)

        self.assertEqual(exceptions.BadRequest, exc.exc_info[0])

    def test_update_recordset_worker_model(self):
        self.service.storage.get_zone.return_value = unit.RoObject(
            type='foo',
            name='example.org.',
            tenant_id='2',
            action='bogus',
            shared=self.zone_shared,
        )
        recordset = mock.Mock(spec=objects.RecordSet)
        recordset.obj_get_changes.return_value = ['foo']
        recordset.obj_get_original_value.return_value = (
            '9c85d9b0-1e9d-4e99-aede-a06664f1af2e'
        )
        recordset.managed = False
        self.service._update_recordset_in_storage = mock.Mock(
            return_value=('x', 'y')
        )

        with fx_worker:
            self.service.update_recordset(self.context, recordset)
        self.assertTrue(
            self.service._update_recordset_in_storage.called)

        self.mock_policy_check.assert_called_with(
            'update_recordset', mock.ANY, {
                'recordset_id': '9c85d9b0-1e9d-4e99-aede-a06664f1af2e',
                'recordset_project_id': '9c85d9b0-1e9d-4e99-aede-a06664f1af2e',
                'zone_id': '9c85d9b0-1e9d-4e99-aede-a06664f1af2e',
                'zone_name': 'example.org.',
                'zone_shared': self.zone_shared,
                'zone_type': 'foo',
                'project_id': '2',
                'tenant_id': '2'
            }
        )

    def test_update_recordset_in_storage(self):
        recordset = mock.Mock()
        recordset.name = 'n'
        recordset.type = 't'
        recordset.id = CentralZoneTestCase.recordset_id
        recordset.obj_get_changes.return_value = {'ttl': 90}
        recordset.ttl = 90
        recordset.records = []
        self.service._is_valid_recordset_name = mock.Mock()
        self.service._is_valid_recordset_placement = mock.Mock()
        self.service._is_valid_recordset_placement_subzone = mock.Mock()
        self.service._is_valid_ttl = mock.Mock()
        self.service._update_zone_in_storage = mock.Mock()

        self.service._update_recordset_in_storage(
            self.context,
            unit.RoObject(serial=3),
            recordset,
        )

        self.assertEqual(
            'n',
            self.service._is_valid_recordset_name.call_args[0][2]
        )
        self.assertEqual(
            ('n', 't', CentralZoneTestCase.recordset_id),
            self.service._is_valid_recordset_placement.call_args[0][2:]
        )
        self.assertEqual(
            'n',
            self.service._is_valid_recordset_placement_subzone.
            call_args[0][2]
        )
        self.assertEqual(
            90,
            self.service._is_valid_ttl.call_args[0][1]
        )
        self.assertTrue(self.service.storage.update_recordset.called)
        self.assertTrue(self.service._update_zone_in_storage.called)

    def test_update_recordset_in_storage_2(self):
        recordset = mock.Mock()
        recordset.name = 'n'
        recordset.type = 't'
        recordset.id = CentralZoneTestCase.recordset_id
        recordset.ttl = None
        recordset.obj_get_changes.return_value = {'ttl': None}
        recordset.records = [unit.RwObject(
            action='a',
            status='s',
            serial=9,
        )]
        self.service._is_valid_recordset_name = mock.Mock()
        self.service._is_valid_recordset_placement = mock.Mock()
        self.service._is_valid_recordset_placement_subzone = mock.Mock()
        self.service._update_zone_in_storage = mock.Mock()
        self.service._enforce_record_quota = mock.Mock()

        self.service._update_recordset_in_storage(
            self.context,
            unit.RoObject(serial=3),
            recordset,
            increment_serial=False,
        )

        self.assertEqual(
            'n',
            self.service._is_valid_recordset_name.call_args[0][2]
        )
        self.assertEqual(
            ('n', 't', CentralZoneTestCase.recordset_id),
            self.service._is_valid_recordset_placement.call_args[0][2:]
        )
        self.assertEqual(
            'n',
            self.service._is_valid_recordset_placement_subzone.
            call_args[0][2]
        )
        self.assertFalse(self.service._update_zone_in_storage.called)
        self.assertTrue(self.service.storage.update_recordset.called)
        self.assertTrue(self.service._enforce_record_quota.called)

    def test_delete_recordset_not_found(self):
        self.service.storage.get_zone.return_value = unit.RoObject(
            action='bogus',
            id=CentralZoneTestCase.zone_id_2,
            name='example.org.',
            tenant_id='2',
            type='foo',
            shared=self.zone_shared,
        )
        self.service.storage.find_recordset.side_effect = (
            exceptions.RecordSetNotFound()
        )
        self.context = mock.Mock()
        self.context.edit_managed_records = False

        exc = self.assertRaises(rpc_dispatcher.ExpectedException,
                                self.service.delete_recordset,
                                self.context,
                                CentralZoneTestCase.zone_id_2,
                                CentralZoneTestCase.recordset_id)

        self.assertEqual(exceptions.RecordSetNotFound, exc.exc_info[0])

    def test_delete_recordset_action_delete(self):
        self.service.storage.get_zone.return_value = unit.RoObject(
            action='DELETE',
            id=CentralZoneTestCase.zone_id_2,
            name='example.org.',
            tenant_id='2',
            type='foo',
        )
        self.service.storage.find_recordset.return_value = unit.RoObject(
            zone_id=CentralZoneTestCase.zone_id_2,
            id=CentralZoneTestCase.recordset_id,
            managed=False,
        )
        self.context = mock.Mock()
        self.context.edit_managed_records = False

        exc = self.assertRaises(rpc_dispatcher.ExpectedException,
                                self.service.delete_recordset,
                                self.context,
                                CentralZoneTestCase.zone_id_2,
                                CentralZoneTestCase.recordset_id)

        self.assertEqual(exceptions.BadRequest, exc.exc_info[0])

    def test_delete_recordset_managed(self):
        self.service.storage.get_zone.return_value = unit.RoObject(
            action='foo',
            id=CentralZoneTestCase.zone_id_2,
            name='example.org.',
            tenant_id='2',
            type='foo',
            shared=self.zone_shared,
        )
        self.service.storage.find_recordset.return_value = unit.RoObject(
            zone_id=CentralZoneTestCase.zone_id_2,
            id=CentralZoneTestCase.recordset_id,
            managed=True,
            tenant_id='2',
        )
        self.context = mock.Mock()
        self.context.edit_managed_records = False

        exc = self.assertRaises(rpc_dispatcher.ExpectedException,
                                self.service.delete_recordset,
                                self.context,
                                CentralZoneTestCase.zone_id_2,
                                CentralZoneTestCase.recordset_id)

        self.assertEqual(exceptions.BadRequest, exc.exc_info[0])

    def test_delete_recordset_worker(self):
        mock_zone = unit.RoObject(
            action='foo',
            id=CentralZoneTestCase.zone_id_2,
            name='example.org.',
            tenant_id='2',
            type='foo',
            shared=self.zone_shared,
        )
        mock_rs = objects.RecordSet(
            zone_id=CentralZoneTestCase.zone_id_2,
            zone_name='example.org.',
            id=CentralZoneTestCase.recordset_id,
            records=objects.RecordList.from_list([]),
        )

        self.service.storage.get_zone.return_value = mock_zone
        self.service.storage.find_recordset.return_value = mock_rs
        self.context = mock.Mock()
        self.context.edit_managed_records = False
        self.service._delete_recordset_in_storage = mock.Mock(
            return_value=(mock_rs, mock_zone)
        )

        with fx_worker:
            self.service.delete_recordset(self.context,
                                          CentralZoneTestCase.zone_id_2,
                                          CentralZoneTestCase.recordset_id)

        self.assertTrue(
            self.service._delete_recordset_in_storage.called)

    def test_delete_recordset_in_storage(self):
        def mock_uds(c, zone, inc):
            return zone

        self.service._update_zone_in_storage = mock_uds
        self.service._delete_recordset_in_storage(
            self.context,
            unit.RoObject(serial=1, shared=self.zone_shared),
            unit.RoObject(id=2, records=[
                unit.RwObject(
                    action='',
                    status='',
                    serial=0,
                    increment_serial=False,
                )
            ])
        )
        self.assertTrue(self.service.storage.update_recordset.called)
        self.assertTrue(self.service.storage.delete_recordset.called)
        rs = self.service.storage.update_recordset.call_args[0][1]
        self.assertEqual(1, len(rs.records))
        self.assertEqual('DELETE', rs.records[0].action)
        self.assertEqual('PENDING', rs.records[0].status)
        self.assertTrue(rs.records[0].serial, 1)

    def test_delete_recordset_in_storage_no_increment_serial(self):
        self.service._update_zone_in_storage = mock.Mock()
        self.service._delete_recordset_in_storage(
            self.context,
            unit.RoObject(serial=1, shared=self.zone_shared),
            unit.RoObject(id=2, records=[
                unit.RwObject(
                    action='',
                    status='',
                    serial=0,
                )
            ]),
            increment_serial=False,
        )
        self.assertTrue(self.service.storage.update_recordset.called)
        self.assertTrue(self.service.storage.delete_recordset.called)
        self.assertFalse(self.service._update_zone_in_storage.called)

    def test_count_recordset(self):
        self.service.count_recordsets(self.context)
        self.mock_policy_check.assert_called_with(
            'count_recordsets', mock.ANY, {
                'project_id': None, 'tenant_id': None}
        )

    def test_count_records(self):
        self.service.count_records(self.context)
        self.mock_policy_check.assert_called_with(
            'count_records', mock.ANY, {'project_id': None, 'tenant_id': None}
        )

    def test_determine_floatingips(self):
        self.context = mock.Mock()
        self.context.project_id = 'tnt'
        self.service.find_records = mock.Mock(return_value=[
            unit.RoObject(managed_extra='')
        ])

        fips = {}
        data, invalid = self.service._determine_floatingips(
            self.context, fips)
        self.assertEqual({}, data)
        self.assertEqual([], invalid)

    def test_determine_floatingips_with_data(self):
        self.context = mock.Mock()
        self.context.project_id = 2
        self.service.find_records = mock.Mock(return_value=[
            unit.RoObject(managed_extra=1, managed_tenant_id=1),
            unit.RoObject(managed_extra=2, managed_tenant_id=2),
        ])

        fips = {
            'k': {'address': 1},
            'k2': {'address': 2},
        }
        data, invalid = self.service._determine_floatingips(
            self.context, fips)
        self.assertEqual(1, len(invalid))
        self.assertEqual(1, invalid[0].managed_tenant_id)
        self.assertEqual(data['k'], ({'address': 1}, None))

    def test_generate_soa_refresh_interval(self):
        central_service = self.central_service
        with random_seed(42):
            refresh_time = central_service._generate_soa_refresh_interval()
            self.assertEqual(3563, refresh_time)


class IsSubzoneTestCase(CentralBasic):
    def setUp(self):
        super().setUp()

        def find_zone(ctx, criterion):
            LOG.debug('Calling find_zone on %r' % criterion)
            if criterion['name'] == 'example.com.':
                LOG.debug('Returning %r' % criterion['name'])
                return criterion['name']

            LOG.debug('Not found')
            raise exceptions.ZoneNotFound

        self.service.storage.find_zone = find_zone

    def test_is_subzone_false(self):
        r = self.service._is_subzone(self.context, 'com',
                                     CentralZoneTestCase.pool_id)
        self.assertFalse(r)

    def FIXME_test_is_subzone_false2(self):
        r = self.service._is_subzone(self.context, 'com.',
                                     CentralZoneTestCase.pool_id)
        self.assertEqual('com.', r)

    def FIXME_test_is_subzone_false3(self):
        r = self.service._is_subzone(self.context, 'example.com.',
                                     CentralZoneTestCase.pool_id)
        self.assertEqual('example.com.', r)

    def test_is_subzone_false4(self):
        r = self.service._is_subzone(
            self.context, 'foo.a.b.example.com.',
            CentralZoneTestCase.pool_id)
        self.assertEqual('example.com.', r)


class CentralZoneExportTests(CentralBasic):
    def setUp(self):
        super().setUp()

        def storage_find_tld(c, d):
            if d['name'] not in ('org',):
                raise exceptions.TldNotFound

        self.service.storage.find_tld = storage_find_tld

    def test_create_zone_export(self):
        self.context = mock.Mock()
        self.context.project_id = 't'

        self.service.storage.get_zone.return_value = unit.RoObject(
            name='example.com.',
            id=CentralZoneTestCase.zone_id,
            shared=False,
            tenant_id='t',
        )

        self.service.storage.create_zone_export = mock.Mock(
            return_value=unit.RwObject(
                id=CentralZoneTestCase.zone_export_id,
                zone_id=CentralZoneTestCase.zone_id,
                task_type='EXPORT',
                status='PENDING',
                message=None,
                tenant_id='t',
                location=None,
            )
        )

        self.service.worker_api.start_zone_export = mock.Mock()

        out = self.service.create_zone_export(
            self.context,
            CentralZoneTestCase.zone_export_id
        )
        self.assertEqual(CentralZoneTestCase.zone_id, out.zone_id)
        self.assertEqual('PENDING', out.status)
        self.assertEqual('EXPORT', out.task_type)
        self.assertIsNone(out.message)
        self.assertEqual('t', out.tenant_id)

    def test_get_zone_export(self):
        self.context = mock.Mock()
        self.context.project_id = 't'

        self.service.storage.get_zone_export.return_value = unit.RoObject(
            zone_id=CentralZoneTestCase.zone_id,
            task_type='EXPORT',
            status='PENDING',
            message=None,
            tenant_id='t'
        )

        out = self.service.get_zone_export(
            self.context,
            CentralZoneTestCase.zone_export_id)

        self.mock_policy_check.assert_called_with(
            'get_zone_export', mock.ANY, {'project_id': 't', 'tenant_id': 't'}
        )

        # Check output
        self.assertEqual(CentralZoneTestCase.zone_id, out.zone_id)
        self.assertEqual('PENDING', out.status)
        self.assertEqual('EXPORT', out.task_type)
        self.assertIsNone(out.message)
        self.assertEqual('t', out.tenant_id)

    def test_find_zone_exports(self):
        self.context = mock.Mock()
        self.context.project_id = 't'
        self.service.storage.find_zone_exports = mock.Mock()

        self.service.find_zone_exports(self.context)

        self.assertTrue(self.service.storage.find_zone_exports.called)

        self.mock_policy_check.assert_called_with(
            'find_zone_exports', mock.ANY, {
                'project_id': 't', 'tenant_id': 't'}
        )

    def test_find_zone_exports_with_custom_criterion(self):
        self.context = mock.Mock()
        self.context.project_id = 't'
        self.service.storage.find_zone_exports = mock.Mock()

        self.service.find_zone_exports(
            self.context, criterion={'project_id': 't'}
        )

        self.assertTrue(self.service.storage.find_zone_exports.called)

        self.mock_policy_check.assert_called_with(
            'find_zone_exports', mock.ANY, {
                'project_id': 't', 'tenant_id': 't'}
        )

    def test_delete_zone_export(self):
        self.context = mock.Mock()
        self.context.project_id = 't'

        self.service.storage.delete_zone_export = mock.Mock(
            return_value=unit.RoObject(
                zone_id=CentralZoneTestCase.zone_id,
                task_type='EXPORT',
                status='PENDING',
                message=None,
                tenant_id='t',
                type='PRIMARY',
            )
        )

        out = self.service.delete_zone_export(
            self.context,
            CentralZoneTestCase.zone_export_id)

        self.assertTrue(self.service.storage.delete_zone_export.called)

        self.assertEqual(CentralZoneTestCase.zone_id, out.zone_id)
        self.assertEqual('PENDING', out.status)
        self.assertEqual('EXPORT', out.task_type)
        self.assertIsNone(out.message)
        self.assertEqual('t', out.tenant_id)

        self.mock_policy_check.assert_called_with(
            'delete_zone_export', mock.ANY, {
                'zone_export_id': 'e887597f-9697-47dd-a202-7a2711f8669c',
                'project_id': 't', 'tenant_id': 't'
            }
        )


class CentralStatusTests(CentralBasic):
    def test_update_zone_or_record_status_no_zone(self):
        zone = unit.RwObject(
            id='uuid',
            action='CREATE',
            status='SUCCESS',
            serial=0,
        )

        self.service.storage.get_zone.return_value = zone
        self.service.storage.find_records.return_value = []

        new_zone = self.service.update_status(
            self.context, zone.id, 'NO_ZONE', 0, 'CREATE')

        self.assertEqual(new_zone.action, 'CREATE')
        self.assertEqual(new_zone.status, 'ERROR')

    def test_update_zone_or_record_status_handle_update_after_create(self):
        zone = unit.RwObject(
            id='uuid',
            action='UPDATE',
            status='PENDING',
            serial=0,
        )

        self.service.storage.get_zone.return_value = zone
        self.service.storage.find_records.return_value = []

        new_zone = self.service.update_status(
            self.context, zone.id, 'PENDING', 0, 'CREATE')

        self.assertEqual(new_zone.action, 'UPDATE')
        self.assertEqual(new_zone.status, 'PENDING')


class CentralQuotaTest(designate.tests.functional.TestCase):
    def setUp(self):
        super().setUp()
        self.config(quota_driver='noop')
        self.context = mock.Mock()
        self.zone = mock.Mock()
        self.quotas_of_one = {
            'zones': 1,
            'zone_recordsets': 1,
            'zone_records': 1,
            'recordset_records': 1,
            'api_export_size': 1
        }
        self.zone.shared = False
        self.service = service.Service()
        self.service._quota = None
        self.service._storage = mock.Mock()
        self.service.notifier = mock.Mock()
        self.service.quota.get_quotas = mock.Mock()

    def test_zone_record_quota_allows_lowering_value(self):
        self.service._quota = mock.Mock()
        self.service.storage.count_records.return_value = 10

        recordset = mock.Mock(spec=objects.RecordSet)
        recordset.managed = False
        recordset.records = ['1.1.1.%i' % (i + 1) for i in range(5)]

        self.service._enforce_record_quota(
            self.context, self.zone, recordset
        )

        # Ensure we check against the number of records that will
        # result in the API call. The 5 value is as if there were 10
        # unmanaged records unders a single recordset. We find 10
        # total - 10 for the recordset being passed in and add the 5
        # from the new recordset.
        check_zone_records = mock.call(
            self.context, self.zone.tenant_id, zone_records=10 - 10 + 5
        )
        self.assertIn(
            check_zone_records, self.service.quota.limit_check.mock_calls
        )

        # Check the recordset limit as well
        check_recordset_records = mock.call(
            self.context, self.zone.tenant_id, recordset_records=5
        )
        self.assertIn(
            check_recordset_records, self.service.quota.limit_check.mock_calls
        )

    def test_enforce_zone_quota(self):
        self.service.quota.get_quotas.return_value = self.quotas_of_one

        # Test creating one zone, 1 quota, no existing zones
        self.service.storage.count_zones.return_value = 0
        self.assertIsNone(
            self.service._enforce_zone_quota(self.context, 'fake_project_id')
        )

        # Test creating one zone, 1 quota, one existing zone
        self.service.storage.count_zones.return_value = 1
        self.assertRaisesRegex(
            exceptions.OverQuota,
            'Quota exceeded for zones',
            self.service._enforce_zone_quota,
            self.context, 'fake_project_id'
        )

    def test_enforce_recordset_quota(self):
        self.service.quota.get_quotas.return_value = self.quotas_of_one

        # Test creating one recordset, 1 quota, no existing recordsets
        self.service.storage.count_recordsets.return_value = 0
        self.assertIsNone(
            self.service._enforce_recordset_quota(
                self.context, self.zone
            )
        )

        # Test creating one recordset, 1 quota, one existing recordset
        self.service.storage.count_recordsets.return_value = 1
        self.assertRaisesRegex(
            exceptions.OverQuota,
            'Quota exceeded for zone_recordsets',
            self.service._enforce_recordset_quota,
            self.context, self.zone
        )

    def test_enforce_record_quota(self):
        self.service.quota.get_quotas.return_value = self.quotas_of_one

        self.service.storage.count_records.side_effect = [
            0, 0,
            1, 0,
            0, 1,
            1, 1,
            1, 1,
            1, 1,
        ]

        managed_recordset = mock.Mock(spec=objects.RecordSet)
        managed_recordset.managed = True

        recordset_one_record = mock.Mock()
        recordset_one_record.managed = False
        recordset_one_record.records = ['192.0.2.1']

        # Test that managed recordsets have no quota limit
        self.assertIsNone(
            self.service._enforce_record_quota(
                self.context, self.zone, managed_recordset
            )
        )
        self.service.storage.count_records.assert_not_called()

        # Test creating recordset with one record, no existing zone records,
        # no existing recordsets
        self.assertIsNone(
            self.service._enforce_record_quota(
                self.context, self.zone, recordset_one_record
            )
        )

        # Test creating recordset with one record, one existing zone record,
        # no exiting recordsets
        self.assertRaisesRegex(
            exceptions.OverQuota,
            'Quota exceeded for zone_records',
            self.service._enforce_record_quota, self.context, self.zone,
            recordset_one_record
        )

        # Test creating recordset with one record, one existing zone record,
        # no exiting recordsets
        # Note: Recordsets replace the existing recordset
        self.assertIsNone(
            self.service._enforce_record_quota(
                self.context, self.zone, recordset_one_record
            )
        )

        # Test creating recordset with one record, no existing zone record,
        # one exiting recordsets
        # Note: Recordsets replace the existing recordset
        self.assertIsNone(
            self.service._enforce_record_quota(
                self.context, self.zone, recordset_one_record
            )
        )

        recordset_two_record = mock.Mock()
        recordset_two_record.managed = False
        recordset_two_record.records = ['192.0.2.1', '192.0.2.2']

        # Test creating recordset with two records, one existing zone record,
        # one exiting recordsets
        self.assertRaisesRegex(
            exceptions.OverQuota,
            'Quota exceeded for zone_records',
            self.service._enforce_record_quota, self.context, self.zone,
            recordset_two_record
        )

        # Test creating a recordset with a shared zone
        mock_zone = MockZone()
        mock_zone.shared = True
        self.service.quota.limit_check = mock.Mock()
        self.service.storage.count_records = mock.Mock(return_value=1)
        self.service._enforce_record_quota(
            self.context, mock_zone, recordset_one_record
        )
        self.service.quota.limit_check.assert_called_with(
            self.context, mock_zone.tenant_id, recordset_records=1
        )
