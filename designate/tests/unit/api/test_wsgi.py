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


from oslo_config import fixture as cfg_fixture
import oslotest.base
from unittest import mock

from designate.api import wsgi
import designate.conf


CONF = designate.conf.CONF


class TestApiWsgi(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

    @mock.patch('paste.deploy.loadapp')
    @mock.patch('designate.heartbeat_emitter.get_heartbeat_emitter')
    @mock.patch('designate.common.profiler.setup_profiler')
    @mock.patch('designate.rpc.init')
    @mock.patch('designate.rpc.initialized')
    @mock.patch('designate.policy.init')
    @mock.patch('oslo_log.log.setup')
    @mock.patch('oslo_config.cfg.CONF')
    def test_init_application(self, mock_cfg, mock_log_setup, mock_policy_init,
                              mock_rpc_initialized,
                              mock_rpc_init,
                              mock_setup_profiler,
                              mock_get_heartbeat_emitter,
                              mock_loadapp):
        CONF.set_override('host', 'foo')
        mock_rpc_initialized.return_value = False

        wsgi.init_application()

        mock_cfg.assert_called_with(
            [], project='designate',
            default_config_files=['/etc/designate/api-paste.ini',
                                  '/etc/designate/designate.conf']
        )
        mock_log_setup.assert_called_with(mock.ANY, 'designate')
        mock_policy_init.assert_called()
        mock_rpc_init.assert_called()
        mock_setup_profiler.assert_called_with('designate-api', 'foo')
        mock_get_heartbeat_emitter.assert_called_with('api')
        mock_loadapp.assert_called_with(
            'config:/etc/designate/api-paste.ini', name='osapi_dns'
        )

    def test_get_config_files(self):
        self.assertEqual(
            ['/etc/designate/api-paste.ini', '/etc/designate/designate.conf'],
            wsgi._get_config_files()
        )

    def test_get_config_files_with_custom_env(self):
        env = {'OS_DESIGNATE_CONFIG_DIR': '/opt/designate'}

        self.assertEqual(
            ['/opt/designate/api-paste.ini', '/opt/designate/designate.conf'],
            wsgi._get_config_files(env)
        )
