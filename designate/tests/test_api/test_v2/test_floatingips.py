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
            headers={'X-Test-Tenant-Id': context.tenant})

        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # TODO(ekarlso): Remove the floatingip key - bug in v2 api
        fip_record = response.json
        self.assertEqual(":".join([fip['region'],
                         fip['id']]), fip_record['id'])
        self.assertEqual(fip['address'], fip_record['address'])
        self.assertEqual(None, fip_record['description'])
        self.assertEqual(None, fip_record['ptrdname'])

    def test_get_floatingip_with_record(self):
        fixture = self.get_ptr_fixture()

        context = self.get_context(tenant='a')

        fip = self.network_api.fake.allocate_floatingip(
            context.tenant)

        self.central_service.update_floatingip(
            context, fip['region'], fip['id'], fixture)

        response = self.client.get(
            '/reverse/floatingips/%s' % ":".join([fip['region'], fip['id']]),
            headers={'X-Test-Tenant-Id': context.tenant})

        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # TODO(ekarlso): Remove the floatingip key - bug in v2 api
        fip_record = response.json
        self.assertEqual(":".join([fip['region'], fip['id']]),
                         fip_record['id'])
        self.assertEqual(fip['address'], fip_record['address'])
        self.assertEqual(None, fip_record['description'])
        self.assertEqual(fixture['ptrdname'], fip_record['ptrdname'])

    def test_get_floatingip_not_allocated(self):
        url = '/reverse/floatingips/foo:04580c52-b253-4eb7-8791-fbb9de9f856f'

        self._assert_exception('not_found', 404, self.client.get, url)

    def test_get_floatingip_invalid_key(self):
        url = '/reverse/floatingips/foo:bar'

        self._assert_exception('bad_request', 400, self.client.get, url)

    def test_list_floatingip_no_allocations(self):
        response = self.client.get('/reverse/floatingips')

        self.assertIn('floatingips', response.json)
        self.assertIn('links', response.json)
        self.assertEqual(0, len(response.json['floatingips']))

    def test_list_floatingip_no_record(self):
        context = self.get_context(tenant='a')

        fip = self.network_api.fake.allocate_floatingip(context.tenant)

        response = self.client.get(
            '/reverse/floatingips',
            headers={'X-Test-Tenant-Id': context.tenant})

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
        fixture = self.get_ptr_fixture()

        context = self.get_context(tenant='a')

        fip = self.network_api.fake.allocate_floatingip(context.tenant)

        self.central_service.update_floatingip(
            context, fip['region'], fip['id'], fixture)

        response = self.client.get(
            '/reverse/floatingips',
            headers={'X-Test-Tenant-Id': context.tenant})

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
        fixture = self.get_ptr_fixture()

        fip = self.network_api.fake.allocate_floatingip('tenant')

        response = self.client.patch_json(
            '/reverse/floatingips/%s' % ":".join([fip['region'], fip['id']]),
            fixture.to_dict(),
            headers={'X-Test-Tenant-Id': 'tenant'})

        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        fip_record = response.json
        self.assertEqual(":".join([fip['region'], fip['id']]),
                         fip_record['id'])
        self.assertEqual(fip['address'], fip_record['address'])
        self.assertEqual(None, fip_record['description'])
        self.assertEqual(fixture['ptrdname'], fip_record['ptrdname'])

    def test_set_floatingip_not_allocated(self):
        fixture = self.get_ptr_fixture()

        fip = self.network_api.fake.allocate_floatingip('tenant')
        self.network_api.fake.deallocate_floatingip(fip['id'])

        url = '/reverse/floatingips/%s' % ":".join([fip['region'], fip['id']])

        self._assert_exception('not_found', 404, self.client.patch_json, url,
                               fixture.to_dict())

    def test_set_floatingip_invalid_ptrdname(self):
        fip = self.network_api.fake.allocate_floatingip('tenant')

        url = '/reverse/floatingips/%s' % ":".join([fip['region'], fip['id']])

        self._assert_exception('invalid_object', 400, self.client.patch_json,
                               url, {'ptrdname': 'test|'})

    def test_set_floatingip_invalid_key(self):
        url = '/reverse/floatingips/%s' % 'foo:random'
        self._assert_exception('bad_request', 400, self.client.patch_json,
                               url, {})

    def test_unset_floatingip(self):
        fixture = self.get_ptr_fixture()
        context = self.get_context(tenant='a')
        elevated_context = context.elevated()
        elevated_context.all_tenants = True

        fip = self.network_api.fake.allocate_floatingip(context.tenant)

        # Unsetting via "None"
        self.central_service.update_floatingip(
            context, fip['region'], fip['id'], fixture)

        criterion = {
            'managed_resource_id': fip['id'],
            'managed_tenant_id': context.tenant
        }
        domain_id = self.central_service.find_record(
            elevated_context, criterion=criterion).domain_id

        # Simulate the update on the backend
        domain_serial = self.central_service.get_domain(
            elevated_context, domain_id).serial
        self.central_service.update_status(
            elevated_context, domain_id, "SUCCESS", domain_serial)

        # Unset PTR ('ptrdname' is None aka null in JSON)
        response = self.client.patch_json(
            '/reverse/floatingips/%s' % ":".join([fip['region'], fip['id']]),
            {'ptrdname': None},
            headers={'X-Test-Tenant-Id': context.tenant})
        self.assertEqual(None, response.json)
        self.assertEqual(200, response.status_int)

        # Simulate the unset on the backend
        domain_serial = self.central_service.get_domain(
            elevated_context, domain_id).serial
        self.central_service.update_status(
            elevated_context, domain_id, "SUCCESS", domain_serial)

        fip = self.central_service.get_floatingip(
            context, fip['region'], fip['id'])
        self.assertEqual(None, fip['ptrdname'])

    def test_unset_floatingip_not_allocated(self):
        fixture = self.get_ptr_fixture()
        context = self.get_context(tenant='a')

        fip = self.network_api.fake.allocate_floatingip(context.tenant)

        self.central_service.update_floatingip(
            context, fip['region'], fip['id'], fixture)

        self.network_api.fake.deallocate_floatingip(fip['id'])

        url = '/reverse/floatingips/%s' % ":".join([fip['region'], fip['id']])

        self._assert_exception('not_found', 404, self.client.patch_json, url,
                               {'ptrdname': None})
