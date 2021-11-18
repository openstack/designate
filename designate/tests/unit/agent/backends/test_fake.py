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
from designate.backend.agent_backend import impl_fake
import designate.tests
from designate.tests.unit.agent import backends


class FakeAgentBackendTestCase(designate.tests.TestCase):
    def setUp(self):
        super(FakeAgentBackendTestCase, self).setUp()

        self.CONF.set_override('listen', ['0.0.0.0:0'], 'service:agent')

        self.backend = impl_fake.FakeBackend('foo')

    def test_start_backend(self):
        self.backend.start()

    def test_stop_backend(self):
        self.backend.stop()

    def test_find_zone_serial(self):
        self.backend.find_zone_serial('example.org.')

    def test_create_zone(self):
        zone = backends.create_dnspy_zone('example.org')
        self.backend.create_zone(zone)

    def test_update_zone(self):
        zone = backends.create_dnspy_zone('example.org')
        self.backend.update_zone(zone)

    def test_delete_zone(self):
        self.backend.delete_zone('example.org.')
