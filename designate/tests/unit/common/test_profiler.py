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


from unittest import mock

from oslo_config import fixture as cfg_fixture
import oslotest.base

from designate.common import profiler
import designate.conf

CONF = designate.conf.CONF


class WsgiMiddlewareTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()

    @mock.patch.object(profiler, 'profiler_web')
    def test_factory_with_profiler_web(self, mock_profiler_web):
        mock_conf = mock.Mock()

        profiler.WsgiMiddleware.factory(mock_conf)

        mock_profiler_web.WsgiMiddleware.factory.assert_called_with(mock_conf)

    @mock.patch.object(profiler, 'profiler_web', None)
    def test_factory_without_profiler_web(self):
        mock_conf = mock.Mock()
        self.assertIsInstance(
            profiler.WsgiMiddleware.factory(mock_conf)('app'),
            profiler.WsgiMiddleware
        )

    def test_factory_call(self):
        mock_request = mock.Mock()

        profiler.WsgiMiddleware('app')(mock_request)

        mock_request.get_response.assert_called_with('app')


class ProfilerTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

    @mock.patch.object(profiler, 'profiler', mock.Mock())
    @mock.patch.object(profiler, 'profiler_opts', mock.Mock())
    @mock.patch.object(profiler, 'profiler_initializer')
    def test_setup_profiler(self, mock_profiler_initializer):
        CONF.set_override('enabled', True, group='profiler')

        profiler.setup_profiler('binary', 'host')

        mock_profiler_initializer.init_from_conf.assert_called_with(
            conf=mock.ANY,
            context=mock.ANY,
            project='designate',
            service='binary',
            host='host'
        )

    @mock.patch.object(profiler, 'profiler', mock.Mock())
    @mock.patch.object(profiler, 'profiler_opts', mock.Mock())
    @mock.patch.object(profiler, 'profiler_initializer')
    def test_setup_profiler_not_enabled(self, mock_profiler_initializer):
        CONF.set_override('enabled', False, group='profiler')

        profiler.setup_profiler('binary', 'host')

        mock_profiler_initializer.init_from_conf.assert_not_called()

    @mock.patch.object(profiler, 'profiler', mock.Mock())
    @mock.patch.object(profiler, 'profiler_opts', None)
    @mock.patch.object(profiler, 'profiler_initializer')
    def test_setup_profiler_missing_dep(self, mock_profiler_initializer):
        CONF.set_override('enabled', True, group='profiler')

        profiler.setup_profiler('binary', 'host')

        mock_profiler_initializer.init_from_conf.assert_not_called()

    @mock.patch.object(profiler, 'profiler')
    def test_trace_cls(self, mock_profiler):
        CONF.set_override('enabled', True, group='profiler')

        @profiler.trace_cls('name', foo='bar')
        class Test:
            pass

        Test()

        mock_profiler.trace_cls.assert_called_with(
            'name', {'foo': 'bar'}
        )
