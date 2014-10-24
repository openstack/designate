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
from designate import objects
from designate.pool_manager.cache.base import PoolManagerCache


class PoolManagerCacheTestCase(object):
    def create_pool_manager_status(self, **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)
        values = kwargs.pop('values', {})

        values = self.get_pool_manager_status_fixture(
            fixture=fixture, values=values)

        return self.cache.create_pool_manager_status(
            context, objects.PoolManagerStatus(**values))

    # Interface Tests
    def test_interface(self):
        self._ensure_interface(PoolManagerCache, self.cache.__class__)

    # Pool manager status tests
    def test_create_pool_manager_status(self):
        domain = self.create_domain()
        values = {
            'server_id': '896aa661-198c-4379-bccd-5d8de7007030',
            'domain_id': domain['id'],
            'status': 'SUCCESS',
            'serial_number': 1,
            'action': 'CREATE'
        }
        expected = objects.PoolManagerStatus(**values)

        actual = self.cache.create_pool_manager_status(
            self.admin_context, expected)

        self.assertIsNotNone(actual['id'])
        self.assertIsNotNone(actual['created_at'])

        self.assertEqual(expected['server_id'], actual['server_id'])
        self.assertEqual(expected['domain_id'], actual['domain_id'])
        self.assertEqual(expected['status'], actual['status'])
        self.assertEqual(expected['serial_number'], actual['serial_number'])
        self.assertEqual(expected['action'], actual['action'])

    def test_create_pool_manager_status_duplicate(self):
        domain = self.create_domain()
        self.create_pool_manager_status(
            fixture=0, values={'domain_id': domain['id']})

        with testtools.ExpectedException(
                exceptions.DuplicatePoolManagerStatus):
            self.create_pool_manager_status(
                fixture=0, values={'domain_id': domain['id']})

    def test_find_pool_manager_statuses(self):
        # Verify that there are no pool manager statuses created
        actual = self.cache.find_pool_manager_statuses(self.admin_context)
        self.assertEqual(0, len(actual))

        # Create a Pool manager status
        domain = self.create_domain()
        expected = self.create_pool_manager_status(
            fixture=0, values={'domain_id': domain['id']})

        actual = self.cache.find_pool_manager_statuses(self.admin_context)
        self.assertEqual(1, len(actual))

        self.assertEqual(expected['server_id'], actual[0]['server_id'])
        self.assertEqual(expected['domain_id'], actual[0]['domain_id'])
        self.assertEqual(expected['status'], actual[0]['status'])
        self.assertEqual(expected['serial_number'], actual[0]['serial_number'])
        self.assertEqual(expected['action'], actual[0]['action'])

    def test_find_pool_manager_statuses_with_criterion(self):
        # Create two pool manager statuses
        domain = self.create_domain()
        expected_one = self.create_pool_manager_status(
            fixture=0, values={'domain_id': domain['id']})
        expected_two = self.create_pool_manager_status(
            fixture=1, values={'domain_id': domain['id']})

        # Verify pool_manager_status_one
        criterion = dict(action=expected_one['action'])

        actuals = self.cache.find_pool_manager_statuses(
            self.admin_context, criterion)
        self.assertEqual(len(actuals), 1)
        self.assertEqual(expected_one['server_id'], actuals[0]['server_id'])
        self.assertEqual(expected_one['domain_id'], actuals[0]['domain_id'])
        self.assertEqual(expected_one['status'], actuals[0]['status'])
        self.assertEqual(
            expected_one['serial_number'], actuals[0]['serial_number'])
        self.assertEqual(expected_one['action'], actuals[0]['action'])

        # Verify pool_manager_status_two
        criterion = dict(action=expected_two['action'])

        actuals = self.cache.find_pool_manager_statuses(
            self.admin_context, criterion)
        self.assertEqual(len(actuals), 1)
        self.assertEqual(expected_two['server_id'], actuals[0]['server_id'])
        self.assertEqual(expected_two['domain_id'], actuals[0]['domain_id'])
        self.assertEqual(expected_two['status'], actuals[0]['status'])
        self.assertEqual(
            expected_two['serial_number'], actuals[0]['serial_number'])
        self.assertEqual(expected_two['action'], actuals[0]['action'])

    def test_get_pool_manager_status(self):
        domain = self.create_domain()
        expected = self.create_pool_manager_status(
            fixture=0, values={'domain_id': domain['id']})
        actual = self.cache.get_pool_manager_status(
            self.admin_context, expected['id'])

        self.assertEqual(expected['server_id'], actual['server_id'])
        self.assertEqual(expected['domain_id'], actual['domain_id'])
        self.assertEqual(expected['status'], actual['status'])
        self.assertEqual(expected['serial_number'], actual['serial_number'])
        self.assertEqual(expected['action'], actual['action'])

    def test_get_pool_manager_status_missing(self):
        with testtools.ExpectedException(exceptions.PoolManagerStatusNotFound):
            uuid = '2c102ffd-7146-4b4e-ad62-b530ee0873fb'
            self.cache.get_pool_manager_status(self.admin_context, uuid)

    def test_find_pool_manager_status_criterion(self):
        # Create two pool manager statuses
        domain = self.create_domain()
        expected_one = self.create_pool_manager_status(
            fixture=0, values={'domain_id': domain['id']})
        expected_two = self.create_pool_manager_status(
            fixture=1, values={'domain_id': domain['id']})

        # Verify pool_manager_status_one
        criterion = dict(action=expected_one['action'])

        actual = self.cache.find_pool_manager_status(
            self.admin_context, criterion)
        self.assertEqual(expected_one['server_id'], actual['server_id'])
        self.assertEqual(expected_one['domain_id'], actual['domain_id'])
        self.assertEqual(expected_one['status'], actual['status'])
        self.assertEqual(
            expected_one['serial_number'], actual['serial_number'])
        self.assertEqual(expected_one['action'], actual['action'])

        # Verify pool_manager_status_two
        criterion = dict(action=expected_two['action'])

        actual = self.cache.find_pool_manager_status(
            self.admin_context, criterion)
        self.assertEqual(expected_two['server_id'], actual['server_id'])
        self.assertEqual(expected_two['domain_id'], actual['domain_id'])
        self.assertEqual(expected_two['status'], actual['status'])
        self.assertEqual(
            expected_two['serial_number'], actual['serial_number'])
        self.assertEqual(expected_two['action'], actual['action'])

    def test_find_pool_manager_status_criterion_missing(self):
        criterion = dict(action='CREATE')

        with testtools.ExpectedException(exceptions.PoolManagerStatusNotFound):
            self.cache.find_pool_manager_status(
                self.admin_context, criterion)

    def test_update_pool_manager_status(self):
        domain = self.create_domain()
        expected = self.create_pool_manager_status(
            fixture=0, values={'domain_id': domain['id']})

        # Update the blacklist
        expected.action = 'UPDATE'

        actual = self.cache.update_pool_manager_status(
            self.admin_context, expected)
        # Verify the new values
        self.assertEqual(expected.action, actual['action'])

    def test_update_pool_manager_status_duplicate(self):
        # Create two pool manager statuses
        domain = self.create_domain()
        pool_manager_status_one = self.create_pool_manager_status(
            fixture=0, values={'domain_id': domain['id']})
        pool_manager_status_two = self.create_pool_manager_status(
            fixture=1, values={'domain_id': domain['id']})

        # Update the second one to be a duplicate of the first
        pool_manager_status_two.status = pool_manager_status_one.status
        pool_manager_status_two.serial_number = \
            pool_manager_status_one.serial_number
        pool_manager_status_two.action = pool_manager_status_one.action

        with testtools.ExpectedException(
                exceptions.DuplicatePoolManagerStatus):
            self.cache.update_pool_manager_status(
                self.admin_context, pool_manager_status_two)

    def test_update_pool_manager_status_missing(self):
        pool_manager_status = objects.PoolManagerStatus(
            id='e8cee063-3a26-42d6-b181-bdbdc2c99d08')

        with testtools.ExpectedException(exceptions.PoolManagerStatusNotFound):
            self.cache.update_pool_manager_status(
                self.admin_context, pool_manager_status)

    def test_delete_pool_manager_status(self):
        domain = self.create_domain()
        pool_manager_status = self.create_pool_manager_status(
            fixture=0, values={'domain_id': domain['id']})

        self.cache.delete_pool_manager_status(
            self.admin_context, pool_manager_status['id'])

        with testtools.ExpectedException(exceptions.PoolManagerStatusNotFound):
            self.cache.get_pool_manager_status(
                self.admin_context, pool_manager_status['id'])

    def test_delete_pool_manager_status_missing(self):
        with testtools.ExpectedException(exceptions.PoolManagerStatusNotFound):
            uuid = '97f57960-f41b-4e93-8e22-8fd6c7e2c183'
            self.cache.delete_pool_manager_status(self.admin_context, uuid)
