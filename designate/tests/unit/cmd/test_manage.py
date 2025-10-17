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
import sys
from unittest import mock

from oslo_config import fixture as cfg_fixture
import oslotest.base

from designate.cmd import manage
import designate.conf
from designate.manage import base


CONF = designate.conf.CONF


class ManageTestCase(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

    @mock.patch('oslo_config.cfg.ConfigOpts.__call__')
    @mock.patch('oslo_config.cfg.ConfigOpts.register_cli_opt')
    @mock.patch('oslo_log.log.setup')
    def test_main(self, mock_log_setup, mock_register_cli_opt,
                  mock_config_opts_call):
        script_name = 'designate-manage'
        sys.argv = [script_name, 'database', 'foo']
        action_fn = mock.MagicMock()
        CONF.category = mock.Mock(action_fn=action_fn)

        self.assertIsNone(manage.main())

        mock_register_cli_opt.assert_called()
        mock_log_setup.assert_called_with(mock.ANY, 'designate')
        mock_config_opts_call.assert_called()
        self.assertTrue(action_fn.called)

    @mock.patch('oslo_config.cfg.ConfigOpts.__call__')
    @mock.patch('oslo_config.cfg.ConfigOpts.register_cli_opt')
    @mock.patch('oslo_log.log.setup')
    def test_main_error(self, mock_log_setup, mock_register_cli_opt,
                        mock_config_opts_call):
        script_name = 'designate-manage'
        sys.argv = [script_name, 'database', 'foo']
        action_fn = mock.MagicMock()
        CONF.category = mock.Mock(action_fn=action_fn)
        action_fn.side_effect = Exception()

        self.assertEqual(255, manage.main())

        mock_register_cli_opt.assert_called()
        mock_log_setup.assert_called_with(mock.ANY, 'designate')
        mock_config_opts_call.assert_called()
        self.assertTrue(action_fn.called)

    def test_get_arg_string(self):
        self.assertEqual('bar', manage.get_arg_string('bar'))
        self.assertEqual('bar', manage.get_arg_string('-bar'))
        self.assertEqual('bar', manage.get_arg_string('--bar'))

    def test_methods_of(self):
        class foo:
            foo = 'bar'

            def public(self):
                pass

            def _private(self):
                pass

        methods = manage.methods_of(foo())

        method_names = [method_name for method_name, method in methods]
        self.assertIn('public', method_names)
        self.assertNotIn('_private', method_names)
        self.assertNotIn('foo', method_names)

    def test_get_available_commands(self):
        available_commands = manage.get_available_commands()

        self.assertIn('database', available_commands)
        self.assertIn('pool', available_commands)
        self.assertIn('tlds', available_commands)

    def test_fetch_func_args(self):
        expected = {
            'pool_id': mock.sentinel.pool_id,
            'current': mock.sentinel.current
        }

        CONF.category = mock.Mock(**expected)

        @base.args('--pool_id')
        @base.args('current')
        def foo():
            pass

        self.assertIn(mock.sentinel.pool_id, manage.fetch_func_args(foo))
        self.assertIn(mock.sentinel.current, manage.fetch_func_args(foo))

    def test_add_command_parsers(self):
        mock_parser = mock.Mock()
        mock_subparsers = mock.Mock()
        mock_subparsers.add_parser.return_value = mock_parser

        manage.add_command_parsers(mock_subparsers)

        mock_subparsers.add_parser.assert_any_call('database')
        mock_subparsers.add_parser.assert_any_call('pool')
        mock_subparsers.add_parser.assert_any_call('tlds')
