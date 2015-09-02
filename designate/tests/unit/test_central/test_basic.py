# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Federico Ceratto <federico.ceratto@hp.com>
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

import unittest

from mock import Mock
from mock import patch
from oslo_config import cfg
from oslo_config import fixture as cfg_fixture
from oslotest import base
from testtools import ExpectedException as raises  # with raises(...): ...
import fixtures
import mock

from designate import exceptions
from designate.central.service import Service
import designate.central.service


# FIXME: create mock, do not use cfg
cfg.CONF.import_opt('storage_driver', 'designate.central',
                    group='service:central')


# TODO(Federico): move this

def unwrap(f):
    """Unwrap a decorated function
    Requires __wrapped_function and __wrapper_name to be set
    """
    for _ in range(42):
        try:
            uf = getattr(f, '__wrapped_function')
            print("Unwrapping %s from %s" % (f.func_name, f.__wrapper_name))
            f = uf
        except AttributeError:
            return f

    return f


class RwObject(object):
    """Object mock: raise exception on __setitem__ or __setattr__
    on any item/attr created after initialization.
    Allows updating existing items/attrs
    """
    def __init__(self, d=None, **kw):
        if d:
            kw.update(d)
        self.__dict__.update(kw)

    def __getitem__(self, k):
        try:
            return self.__dict__[k]
        except KeyError:
            cn = self.__class__.__name__
            raise NotImplementedError(
                "Attempt to perform __getitem__"
                " %r on %s %r" % (cn, k, self.__dict__)
            )

    def __setitem__(self, k, v):
        if k in self.__dict__:
            self.__dict__.update({k: v})
            return

        cn = self.__class__.__name__
        raise NotImplementedError(
            "Attempt to perform __setitem__ or __setattr__"
            " %r on %s %r" % (cn, k, self.__dict__)
        )

    def __setattr__(self, k, v):
        self.__setitem__(k, v)


class RoObject(RwObject):
    """Read-only Object mock: raise exception on unexpected
    __setitem__ or __setattr__
    """
    def __setitem__(self, k, v):
        cn = self.__class__.__name__
        raise NotImplementedError(
            "Attempt to perform __setitem__ or __setattr__"
            " %r on %s %r" % (cn, k, self.__dict__)
        )


class MockObjectTest(base.BaseTestCase):
    def test_ro(self):
        o = RoObject(a=1)
        self.assertEqual(o['a'], 1)
        self.assertEqual(o.a, 1)
        with raises(NotImplementedError):
            o.a = 2
        with raises(NotImplementedError):
            o.new = 1
        with raises(NotImplementedError):
            o['a'] = 2
        with raises(NotImplementedError):
            o['new'] = 1

    def test_rw(self):
        o = RwObject(a=1)
        self.assertEqual(o['a'], 1)
        self.assertEqual(o.a, 1)
        o.a = 2
        self.assertEqual(o.a, 2)
        self.assertEqual(o['a'], 2)
        o['a'] = 3
        self.assertEqual(o.a, 3)
        self.assertEqual(o['a'], 3)
        with raises(NotImplementedError):
            o.new = 1
        with raises(NotImplementedError):
            o['new'] = 1


def mock_out(name):
    def decorator(meth):
        def wrapper(self, a):
            return meth(self, a)

        wrapper = mock.patch(name)(wrapper)
        return wrapper
    return decorator


class MockDomain(object):
    id = 1
    name = 'example.org'
    pool_id = 1
    tenant_id = 3
    ttl = 1
    type = "PRIMARY"
    serial = 123

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


class MockRecordSet(object):
    id = 1
    name = 'example.org.'
    pool_id = 1
    tenant_id = 3
    ttl = 1
    type = "PRIMARY"
    serial = 123

    def obj_attr_is_set(self, n):
        if n == 'records':
            return False
        raise NotImplementedError()


class MockRecord(object):
    hostname = 'bar'

    def __getitem__(self, n):
        assert n == 'hostname'
        return 'bar'


class MockPool(object):
    ns_records = [MockRecord(), ]


# Fixtures

fx_mdns_api = fixtures.MockPatch('designate.central.service.mdns_rpcapi')

mdns_api = mock.PropertyMock(
    return_value=mock.NonCallableMagicMock(spec_set=[
        'a'
    ])
)

fx_pool_manager = fixtures.MockPatch(
    'designate.central.service.pool_manager_rpcapi.Pool'
    'ManagerAPI.get_instance',
    mock.MagicMock(spec_set=[
        'create_domain',
        'update_domain',
        'delete_domain'
    ])
)

fx_disable_notification = fixtures.MockPatch('designate.central.notification')


class NotMockedError(NotImplementedError):
    pass


@patch('designate.central.service.storage',
       mock.NonCallableMock(side_effect=NotMockedError))
class CentralBasic(base.BaseTestCase):

    def setUp(self):
        super(CentralBasic, self).setUp()
        self.CONF = self.useFixture(cfg_fixture.Config(cfg.CONF)).conf

        mock_storage = mock.NonCallableMagicMock(spec_set=[
            'count_domains', 'count_records', 'count_recordsets',
            'count_tenants', 'create_blacklist', 'create_domain',
            'create_pool', 'create_pool_attribute', 'create_quota',
            'create_record', 'create_recordset', 'create_tld',
            'create_tsigkey',
            'create_zone_task', 'delete_blacklist', 'delete_domain',
            'delete_pool', 'delete_pool_attribute', 'delete_quota',
            'delete_record', 'delete_recordset', 'delete_tld',
            'delete_tsigkey', 'delete_zone_task', 'find_blacklist',
            'find_blacklists', 'find_domain', 'find_domains', 'find_pool',
            'find_pool_attribute', 'find_pool_attributes', 'find_pools',
            'find_quota', 'find_quotas', 'find_record', 'find_records',
            'find_recordset', 'find_recordsets', 'find_recordsets_axfr',
            'find_tenants', 'find_tld', 'find_tlds', 'find_tsigkeys',
            'find_zone_task', 'find_zone_tasks', 'get_blacklist',
            'get_canonical_name', 'get_cfg_opts', 'get_domain', 'get_driver',
            'get_extra_cfg_opts', 'get_plugin_name', 'get_plugin_type',
            'get_pool', 'get_pool_attribute', 'get_quota', 'get_record',
            'get_recordset', 'get_tenant', 'get_tld', 'get_tsigkey',
            'get_zone_task', 'ping', 'register_cfg_opts',
            'register_extra_cfg_opts', 'update_blacklist', 'update_domain',
            'update_pool', 'update_pool_attribute', 'update_quota',
            'update_record', 'update_recordset', 'update_tld',
            'update_tsigkey', 'update_zone_task', 'commit', 'begin',
            'rollback', ])
        attrs = {
            'count_domains.return_value': 0,
            'find_domain.return_value': MockDomain(),
            'get_pool.return_value': MockPool(),
            'begin.return_value': None,
        }
        mock_storage.configure_mock(**attrs)
        designate.central.service.storage.get_storage.return_value = \
            mock_storage

        designate.central.service.policy = mock.NonCallableMock(spec_set=[
            'reset',
            'set_rules',
            'init',
            'check',
        ])

        designate.central.service.quota = mock.NonCallableMock(spec_set=[
            'get_quota',
        ])

        designate.central.service.storage = mock.NonCallableMock(spec_set=[
            'get_storage',
        ])
        designate.central.service.rpcapi = mock.Mock()
        designate.central.service.pool_manager_rpcapi = mock.Mock()
        self.context = mock.NonCallableMock(spec_set=[
            'elevated',
            'sudo',
            'abandon',
        ])

        self.service = Service()
        self.service.check_for_tlds = True
        self.service.notifier = mock.Mock()


class CentralServiceTestCase(CentralBasic):

    def setUp(self):
        super(CentralServiceTestCase, self).setUp()

    def test_mdns_api_patch(self):
        with fx_mdns_api:
            q = self.service.mdns_api
            assert 'mdns_rpcapi.MdnsAPI.get_instance' in repr(q)

    def test_conf_fixture(self):
        assert 'service:central' in designate.central.service.cfg.CONF

    def test_init(self):
        self.assertTrue(self.service.check_for_tlds)
        self.assertTrue(designate.central.service.storage.get_storage.called)

    def test__is_valid_ttl(self):
        self.CONF.set_override('min_ttl', 10, 'service:central')
        self.service._is_valid_ttl(self.context, 20)

        # policy.check() not to raise: the user is allowed to create low TTLs
        designate.central.service.policy.check = mock.Mock(return_value=None)
        self.service._is_valid_ttl(self.context, None)
        self.service._is_valid_ttl(self.context, 1)

        # policy.check() to raise
        designate.central.service.policy.check = mock.Mock(
            side_effect=exceptions.Forbidden
        )
        with raises(exceptions.InvalidTTL):
            self.service._is_valid_ttl(self.context, 3)

    def test__update_soa_secondary(self):
        ctx = mock.Mock()
        mock_zone = RoObject(type='SECONDARY')

        self.service._update_soa(ctx, mock_zone)
        self.assertFalse(ctx.elevated.called)

    def test__update_soa(self):
        class MockZone(dict):
            type = 'PRIMARY'
            pool_id = 1

        class MockRecord(object):
            data = None

        mock_soa = RoObject(records=[MockRecord()])

        self.context.elevated = mock.Mock()
        self.service._update_domain_in_storage = mock.Mock()
        self.service.storage.get_pool = mock.Mock(return_value=MockPool())
        self.service.find_recordset = mock.Mock(return_value=mock_soa)
        self.service._build_soa_record = mock.Mock()
        self.service._update_recordset_in_storage = mock.Mock()

        self.service._update_soa(self.context, MockDomain())

        self.assertTrue(self.service._update_recordset_in_storage.called)
        self.assertTrue(self.context.elevated.called)

    def test_count_domains(self):
        self.service.count_domains(self.context)
        self.service.storage.count_domains.assert_called_once_with(
            self.context, {}
        )

    def test_count_domains_criterion(self):
        self.service.count_domains(self.context, criterion={'a': 1})
        self.service.storage.count_domains.assert_called_once_with(
            self.context, {'a': 1}
        )

    def test_create_recordset_in_storage(self):
        self.service._enforce_recordset_quota = mock.Mock()
        self.service._is_valid_ttl = mock.Mock()
        self.service._is_valid_recordset_name = mock.Mock()
        self.service._is_valid_recordset_placement = mock.Mock()
        self.service._is_valid_recordset_placement_subdomain = mock.Mock()
        self.service.storage.create_recordset = mock.Mock(return_value='rs')
        self.service._update_domain_in_storage = mock.Mock()

        rs, domain = self.service._create_recordset_in_storage(
            self.context, MockDomain(), MockRecordSet()
        )
        self.assertEqual(rs, 'rs')
        self.assertFalse(self.service._update_domain_in_storage.called)

    def test__create_soa(self):
        self.service._create_recordset_in_storage = Mock(
            return_value=(None, None)
        )
        self.service._build_soa_record = Mock(
            return_value='example.org. foo.bar 1 60 5 999 1'
        )
        zone = MockDomain()
        self.service._create_soa(self.context, zone)

        ctx, md, rset = self.service._create_recordset_in_storage.call_args[0]

        self.assertEqual(rset.name, 'example.org.')
        self.assertEqual(rset.type, 'SOA')
        self.assertEqual(rset.type, 'SOA')
        self.assertEqual(len(rset.records.objects), 1)
        self.assertEqual(rset.records.objects[0].managed, True)

    def test__create_domain_in_storage(self):
        self.service._create_soa = Mock()
        self.service._create_ns = Mock()
        self.service.get_domain_servers = Mock(
            return_value=[RoObject(hostname='host_foo')]
        )

        def cr_dom(ctx, domain):
            return domain

        self.service.storage.create_domain = cr_dom

        domain = self.service._create_domain_in_storage(
            self.context, MockDomain()
        )
        self.assertEqual(domain.status, 'PENDING')
        self.assertEqual(domain.action, 'CREATE')
        ctx, domain, hostnames = self.service._create_ns.call_args[0]
        self.assertEqual(hostnames, ['host_foo'])

    @unittest.expectedFailure  # FIXME
    def test_create_domain_forbidden(self):
        assert not self.service.storage.count_domains.called
        designate.central.service.policy.check = mock.Mock(return_value=None)
        self.service._enforce_domain_quota = mock.Mock(return_value=None)
        self.service._is_valid_domain_name = mock.Mock(return_value=None)
        self.service._is_valid_ttl = mock.Mock(return_value=True)
        self.service._is_subdomain = Mock()
        self.service._create_domain_in_storage = mock.Mock(
            return_value=MockDomain()
        )
        self.service.storage.find_domain(self.context, {})

        parent_domain = self.service._is_subdomain(
            self.context, 'bogusname', 1234)

        # self.assertEqual(parent_domain, '')
        self.service.check_for_tlds = False
        with raises(exceptions.Forbidden):
            self.service.create_domain(self.context, MockDomain())

        # TODO(Federico) add more create_domain tests
        assert parent_domain


class CentralDomainTestCase(CentralBasic):
    def setUp(self):
        super(CentralDomainTestCase, self).setUp()

        def storage_find_tld(c, d):
            if d['name'] not in ('org',):
                raise exceptions.TldNotFound

        self.service.storage.find_tld = storage_find_tld

    def test__is_valid_domain_name_valid(self):
        self.service._is_blacklisted_domain_name = Mock()
        self.service._is_valid_domain_name(self.context, 'valid.org.')

    def test__is_valid_domain_name_invalid(self):
        self.service._is_blacklisted_domain_name = Mock()
        with raises(exceptions.InvalidDomainName):
            self.service._is_valid_domain_name(self.context, 'example^org.')

    def test__is_valid_domain_name_invalid_2(self):
        self.service._is_blacklisted_domain_name = Mock()
        with raises(exceptions.InvalidDomainName):
            self.service._is_valid_domain_name(self.context, 'example.tld.')

    def test__is_valid_domain_name_invalid_same_as_tld(self):
        self.service._is_blacklisted_domain_name = Mock()
        with raises(exceptions.InvalidDomainName):
            self.service._is_valid_domain_name(self.context, 'com.com.')

    def test__is_valid_domain_name_invalid_tld(self):
        self.service._is_blacklisted_domain_name = Mock()
        with raises(exceptions.InvalidDomainName):
            self.service._is_valid_domain_name(self.context, 'tld.')

    def test__is_valid_domain_name_blacklisted(self):
        self.service._is_blacklisted_domain_name = Mock(
            side_effect=exceptions.InvalidDomainName)
        with raises(exceptions.InvalidDomainName):
            self.service._is_valid_domain_name(self.context, 'valid.com.')

    def test__is_blacklisted_domain_name(self):
        self.service.storage.find_blacklists.return_value = [
            RoObject(pattern='a'), RoObject(pattern='b')
        ]
        blacklist_tests = (
            ('example.org', True),
            ('example.net', True),
            ('hi', False),
            ('', False)
        )
        for domain, expected in blacklist_tests:
            self.assertEqual(
                self.service._is_blacklisted_domain_name(self.context, domain),
                expected
            )

    def test__is_valid_recordset_name(self):
        domain = RoObject(name='example.org.')
        self.service._is_valid_recordset_name(self.context, domain,
                                              'foo..example.org.')

    def test__is_valid_recordset_name_no_dot(self):
        domain = RoObject(name='example.org.')
        with raises(ValueError):
            self.service._is_valid_recordset_name(self.context, domain,
                                                  'foo.example.org')

    def test__is_valid_recordset_name_too_long(self):
        domain = RoObject(name='example.org.')
        designate.central.service.cfg.CONF['service:central'].\
            max_recordset_name_len = 255
        rs_name = 'a' * 255 + '.org.'
        with raises(exceptions.InvalidRecordSetName) as e:
            self.service._is_valid_recordset_name(self.context, domain,
                                                  rs_name)
            self.assertEqual(e.message, 'Name too long')

    def test__is_valid_recordset_name_wrong_domain(self):
        domain = RoObject(name='example.org.')
        with raises(exceptions.InvalidRecordSetLocation):
            self.service._is_valid_recordset_name(self.context, domain,
                                                  'foo.example.com.')

    def test_is_valid_recordset_placement_cname(self):
        domain = RoObject(name='example.org.')
        with raises(exceptions.InvalidRecordSetLocation) as e:
            self.service._is_valid_recordset_placement(
                self.context,
                domain,
                'example.org.',
                'CNAME',
            )
            self.assertEqual(
                e.message,
                'CNAME recordsets may not be created at the zone apex'
            )

    def test_is_valid_recordset_placement_failing(self):
        domain = RoObject(name='example.org.', id='1')
        self.service.storage.find_recordsets.return_value = [
            RoObject(id='2')
        ]
        with raises(exceptions.InvalidRecordSetLocation) as e:
            self.service._is_valid_recordset_placement(
                self.context,
                domain,
                'example.org.',
                'A',
            )
            self.assertEqual(
                e.message,
                'CNAME recordsets may not share a name with any other records'
            )

    def test_is_valid_recordset_placement_failing_2(self):
        domain = RoObject(name='example.org.', id='1')
        self.service.storage.find_recordsets.return_value = [
            RoObject(),
            RoObject()
        ]
        with raises(exceptions.InvalidRecordSetLocation) as e:
            self.service._is_valid_recordset_placement(
                self.context,
                domain,
                'example.org.',
                'A',
            )
            self.assertEqual(
                e.message,
                'CNAME recordsets may not share a name with any other records'
            )

    def test_is_valid_recordset_placement(self):
        domain = RoObject(name='example.org.', id='1')
        self.service.storage.find_recordsets.return_value = []
        ret = self.service._is_valid_recordset_placement(
            self.context,
            domain,
            'example.org.',
            'A',
        )
        self.assertTrue(ret)

    def test__is_valid_recordset_placement_subdomain(self):
        domain = RoObject(name='example.org.', id='1')
        self.service._is_valid_recordset_placement_subdomain(
            self.context,
            domain,
            'example.org.'
        )

    def test__is_valid_recordset_placement_subdomain_2(self):
        domain = RoObject(name='example.org.', id='1')
        self.service._is_valid_recordset_name = Mock(side_effect=Exception)
        self.service.storage.find_domains.return_value = [
            RoObject(name='foo.example.org.')
        ]
        self.service._is_valid_recordset_placement_subdomain(
            self.context,
            domain,
            'bar.example.org.'
        )

    def test__is_valid_recordset_placement_subdomain_failing(self):
        domain = RoObject(name='example.org.', id='1')
        self.service._is_valid_recordset_name = Mock()
        self.service.storage.find_domains.return_value = [
            RoObject(name='foo.example.org.')
        ]
        with raises(exceptions.InvalidRecordSetLocation):
            self.service._is_valid_recordset_placement_subdomain(
                self.context,
                domain,
                'bar.example.org.'
            )

    def test__is_superdomain(self):
        self.service.storage.find_domains = Mock()
        self.service._is_superdomain(self.context, 'example.org.', '1')
        _class_self_, crit = self.service.storage.find_domains.call_args[0]
        self.assertEqual(crit, {'name': '%.example.org.', 'pool_id': '1'})

    @patch('designate.central.service.utils.increment_serial')
    def FIXME_test__increment_domain_serial(self, utils_inc_ser):
        fixtures.MockPatch('designate.central.service.utils.increment_serial')
        domain = RoObject(serial=1)
        self.service._increment_domain_serial(self.context, domain)

    def test__create_ns(self):
        self.service._create_recordset_in_storage = Mock(return_value=(0, 0))
        self.service._create_ns(
            self.context,
            RoObject(type='PRIMARY', name='example.org.'),
            [RoObject(), RoObject(), RoObject()]
        )
        ctx, zone, rset = \
            self.service._create_recordset_in_storage.call_args[0]

        self.assertEqual(rset.name, 'example.org.')
        self.assertEqual(rset.type, 'NS')
        self.assertEqual(len(rset.records), 3)
        self.assertTrue(rset.records[0].managed)

    def test__create_ns_skip(self):
        self.service._create_recordset_in_storage = Mock()
        self.service._create_ns(
            self.context,
            RoObject(type='SECONDARY', name='example.org.'),
            [],
        )
        self.assertFalse(self.service._create_recordset_in_storage.called)

    def test__add_ns_creation(self):
        self.service._create_ns = Mock()
        self.service.find_recordset = Mock(
            side_effect=exceptions.RecordSetNotFound
        )
        self.service._add_ns(
            self.context,
            RoObject(id='1'),
            RoObject(name='bar')
        )
        ctx, zone, records = self.service._create_ns.call_args[0]
        self.assertTrue(len(records), 1)

    def test__add_ns(self):
        self.service._update_recordset_in_storage = Mock()
        self.service.find_recordset = Mock(
            return_value=RoObject(records=[])
        )
        self.service._add_ns(
            self.context,
            RoObject(id='1'),
            RoObject(name='bar')
        )
        ctx, zone, rset = \
            self.service._update_recordset_in_storage.call_args[0]
        self.assertEqual(len(rset.records), 1)
        self.assertTrue(rset.records[0].managed)
        self.assertEqual(rset.records[0].data.name, 'bar')

    def test_create_domain_no_servers(self):
        self.service._enforce_domain_quota = Mock()
        self.service._is_valid_domain_name = Mock()
        self.service._is_valid_ttl = Mock()
        self.service._is_subdomain = Mock(
            return_value=False
        )
        self.service._is_superdomain = Mock(
            return_value=[]
        )
        self.service.storage.get_pool.return_value = RoObject(
            ns_records=[]
        )

        with raises(exceptions.NoServersConfigured):
            self.service.create_domain(
                self.context,
                RoObject(tenant_id='1', name='example.com.', ttl=60,
                         pool_id='2')
            )

    def test_create_domain(self):
        self.service._enforce_domain_quota = Mock()
        self.service._create_domain_in_storage = Mock(
            return_value=RoObject(
                name='example.com.',
                type='PRIMARY',
            )
        )
        self.service._is_valid_domain_name = Mock()
        self.service._is_valid_ttl = Mock()
        self.service._is_subdomain = Mock(
            return_value=False
        )
        self.service._is_superdomain = Mock(
            return_value=[]
        )
        self.service.storage.get_pool.return_value = RoObject(
            ns_records=[RoObject()]
        )
        # self.service.create_domain = unwrap(self.service.create_domain)

        out = self.service.create_domain(
            self.context,
            RoObject(
                tenant_id='1',
                name='example.com.',
                ttl=60,
                pool_id='2',
                type='PRIMARY'
            )
        )
        self.assertEqual(out.name, 'example.com.')

    def test_get_domain(self):
        self.service.storage.get_domain.return_value = RoObject(
            name='foo',
            tenant_id='2',
        )
        self.service.get_domain(self.context, '1')
        n, ctx, target = designate.central.service.policy.check.call_args[0]
        self.assertEqual(target['domain_id'], '1')
        self.assertEqual(target['domain_name'], 'foo')
        self.assertEqual(target['tenant_id'], '2')

    def test_get_domain_servers(self):
        self.service.storage.get_domain.return_value = RoObject(
            name='foo',
            tenant_id='2',
            pool_id='3',
        )

        self.service.get_domain_servers(
            self.context,
            domain_id='1'
        )

        ctx, pool_id = self.service.storage.get_pool.call_args[0]
        self.assertEqual(pool_id, '3')

    def test_find_domains(self):
        self.context = RoObject(tenant='t')
        self.service.storage.find_domains = Mock()
        self.service.find_domains(self.context)
        assert self.service.storage.find_domains.called
        pcheck, ctx, target = \
            designate.central.service.policy.check.call_args[0]
        self.assertEqual(pcheck, 'find_domains')

    def test_find_domain(self):
        self.context = RoObject(tenant='t')
        self.service.storage.find_domain = Mock()
        self.service.find_domain(self.context)
        assert self.service.storage.find_domain.called
        pcheck, ctx, target = \
            designate.central.service.policy.check.call_args[0]
        self.assertEqual(pcheck, 'find_domain')

    def test_delete_domain_has_subdomain(self):
        self.context.abandon = False
        self.service.storage.get_domain.return_value = RoObject(
            name='foo',
            tenant_id='2',
        )
        self.service.storage.count_domains.return_value = 2
        with raises(exceptions.DomainHasSubdomain):
            self.service.delete_domain(self.context, '1')

        pcheck, ctx, target = \
            designate.central.service.policy.check.call_args[0]
        self.assertEqual(pcheck, 'delete_domain')

    def test_delete_domain_abandon(self):
        self.service.storage.get_domain.return_value = RoObject(
            name='foo',
            tenant_id='2',
            id='9'
        )
        designate.central.service.policy = mock.NonCallableMock(spec_set=[
            'reset',
            'set_rules',
            'init',
            'check',
        ])
        self.context.abandon = True
        self.service.storage.count_domains.return_value = 0
        self.service.delete_domain(self.context, '1')
        assert self.service.storage.delete_domain.called
        assert not self.service.pool_manager_api.delete_domain.called
        pcheck, ctx, target = \
            designate.central.service.policy.check.call_args[0]
        self.assertEqual(pcheck, 'abandon_domain')

    def test_delete_domain(self):
        self.context.abandon = False
        self.service.storage.get_domain.return_value = RoObject(
            name='foo',
            tenant_id='2',
        )
        self.service._delete_domain_in_storage = Mock(
            return_value=RoObject(
                name='foo'
            )
        )
        self.service.storage.count_domains.return_value = 0
        out = self.service.delete_domain(self.context, '1')
        assert not self.service.storage.delete_domain.called
        assert self.service.pool_manager_api.delete_domain.called
        assert designate.central.service.policy.check.called
        ctx, deleted_dom = \
            self.service.pool_manager_api.delete_domain.call_args[0]
        self.assertEqual(deleted_dom.name, 'foo')
        self.assertEqual(out.name, 'foo')
        pcheck, ctx, target = \
            designate.central.service.policy.check.call_args[0]
        self.assertEqual(pcheck, 'delete_domain')

    def test__delete_domain_in_storage(self):
        self.service._delete_domain_in_storage(
            self.context,
            RwObject(action='', status=''),
        )
        d = self.service.storage.update_domain.call_args[0][1]
        self.assertEqual(d.action, 'DELETE')
        self.assertEqual(d.status, 'PENDING')

    def test__xfr_domain_secondary(self):
        self.service.storage.get_domain.return_value = RoObject(
            name='example.org.',
            tenant_id='2',
            type='SECONDARY'
        )
        with fx_mdns_api:
            self.service.xfr_domain(self.context, '1')
            assert self.service.mdns_api.perform_zone_xfr.called

        assert designate.central.service.policy.check.called
        self.assertEqual(
            designate.central.service.policy.check.call_args[0][0],
            'xfr_domain'
        )

    def test__xfr_domain_not_secondary(self):
        self.service.storage.get_domain.return_value = RoObject(
            name='example.org.',
            tenant_id='2',
            type='PRIMARY'
        )
        with raises(exceptions.BadRequest):
            self.service.xfr_domain(self.context, '1')

    def test_count_report(self):
        self.service.count_domains = Mock(return_value=1)
        self.service.count_records = Mock(return_value=2)
        self.service.count_tenants = Mock(return_value=3)
        reports = self.service.count_report(
            self.context,
            criterion=None
        )
        self.assertEqual(reports, [{'zones': 1, 'records': 2, 'tenants': 3}])

    def test_count_report_zones(self):
        self.service.count_domains = Mock(return_value=1)
        self.service.count_records = Mock(return_value=2)
        self.service.count_tenants = Mock(return_value=3)
        reports = self.service.count_report(
            self.context,
            criterion='zones'
        )
        self.assertEqual(reports, [{'zones': 1}])

    def test_count_report_records(self):
        self.service.count_domains = Mock(return_value=1)
        self.service.count_records = Mock(return_value=2)
        self.service.count_tenants = Mock(return_value=3)
        reports = self.service.count_report(
            self.context,
            criterion='records'
        )
        self.assertEqual(reports, [{'records': 2}])

    def test_count_report_tenants(self):
        self.service.count_domains = Mock(return_value=1)
        self.service.count_records = Mock(return_value=2)
        self.service.count_tenants = Mock(return_value=3)
        reports = self.service.count_report(
            self.context,
            criterion='tenants'
        )
        self.assertEqual(reports, [{'tenants': 3}])

    def test_count_report_not_found(self):
        self.service.count_domains = Mock(return_value=1)
        self.service.count_records = Mock(return_value=2)
        self.service.count_tenants = Mock(return_value=3)
        with raises(exceptions.ReportNotFound):
            self.service.count_report(
                self.context,
                criterion='bogus'
            )

    def test_touch_domain(self):
        self.service._touch_domain_in_storage = Mock()
        self.service.storage.get_domain.return_value = RoObject(
            name='example.org.',
            tenant_id='2',
        )
        with fx_pool_manager:
            self.service.touch_domain(self.context, '1')

        assert designate.central.service.policy.check.called
        self.assertEqual(
            designate.central.service.policy.check.call_args[0][0],
            'touch_domain'
        )

    def test_get_recordset_not_found(self):
        self.service.storage.get_domain.return_value = RoObject(
            id='2',
        )
        self.service.storage.get_recordset.return_value = RoObject(
            domain_id='3'
        )
        with raises(exceptions.RecordSetNotFound):
            self.service.get_recordset(
                self.context,
                '1',
                '2'
            )

    def test_get_recordset(self):
        self.service.storage.get_domain.return_value = RoObject(
            id='2',
            name='example.org.',
            tenant_id='2',
        )
        self.service.storage.get_recordset.return_value = RoObject(
            domain_id='2',
            id='3'
        )
        self.service.get_recordset(
            self.context,
            '1',
            '2',
        )
        self.assertEqual(
            designate.central.service.policy.check.call_args[0][0],
            'get_recordset'
        )
        t, ctx, target = designate.central.service.policy.check.call_args[0]
        self.assertEqual(t, 'get_recordset')
        self.assertEqual(target, {
            'domain_id': '1',
            'domain_name': 'example.org.',
            'recordset_id': '3',
            'tenant_id': '2'
        })

    def test_find_recordsets(self):
        self.context = Mock()
        self.context.tenant = 't'
        self.service.find_recordsets(self.context)
        assert self.service.storage.find_recordsets.called
        n, ctx, target = designate.central.service.policy.check.call_args[0]
        self.assertEqual(n, 'find_recordsets')
        self.assertEqual(target, {'tenant_id': 't'})

    def test_find_recordset(self):
        self.context = Mock()
        self.context.tenant = 't'
        self.service.find_recordset(self.context)
        assert self.service.storage.find_recordset.called
        n, ctx, target = designate.central.service.policy.check.call_args[0]
        self.assertEqual(n, 'find_recordset')
        self.assertEqual(target, {'tenant_id': 't'})

    def test_update_recordset_fail_on_changes(self):
        self.service.storage.get_domain.return_value = RoObject()
        recordset = Mock()
        recordset.obj_get_original_value.return_value = '1'

        recordset.obj_get_changes.return_value = ['tenant_id', 'foo']
        with raises(exceptions.BadRequest):
            self.service.update_recordset(self.context, recordset)

        recordset.obj_get_changes.return_value = ['domain_id', 'foo']
        with raises(exceptions.BadRequest):
            self.service.update_recordset(self.context, recordset)

        recordset.obj_get_changes.return_value = ['type', 'foo']
        with raises(exceptions.BadRequest):
            self.service.update_recordset(self.context, recordset)

    def test_update_recordset_action_delete(self):
        self.service.storage.get_domain.return_value = RoObject(
            action='DELETE',
        )
        recordset = Mock()
        recordset.obj_get_changes.return_value = ['foo']
        with raises(exceptions.BadRequest):
            self.service.update_recordset(self.context, recordset)

    def test_update_recordset_action_fail_on_managed(self):
        self.service.storage.get_domain.return_value = RoObject(
            type='foo',
            name='example.org.',
            tenant_id='2',
            action='bogus',
        )
        recordset = Mock()
        recordset.obj_get_changes.return_value = ['foo']
        recordset.managed = True
        self.context = Mock()
        self.context.edit_managed_records = False
        with raises(exceptions.BadRequest):
            self.service.update_recordset(self.context, recordset)

    def test_update_recordset(self):
        self.service.storage.get_domain.return_value = RoObject(
            type='foo',
            name='example.org.',
            tenant_id='2',
            action='bogus',
        )
        recordset = Mock()
        recordset.obj_get_changes.return_value = ['foo']
        recordset.obj_get_original_value.return_value = '1'
        recordset.managed = False
        self.service._update_recordset_in_storage = Mock(
            return_value=('x', 'y')
        )

        with fx_pool_manager:
            self.service.update_recordset(self.context, recordset)
            assert self.service._update_recordset_in_storage.called

        n, ctx, target = designate.central.service.policy.check.call_args[0]
        self.assertEqual(n, 'update_recordset')
        self.assertEqual(target, {
            'domain_id': '1',
            'domain_name': 'example.org.',
            'domain_type': 'foo',
            'recordset_id': '1',
            'tenant_id': '2',
        })

    def test__update_recordset_in_storage(self):
        recordset = Mock()
        recordset.name = 'n'
        recordset.type = 't'
        recordset.id = 'i'
        recordset.obj_get_changes.return_value = {'ttl': 90}
        recordset.records = []
        self.service._is_valid_recordset_name = Mock()
        self.service._is_valid_recordset_placement = Mock()
        self.service._is_valid_recordset_placement_subdomain = Mock()
        self.service._is_valid_ttl = Mock()
        self.service._update_domain_in_storage = Mock()

        self.service._update_recordset_in_storage(
            self.context,
            RoObject(serial=3),
            recordset,
        )

        self.assertEqual(
            self.service._is_valid_recordset_name.call_args[0][2],
            'n'
        )
        self.assertEqual(
            self.service._is_valid_recordset_placement.call_args[0][2:],
            ('n', 't', 'i')
        )
        self.assertEqual(
            self.service._is_valid_recordset_placement_subdomain.
            call_args[0][2],
            'n'
        )
        self.assertEqual(
            self.service._is_valid_ttl.call_args[0][1],
            90
        )
        assert self.service.storage.update_recordset.called
        assert self.service._update_domain_in_storage.called

    def test__update_recordset_in_storage_2(self):
        recordset = Mock()
        recordset.name = 'n'
        recordset.type = 't'
        recordset.id = 'i'
        recordset.obj_get_changes.return_value = {'ttl': None}
        recordset.records = [RwObject(
            action='a',
            status='s',
            serial=9,
        )]
        self.service._is_valid_recordset_name = Mock()
        self.service._is_valid_recordset_placement = Mock()
        self.service._is_valid_recordset_placement_subdomain = Mock()
        self.service._is_valid_ttl = Mock()
        self.service._update_domain_in_storage = Mock()

        self.service._update_recordset_in_storage(
            self.context,
            RoObject(serial=3),
            recordset,
            increment_serial=False,
        )

        self.assertEqual(
            self.service._is_valid_recordset_name.call_args[0][2],
            'n'
        )
        self.assertEqual(
            self.service._is_valid_recordset_placement.call_args[0][2:],
            ('n', 't', 'i')
        )
        self.assertEqual(
            self.service._is_valid_recordset_placement_subdomain.
            call_args[0][2],
            'n'
        )
        assert not self.service._is_valid_ttl.called
        assert not self.service._update_domain_in_storage.called
        assert self.service.storage.update_recordset.called

    def test_delete_recordset_not_found(self):
        self.service.storage.get_domain.return_value = RoObject(
            action='bogus',
            id=4,
            name='example.org.',
            tenant_id='2',
            type='foo',
        )
        self.service.storage.get_recordset.return_value = RoObject(
            domain_id='d',
            id='i',
            managed=False,
        )
        self.context = Mock()
        self.context.edit_managed_records = False
        with raises(exceptions.RecordSetNotFound):
            self.service.delete_recordset(self.context, 'd', 'r')

    def test_delete_recordset_action_delete(self):
        self.service.storage.get_domain.return_value = RoObject(
            action='DELETE',
            id=4,
            name='example.org.',
            tenant_id='2',
            type='foo',
        )
        self.service.storage.get_recordset.return_value = RoObject(
            domain_id=4,
            id='i',
            managed=False,
        )
        self.context = Mock()
        self.context.edit_managed_records = False
        with raises(exceptions.BadRequest):
            self.service.delete_recordset(self.context, 'd', 'r')

    def test_delete_recordset_managed(self):
        self.service.storage.get_domain.return_value = RoObject(
            action='foo',
            id=4,
            name='example.org.',
            tenant_id='2',
            type='foo',
        )
        self.service.storage.get_recordset.return_value = RoObject(
            domain_id=4,
            id='i',
            managed=True,
        )
        self.context = Mock()
        self.context.edit_managed_records = False
        with raises(exceptions.BadRequest):
            self.service.delete_recordset(self.context, 'd', 'r')

    def test_delete_recordset(self):
        self.service.storage.get_domain.return_value = RoObject(
            action='foo',
            id=4,
            name='example.org.',
            tenant_id='2',
            type='foo',
        )
        self.service.storage.get_recordset.return_value = RoObject(
            domain_id=4,
            id='i',
            managed=False,
        )
        self.context = Mock()
        self.context.edit_managed_records = False
        self.service._delete_recordset_in_storage = Mock(
            return_value=('', '')
        )
        with fx_pool_manager:
            self.service.delete_recordset(self.context, 'd', 'r')
            assert self.service.pool_manager_api.update_domain.called

        assert self.service._delete_recordset_in_storage.called

    def test__delete_recordset_in_storage(self):
        def mock_uds(c, domain, inc):
            return domain
        self.service._update_domain_in_storage = mock_uds
        self.service._delete_recordset_in_storage(
            self.context,
            RoObject(serial=1),
            RoObject(id=2, records=[
                RwObject(
                    action='',
                    status='',
                    serial=0,
                )
            ])
        )
        assert self.service.storage.update_recordset.called
        assert self.service.storage.delete_recordset.called
        rs = self.service.storage.update_recordset.call_args[0][1]
        self.assertEqual(len(rs.records), 1)
        self.assertEqual(rs.records[0].action, 'DELETE')
        self.assertEqual(rs.records[0].status, 'PENDING')
        self.assertEqual(rs.records[0].serial, 1)

    def test__delete_recordset_in_storage_no_increment_serial(self):
        self.service._update_domain_in_storage = Mock()
        self.service._delete_recordset_in_storage(
            self.context,
            RoObject(serial=1),
            RoObject(id=2, records=[
                RwObject(
                    action='',
                    status='',
                    serial=0,
                )
            ]),
            increment_serial=False,
        )
        assert self.service.storage.update_recordset.called
        assert self.service.storage.delete_recordset.called
        assert not self.service._update_domain_in_storage.called

    def test_count_recordset(self):
        self.service.count_recordsets(self.context)
        n, ctx, target = designate.central.service.policy.check.call_args[0]
        self.assertEqual(n, 'count_recordsets')
        self.assertEqual(target, {'tenant_id': None})
        self.assertEqual(
            self.service.storage.count_recordsets.call_args[0][1],
            {}
        )

    def test_create_record_fail_on_delete(self):
        self.service.storage.get_domain.return_value = RoObject(
            action='DELETE',
            id=4,
            name='example.org.',
            tenant_id='2',
            type='foo',
        )
        with raises(exceptions.BadRequest):
            self.service.create_record(
                self.context,
                1,
                2,
                RoObject(),
            )

    def test_create_record(self):
        self.service._create_record_in_storage = Mock(
            return_value=(None, None)
        )
        self.service.storage.get_domain.return_value = RoObject(
            action='a',
            id=4,
            name='example.org.',
            tenant_id='2',
            type='foo',
        )
        self.service.storage.get_recordset.return_value = RoObject(
            name='rs',
        )
        with fx_pool_manager:
            self.service.create_record(
                self.context,
                1,
                2,
                RoObject(),
            )
            assert self.service.pool_manager_api.update_domain.called

        n, ctx, target = designate.central.service.policy.check.call_args[0]
        self.assertEqual(n, 'create_record')
        self.assertEqual(target, {
            'domain_id': 1,
            'domain_name': 'example.org.',
            'domain_type': 'foo',
            'recordset_id': 2,
            'recordset_name': 'rs',
            'tenant_id': '2'
        })

    def test__create_record_in_storage(self):
        self.service._enforce_record_quota = Mock()
        self.service._create_record_in_storage(
            self.context,
            RoObject(id=1, serial=4),
            RoObject(id=2),
            RwObject(
                action='',
                status='',
                serial='',
            ),
            increment_serial=False
        )
        ctx, did, rid, record = self.service.storage.create_record.call_args[0]
        self.assertEqual(did, 1)
        self.assertEqual(rid, 2)
        self.assertEqual(record.action, 'CREATE')
        self.assertEqual(record.status, 'PENDING')
        self.assertEqual(record.serial, 4)

    def test_get_record_not_found(self):
        self.service.storage.get_domain.return_value = RoObject(
            id=2,
        )
        self.service.storage.get_recordset.return_value = RoObject(
            domain_id=3
        )
        with raises(exceptions.RecordNotFound):
            self.service.get_record(self.context, 1, 2, 3)

    def test_get_record_not_found_2(self):
        self.service.storage.get_domain.return_value = RoObject(
            id=2,
            name='example.org.',
            tenant_id=2,
        )
        self.service.storage.get_recordset.return_value = RoObject(
            domain_id=2,
            id=999,  # not matching record.recordset_id
            name='foo'
        )
        self.service.storage.get_record.return_value = RoObject(
            id=5,
            domain_id=2,
            recordset_id=3
        )
        with raises(exceptions.RecordNotFound):
            self.service.get_record(self.context, 1, 2, 3)

    def test_get_record(self):
        self.service.storage.get_domain.return_value = RoObject(
            id=2,
            name='example.org.',
            tenant_id=2,
        )
        self.service.storage.get_recordset.return_value = RoObject(
            domain_id=2,
            id=3,
            name='foo'
        )
        self.service.storage.get_record.return_value = RoObject(
            id=5,
            domain_id=2,
            recordset_id=3
        )
        self.service.get_record(self.context, 1, 2, 3)
        self.assertEqual(
            designate.central.service.policy.check.call_args[0][0],
            'get_record'
        )
        t, ctx, target = designate.central.service.policy.check.call_args[0]
        self.assertEqual(t, 'get_record')
        self.assertEqual(target, {
            'domain_id': 1,
            'domain_name': 'example.org.',
            'record_id': 5,
            'recordset_id': 2,
            'recordset_name': 'foo',
            'tenant_id': 2
        })

    def test_update_record_fail_on_changes(self):
        self.service.storage.get_domain.return_value = RoObject(
            action='a',
            name='n',
            type='t',
            tenant_id='tid',
        )
        record = Mock()
        record.obj_get_original_value.return_value = 1

        record.obj_get_changes.return_value = ['tenant_id', 'foo']
        with raises(exceptions.BadRequest):
            self.service.update_record(self.context, record)

        record.obj_get_changes.return_value = ['domain_id', 'foo']
        with raises(exceptions.BadRequest):
            self.service.update_record(self.context, record)

        record.obj_get_changes.return_value = ['recordset_id', 'foo']
        with raises(exceptions.BadRequest):
            self.service.update_record(self.context, record)

    def test_update_record_action_delete(self):
        self.service.storage.get_domain.return_value = RoObject(
            action='DELETE',
        )
        record = Mock()
        with raises(exceptions.BadRequest):
            self.service.update_record(self.context, record)

    def test_update_record_action_fail_on_managed(self):
        self.service.storage.get_domain.return_value = RoObject(
            action='a',
            name='n',
            tenant_id='tid',
            type='t',
        )
        self.service.storage.get_recordset.return_value = RoObject(
            name='rsn',
            managed=True
        )
        record = Mock()
        record.obj_get_changes.return_value = ['foo']
        self.context = Mock()
        self.context.edit_managed_records = False
        with raises(exceptions.BadRequest):
            self.service.update_record(self.context, record)

    def test_update_record(self):
        self.service.storage.get_domain.return_value = RoObject(
            action='a',
            name='n',
            tenant_id='tid',
            type='t',
        )
        self.service.storage.get_recordset.return_value = RoObject(
            name='rsn',
            managed=False
        )
        record = Mock()
        record.obj_get_changes.return_value = ['foo']
        record.obj_get_original_value.return_value = '1'
        record.managed = False
        self.service._update_record_in_storage = Mock(
            return_value=('x', 'y')
        )

        with fx_pool_manager:
            self.service.update_record(self.context, record)
            assert self.service._update_record_in_storage.called

        n, ctx, target = designate.central.service.policy.check.call_args[0]
        self.assertEqual(n, 'update_record')
        self.assertEqual(target, {
            'domain_id': '1',
            'domain_name': 'n',
            'domain_type': 't',
            'record_id': '1',
            'recordset_id': '1',
            'recordset_name': 'rsn',
            'tenant_id': 'tid'
        })

    def test__update_record_in_storage(self):
        self.service._update_domain_in_storage = Mock()
        self.service._update_record_in_storage(
            self.context,
            RoObject(serial=1),
            RwObject(
                action='',
                status='',
                serial='',
            ),
            increment_serial=False
        )
        ctx, record = self.service.storage.update_record.call_args[0]
        self.assertEqual(record.action, 'UPDATE')
        self.assertEqual(record.status, 'PENDING')
        self.assertEqual(record.serial, 1)

    def test_delete_record_action_delete(self):
        self.service.storage.get_domain.return_value = RoObject(
            action='DELETE',
        )
        with raises(exceptions.BadRequest):
            self.service.delete_record(self.context, 1, 2, 3)

    def test_delete_record_not_found(self):
        self.service.storage.get_domain.return_value = RoObject(
            action='a',
            id=2
        )
        self.service.storage.get_record.return_value = RoObject(
            domain_id=999,
        )
        self.service.storage.get_recordset.return_value = RoObject(
            id=888,
        )
        # domain.id != record.domain_id
        with raises(exceptions.RecordNotFound):
            self.service.delete_record(self.context, 1, 2, 3)

        self.service.storage.get_record.return_value = RoObject(
            id=1,
            domain_id=2,
            recordset_id=7777,
        )
        #  recordset.id != record.recordset_id
        with raises(exceptions.RecordNotFound):
            self.service.delete_record(self.context, 1, 2, 3)

    def test_delete_record(self):
        self.service._delete_record_in_storage = Mock(
            return_value=(None, None)
        )
        self.service.storage.get_domain.return_value = RoObject(
            action='a',
            id=2,
            name='dn',
            tenant_id='tid',
            type='t',
        )
        self.service.storage.get_record.return_value = RoObject(
            id=4,
            domain_id=2,
            recordset_id=3,
        )
        self.service.storage.get_recordset.return_value = RoObject(
            name='rsn',
            id=3,
            managed=False,
        )

        with fx_pool_manager:
            self.service.delete_record(self.context, 1, 2, 3)

        t, ctx, target = designate.central.service.policy.check.call_args[0]
        self.assertEqual(t, 'delete_record')
        self.assertEqual(target, {
            'domain_id': 1,
            'domain_name': 'dn',
            'domain_type': 't',
            'record_id': 4,
            'recordset_id': 2,
            'recordset_name': 'rsn',
            'tenant_id': 'tid'
        })

    def test_delete_record_fail_on_managed(self):
        self.service._delete_record_in_storage = Mock(
            return_value=(None, None)
        )
        self.service.storage.get_domain.return_value = RoObject(
            action='a',
            id=2,
            name='dn',
            tenant_id='tid',
            type='t',
        )
        self.service.storage.get_record.return_value = RoObject(
            id=4,
            domain_id=2,
            recordset_id=3,
        )
        self.service.storage.get_recordset.return_value = RoObject(
            name='rsn',
            id=3,
            managed=True,
        )
        self.context = Mock()
        self.context.edit_managed_records = False

        with fx_pool_manager:
            with raises(exceptions.BadRequest):
                self.service.delete_record(self.context, 1, 2, 3)

    def test__delete_record_in_storage(self):
        self.service._delete_record_in_storage(
            self.context,
            RoObject(serial=2),
            RwObject(action='', status='', serial=''),
            increment_serial=False
        )
        r = self.service.storage.update_record.call_args[0][1]
        self.assertEqual(r.action, 'DELETE')
        self.assertEqual(r.status, 'PENDING')
        self.assertEqual(r.serial, 2)

    def test_count_records(self):
        self.service.count_records(self.context)
        t, ctx, target = designate.central.service.policy.check.call_args[0]
        self.assertEqual(t, 'count_records')
        self.assertEqual(target, {'tenant_id': None})

    def test_sync_domains(self):
        self.service._sync_domain = Mock()
        self.service.storage.find_domains.return_value = [
            RoObject(id=1),
            RoObject(id=2)
        ]

        res = self.service.sync_domains(self.context)
        t, ctx = designate.central.service.policy.check.call_args[0]
        self.assertEqual(t, 'diagnostics_sync_domains')
        self.assertEqual(len(res), 2)

    def test_sync_domain(self):
        self.service._sync_domain = Mock()
        self.service.storage.get_domain.return_value = RoObject(
            id=1,
            name='n',
            tenant_id='tid',
        )

        self.service.sync_domain(self.context, 1)

        t, ctx, target = designate.central.service.policy.check.call_args[0]
        self.assertEqual(t, 'diagnostics_sync_domain')
        self.assertEqual(target, {'tenant_id': 'tid', 'domain_id': 1,
                                  'domain_name': 'n'})

    def test_sync_record(self):
        self.service.storage.get_domain.return_value = RoObject(
            id=1,
            name='n',
            tenant_id='tid',
        )
        self.service.storage.get_recordset.return_value = RoObject(
            name='n',
        )

        self.service.sync_record(self.context, 1, 2, 3)

        t, ctx, target = designate.central.service.policy.check.call_args[0]
        self.assertEqual(t, 'diagnostics_sync_record')
        self.assertEqual(target, {
            'domain_id': 1,
            'domain_name': 'n',
            'record_id': 3,
            'recordset_id': 2,
            'recordset_name': 'n',
            'tenant_id': 'tid'
        })

    def test_ping(self):
        self.service.storage.ping.return_value = True
        r = self.service.ping(self.context)
        self.assertEqual(r['backend'], {'status': None})
        self.assertTrue(r['status'])
        self.assertTrue(r['storage'])

    def test_ping2(self):
        self.service.storage.ping.return_value = False
        r = self.service.ping(self.context)
        self.assertEqual(r['backend'], {'status': None})
        self.assertFalse(r['status'])
        self.assertFalse(r['storage'])

    def test__determine_floatingips(self):
        self.context = Mock()
        self.context.tenant = 'tnt'
        self.service.find_records = Mock(return_value=[
            RoObject(managed_extra='')
        ])

        fips = {}
        data, invalid = self.service._determine_floatingips(self.context, fips)
        self.assertEqual(data, {})
        self.assertEqual(invalid, [])

    def test__determine_floatingips_with_data(self):
        self.context = Mock()
        self.context.tenant = 2
        self.service.find_records = Mock(return_value=[
            RoObject(managed_extra=1, managed_tenant_id=1),
            RoObject(managed_extra=2, managed_tenant_id=2),
        ])

        fips = {
            'k': {'address': 1},
            'k2': {'address': 2},
        }
        data, invalid = self.service._determine_floatingips(self.context, fips)
        self.assertEqual(len(invalid), 1)
        self.assertEqual(invalid[0].managed_tenant_id, 1)
        self.assertEqual(data['k'], ({'address': 1}, None))


class IsSubdomainTestCase(CentralBasic):
    def setUp(self):
        super(IsSubdomainTestCase, self).setUp()

        def find_domain(ctx, criterion):
            print("Calling find_domain on %r" % criterion)
            if criterion['name'] == 'example.com.':
                print("Returning %r" % criterion['name'])
                return criterion['name']

            print("Not found")
            raise exceptions.DomainNotFound

        self.service.storage.find_domain = find_domain

    def test__is_subdomain_false(self):
        r = self.service._is_subdomain(self.context, 'com', '1')
        self.assertFalse(r)

    def FIXME_test__is_subdomain_false2(self):
        r = self.service._is_subdomain(self.context, 'com.', '1')
        self.assertEqual(r, 'com.')

    def FIXME_test__is_subdomain_false3(self):
        r = self.service._is_subdomain(self.context, 'example.com.', '1')
        self.assertEqual(r, 'example.com.')

    def test__is_subdomain_false4(self):
        r = self.service._is_subdomain(self.context, 'foo.a.b.example.com.',
                                       '1')
        self.assertEqual(r, 'example.com.')


class CentralZoneExportTests(CentralBasic):
    def setUp(self):
        super(CentralZoneExportTests, self).setUp()

        def storage_find_tld(c, d):
            if d['name'] not in ('org',):
                raise exceptions.TldNotFound

        self.service.storage.find_tld = storage_find_tld

    def test_create_zone_export(self):
        self.context = Mock()
        self.context.tenant = 't'

        self.service.storage.get_domain.return_value = RoObject(
            name='example.com.',
            id='123'
        )

        self.service.storage.create_zone_export = Mock(
            return_value=RoObject(
                domain_id='123',
                task_type='EXPORT',
                status='PENDING',
                message=None,
                tenant_id='t'
            )
        )

        self.service.zone_manager_api.start_zone_export = Mock()

        out = self.service.create_zone_export(
            self.context,
            '123'
        )
        self.assertEqual(out.domain_id, '123')
        self.assertEqual(out.status, 'PENDING')
        self.assertEqual(out.task_type, 'EXPORT')
        self.assertEqual(out.message, None)
        self.assertEqual(out.tenant_id, 't')

    def test_get_zone_export(self):
        self.context = Mock()
        self.context.tenant = 't'

        self.service.storage.get_zone_export.return_value = RoObject(
                domain_id='123',
                task_type='EXPORT',
                status='PENDING',
                message=None,
                tenant_id='t'
        )

        out = self.service.get_zone_export(self.context, '1')

        n, ctx, target = designate.central.service.policy.check.call_args[0]

        # Check arguments to policy
        self.assertEqual(target['tenant_id'], 't')

        # Check output
        self.assertEqual(out.domain_id, '123')
        self.assertEqual(out.status, 'PENDING')
        self.assertEqual(out.task_type, 'EXPORT')
        self.assertEqual(out.message, None)
        self.assertEqual(out.tenant_id, 't')

    def test_find_zone_exports(self):
        self.context = Mock()
        self.context.tenant = 't'
        self.service.storage.find_zone_exports = Mock()

        self.service.find_zone_exports(self.context)

        assert self.service.storage.find_zone_exports.called
        pcheck, ctx, target = \
            designate.central.service.policy.check.call_args[0]
        self.assertEqual(pcheck, 'find_zone_exports')

    def test_delete_zone_export(self):
        self.context = Mock()
        self.context.tenant = 't'

        self.service.storage.delete_zone_export = Mock(
            return_value=RoObject(
                domain_id='123',
                task_type='EXPORT',
                status='PENDING',
                message=None,
                tenant_id='t'
            )
        )

        out = self.service.delete_zone_export(self.context, '1')

        assert self.service.storage.delete_zone_export.called

        self.assertEqual(out.domain_id, '123')
        self.assertEqual(out.status, 'PENDING')
        self.assertEqual(out.task_type, 'EXPORT')
        self.assertEqual(out.message, None)
        self.assertEqual(out.tenant_id, 't')

        assert designate.central.service.policy.check.called
        pcheck, ctx, target = \
            designate.central.service.policy.check.call_args[0]
        self.assertEqual(pcheck, 'delete_zone_export')
