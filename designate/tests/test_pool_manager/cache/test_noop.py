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
import testtools

from designate import exceptions
from designate.pool_manager import cache
from designate.tests import TestCase
from designate.tests.test_pool_manager.cache import PoolManagerCacheTestCase


class NoopPoolManagerCacheTest(PoolManagerCacheTestCase, TestCase):
    def setUp(self):
        super(NoopPoolManagerCacheTest, self).setUp()

        self.cache = cache.get_pool_manager_cache('noop')

    def test_store_and_retrieve(self):
        expected = self.create_pool_manager_status()
        self.cache.store(self.admin_context, expected)

        with testtools.ExpectedException(exceptions.PoolManagerStatusNotFound):
            self.cache.retrieve(
                self.admin_context, expected.nameserver_id, expected.domain_id,
                expected.action)
