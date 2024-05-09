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
# under the License.mport threading


from unittest import mock

from oslo_config import fixture as cfg_fixture
import oslotest.base

from designate.common import profiler
import designate.conf
from designate import policy
from designate import rpc
from designate.sink import service
from designate.tests import base_fixtures


CONF = designate.conf.CONF


class TestSinkService(oslotest.base.BaseTestCase):
    @mock.patch.object(policy, 'init')
    @mock.patch.object(rpc, 'get_client')
    @mock.patch.object(profiler, 'setup_profiler')
    def setUp(self, mock_setup_profiler, mock_get_client, mock_policy_init):
        super().setUp()
        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(self.stdlog)
        self.useFixture(cfg_fixture.Config(CONF))

        CONF.set_override(
            'enabled_notification_handlers', ['fake'], 'service:sink'
        )
        CONF.set_override(
            'allowed_event_types', ['compute.instance.create.end'],
            'handler:fake'
        )

        self.service = service.Service()

        self.context = mock.Mock()

        mock_setup_profiler.assert_called()
        mock_get_client.assert_called()
        mock_policy_init.assert_called()

    @mock.patch.object(rpc, 'get_notification_listener')
    def test_service_start(self, mock_notification_listener):
        self.service.start()

        mock_notification_listener.assert_called()

    @mock.patch.object(policy, 'init', mock.Mock())
    @mock.patch.object(rpc, 'get_client', mock.Mock())
    @mock.patch.object(profiler, 'setup_profiler', mock.Mock())
    @mock.patch.object(designate.rpc, 'get_notification_listener')
    def test_service_start_no_targets(self, mock_notification_listener):
        CONF.set_override(
            'enabled_notification_handlers', [], 'service:sink'
        )

        sink_service = service.Service()

        sink_service.start()

        mock_notification_listener.assert_not_called()

    def test_service_stop(self):
        self.service._notification_listener = None

        self.service.stop()

        self.assertIn('Stopping sink service', self.stdlog.logger.output)
        self.assertIsNone(self.service._notification_listener)

    def test_service_stop_and_notification_listener_stopped(self):
        self.service._notification_listener = mock.Mock()

        self.service.stop()

        self.assertIn('Stopping sink service', self.stdlog.logger.output)
        self.service._notification_listener.stop.assert_called_with()

    def test_service_name(self):
        self.assertEqual('sink', self.service.service_name)

    def test_get_allowed_event_types(self):
        self.assertEqual(
            ['compute.instance.create.end'],
            self.service.get_allowed_event_types(self.service.handlers)
        )

    def test_get_allowed_event_types_with_duplicates(self):
        mock_handler1 = mock.Mock()
        mock_handler2 = mock.Mock()

        mock_handler1.get_event_types.return_value = [
            'compute.instance.create.start'
        ]
        mock_handler2.get_event_types.return_value = [
            'compute.instance.create.end',
            'compute.instance.create.start'
        ]

        handlers = [mock_handler1, mock_handler2]

        self.assertEqual(
            ['compute.instance.create.start', 'compute.instance.create.end'],
            self.service.get_allowed_event_types(handlers)
        )

    def test_service_info(self):
        events = [
            'compute.instance.create.end',
            'compute.instance.create.start'
        ]
        self.service.allowed_event_types = events

        for event in events:
            self.service.info(
                self.context, 'publisher_id', event, mock.Mock(), mock.Mock()
            )

        self.assertIn(
            'received notification - compute.instance.create.end',
            self.stdlog.logger.output
        )
        self.assertNotIn(
            'received notification - compute.instance.create.start',
            self.stdlog.logger.output
        )
