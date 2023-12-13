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
import oslotest.base

import designate.conf
from designate import context
from designate.network_api import fake
from designate.network_api import get_network_api


CONF = designate.conf.CONF


class FakeNetworkAPITest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

        self.api = get_network_api('fake')
        self.context = context.DesignateContext(
            user_id='12345', project_id='54321',
        )
        self.addCleanup(fake.reset_floatingips)

    def test_list_floatingips(self):
        fake.allocate_floatingip(self.context.project_id)
        fake.allocate_floatingip('12345')

        self.assertEqual(1, len(self.api.list_floatingips(self.context)))

    def test_list_floatingips_is_admin(self):
        fake.allocate_floatingip(self.context.project_id)
        fake.allocate_floatingip('12345')
        self.context.is_admin = True

        self.assertEqual(2, len(self.api.list_floatingips(self.context)))

    def test_allocate_floatingip(self):
        fip = fake.allocate_floatingip(self.context.project_id)

        self.assertIn('192.0.2', fip['address'])
        self.assertEqual('RegionOne', fip['region'])
        self.assertIn('id', fip)

    def test_deallocate_floatingip(self):
        fip = fake.allocate_floatingip(self.context.project_id)

        self.assertIn('192.0.2', fip['address'])
        self.assertEqual('RegionOne', fip['region'])
        self.assertIn('id', fip)

        self.assertIsNone(fake.deallocate_floatingip(self.context.project_id))
