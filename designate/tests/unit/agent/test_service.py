# Copyright 2014 Rackspace Inc.
#
# Author: Tim Simmons <tim.simmons@rackspace.com>
#
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

from designate.agent import service
from designate.backend import agent_backend
from designate.backend.agent_backend import impl_fake
from designate import dnsmiddleware
import designate.tests
from designate.tests import fixtures
from designate import utils


class AgentServiceTest(designate.tests.TestCase):
    def setUp(self):
        super(AgentServiceTest, self).setUp()
        self.stdlog = fixtures.StandardLogging()
        self.useFixture(self.stdlog)

        self.CONF.set_override('listen', ['0.0.0.0:0'], 'service:agent')
        self.CONF.set_override('notify_delay', 0, 'service:agent')

        self.service = service.Service()
        self.service.dns_service._start = mock.Mock()

    def test_service_start(self):
        self.service.start()

        self.assertTrue(self.service.dns_service._start.called)

    def test_service_stop(self):
        self.service.dns_service.stop = mock.Mock()
        self.service.backend.stop = mock.Mock()

        self.service.stop()

        self.assertTrue(self.service.dns_service.stop.called)
        self.assertTrue(self.service.backend.stop.called)

        self.assertIn('Stopping agent service', self.stdlog.logger.output)

    def test_service_name(self):
        self.assertEqual('agent', self.service.service_name)

    def test_get_backend(self):
        backend = agent_backend.get_backend('fake', agent_service=self.service)
        self.assertIsInstance(backend, impl_fake.FakeBackend)

    @mock.patch.object(utils, 'cache_result')
    def test_get_dns_application(self, mock_cache_result):
        self.assertIsInstance(
            self.service.dns_application,
            dnsmiddleware.SerializationMiddleware
        )

    @mock.patch.object(utils, 'cache_result')
    def test_get_dns_application_with_notify_delay(self, mock_cache_result):
        self.service = service.Service()

        self.CONF.set_override('notify_delay', 1.0, 'service:agent')

        self.assertIsInstance(
            self.service.dns_application,
            dnsmiddleware.SerializationMiddleware
        )
