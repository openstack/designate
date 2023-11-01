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

import oslotest.base

import designate.conf
from designate.notification_handler import fake
from designate.sink import service
from designate.tests import fixtures
from designate.tests import test_notification_handler


CONF = designate.conf.CONF


class TestSinkNotification(oslotest.base.BaseTestCase,
                           test_notification_handler.NotificationHandlerMixin):

    def setUp(self):
        super().setUp()
        self.stdlog = fixtures.StandardLogging()
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
        CONF([], project='designate')

        self.context = mock.Mock()
        self.service = service.Service()

    def test_notification(self):
        event_type = 'compute.instance.create.end'
        fixture = self.get_notification_fixture('nova', event_type)

        self.service.info(self.context, None, event_type,
                          fixture['payload'], None)

        self.assertIn(
            'handler:fake: received notification - %s' % event_type,
            self.stdlog.logger.output
        )

    def test_notification_with_unknown_event(self):
        event_type = 'compute.instance.create.start'
        fixture = self.get_notification_fixture('nova', event_type)

        self.service.info(self.context, None, event_type,
                          fixture['payload'], None)

        self.assertNotIn(
            'handler:fake: received notification - %s' % event_type,
            self.stdlog.logger.output
        )

    def test_notification_without_handler(self):
        CONF.set_override('enabled_notification_handlers', [], 'service:sink')
        self.service = service.Service()

        event_type = 'compute.instance.create.end'
        fixture = self.get_notification_fixture('nova', event_type)

        self.service.info(self.context, None, event_type,
                          fixture['payload'], None)

        self.assertIn(
            'No designate-sink handlers enabled or loaded',
            self.stdlog.logger.output
        )
