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
import random
from unittest import mock

import jinja2
from oslo_concurrency import processutils
from oslo_config import fixture as cfg_fixture
import oslotest.base

import designate.conf
from designate import exceptions
from designate.tests import base_fixtures
from designate import utils


CONF = designate.conf.CONF


class TestUtils(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(cfg_fixture.Config(CONF))
        self.useFixture(self.stdlog)

    def test_validate_uuid(self):
        @utils.validate_uuid('zone_id')
        def validate_uuid(cls, zone_id):
            return True
        self.assertTrue(
            validate_uuid(None, '6a8caf9d-679e-4fc1-80e9-13496f6a783f')
        )

    def test_validate_invalid_uuid(self):
        @utils.validate_uuid('zone_id')
        def validate_uuid(cls, zone_id):
            return True

        self.assertRaisesRegex(
            exceptions.InvalidUUID,
            'Invalid UUID zone_id: 62f89e5f088c7',
            validate_uuid, None, '62f89e5f088c7'
        )

    def test_validate_uuid_no_arguments(self):
        @utils.validate_uuid('zone_id')
        def validate_uuid(cls):
            return
        self.assertRaises(exceptions.NotFound, validate_uuid)

    def test_invalid_uuid_no_argument_provided(self):
        @utils.validate_uuid('zone_id')
        def validate_uuid(cls):
            return
        self.assertRaises(exceptions.NotFound, validate_uuid, None)

    @mock.patch('os.path.exists')
    @mock.patch('os.path.abspath')
    def test_find_config(self, mock_abspath, mock_path_exists):
        CONF.set_override('pybasedir', '/tmp/workspace/designate')

        mock_path_exists.side_effect = [True, False, False, False, False]
        mock_abspath.return_value = '/tmp/designate/designate.conf'

        config_files = utils.find_config('designate.conf')

        self.assertEqual(['/tmp/designate/designate.conf'], config_files)
        mock_abspath.assert_called_once()

    @mock.patch.object(processutils, 'execute')
    def test_execute(self, mock_execute):
        mock_execute.return_value = ('designate.conf\npools.yaml\n', '')

        out, err = utils.execute(
            '/bin/ls', '/etc/designate/',
            run_as_root=False
        )

        mock_execute.assert_called_once_with(
            '/bin/ls', '/etc/designate/',
            root_helper='sudo designate-rootwrap /etc/designate/rootwrap.conf',
            run_as_root=False
        )

        self.assertEqual('designate.conf\npools.yaml\n', out)
        self.assertFalse(err)

    @mock.patch.object(processutils, 'execute')
    def test_execute_with_rootwrap(self, mock_execute):
        CONF.set_override('root_helper', 'sudo designate-test')

        mock_execute.return_value = ('designate.conf\npools.yaml\n', '')

        out, err = utils.execute(
            '/bin/ls', '/etc/designate/',
            run_as_root=True
        )

        mock_execute.assert_called_once_with(
            '/bin/ls', '/etc/designate/',
            root_helper='sudo designate-test',
            run_as_root=True
        )

        self.assertEqual('designate.conf\npools.yaml\n', out)
        self.assertFalse(err)

    def test_deep_dict_merge(self):
        a = {
            'a': {'dns': 'record'},
            'b': 'b',
            'c': 'c',
        }

        b = {
            'a': {'domain': 'zone'},
            'c': 1,
            'd': 'd',
        }

        self.assertEqual(
            {
                'a': {
                    'dns': 'record', 'domain': 'zone'
                },
                'b': 'b', 'c': 1, 'd': 'd'
            },
            utils.deep_dict_merge(a, b)
        )

    def test_deep_dict_merge_not_dict(self):
        result = utils.deep_dict_merge(dict(), list())

        self.assertIsInstance(result, list)

    def test_get_proxies(self):
        CONF.set_override('no_proxy', 'example.com', 'proxy')
        CONF.set_override('http_proxy', 'example.org', 'proxy')
        CONF.set_override('https_proxy', 'example.net', 'proxy')

        result = utils.get_proxies()

        self.assertEqual(['example.com'], result.get('no_proxy'))
        self.assertEqual('example.org', result.get('http'))
        self.assertEqual('example.net', result.get('https'))

    def test_get_proxies_default_values(self):
        result = utils.get_proxies()

        self.assertIsNone(result.get('no_proxy'))
        self.assertIsNone(result.get('http'))
        self.assertIsNone(result.get('https'))

    def test_get_proxies_with_no_proxy(self):
        CONF.set_override('no_proxy', 'example.org', 'proxy')

        result = utils.get_proxies()

        self.assertEqual(['example.org'], result.get('no_proxy'))
        self.assertIsNone(result.get('http'))
        self.assertIsNone(result.get('https'))

    def test_get_proxies_with_http_proxy(self):
        CONF.set_override('http_proxy', 'example.org', 'proxy')

        result = utils.get_proxies()

        self.assertIsNone(result.get('no_proxy'))
        self.assertEqual('example.org', result.get('http'))
        self.assertEqual('example.org', result.get('https'))

    def test_get_proxies_with_https_proxy(self):
        CONF.set_override('https_proxy', 'example.org', 'proxy')

        result = utils.get_proxies()

        self.assertIsNone(result.get('no_proxy'))
        self.assertIsNone(result.get('http'))
        self.assertEqual('example.org', result.get('https'))

    def test_resource_string(self):
        resource_string = utils.resource_string(
            'templates', 'bind9-zone.jinja2'
        )

        self.assertIsNotNone(resource_string)

    def test_resource_string_missing(self):
        self.assertRaisesRegex(
            exceptions.ResourceNotFound,
            'Could not find the requested resource',
            utils.resource_string, 'invalid.jinja2'
        )

    def test_resource_string_empty_args(self):
        self.assertRaises(
            ValueError,
            utils.resource_string
        )

    def test_load_schema_missing(self):
        self.assertRaisesRegex(
            exceptions.ResourceNotFound,
            'Could not find the requested resource',
            utils.load_schema, 'v1', 'missing'
        )

    @mock.patch.object(utils, 'resource_string')
    def test_load_template(self, mock_resource_string):
        mock_resource_string.return_value = b'Hello {{name}}'

        template = utils.load_template('bind9-zone.jinja2')

        self.assertIsInstance(template, jinja2.Template)

    @mock.patch.object(utils, 'resource_string')
    def test_load_template_keep_trailing_newline(self, mock_resource_string):
        mock_resource_string.return_value = b'Hello {{name}}'

        template = utils.load_template('bind9-zone.jinja2')

        self.assertTrue(template.environment.keep_trailing_newline)

    def test_load_template_missing(self):
        self.assertRaises(
            exceptions.ResourceNotFound,
            utils.load_template, 'invalid.jinja2'
        )

    def test_render_template(self):
        template = jinja2.Template('Hello {{name}}')

        result = utils.render_template(template, name='World')

        self.assertEqual('Hello World', result)

    def test_split_host_port(self):
        host, port = utils.split_host_port('abc:25')
        self.assertEqual(('abc', 25), (host, port))

    def test_split_host_port_with_invalid_port(self):
        host, port = utils.split_host_port('abc:abc')
        self.assertEqual(('abc:abc', 53), (host, port))

    def test_get_paging_params(self):
        CONF.set_override('default_limit_v2', 100, 'service:api')

        context = mock.Mock()
        params = {
            'updated_at': None,
            'created_at': '2019-06-28T04:17:34.000000',
            'pattern': 'blacklisted.com.',
            'id': 'f6663a98-281e-4cea-b0c3-3bc425e086ea',
        }

        marker, limit, sort_key, sort_dir = utils.get_paging_params(
            context, params, ['created_at', 'id', 'updated_at', 'pattern']
        )

        self.assertIsNone(marker)
        self.assertEqual(100, limit)
        self.assertIsNone(sort_key)
        self.assertIsNone(sort_dir)

    def test_get_paging_params_without_sort_keys(self):
        CONF.set_override('default_limit_v2', 0, 'service:api')

        context = mock.Mock()
        params = {
            'updated_at': None,
            'created_at': '2019-06-28T04:17:34.000000',
            'pattern': 'blacklisted.com.',
            'id': 'f6663a98-281e-4cea-b0c3-3bc425e086ea',
        }

        marker, limit, sort_key, sort_dir = utils.get_paging_params(
            context, params, sort_keys=None
        )

        self.assertIsNone(marker)
        self.assertEqual(0, limit)
        self.assertIsNone(sort_key)
        self.assertIsNone(sort_dir)

    def test_get_paging_params_sort_by_tenant_id(self):
        CONF.set_override('default_limit_v2', 100, 'service:api')

        context = mock.Mock()
        context.all_tenants = True
        params = {
            'updated_at': None,
            'created_at': '2019-06-28T04:17:34.000000',
            'pattern': 'blacklisted.com.',
            'id': 'f6663a98-281e-4cea-b0c3-3bc425e086ea',
            'sort_key': 'tenant_id',
        }

        marker, limit, sort_key, sort_dir = utils.get_paging_params(
            context, params,
            ['created_at', 'id', 'updated_at', 'pattern', 'tenant_id']
        )

        self.assertIsNone(marker)
        self.assertEqual(100, limit)
        self.assertEqual('tenant_id', sort_key)
        self.assertIsNone(sort_dir)

    def test_get_paging_params_sort_tenant_without_all_tenants(self):
        CONF.set_override('default_limit_v2', 100, 'service:api')

        context = mock.Mock()
        context.all_tenants = False
        params = {
            'updated_at': None,
            'created_at': '2019-06-28T04:17:34.000000',
            'pattern': 'blacklisted.com.',
            'id': 'f6663a98-281e-4cea-b0c3-3bc425e086ea',
            'sort_key': 'tenant_id',
        }

        marker, limit, sort_key, sort_dir = utils.get_paging_params(
            context, params,
            ['created_at', 'id', 'updated_at', 'pattern', 'tenant_id']
        )

        self.assertIsNone(marker)
        self.assertEqual(100, limit)
        self.assertIsNone(sort_key)
        self.assertIsNone(sort_dir)

    def test_get_paging_params_invalid_limit(self):
        context = mock.Mock()

        self.assertRaises(
            exceptions.InvalidLimit,
            utils.get_paging_params,
            context, {'limit': 9223372036854775809}, []
        )

        self.assertRaises(
            exceptions.InvalidLimit,
            utils.get_paging_params,
            context, {'limit': -1}, []
        )

    def test_get_paging_params_max_limit(self):
        CONF.set_override('max_limit_v2', 1000, 'service:api')

        context = mock.Mock()

        result = utils.get_paging_params(context, {'limit': 'max'}, [])

        self.assertEqual(result[1], 1000)

    def test_get_paging_params_invalid_sort_dir(self):
        context = mock.Mock()

        self.assertRaisesRegex(
            exceptions.InvalidSortDir,
            'Unknown sort direction, must be',
            utils.get_paging_params, context, {'sort_dir': 'dsc'}, []
        )

    def test_get_paging_params_invalid_sort_key(self):
        context = mock.Mock()

        self.assertRaisesRegex(
            exceptions.InvalidSortKey,
            'sort key must be one of',
            utils.get_paging_params, context, {'sort_key': 'dsc'},
            ['asc', 'desc']
        )

    @mock.patch('socket.socket')
    def test_bind_tcp(self, mock_sock_impl):
        mock_sock = mock.MagicMock()
        mock_sock_impl.return_value = mock_sock

        utils.bind_tcp('203.0.113.1', 53, 100, 1)

        mock_sock.settimeout.assert_called_once_with(1)

        mock_sock.bind.assert_called_once_with(('203.0.113.1', 53))

        mock_sock.listen.assert_called_once_with(100)

        self.assertIn(
            'Opening TCP Listening Socket on 203.0.113.1:53',
            self.stdlog.logger.output
        )

    @mock.patch('socket.socket')
    def test_bind_tcp_without_port(self, mock_sock_impl):
        random_port = random.randint(1024, 65535)
        mock_sock = mock.MagicMock()
        mock_sock_impl.return_value = mock_sock

        mock_sock.getsockname.return_value = ('203.0.113.1', random_port)

        utils.bind_tcp('203.0.113.1', 0, 100, 1)

        self.assertIn(
            'Listening on TCP port %(port)d' % {'port': random_port},
            self.stdlog.logger.output
        )

    @mock.patch('socket.socket')
    def test_bind_tcp_without_reuse_port(self, mock_sock_impl):
        mock_sock = mock.MagicMock()
        mock_sock_impl.return_value = mock_sock
        mock_sock.setsockopt.side_effect = [None, None, AttributeError, None]

        utils.bind_tcp('203.0.113.1', 53, 100, 1)

        self.assertIn(
            'SO_REUSEPORT not available, ignoring.',
            self.stdlog.logger.output
        )

    @mock.patch('socket.socket')
    def test_bind_udp(self, mock_sock_impl):
        mock_sock = mock.MagicMock()
        mock_sock_impl.return_value = mock_sock

        utils.bind_udp('203.0.113.1', 53)

        mock_sock.settimeout.assert_called_once_with(1)

        mock_sock.bind.assert_called_once_with(('203.0.113.1', 53))

        self.assertIn(
            'Opening UDP Listening Socket on 203.0.113.1:53',
            self.stdlog.logger.output
        )

    @mock.patch('socket.socket')
    def test_bind_udp_without_port(self, mock_sock_impl):
        random_port = random.randint(1024, 65535)
        mock_sock = mock.MagicMock()
        mock_sock_impl.return_value = mock_sock

        mock_sock.getsockname.return_value = ('203.0.113.1', random_port)

        utils.bind_udp('203.0.113.1', 0)

        self.assertIn(
            'Listening on UDP port %(port)d' % {'port': random_port},
            self.stdlog.logger.output
        )

    @mock.patch('socket.socket')
    def test_bind_udp_without_reuse_port(self, mock_sock_impl):
        mock_sock = mock.MagicMock()
        mock_sock_impl.return_value = mock_sock
        mock_sock.setsockopt.side_effect = [None, AttributeError]

        utils.bind_udp('203.0.113.1', 53)

        self.assertIn(
            'SO_REUSEPORT not available, ignoring.',
            self.stdlog.logger.output
        )
