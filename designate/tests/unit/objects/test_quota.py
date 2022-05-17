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
import oslotest.base

from designate.common import constants
from designate import objects

LOG = logging.getLogger(__name__)


class QuotaTest(oslotest.base.BaseTestCase):
    def test_quota_min(self):
        for current_quota in constants.VALID_QUOTAS:
            quota = objects.Quota(tenant_id='123', resource=current_quota,
                                  hard_limit=constants.MIN_QUOTA)

            self.assertEqual('123', quota.tenant_id)
            self.assertEqual(current_quota, quota.resource)
            self.assertEqual(constants.MIN_QUOTA, quota.hard_limit)

    def test_quota_max(self):
        for current_quota in constants.VALID_QUOTAS:
            quota = objects.Quota(tenant_id='123', resource=current_quota,
                                  hard_limit=constants.MAX_QUOTA)

            self.assertEqual('123', quota.tenant_id)
            self.assertEqual(current_quota, quota.resource)
            self.assertEqual(constants.MAX_QUOTA, quota.hard_limit)

    def test_quota_too_small(self):
        for current_quota in constants.VALID_QUOTAS:
            self.assertRaises(ValueError, objects.Quota, tenant_id='123',
                              resource=current_quota,
                              hard_limit=constants.MIN_QUOTA - 1)

    def test_quota_too_large(self):
        for current_quota in constants.VALID_QUOTAS:
            self.assertRaises(ValueError, objects.Quota, tenant_id='123',
                              resource=current_quota,
                              hard_limit=constants.MAX_QUOTA + 1)

    def test_quota_invalid(self):
        for current_quota in constants.VALID_QUOTAS:
            self.assertRaises(ValueError, objects.Quota, tenant_id='123',
                              resource=current_quota,
                              hard_limit='bogus')

    def test_quota_list(self):
        quotas = objects.QuotaList()
        quotas.append(objects.Quota(
            tenant_id='123', resource=constants.QUOTA_RECORDSET_RECORDS))
        quotas.append(objects.Quota(tenant_id='123',
                                    resource=constants.QUOTA_ZONE_RECORDS))
        quotas.append(objects.Quota(tenant_id='123',
                                    resource=constants.QUOTA_ZONE_RECORDSETS))

        self.assertEqual(constants.QUOTA_RECORDSET_RECORDS, quotas[0].resource)
        self.assertEqual(constants.QUOTA_ZONE_RECORDS, quotas[1].resource)
        self.assertEqual(constants.QUOTA_ZONE_RECORDSETS, quotas[2].resource)

    def test_quota_list_from_dict(self):
        quotas = objects.QuotaList().from_dict({
            constants.QUOTA_ZONES: 100,
            constants.QUOTA_ZONE_RECORDSETS: 101,
            constants.QUOTA_ZONE_RECORDS: 102,
            constants.QUOTA_RECORDSET_RECORDS: 103,
            constants.QUOTA_API_EXPORT_SIZE: 104,
        })

        self.assertEqual(constants.QUOTA_ZONES, quotas[0].resource)
        self.assertEqual(100, quotas[0].hard_limit)
        self.assertEqual(constants.QUOTA_API_EXPORT_SIZE, quotas[4].resource)
        self.assertEqual(104, quotas[4].hard_limit)

    def test_quota_list_to_dict(self):
        quotas = objects.QuotaList().from_dict({
            constants.QUOTA_ZONES: 100,
            constants.QUOTA_ZONE_RECORDSETS: 101,
        })

        self.assertEqual(100, quotas.to_dict()[constants.QUOTA_ZONES])
        self.assertEqual(101,
                         quotas.to_dict()[constants.QUOTA_ZONE_RECORDSETS])
