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
from designate import quota
from designate import tests
from designate.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class StorageQuotaTest(tests.TestCase):
    def setUp(self):
        super(StorageQuotaTest, self).setUp()
        self.config(quota_driver='storage')
        self.quota = quota.get_quota()

    def test_set_quota_create(self):
        quota = self.quota.set_quota(self.admin_context, 'tenant_id',
                                     'domains', 1500)

        self.assertEqual(quota, {'domains': 1500})

        # Drop into the storage layer directly to ensure the quota was created
        # sucessfully.
        criterion = {
            'tenant_id': 'tenant_id',
            'resource': 'domains'
        }

        quota = self.quota.storage_api.find_quota(self.admin_context,
                                                  criterion)

        self.assertEqual(quota['tenant_id'], 'tenant_id')
        self.assertEqual(quota['resource'], 'domains')
        self.assertEqual(quota['hard_limit'], 1500)

    def test_set_quota_update(self):
        # First up, Create the quota
        self.quota.set_quota(self.admin_context, 'tenant_id', 'domains', 1500)

        # Next, update the quota
        self.quota.set_quota(self.admin_context, 'tenant_id', 'domains', 1234)

        # Drop into the storage layer directly to ensure the quota was updated
        # sucessfully
        criterion = {
            'tenant_id': 'tenant_id',
            'resource': 'domains'
        }

        quota = self.quota.storage_api.find_quota(self.admin_context,
                                                  criterion)

        self.assertEqual(quota['tenant_id'], 'tenant_id')
        self.assertEqual(quota['resource'], 'domains')
        self.assertEqual(quota['hard_limit'], 1234)

    def test_reset_quotas(self):
        # First up, Create a domains quota
        self.quota.set_quota(self.admin_context, 'tenant_id', 'domains', 1500)

        # Then, Create a domain_records quota
        self.quota.set_quota(self.admin_context, 'tenant_id', 'domain_records',
                             800)

        # Now, Reset the tenants quota
        self.quota.reset_quotas(self.admin_context, 'tenant_id')

        # Drop into the storage layer directly to ensure the tenant has no
        # specific quotas registed.
        criterion = {
            'tenant_id': 'tenant_id'
        }

        quotas = self.quota.storage_api.find_quotas(self.admin_context,
                                                    criterion)

        self.assertEqual(0, len(quotas))
