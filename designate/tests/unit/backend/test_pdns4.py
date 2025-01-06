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

import oslotest.base
import requests_mock
from unittest import mock

from designate.backend import impl_pdns4
from designate import context
from designate import exceptions
from designate import objects
from designate.tests import base_fixtures


class PDNS4BackendTestCase(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(self.stdlog)

        self.context = mock.Mock()
        self.admin_context = mock.Mock()
        mock.patch.object(
            context.DesignateContext, 'get_admin_context',
            return_value=self.admin_context).start()

        self.base_address = 'http://203.0.113.1:8081/api/v1/servers'
        self.zone = objects.Zone(
            id='e2bed4dc-9d01-11e4-89d3-123b93f75cba',
            name='example.com.',
            email='example@example.com',
        )
        self.target = {
            'id': '4588652b-50e7-46b9-b688-a9bad40a873e',
            'type': 'pdns4',
            'masters': [
                {'host': '192.0.2.1', 'port': 53},
                {'host': '192.0.2.2', 'port': 35},
            ],
            'options': [
                {'key': 'api_endpoint', 'value': 'http://203.0.113.1:8081'},
                {'key': 'api_token', 'value': 'api_key'},
                {'key': 'api_ca_cert', 'value': ''}
            ],
        }

        self.backend = impl_pdns4.PDNS4Backend(
            objects.PoolTarget.from_dict(self.target)
        )

    @requests_mock.mock()
    def test_create_zone_success(self, req_mock):
        req_mock.post(
            '%s/localhost/zones' % self.base_address,
        )
        req_mock.get(
            f'{self.base_address}/localhost/zones/{self.zone.name}',
            status_code=404,
        )

        self.backend.create_zone(self.context, self.zone)

        self.assertEqual(
            req_mock.last_request.json(),
            {
                'kind': 'slave',
                'masters': ['192.0.2.1:53', '192.0.2.2:35'],
                'name': 'example.com.',
            }
        )

        self.assertEqual(
            req_mock.last_request.headers.get('X-API-Key'), 'api_key'
        )

    @requests_mock.mock()
    def test_create_zone_ipv6(self, req_mock):
        self.target['masters'] = [
            {'host': '2001:db8::9abc', 'port': 53},
        ]

        self.backend = impl_pdns4.PDNS4Backend(
            objects.PoolTarget.from_dict(self.target)
        )

        req_mock.post(
            '%s/localhost/zones' % self.base_address,
        )
        req_mock.get(
            f'{self.base_address}/localhost/zones/{self.zone.name}',
            status_code=404,
        )

        self.backend.create_zone(self.context, self.zone)

        self.assertEqual(
            req_mock.last_request.json(),
            {
                'kind': 'slave',
                'masters': ['[2001:db8::9abc]:53'],
                'name': 'example.com.',
            }
        )

        self.assertEqual(
            req_mock.last_request.headers.get('X-API-Key'), 'api_key'
        )

    @requests_mock.mock()
    def test_create_zone_hostname(self, req_mock):
        self.target['masters'] = [
            {'host': 'mdns.designate.example.com.', 'port': 53},
        ]

        self.backend = impl_pdns4.PDNS4Backend(
            objects.PoolTarget.from_dict(self.target)
        )

        req_mock.post(
            '%s/localhost/zones' % self.base_address,
        )
        req_mock.get(
            f'{self.base_address}/localhost/zones/{self.zone.name}',
            status_code=404,
        )

        self.backend.create_zone(self.context, self.zone)

        self.assertEqual(
            req_mock.last_request.json(),
            {
                'kind': 'slave',
                'masters': ['mdns.designate.example.com.:53'],
                'name': 'example.com.',
            }
        )

        self.assertEqual(
            req_mock.last_request.headers.get('X-API-Key'), 'api_key'
        )

    @requests_mock.mock()
    def test_create_zone_already_exists(self, req_mock):
        req_mock.post(
            '%s/localhost/zones' % self.base_address,
        )
        req_mock.get(
            f'{self.base_address}/localhost/zones/{self.zone.name}',
            status_code=200,
        )
        req_mock.delete(
            '%s/localhost/zones/example.com.' % self.base_address,
        )

        self.backend.create_zone(self.context, self.zone)

        self.assertEqual(
            req_mock.last_request.json(),
            {
                'kind': 'slave',
                'masters': ['192.0.2.1:53', '192.0.2.2:35'],
                'name': 'example.com.',
            }
        )

        self.assertEqual(
            req_mock.last_request.headers.get('X-API-Key'), 'api_key'
        )

    @requests_mock.mock()
    def test_create_zone_already_exists_and_fails_to_delete(self, req_mock):
        req_mock.post(
            '%s/localhost/zones' % self.base_address,
            status_code=500,
        )
        req_mock.get(
            f'{self.base_address}/localhost/zones/{self.zone.name}',
            status_code=200,
        )
        req_mock.delete(
            '%s/localhost/zones/example.com.' % self.base_address,
            status_code=500,
        )

        self.assertRaisesRegex(
            exceptions.Backend,
            '500 Server Error: None for url: '
            '%s/localhost/zones' % self.base_address,
            self.backend.create_zone, self.context, self.zone
        )

        self.assertIn(
            "Could not delete pre-existing zone "
            "<Zone id:'e2bed4dc-9d01-11e4-89d3-123b93f75cba' "
            "type:'None' name:'example.com.' pool_id:'None' serial:'None' "
            "action:'None' status:'None' shard:'None'>",
            self.stdlog.logger.output
        )

        self.assertIn(
            "<Zone id:'e2bed4dc-9d01-11e4-89d3-123b93f75cba' type:'None' "
            "name:'example.com.' pool_id:'None' serial:'None' action:'None' "
            "status:'None' shard:'None'> exists on the server. "
            "Deleting zone before creation",
            self.stdlog.logger.output
        )

    @requests_mock.mock()
    def test_create_zone_with_tsigkey(self, req_mock):
        req_mock.post(
            '%s/localhost/zones' % self.base_address,
        )
        req_mock.get(
            f'{self.base_address}/localhost/zones/{self.zone.name}',
            status_code=404,
        )

        target = dict(self.target)
        target['options'].append(
            {'key': 'tsigkey_name', 'value': 'tsig_key'}
        )
        backend = impl_pdns4.PDNS4Backend(
            objects.PoolTarget.from_dict(target)
        )

        backend.create_zone(self.context, self.zone)

        self.assertEqual(
            req_mock.last_request.json(),
            {
                'kind': 'slave',
                'masters': ['192.0.2.1:53', '192.0.2.2:35'],
                'name': 'example.com.',
                'slave_tsig_key_ids': ['tsig_key'],
            }
        )

        self.assertEqual(
            req_mock.last_request.headers.get('X-API-Key'), 'api_key'
        )

    @requests_mock.mock()
    def test_create_zone_fail(self, req_mock):
        req_mock.post(
            '%s/localhost/zones' % self.base_address,
            status_code=500,
        )
        req_mock.get(
            f'{self.base_address}/localhost/zones/{self.zone.name}',
            status_code=404,
        )

        self.assertRaisesRegex(
            exceptions.Backend,
            '500 Server Error: None for url: '
            '%s/localhost/zones' % self.base_address,
            self.backend.create_zone, self.context, self.zone
        )

        self.assertEqual(
            req_mock.last_request.headers.get('X-API-Key'), 'api_key'
        )

    @requests_mock.mock()
    def test_create_zone_fail_with_failed_delete(self, req_mock):
        req_mock.post(
            '%s/localhost/zones' % self.base_address,
            status_code=500,
        )
        req_mock.get(
            f'{self.base_address}/localhost/zones/{self.zone.name}',
            [{'status_code': 404}, {'status_code': 200}],
        )
        req_mock.delete(
            '%s/localhost/zones/example.com.' % self.base_address,
            status_code=500,
        )

        self.assertRaisesRegex(
            exceptions.Backend,
            '500 Server Error: None for url: '
            '%s/localhost/zones' % self.base_address,
            self.backend.create_zone, self.context, self.zone
        )

        self.assertEqual(
            req_mock.last_request.headers.get('X-API-Key'), 'api_key'
        )

        self.assertIn(
            "<Zone id:'e2bed4dc-9d01-11e4-89d3-123b93f75cba' type:'None' "
            "name:'example.com.' pool_id:'None' serial:'None' action:'None' "
            "status:'None' shard:'None'> was created with an error. "
            "Deleting zone",
            self.stdlog.logger.output
        )

        self.assertIn(
            "Could not delete errored zone "
            "<Zone id:'e2bed4dc-9d01-11e4-89d3-123b93f75cba' type:'None' "
            "name:'example.com.' pool_id:'None' serial:'None' action:'None' "
            "status:'None' shard:'None'>",
            self.stdlog.logger.output
        )

    @requests_mock.mock()
    def test_delete_zone_success(self, req_mock):
        req_mock.delete(
            '%s/localhost/zones/example.com.' % self.base_address,
        )
        req_mock.get(
            f'{self.base_address}/localhost/zones/{self.zone.name}',
            status_code=200,
        )

        self.backend.delete_zone(self.context, self.zone)

        self.assertEqual(
            req_mock.last_request.headers.get('X-API-Key'), 'api_key'
        )

    @requests_mock.mock()
    def test_delete_zone_missing(self, req_mock):
        req_mock.delete(
            '%s/localhost/zones/example.com.' % self.base_address,
        )

        # pdns returns 422 if asked about a zone that doesn't exist.
        req_mock.get(
            f'{self.base_address}/localhost/zones/{self.zone.name}',
            status_code=422,
        )

        self.backend.delete_zone(self.context, self.zone)

        self.assertEqual(
            req_mock.last_request.headers.get('X-API-Key'), 'api_key'
        )

    @requests_mock.mock()
    def test_delete_zone_fail(self, req_mock):
        req_mock.delete(
            '%s/localhost/zones/example.com.' % self.base_address,
            status_code=500,
        )
        req_mock.get(
            f'{self.base_address}/localhost/zones/{self.zone.name}',
            status_code=200,
        )

        self.assertRaisesRegex(
            exceptions.Backend,
            '500 Server Error: None for url: '
            '%s/localhost/zones' % self.base_address,
            self.backend.delete_zone, self.context, self.zone
        )

        self.assertEqual(
            req_mock.last_request.headers.get('X-API-Key'), 'api_key'
        )

    @mock.patch('os.path.exists')
    def test_verify_ssl(self, mock_path_exists):
        mock_path_exists.return_value = True

        self.backend.api_ca_cert = 'valid_cert'

        self.assertEqual('valid_cert', self.backend._verify_ssl())

    @mock.patch('os.path.exists')
    def test_verify_ssl_does_not_exist(self, mock_path_exists):
        mock_path_exists.return_value = False

        self.backend.api_ca_cert = 'valid_cert'

        self.assertFalse(self.backend._verify_ssl())

    def test_verify_ssl_not_valid(self):
        self.assertFalse(self.backend._verify_ssl())

        self.backend.api_ca_cert = 'changeme'
        self.assertFalse(self.backend._verify_ssl())

        self.backend.api_ca_cert = ''
        self.assertFalse(self.backend._verify_ssl())

        self.backend.api_ca_cert = None
        self.assertFalse(self.backend._verify_ssl())
