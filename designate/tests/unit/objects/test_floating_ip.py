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


from oslo_config import fixture as cfg_fixture
from oslo_log import log as logging
import oslotest.base

import designate.conf
from designate import objects


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class FloatingIpTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

    def test_allow_floating_ip_ttl_zero(self):
        floating_ip = objects.FloatingIP(
            ptrdname='ptr1.example.org.',
            description='test',
            address='192.0.2.50',
            ttl=0,
        )
        floating_ip.validate()

        self.assertEqual('ptr1.example.org.', floating_ip.ptrdname)
        self.assertEqual('test', floating_ip.description)
        self.assertEqual('192.0.2.50', floating_ip.address)
        self.assertEqual(0, floating_ip.ttl)
