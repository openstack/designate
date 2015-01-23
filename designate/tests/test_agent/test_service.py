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
from designate.tests.test_agent import AgentTestCase


class AgentServiceTest(AgentTestCase):
    def setUp(self):
        super(AgentServiceTest, self).setUp()

        # Use a random port
        self.config(port=0, group='service:agent')

        self.service = self.start_service('agent')

    def test_stop(self):
        # NOTE: Start is already done by the fixture in start_service()
        self.service.stop()
