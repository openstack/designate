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

from designate import objects

LOG = logging.getLogger(__name__)


class QuotaTest(oslotest.base.BaseTestCase):
    def test_quota(self):
        quota = objects.Quota(
            tenant_id='123', resource='dns', hard_limit=100
        )

        self.assertEqual('123', quota.tenant_id)
        self.assertEqual('dns', quota.resource)
        self.assertEqual(100, quota.hard_limit)

    def test_quota_list(self):
        quotas = objects.QuotaList()
        quotas.append(objects.Quota(tenant_id='123', resource='dns1'))
        quotas.append(objects.Quota(tenant_id='123', resource='dns2'))
        quotas.append(objects.Quota(tenant_id='123', resource='dns3'))

        self.assertEqual('dns1', quotas[0].resource)
        self.assertEqual('dns2', quotas[1].resource)
        self.assertEqual('dns3', quotas[2].resource)

    def test_quota_list_from_dict(self):
        quotas = objects.QuotaList().from_dict({
            'zones': 100,
            'zone_recordsets': 101,
            'zone_records': 102,
            'recordset_records': 103,
            'api_export_size': 104,
        })

        self.assertEqual('zones', quotas[0].resource)
        self.assertEqual(100, quotas[0].hard_limit)
        self.assertEqual('api_export_size', quotas[4].resource)
        self.assertEqual(104, quotas[4].hard_limit)

    def test_quota_list_to_dict(self):
        quotas = objects.QuotaList().from_dict({
            'zones': 100,
            'zone_recordsets': 101,
        })

        self.assertEqual(100, quotas.to_dict()['zones'])
        self.assertEqual(101, quotas.to_dict()['zone_recordsets'])
