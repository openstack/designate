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

import designate.conf
from designate.notification_handler import fake
from designate import policy
from designate import rpc
from designate.sink import service
from designate.tests import base_fixtures


CONF = designate.conf.CONF


class TestSinkNotification(oslotest.base.BaseTestCase):

    @mock.patch.object(policy, 'init')
    @mock.patch.object(rpc, 'get_client')
    @mock.patch.object(rpc, 'init')
    @mock.patch.object(rpc, 'initialized')
    def setUp(self, mock_rpc_initialized, mock_rpc_init, mock_rpc_get_client,
              mock_policy_init):
        super().setUp()

        mock_rpc_initialized.return_value = False

        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(cfg_fixture.Config(CONF))
        self.useFixture(self.stdlog)

        CONF.set_override(
            'enabled_notification_handlers',
            [fake.FakeHandler.__plugin_name__],
            'service:sink'
        )
        CONF.set_override(
            'allowed_event_types', ['compute.instance.create.end'],
            'handler:fake'
        )

        self.context = mock.Mock()
        self.service = service.Service()

        mock_policy_init.assert_called_once()
        mock_rpc_initialized.assert_called_once()
        mock_rpc_init.assert_called_once()

    def test_notification(self):
        event_type = 'compute.instance.create.end'
        fixture = base_fixtures.get_notification_fixture('nova', event_type)

        self.service.info(self.context, None, event_type,
                          fixture['payload'], None)

        self.assertIn(
            'handler:fake: received notification - %s' % event_type,
            self.stdlog.logger.output
        )

    def test_notification_with_unknown_event(self):
        event_type = 'compute.instance.create.start'
        fixture = base_fixtures.get_notification_fixture('nova', event_type)

        self.service.info(self.context, None, event_type,
                          fixture['payload'], None)

        self.assertNotIn(
            'handler:fake: received notification - %s' % event_type,
            self.stdlog.logger.output
        )

    @mock.patch.object(policy, 'init', mock.Mock())
    @mock.patch.object(rpc, 'get_client', mock.Mock())
    @mock.patch.object(rpc, 'init', mock.Mock())
    @mock.patch.object(rpc, 'initialized', mock.Mock(return_value=False))
    def test_notification_without_handler(self):
        CONF.set_override('enabled_notification_handlers', [], 'service:sink')

        self.service = service.Service()

        event_type = 'compute.instance.create.end'
        fixture = base_fixtures.get_notification_fixture('nova', event_type)

        self.service.info(self.context, None, event_type,
                          fixture['payload'], None)

        self.assertIn(
            'No designate-sink handlers enabled or loaded',
            self.stdlog.logger.output
        )
