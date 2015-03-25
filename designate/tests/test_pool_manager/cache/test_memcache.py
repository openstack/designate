# Copyright 2014 eBay Inc.
#
# Author: Ron Rickard <rrickard@ebaysf.com>
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
from mock import Mock

from designate.pool_manager import cache
from designate.tests import TestCase
from designate.tests.test_pool_manager.cache import PoolManagerCacheTestCase


class MemcachePoolManagerCacheTest(PoolManagerCacheTestCase, TestCase):
    def setUp(self):
        super(MemcachePoolManagerCacheTest, self).setUp()

        self.cache = cache.get_pool_manager_cache('memcache')
        self.mock_status = Mock(
            nameserver_id='nameserver_id',
            domain_id='domain_id',
            action='CREATE',
        )

    def test_store_and_retrieve(self):
        expected = self.create_pool_manager_status()
        self.cache.store(self.admin_context, expected)

        actual = self.cache.retrieve(
            self.admin_context, expected.nameserver_id, expected.domain_id,
            expected.action)

        self.assertEqual(expected.nameserver_id, actual.nameserver_id)
        self.assertEqual(expected.domain_id, actual.domain_id)
        self.assertEqual(expected.status, actual.status)
        self.assertEqual(expected.serial_number, actual.serial_number)
        self.assertEqual(expected.action, actual.action)

    def test_serial_number_key_is_a_string(self):
        """Memcache requires keys be strings.

        RabbitMQ messages are unicode by default, so any string
        interpolation requires explicit encoding.
        """
        key = self.cache._build_serial_number_key(self.mock_status)
        self.assertIsInstance(key, str)
        self.assertEqual(key, 'nameserver_id-domain_id-CREATE-serial_number')

    def test_status_key_is_a_string(self):
        """Memcache requires keys be strings.

        RabbitMQ messages are unicode by default, so any string
        interpolation requires explicit encoding.
        """
        key = self.cache._build_status_key(self.mock_status)
        self.assertIsInstance(key, str)
        self.assertEqual(key, 'nameserver_id-domain_id-CREATE-status')
