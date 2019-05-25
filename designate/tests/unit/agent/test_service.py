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
import mock

import designate.tests
from designate import dnsutils
from designate import utils
from designate.agent import service
from designate.backend import agent_backend
from designate.backend.agent_backend import impl_fake


class AgentServiceTest(designate.tests.TestCase):
    def setUp(self):
        super(AgentServiceTest, self).setUp()

        self.CONF.set_override('port', 0, 'service:agent')
        self.CONF.set_override('notify_delay', 0, 'service:agent')

        self.service = service.Service()
        self.service._start = mock.Mock()
        self.service._rpc_server = mock.Mock()

    def test_service_name(self):
        self.assertEqual('agent', self.service.service_name)

    def test_start(self):
        self.service.start()

        self.assertTrue(self.service._start.called)

    def test_stop(self):
        self.service.stop()

    def test_get_backend(self):
        backend = agent_backend.get_backend('fake', agent_service=self.service)
        self.assertIsInstance(backend, impl_fake.FakeBackend)

    @mock.patch.object(utils, 'cache_result')
    def test_get_dns_application(self, mock_cache_result):
        self.assertIsInstance(
            self.service._dns_application, dnsutils.SerializationMiddleware
        )

    @mock.patch.object(utils, 'cache_result')
    def test_get_dns_application_with_notify_delay(self, mock_cache_result):
        self.service = service.Service()
        self.service._start = mock.Mock()
        self.service._rpc_server = mock.Mock()

        self.CONF.set_override('notify_delay', 1.0, 'service:agent')

        self.assertIsInstance(
            self.service._dns_application, dnsutils.SerializationMiddleware
        )
