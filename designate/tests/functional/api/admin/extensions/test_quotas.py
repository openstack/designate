# COPYRIGHT 2014 Rackspace
#
# Author: Tim Simmons <tim.simmons@rackspace.com>
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


import designate.conf
from designate.tests.functional.api import admin


CONF = designate.conf.CONF


class AdminApiQuotasTest(admin.AdminApiTestCase):
    def setUp(self):
        self.config(enabled_extensions_admin=['quotas'], group='service:api')
        super().setUp()

    def test_get_quotas(self):
        self.policy({'get_quotas': '@'})
        context = self.get_admin_context()

        response = self.client.get('/quotas/%s' % context.project_id,
                                   headers={'X-Test-Tenant-Id':
                                            context.project_id})

        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        self.assertIn('quota', response.json)
        self.assertIn('zones', response.json['quota'])
        self.assertIn('api_export_size', response.json['quota'])
        self.assertIn('zone_records', response.json['quota'])
        self.assertIn('zone_recordsets', response.json['quota'])
        self.assertIn('recordset_records', response.json['quota'])

        max_zones = response.json['quota']['zones']
        max_zone_records = response.json['quota']['zone_records']
        self.assertEqual(CONF.quota_zones, max_zones)
        self.assertEqual(CONF.quota_zone_records, max_zone_records)

    def test_get_quotas_detailed(self):
        self.policy({'get_quotas': '@'})
        context = self.get_admin_context()

        response = self.client.get(
            '/quotas/%s?detail=yes' % context.project_id,
            headers={'X-Test-Tenant-Id': context.project_id}
        )

        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        self.assertIn('quota', response.json)
        self.assertIn('zones', response.json['quota'])
        self.assertIn('api_export_size', response.json['quota'])
        self.assertIn('zone_records', response.json['quota'])
        self.assertIn('zone_recordsets', response.json['quota'])
        self.assertIn('recordset_records', response.json['quota'])

        max_zones = response.json['quota']['zones']
        max_zone_records = response.json['quota']['zone_records']
        self.assertEqual(CONF.quota_zones, max_zones)
        self.assertEqual(CONF.quota_zone_records, max_zone_records)

    def test_patch_quotas(self):
        self.policy({'set_quotas': '@'})
        context = self.get_context(project_id='a', is_admin=True)

        response = self.client.get('/quotas/%s' % 'a',
                                   headers={'X-Test-Tenant-Id':
                                            context.project_id})

        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        self.assertIn('quota', response.json)
        self.assertIn('zones', response.json['quota'])
        current_count = response.json['quota']['zones']

        body = {'quota': {"zones": 1337}}
        response = self.client.patch_json('/quotas/%s' % 'a', body,
                                          status=200,
                                          headers={'X-Test-Tenant-Id':
                                                   context.project_id})
        self.assertEqual(200, response.status_int)

        response = self.client.get('/quotas/%s' % 'a',
                                   headers={'X-Test-Tenant-Id':
                                            context.project_id})

        new_count = response.json['quota']['zones']

        self.assertNotEqual(current_count, new_count)

    def test_patch_quotas_validation(self):
        self.policy({'set_quotas': '@'})
        context = self.get_context(project_id='a', is_admin=True)
        url = '/quotas/%s' % 'a'

        # Test a negative number for zones
        body = {'quota': {"zones": -1337}}

        # Ensure it fails with a 400
        self._assert_exception(
            'invalid_object', 400, self.client.patch_json,
            url, body,
            headers={'X-Test-Tenant-Id': context.project_id}
        )

        # Test a number > maximum (2147483647) for zones
        body = {'quota': {"zones": 2147483648}}

        # Ensure it fails with a 400
        self._assert_exception(
            'invalid_object', 400, self.client.patch_json,
            url, body,
            headers={'X-Test-Tenant-Id': context.project_id}
        )

    def test_reset_quotas(self):
        self.policy({'reset_quotas': '@'})
        context = self.get_context(project_id='a', is_admin=True)

        response = self.client.get('/quotas/%s' % 'a',
                                   headers={'X-Test-Tenant-Id':
                                            context.project_id})

        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        self.assertIn('quota', response.json)
        self.assertIn('zones', response.json['quota'])
        current_count = response.json['quota']['zones']

        body = {'quota': {"zones": 1337}}
        response = self.client.patch_json('/quotas/%s' % 'a', body,
                                          status=200,
                                          headers={'X-Test-Tenant-Id':
                                                   context.project_id})
        self.assertEqual(200, response.status_int)

        response = self.client.get('/quotas/%s' % 'a',
                                   headers={'X-Test-Tenant-Id':
                                            context.project_id})

        new_count = response.json['quota']['zones']

        self.assertNotEqual(current_count, new_count)

        response = self.client.delete('/quotas/%s' % 'a',
                                      headers={'X-Test-Tenant-Id':
                                               context.project_id}, status=204)
        response = self.client.get('/quotas/%s' % 'a',
                                   headers={'X-Test-Tenant-Id':
                                            context.project_id})

        newest_count = response.json['quota']['zones']
        self.assertNotEqual(new_count, newest_count)
        self.assertEqual(current_count, newest_count)
