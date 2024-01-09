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


CONF = designate.conf.CONF


class TestFakeHandler(oslotest.base.BaseTestCase):
    @mock.patch('designate.rpc.get_client', mock.Mock())
    def setUp(self):
        super().setUp()

        self.useFixture(cfg_fixture.Config(CONF))

        CONF.set_override(
            'enabled_notification_handlers',
            [fake.FakeHandler.__plugin_name__],
            'service:sink'
        )
        CONF.set_override(
            'allowed_event_types', ['compute.instance.create.end'],
            'handler:fake'
        )

        self.handler = fake.FakeHandler()

    def test_get_name(self):
        self.assertEqual(
            self.handler.name,
            'handler:fake'
        )

    def test_get_canonical_name(self):
        self.assertEqual(
            self.handler.get_canonical_name(),
            'handler:fake'
        )

    def test_get_exchange_topics(self):
        self.assertEqual(
            self.handler.get_exchange_topics(),
            ('fake', ['notifications'])
        )

    def test_get_event_types(self):
        self.assertEqual(
            self.handler.get_event_types(),
            ['compute.instance.create.end']
        )
