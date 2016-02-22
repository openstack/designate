# coding=utf-8
# COPYRIGHT 2015 Rackspace
#
# Author: Betsy Luzader <betsy.luzader@rackspace.com>
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
from oslo_config import cfg

from designate.tests.test_api.test_admin import AdminApiTestCase

cfg.CONF.import_opt('enabled_extensions_admin', 'designate.api.admin',
                    group='service:api')


class AdminApiReportsTest(AdminApiTestCase):
    def setUp(self):
        self.config(enabled_extensions_admin=['reports'], group='service:api')
        super(AdminApiReportsTest, self).setUp()

    def test_get_counts(self):
        self.policy({'count_tenants': '@'})

        response = self.client.get('/reports/counts')

        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        self.assertIn('counts', response.json)
        self.assertIn('zones', response.json['counts'][0])
        self.assertIn('records', response.json['counts'][0])
        self.assertIn('tenants', response.json['counts'][0])

        # Assert that they are all equal to 0
        self.assertEqual(0, response.json['counts'][0]['zones'])
        self.assertEqual(0, response.json['counts'][0]['records'])
        self.assertEqual(0, response.json['counts'][0]['tenants'])

        # Add a zone and check the counts
        self.create_zone()
        response = self.client.get('/reports/counts')
        # Should be one zone
        self.assertEqual(1, response.json['counts'][0]['zones'])
        # Should be 1 NS and 1 SOA records
        self.assertEqual(2, response.json['counts'][0]['records'])
        # Should be 1 tenant
        self.assertEqual(1, response.json['counts'][0]['tenants'])

    def test_get_counts_zones(self):
        self.policy({'count_zones': '@'})
        response = self.client.get('/reports/counts/zones')

        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        self.assertIn('counts', response.json)
        self.assertIn('zones', response.json['counts'][0])

        self.assertEqual(0, response.json['counts'][0]['zones'])

        # Create 2 zones
        self.create_zone(fixture=0)
        self.create_zone(fixture=1)

        response = self.client.get('/reports/counts/zones')

        self.assertEqual(2, response.json['counts'][0]['zones'])

    def test_get_counts_zones_delayed_notify(self):
        # Count zones that are pending a NOTIFY transaction
        self.policy({'count_zones_delayed_notify': '@'})
        response = self.client.get('/reports/counts/zones_delayed_notify')

        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)
        self.assertIn('counts', response.json)
        self.assertIn('zones_delayed_notify', response.json['counts'][0])
        self.assertEqual(0, response.json['counts'][0]['zones_delayed_notify'])

        # Create 2 zones in pending notify and 1 with delayed_notify=False
        self.create_zone(fixture=0, delayed_notify=True)
        self.create_zone(fixture=1, delayed_notify=True)
        self.create_zone(fixture=2)

        response = self.client.get('/reports/counts/zones')
        self.assertEqual(3, response.json['counts'][0]['zones'])

        response = self.client.get('/reports/counts/zones_delayed_notify')
        self.assertEqual(2, response.json['counts'][0]['zones_delayed_notify'])

    def test_get_counts_records(self):
        self.policy({'count_records': '@'})
        response = self.client.get('/reports/counts/records')

        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        self.assertIn('counts', response.json)
        self.assertIn('records', response.json['counts'][0])

        self.assertEqual(0, response.json['counts'][0]['records'])

        # Create a zone
        self.create_zone()

        response = self.client.get('/reports/counts/records')

        # Should have 1 NS and 1 SOA record
        self.assertEqual(2, response.json['counts'][0]['records'])

    def test_get_counts_tenants(self):
        self.policy({'count_tenants': '@'})
        response = self.client.get('/reports/counts/tenants')

        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        self.assertIn('counts', response.json)
        self.assertIn('tenants', response.json['counts'][0])

        self.assertEqual(0, response.json['counts'][0]['tenants'])

        # Create a zone
        self.create_zone()

        response = self.client.get('/reports/counts/tenants')

        # Should have 1 tenant
        self.assertEqual(1, response.json['counts'][0]['tenants'])

    def test_get_tenants(self):
        self.policy({'find_tenants': '@'})
        self.create_zone()

        response = self.client.get('/reports/tenants')

        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        self.assertIn('tenants', response.json)
        self.assertIn('zone_count', response.json['tenants'][0])

        self.assertEqual(1, response.json['tenants'][0]['zone_count'])

    def test_get_tenant(self):
        self.policy({'find_tenants': '@'})
        zone = self.create_zone()
        tenant = zone.tenant_id

        response = self.client.get('/reports/tenants/%s' % tenant)
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        self.assertIn('zones', response.json)

        self.assertIn('example.com.', response.json['zones'])
