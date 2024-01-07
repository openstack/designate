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
import designate.rpc
from designate.sink import service
from designate.tests import base_fixtures


CONF = designate.conf.CONF


class TestSinkService(oslotest.base.BaseTestCase):
    @mock.patch('designate.policy.init', mock.Mock())
    def setUp(self):
        super().setUp()
        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(self.stdlog)
        self.useFixture(cfg_fixture.Config(CONF))

        CONF.set_override(
            'enabled_notification_handlers', ['fake'], 'service:sink'
        )

        self.service = service.Service()

    @mock.patch.object(designate.rpc, 'get_notification_listener')
    def test_service_start(self, mock_notification_listener):
        self.service.start()

        self.assertTrue(mock_notification_listener.called)

    def test_service_stop(self):
        self.service.stop()

        self.assertIn('Stopping sink service', self.stdlog.logger.output)

    def test_service_name(self):
        self.assertEqual('sink', self.service.service_name)
