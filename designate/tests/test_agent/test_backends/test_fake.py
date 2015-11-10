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
import dns.zone

from designate.agent import service
from designate.backend import agent_backend
from designate.tests import TestCase
from designate.tests.test_agent.test_backends import BackendTestMixin


class FakeAgentBackendTestCase(TestCase, BackendTestMixin):

    def setUp(self):
        super(FakeAgentBackendTestCase, self).setUp()
        # Use a random port
        self.config(port=0, group='service:agent')
        self.backend = agent_backend.get_backend('fake',
                agent_service=service.Service())
        self.backend.start()

    def tearDown(self):
        super(FakeAgentBackendTestCase, self).tearDown()
        self.backend.agent_service.stop()
        self.backend.stop()

    def test_find_zone_serial(self):
        self.backend.find_zone_serial('example.org.')

    def test_create_zone(self):
        zone = self._create_dnspy_zone('example.org')
        self.backend.create_zone(zone)

    def test_update_zone(self):
        zone = self._create_dnspy_zone('example.org')
        self.backend.update_zone(zone)

    def test_delete_zone(self):
        self.backend.delete_zone('example.org.')

    # Helper
    def _create_dnspy_zone(self, name):
        zone_text = ('$ORIGIN %(name)s\n%(name)s 3600 IN SOA %(ns)s '
        'email.email.com. 1421777854 3600 600 86400 3600\n%(name)s 3600 IN NS '
        '%(ns)s\n') % {'name': name, 'ns': 'ns1.designate.com'}

        return dns.zone.from_text(zone_text, check_origin=False)
