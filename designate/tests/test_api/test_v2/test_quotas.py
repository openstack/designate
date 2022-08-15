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

from designate.tests.test_api.test_v2 import ApiV2TestCase

LOG = logging.getLogger(__name__)


class ApiV2QuotasTest(ApiV2TestCase):
    def setUp(self):
        super(ApiV2QuotasTest, self).setUp()

    def test_get_quotas(self):
        self.config(quota_api_export_size=1)

        context = self.get_context(project_id='a')

        result = self.client.get(
            '/quotas/%s' % context.project_id, status=200,
            headers={'X-Test-Tenant-Id': context.project_id}
        )
        self.assertEqual(
            {
                'zones': 10,
                'zone_recordsets': 500,
                'zone_records': 500,
                'recordset_records': 20,
                'api_export_size': 1
            },
            result.json
        )

    def test_get_all_quotas(self):
        self.config(quota_zone_recordsets=1)

        result = self.client.get(
            '/quotas', status=200,
        )

        self.assertEqual(
            {
                'api_export_size': 1000,
                'recordset_records': 20,
                'zone_records': 500,
                'zone_recordsets': 1,
                'zones': 10
            },
            result.json
        )

    def test_set_quotas(self):
        self.policy({'set_quota': '@'})

        context = self.get_context(project_id='a')
        self.client.patch_json(
            '/quotas/%s' % context.project_id, {'zones': 123}, status=200,
            headers={'X-Test-Tenant-Id': context.project_id}
        )

        result = self.client.get(
            '/quotas/%s' % context.project_id, status=200,
            headers={'X-Test-Tenant-Id': context.project_id}
        )
        self.assertEqual(
            {
                'zones': 123,
                'zone_recordsets': 500,
                'zone_records': 500,
                'recordset_records': 20,
                'api_export_size': 1000
            },
            result.json
        )

    def test_set_quotas_with_verify_project_id(self):
        self.config(
            quotas_verify_project_id=True,
            group='service:api'
        )

        self.policy({'set_quota': '@'})

        context = self.get_context(project_id='a')
        self.client.patch_json(
            '/quotas/%s' % context.project_id, {'zones': 123}, status=200,
            headers={'X-Test-Tenant-Id': context.project_id}
        )

        result = self.client.get(
            '/quotas/%s' % context.project_id, status=200,
            headers={'X-Test-Tenant-Id': context.project_id}
        )
        self.assertEqual(
            {
                'zones': 123,
                'zone_recordsets': 500,
                'zone_records': 500,
                'recordset_records': 20,
                'api_export_size': 1000
            },
            result.json
        )

    def test_delete_quotas(self):
        self.config(quota_zone_records=1)

        self.policy({'set_quota': '@'})

        context = self.get_context(project_id='a')

        # Update recordset_records quota.
        result = self.client.patch_json(
            '/quotas/%s' % context.project_id, {'recordset_records': 123},
            status=200,
            headers={'X-Test-Tenant-Id': context.project_id}
        )
        self.assertEqual(
            {
                'zones': 10,
                'zone_recordsets': 500,
                'zone_records': 1,
                'recordset_records': 123,
                'api_export_size': 1000
            },
            result.json
        )

        # Delete quota.
        self.client.delete(
            '/quotas/%s' % context.project_id, status=204,
            headers={'X-Test-Tenant-Id': context.project_id}
        )

        # Make sure we are back to the default quotas.
        result = self.client.get(
            '/quotas/%s' % context.project_id, status=200,
            headers={'X-Test-Tenant-Id': context.project_id}
        )
        self.assertEqual(
            {
                'zones': 10,
                'zone_recordsets': 500,
                'zone_records': 1,
                'recordset_records': 20,
                'api_export_size': 1000
            },
            result.json
        )
