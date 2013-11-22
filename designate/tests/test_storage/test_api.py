# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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
import mock
import testtools
from designate.openstack.common import log as logging
from designate.tests import TestCase
from designate.storage import api as storage_api

LOG = logging.getLogger(__name__)


class SentinelException(Exception):
    pass


class StorageAPITest(TestCase):
    def setUp(self):
        super(StorageAPITest, self).setUp()
        self.storage_api = storage_api.StorageAPI()
        self.storage_mock = mock.Mock()
        self.storage_api.storage = self.storage_mock

    def _set_side_effect(self, method, side_effect):
        methodc = getattr(self.storage_mock, method)
        methodc.side_effect = side_effect

    def _assert_called_with(self, method, *args, **kwargs):
        methodc = getattr(self.storage_mock, method)
        methodc.assert_called_with(*args, **kwargs)

    def _assert_has_calls(self, method, *args, **kwargs):
        methodc = getattr(self.storage_mock, method)
        methodc.assert_has_calls(*args, **kwargs)

    def _assert_call_count(self, method, call_count):
        methodc = getattr(self.storage_mock, method)
        self.assertEqual(methodc.call_count, call_count)

    # Quota Tests
    def test_create_quota(self):
        context = mock.sentinel.context
        values = mock.sentinel.values
        quota = mock.sentinel.quota

        self._set_side_effect('create_quota', [quota])

        with self.storage_api.create_quota(context, values) as q:
            self.assertEqual(quota, q)

        self._assert_called_with('create_quota', context, values)

    def test_create_quota_failure(self):
        context = mock.sentinel.context
        values = mock.sentinel.values

        self._set_side_effect('create_quota', [{'id': 12345}])

        with testtools.ExpectedException(SentinelException):
            with self.storage_api.create_quota(context, values):
                raise SentinelException('Something Went Wrong')

        self._assert_called_with('create_quota', context, values)
        self._assert_called_with('delete_quota', context, 12345)

    def test_get_quota(self):
        context = mock.sentinel.context
        quota_id = mock.sentinel.quota_id
        quota = mock.sentinel.quota

        self._set_side_effect('get_quota', [quota])

        result = self.storage_api.get_quota(context, quota_id)
        self._assert_called_with('get_quota', context, quota_id)
        self.assertEqual(quota, result)

    def test_find_quotas(self):
        context = mock.sentinel.context
        criterion = mock.sentinel.criterion
        quota = mock.sentinel.quota

        self._set_side_effect('find_quotas', [[quota]])

        result = self.storage_api.find_quotas(context, criterion)
        self._assert_called_with('find_quotas', context, criterion)
        self.assertEqual([quota], result)

    def test_find_quota(self):
        context = mock.sentinel.context
        criterion = mock.sentinel.criterion
        quota = mock.sentinel.quota

        self._set_side_effect('find_quota', [quota])

        result = self.storage_api.find_quota(context, criterion)
        self._assert_called_with('find_quota', context, criterion)
        self.assertEqual(quota, result)

    def test_update_quota(self):
        context = mock.sentinel.context
        values = mock.sentinel.values

        with self.storage_api.update_quota(context, 123, values):
            pass

        self._assert_called_with('update_quota', context, 123, values)

    def test_update_quota_failure(self):
        context = mock.sentinel.context
        values = {'test': 2}

        self._set_side_effect('get_quota', [{'id': 123, 'test': 1}])

        with testtools.ExpectedException(SentinelException):
            with self.storage_api.update_quota(context, 123, values):
                raise SentinelException('Something Went Wrong')

        self._assert_has_calls('update_quota', [
            mock.call(context, 123, values),
            mock.call(context, 123, {'test': 1}),
        ])

    def test_delete_quota(self):
        context = mock.sentinel.context
        quota = mock.sentinel.quota

        self._set_side_effect('get_quota', [quota])

        with self.storage_api.delete_quota(context, 123) as q:
            self.assertEqual(quota, q)

        self._assert_called_with('delete_quota', context, 123)

    def test_delete_quota_failure(self):
        context = mock.sentinel.context
        quota = mock.sentinel.quota

        self._set_side_effect('get_quota', [quota])

        with testtools.ExpectedException(SentinelException):
            with self.storage_api.delete_quota(context, 123):
                raise SentinelException('Something Went Wrong')

        self._assert_call_count('delete_quota', 0)

    # Server Tests
    def test_create_server(self):
        context = mock.sentinel.context
        values = mock.sentinel.values
        server = mock.sentinel.server

        self._set_side_effect('create_server', [server])

        with self.storage_api.create_server(context, values) as q:
            self.assertEqual(server, q)

        self._assert_called_with('create_server', context, values)

    def test_create_server_failure(self):
        context = mock.sentinel.context
        values = mock.sentinel.values

        self._set_side_effect('create_server', [{'id': 12345}])

        with testtools.ExpectedException(SentinelException):
            with self.storage_api.create_server(context, values):
                raise SentinelException('Something Went Wrong')

        self._assert_called_with('create_server', context, values)
        self._assert_called_with('delete_server', context, 12345)

    def test_get_server(self):
        context = mock.sentinel.context
        server_id = mock.sentinel.server_id
        server = mock.sentinel.server

        self._set_side_effect('get_server', [server])

        result = self.storage_api.get_server(context, server_id)
        self._assert_called_with('get_server', context, server_id)
        self.assertEqual(server, result)

    def test_find_servers(self):
        context = mock.sentinel.context
        criterion = mock.sentinel.criterion
        server = mock.sentinel.server

        self._set_side_effect('find_servers', [[server]])

        result = self.storage_api.find_servers(context, criterion)
        self._assert_called_with('find_servers', context, criterion)
        self.assertEqual([server], result)

    def test_find_server(self):
        context = mock.sentinel.context
        criterion = mock.sentinel.criterion
        server = mock.sentinel.server

        self._set_side_effect('find_server', [server])

        result = self.storage_api.find_server(context, criterion)
        self._assert_called_with('find_server', context, criterion)
        self.assertEqual(server, result)

    def test_update_server(self):
        context = mock.sentinel.context
        values = mock.sentinel.values

        with self.storage_api.update_server(context, 123, values):
            pass

        self._assert_called_with('update_server', context, 123, values)

    def test_update_server_failure(self):
        context = mock.sentinel.context
        values = {'test': 2}

        self._set_side_effect('get_server', [{'id': 123, 'test': 1}])

        with testtools.ExpectedException(SentinelException):
            with self.storage_api.update_server(context, 123, values):
                raise SentinelException('Something Went Wrong')

        self._assert_has_calls('update_server', [
            mock.call(context, 123, values),
            mock.call(context, 123, {'test': 1}),
        ])

    def test_delete_server(self):
        context = mock.sentinel.context
        server = mock.sentinel.server

        self._set_side_effect('get_server', [server])

        with self.storage_api.delete_server(context, 123) as q:
            self.assertEqual(server, q)

        self._assert_called_with('delete_server', context, 123)

    def test_delete_server_failure(self):
        context = mock.sentinel.context
        server = mock.sentinel.server

        self._set_side_effect('get_server', [server])

        with testtools.ExpectedException(SentinelException):
            with self.storage_api.delete_server(context, 123):
                raise SentinelException('Something Went Wrong')

        self._assert_call_count('delete_server', 0)

    # Tsigkey Tests
    def test_create_tsigkey(self):
        context = mock.sentinel.context
        values = mock.sentinel.values
        tsigkey = mock.sentinel.tsigkey

        self._set_side_effect('create_tsigkey', [tsigkey])

        with self.storage_api.create_tsigkey(context, values) as q:
            self.assertEqual(tsigkey, q)

        self._assert_called_with('create_tsigkey', context, values)

    def test_create_tsigkey_failure(self):
        context = mock.sentinel.context
        values = mock.sentinel.values

        self._set_side_effect('create_tsigkey', [{'id': 12345}])

        with testtools.ExpectedException(SentinelException):
            with self.storage_api.create_tsigkey(context, values):
                raise SentinelException('Something Went Wrong')

        self._assert_called_with('create_tsigkey', context, values)
        self._assert_called_with('delete_tsigkey', context, 12345)

    def test_get_tsigkey(self):
        context = mock.sentinel.context
        tsigkey_id = mock.sentinel.tsigkey_id
        tsigkey = mock.sentinel.tsigkey

        self._set_side_effect('get_tsigkey', [tsigkey])

        result = self.storage_api.get_tsigkey(context, tsigkey_id)
        self._assert_called_with('get_tsigkey', context, tsigkey_id)
        self.assertEqual(tsigkey, result)

    def test_find_tsigkeys(self):
        context = mock.sentinel.context
        criterion = mock.sentinel.criterion
        tsigkey = mock.sentinel.tsigkey

        self._set_side_effect('find_tsigkeys', [[tsigkey]])

        result = self.storage_api.find_tsigkeys(context, criterion)
        self._assert_called_with('find_tsigkeys', context, criterion)
        self.assertEqual([tsigkey], result)

    def test_find_tsigkey(self):
        context = mock.sentinel.context
        criterion = mock.sentinel.criterion
        tsigkey = mock.sentinel.tsigkey

        self._set_side_effect('find_tsigkey', [tsigkey])

        result = self.storage_api.find_tsigkey(context, criterion)
        self._assert_called_with('find_tsigkey', context, criterion)
        self.assertEqual(tsigkey, result)

    def test_update_tsigkey(self):
        context = mock.sentinel.context
        values = mock.sentinel.values

        with self.storage_api.update_tsigkey(context, 123, values):
            pass

        self._assert_called_with('update_tsigkey', context, 123, values)

    def test_update_tsigkey_failure(self):
        context = mock.sentinel.context
        values = {'test': 2}

        self._set_side_effect('get_tsigkey', [{'id': 123, 'test': 1}])

        with testtools.ExpectedException(SentinelException):
            with self.storage_api.update_tsigkey(context, 123, values):
                raise SentinelException('Something Went Wrong')

        self._assert_has_calls('update_tsigkey', [
            mock.call(context, 123, values),
            mock.call(context, 123, {'test': 1}),
        ])

    def test_delete_tsigkey(self):
        context = mock.sentinel.context
        tsigkey = mock.sentinel.tsigkey

        self._set_side_effect('get_tsigkey', [tsigkey])

        with self.storage_api.delete_tsigkey(context, 123) as q:
            self.assertEqual(tsigkey, q)

        self._assert_called_with('delete_tsigkey', context, 123)

    def test_delete_tsigkey_failure(self):
        context = mock.sentinel.context
        tsigkey = mock.sentinel.tsigkey

        self._set_side_effect('get_tsigkey', [tsigkey])

        with testtools.ExpectedException(SentinelException):
            with self.storage_api.delete_tsigkey(context, 123):
                raise SentinelException('Something Went Wrong')

        self._assert_call_count('delete_tsigkey', 0)

    # Tenant Tests
    def test_find_tenants(self):
        context = mock.sentinel.context
        tenant = mock.sentinel.tenant

        self._set_side_effect('find_tenants', [[tenant]])

        result = self.storage_api.find_tenants(context)
        self._assert_called_with('find_tenants', context)
        self.assertEqual([tenant], result)

    def test_get_tenant(self):
        context = mock.sentinel.context
        tenant = mock.sentinel.tenant

        self._set_side_effect('get_tenant', [tenant])

        result = self.storage_api.get_tenant(context, 123)
        self._assert_called_with('get_tenant', context, 123)
        self.assertEqual(tenant, result)

    def test_count_tenants(self):
        context = mock.sentinel.context

        self._set_side_effect('count_tenants', [1])

        result = self.storage_api.count_tenants(context)
        self._assert_called_with('count_tenants', context)
        self.assertEqual(1, result)

    # Domain Tests
    def test_create_domain(self):
        context = mock.sentinel.context
        values = mock.sentinel.values
        domain = mock.sentinel.domain

        self._set_side_effect('create_domain', [domain])

        with self.storage_api.create_domain(context, values) as q:
            self.assertEqual(domain, q)

        self._assert_called_with('create_domain', context, values)

    def test_create_domain_failure(self):
        context = mock.sentinel.context
        values = mock.sentinel.values

        self._set_side_effect('create_domain', [{'id': 12345}])

        with testtools.ExpectedException(SentinelException):
            with self.storage_api.create_domain(context, values):
                raise SentinelException('Something Went Wrong')

        self._assert_called_with('create_domain', context, values)
        self._assert_called_with('delete_domain', context, 12345)

    def test_get_domain(self):
        context = mock.sentinel.context
        domain_id = mock.sentinel.domain_id
        domain = mock.sentinel.domain

        self._set_side_effect('get_domain', [domain])

        result = self.storage_api.get_domain(context, domain_id)
        self._assert_called_with('get_domain', context, domain_id)
        self.assertEqual(domain, result)

    def test_find_domains(self):
        context = mock.sentinel.context
        criterion = mock.sentinel.criterion
        domain = mock.sentinel.domain

        self._set_side_effect('find_domains', [[domain]])

        result = self.storage_api.find_domains(context, criterion)
        self._assert_called_with('find_domains', context, criterion)
        self.assertEqual([domain], result)

    def test_find_domain(self):
        context = mock.sentinel.context
        criterion = mock.sentinel.criterion
        domain = mock.sentinel.domain

        self._set_side_effect('find_domain', [domain])

        result = self.storage_api.find_domain(context, criterion)
        self._assert_called_with('find_domain', context, criterion)
        self.assertEqual(domain, result)

    def test_update_domain(self):
        context = mock.sentinel.context
        values = mock.sentinel.values

        with self.storage_api.update_domain(context, 123, values):
            pass

        self._assert_called_with('update_domain', context, 123, values)

    def test_update_domain_failure(self):
        context = mock.sentinel.context
        values = {'test': 2}

        self._set_side_effect('get_domain', [{'id': 123, 'test': 1}])

        with testtools.ExpectedException(SentinelException):
            with self.storage_api.update_domain(context, 123, values):
                raise SentinelException('Something Went Wrong')

        self._assert_has_calls('update_domain', [
            mock.call(context, 123, values),
            mock.call(context, 123, {'test': 1}),
        ])

    def test_delete_domain(self):
        context = mock.sentinel.context
        domain = mock.sentinel.domain

        self._set_side_effect('get_domain', [domain])

        with self.storage_api.delete_domain(context, 123) as q:
            self.assertEqual(domain, q)

        self._assert_called_with('delete_domain', context, 123)

    def test_delete_domain_failure(self):
        context = mock.sentinel.context
        domain = mock.sentinel.domain

        self._set_side_effect('get_domain', [domain])

        with testtools.ExpectedException(SentinelException):
            with self.storage_api.delete_domain(context, 123):
                raise SentinelException('Something Went Wrong')

        self._assert_call_count('delete_domain', 0)

    # Record Tests
    def test_create_record(self):
        context = mock.sentinel.context
        values = mock.sentinel.values
        record = mock.sentinel.record

        self._set_side_effect('create_record', [record])

        with self.storage_api.create_record(context, 123, values) as q:
            self.assertEqual(record, q)

        self._assert_called_with('create_record', context, 123, values)

    def test_create_record_failure(self):
        context = mock.sentinel.context
        values = mock.sentinel.values

        self._set_side_effect('create_record', [{'id': 12345}])

        with testtools.ExpectedException(SentinelException):
            with self.storage_api.create_record(context, 123, values):
                raise SentinelException('Something Went Wrong')

        self._assert_called_with('create_record', context, 123, values)
        self._assert_called_with('delete_record', context, 12345)

    def test_get_record(self):
        context = mock.sentinel.context
        record_id = mock.sentinel.record_id
        record = mock.sentinel.record

        self._set_side_effect('get_record', [record])

        result = self.storage_api.get_record(context, record_id)
        self._assert_called_with('get_record', context, record_id)
        self.assertEqual(record, result)

    def test_find_records(self):
        context = mock.sentinel.context
        criterion = mock.sentinel.criterion
        record = mock.sentinel.record

        self._set_side_effect('find_records', [[record]])

        result = self.storage_api.find_records(context, criterion)
        self._assert_called_with('find_records', context, criterion)
        self.assertEqual([record], result)

    def test_find_record(self):
        context = mock.sentinel.context
        criterion = mock.sentinel.criterion
        record = mock.sentinel.record

        self._set_side_effect('find_record', [record])

        result = self.storage_api.find_record(context, criterion)
        self._assert_called_with('find_record', context, criterion)
        self.assertEqual(record, result)

    def test_update_record(self):
        context = mock.sentinel.context
        values = mock.sentinel.values

        with self.storage_api.update_record(context, 123, values):
            pass

        self._assert_called_with('update_record', context, 123, values)

    def test_update_record_failure(self):
        context = mock.sentinel.context
        values = {'test': 2}

        self._set_side_effect('get_record', [{'id': 123, 'test': 1}])

        with testtools.ExpectedException(SentinelException):
            with self.storage_api.update_record(context, 123, values):
                raise SentinelException('Something Went Wrong')

        self._assert_has_calls('update_record', [
            mock.call(context, 123, values),
            mock.call(context, 123, {'test': 1}),
        ])

    def test_delete_record(self):
        context = mock.sentinel.context
        record = mock.sentinel.record

        self._set_side_effect('get_record', [record])

        with self.storage_api.delete_record(context, 123) as q:
            self.assertEqual(record, q)

        self._assert_called_with('delete_record', context, 123)

    def test_delete_record_failure(self):
        context = mock.sentinel.context
        record = mock.sentinel.record

        self._set_side_effect('get_record', [record])

        with testtools.ExpectedException(SentinelException):
            with self.storage_api.delete_record(context, 123):
                raise SentinelException('Something Went Wrong')

        self._assert_call_count('delete_record', 0)
