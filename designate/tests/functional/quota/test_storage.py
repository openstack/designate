# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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
from oslo_log import log as logging

from designate.common import constants
from designate import exceptions
from designate import quota
import designate.tests.functional

LOG = logging.getLogger(__name__)


class StorageQuotaTest(designate.tests.functional.TestCase):
    def setUp(self):
        super().setUp()
        self.config(quota_driver='storage')
        self.quota = quota.get_quota()

    def test_set_quota_create_min(self):
        context = self.get_admin_context()
        context.all_tenants = True

        for current_quota in constants.VALID_QUOTAS:
            quota = self.quota.set_quota(context, 'tenant_id',
                                         current_quota, constants.MIN_QUOTA)

            self.assertEqual({current_quota: constants.MIN_QUOTA}, quota)

            # Drop into the storage layer directly to ensure the quota was
            # created successfully
            criterion = {
                'tenant_id': 'tenant_id',
                'resource': current_quota
            }

            quota = self.quota.storage.find_quota(context, criterion)

            self.assertEqual('tenant_id', quota['tenant_id'])
            self.assertEqual(current_quota, quota['resource'])
            self.assertEqual(constants.MIN_QUOTA, quota['hard_limit'])

    def test_set_quota_create_max(self):
        context = self.get_admin_context()
        context.all_tenants = True

        for current_quota in constants.VALID_QUOTAS:
            quota = self.quota.set_quota(context, 'tenant_id',
                                         current_quota, constants.MAX_QUOTA)

            self.assertEqual({current_quota: constants.MAX_QUOTA}, quota)

            # Drop into the storage layer directly to ensure the quota was
            # created successfully
            criterion = {
                'tenant_id': 'tenant_id',
                'resource': current_quota
            }

            quota = self.quota.storage.find_quota(context, criterion)

            self.assertEqual('tenant_id', quota['tenant_id'])
            self.assertEqual(current_quota, quota['resource'])
            self.assertEqual(constants.MAX_QUOTA, quota['hard_limit'])

    def test_get_quota(self):
        context = self.get_admin_context()
        context.all_tenants = True

        for current_quota in constants.VALID_QUOTAS:
            self.quota.set_quota(context, 'tenant_id', current_quota, 1500)
            self.assertEqual(
                {current_quota: 1500},
                self.quota.get_quota(context, 'tenant_id', current_quota)
            )

    def test_set_unknown_quota(self):
        context = self.get_admin_context()
        context.all_tenants = True

        self.assertRaisesRegex(
            exceptions.QuotaResourceUnknown,
            'unknown is not a valid quota resource',
            self.quota.set_quota, context, 'tenant_id', 'unknown', 1500
        )

    def test_set_quota_update(self):
        context = self.get_admin_context()
        context.all_tenants = True

        for current_quota in constants.VALID_QUOTAS:
            # First up, Create the quota
            self.quota.set_quota(context, 'tenant_id', current_quota, 1500)

            # Next, update the quota
            self.quota.set_quota(context, 'tenant_id', current_quota, 1234)

            # Drop into the storage layer directly to ensure the quota was
            # updated successfully
            criterion = {
                'tenant_id': 'tenant_id',
                'resource': current_quota
            }

            quota = self.quota.storage.find_quota(context, criterion)

            self.assertEqual('tenant_id', quota['tenant_id'])
            self.assertEqual(current_quota, quota['resource'])
            self.assertEqual(1234, quota['hard_limit'])

    def test_reset_quotas(self):
        context = self.get_admin_context()
        context.all_tenants = True

        # First up, Create a zones quota
        self.quota.set_quota(context, 'tenant_id', 'zones', 1500)

        # Then, Create a zone_records quota
        self.quota.set_quota(context, 'tenant_id', 'zone_records', 800)

        # Now, Reset the tenants quota
        self.quota.reset_quotas(context, 'tenant_id')

        # Drop into the storage layer directly to ensure the tenant has no
        # specific quotas registed.
        criterion = {
            'tenant_id': 'tenant_id'
        }

        quotas = self.quota.storage.find_quotas(context, criterion)
        self.assertEqual(0, len(quotas))
