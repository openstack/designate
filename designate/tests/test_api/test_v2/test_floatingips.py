# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@managedit.ie>
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
from designate.tests.test_api.test_v2 import ApiV2TestCase


"""
NOTE: Record invalidation is tested in Central tests
"""


class ApiV2ReverseFloatingIPTest(ApiV2TestCase):
    def test_get_floatingip_no_record(self):
        context = self.get_context(tenant='a')

        fip = self.network_api.fake.allocate_floatingip(context.tenant)

        response = self.client.get(
            '/reverse/floatingips/%s' % ":".join([fip['region'], fip['id']]),
            headers={'X-Test-Tenant-Id': context.tenant_id})

        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)
        self.assertIn('floatingip', response.json)

        #TODO(ekarlso): Remove the floatingip key - bug in v2 api
        fip_record = response.json['floatingip']
        self.assertEqual(":".join([fip['region'],
                         fip['id']]), fip_record['id'])
        self.assertEqual(fip['address'], fip_record['address'])
        self.assertEqual(None, fip_record['description'])
        self.assertEqual(None, fip_record['ptrdname'])

    def test_get_floatingip_with_record(self):
        self.create_server()

        fixture = self.get_ptr_fixture()

        context = self.get_context(tenant='a')

        fip = self.network_api.fake.allocate_floatingip(
            context.tenant)

        self.central_service.update_floatingip(
            context, fip['region'], fip['id'], fixture)

        response = self.client.get(
            '/reverse/floatingips/%s' % ":".join([fip['region'], fip['id']]),
            headers={'X-Test-Tenant-Id': context.tenant_id})

        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)
        self.assertIn('floatingip', response.json)

        # TODO(ekarlso): Remove the floatingip key - bug in v2 api
        fip_record = response.json['floatingip']
        self.assertEqual(":".join([fip['region'], fip['id']]),
                         fip_record['id'])
        self.assertEqual(fip['address'], fip_record['address'])
        self.assertEqual(None, fip_record['description'])
        self.assertEqual(fixture['ptrdname'], fip_record['ptrdname'])

    def test_get_floatingip_not_allocated(self):
        url = '/reverse/floatingips/foo:04580c52-b253-4eb7-8791-fbb9de9f856f'
        response = self.client.get(url, status=404)

        self.assertIn('request_id', response.json)
        self.assertEqual(404, response.json['code'])
        self.assertEqual('not_found', response.json['type'])

    def test_get_floatingip_invalid_key(self):
        response = self.client.get('/reverse/floatingips/foo:bar', status=400)

        self.assertIn('message', response.json)
        self.assertIn('request_id', response.json)
        self.assertEqual(400, response.json['code'])
        self.assertEqual('bad_request', response.json['type'])

    def test_list_floatingip_no_allocations(self):
        response = self.client.get('/reverse/floatingips')

        self.assertIn('floatingips', response.json)
        self.assertIn('links', response.json)
        self.assertEqual(0, len(response.json['floatingips']))

    def test_list_floatingip_no_record(self):
        context = self.get_context(tenant='a')

        fip = self.network_api.fake.allocate_floatingip(context.tenant_id)

        response = self.client.get(
            '/reverse/floatingips',
            headers={'X-Test-Tenant-Id': context.tenant_id})

        self.assertIn('floatingips', response.json)
        self.assertIn('links', response.json)
        self.assertEqual(1, len(response.json['floatingips']))

        fip_record = response.json['floatingips'][0]
        self.assertEqual(None, fip_record['ptrdname'])
        self.assertEqual(":".join([fip['region'], fip['id']]),
                         fip_record['id'])
        self.assertEqual(fip['address'], fip_record['address'])
        self.assertEqual(None, fip_record['description'])

    def test_list_floatingip_with_record(self):
        self.create_server()

        fixture = self.get_ptr_fixture()

        context = self.get_context(tenant='a')

        fip = self.network_api.fake.allocate_floatingip(context.tenant_id)

        self.central_service.update_floatingip(
            context, fip['region'], fip['id'], fixture)

        response = self.client.get(
            '/reverse/floatingips',
            headers={'X-Test-Tenant-Id': context.tenant_id})

        self.assertIn('floatingips', response.json)
        self.assertIn('links', response.json)
        self.assertEqual(1, len(response.json['floatingips']))

        fip_record = response.json['floatingips'][0]
        self.assertEqual(fixture['ptrdname'], fip_record['ptrdname'])
        self.assertEqual(":".join([fip['region'], fip['id']]),
                         fip_record['id'])
        self.assertEqual(fip['address'], fip_record['address'])
        self.assertEqual(None, fip_record['description'])
        self.assertEqual(fixture['ptrdname'], fip_record['ptrdname'])

    def test_set_floatingip(self):
        self.create_server()
        fixture = self.get_ptr_fixture()

        fip = self.network_api.fake.allocate_floatingip('tenant')

        response = self.client.patch_json(
            '/reverse/floatingips/%s' % ":".join([fip['region'], fip['id']]),
            {"floatingip": fixture},
            headers={'X-Test-Tenant-Id': 'tenant'})

        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)
        self.assertIn('floatingip', response.json)

        fip_record = response.json['floatingip']
        self.assertEqual(":".join([fip['region'], fip['id']]),
                         fip_record['id'])
        self.assertEqual(fip['address'], fip_record['address'])
        self.assertEqual(None, fip_record['description'])
        self.assertEqual(fixture['ptrdname'], fip_record['ptrdname'])

    def test_set_floatingip_not_allocated(self):
        fixture = self.get_ptr_fixture()

        fip = self.network_api.fake.allocate_floatingip('tenant')
        self.network_api.fake.deallocate_floatingip(fip['id'])

        response = self.client.patch_json(
            '/reverse/floatingips/%s' % ":".join([fip['region'], fip['id']]),
            {"floatingip": fixture}, status=404)

        self.assertIn('message', response.json)
        self.assertIn('request_id', response.json)
        self.assertEqual(404, response.json['code'])
        self.assertEqual('not_found', response.json['type'])

    def test_set_floatingip_invalid_ptrdname(self):
        fip = self.network_api.fake.allocate_floatingip('tenant')

        response = self.client.patch_json(
            '/reverse/floatingips/%s' % ":".join([fip['region'], fip['id']]),
            {"floatingip": {'ptrxname': 'test'}}, status=400)

        self.assertIn('message', response.json)
        self.assertIn('request_id', response.json)
        self.assertEqual(400, response.json['code'])
        self.assertEqual('invalid_object', response.json['type'])

    def test_set_floatingip_invalid_key(self):
        response = self.client.patch_json(
            '/reverse/floatingips/%s' % 'foo:random', {}, status=400)

        self.assertIn('message', response.json)
        self.assertIn('request_id', response.json)
        self.assertEqual(400, response.json['code'])
        self.assertEqual('bad_request', response.json['type'])

    def test_unset_floatingip(self):
        self.create_server()

        fixture = self.get_ptr_fixture()
        context = self.get_context(tenant='a')

        fip = self.network_api.fake.allocate_floatingip(context.tenant_id)

        # Unsetting via "None"
        self.central_service.update_floatingip(
            context, fip['region'], fip['id'], fixture)

        # Unset PTR ('ptrdname' is None aka null in JSON)
        response = self.client.patch_json(
            '/reverse/floatingips/%s' % ":".join([fip['region'], fip['id']]),
            {'floatingip': {'ptrdname': None}},
            headers={'X-Test-Tenant-Id': context.tenant})
        self.assertEqual(None, response.json)
        self.assertEqual(200, response.status_int)

        fip = self.central_service.get_floatingip(
            context, fip['region'], fip['id'])
        self.assertEqual(None, fip['ptrdname'])

    def test_unset_floatingip_not_allocated(self):
        self.create_server()

        fixture = self.get_ptr_fixture()
        context = self.get_context(tenant='a')

        fip = self.network_api.fake.allocate_floatingip(context.tenant)

        self.central_service.update_floatingip(
            context, fip['region'], fip['id'], fixture)

        self.network_api.fake.deallocate_floatingip(fip['id'])

        response = self.client.patch_json(
            '/reverse/floatingips/%s' % ":".join([fip['region'], fip['id']]),
            {"floatingip": {'ptrdname': None}}, status=404)

        self.assertIn('message', response.json)
        self.assertIn('request_id', response.json)
        self.assertEqual(404, response.json['code'])
        self.assertEqual('not_found', response.json['type'])
