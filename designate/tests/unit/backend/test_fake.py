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

import oslotest.base

from designate.backend import impl_fake
from designate import context
from designate import objects
from designate.tests import base_fixtures


class FakeBackendTestCase(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(self.stdlog)

        self.admin_context = mock.Mock()
        mock.patch.object(
            context.DesignateContext, 'get_admin_context',
            return_value=self.admin_context).start()

        self.zone = objects.Zone(
            id='cca7908b-dad4-4c50-adba-fb67d4c556e8',
            name='example.test.',
            email='example@example.test'
        )
        self.target = {
            'id': '4588652b-50e7-46b9-b688-a9bad40a873e',
            'type': 'fake',
            'masters': [
                {'host': '192.0.2.1', 'port': 53},
                {'host': '192.0.2.2', 'port': 35}
            ],
            'options': [
            ],
        }

        self.backend = impl_fake.FakeBackend(
            objects.PoolTarget.from_dict(self.target)
        )

    def test_create_zone(self):
        self.backend.create_zone(self.admin_context, self.zone)

        self.assertIn(
            "Create Zone <Zone id:'cca7908b-dad4-4c50-adba-fb67d4c556e8' "
            "type:'None' name:'example.test.' pool_id:'None' serial:'None' "
            "action:'None' status:'None' shard:'None'>",
            self.stdlog.logger.output
        )

    def test_delete_zone(self):
        self.backend.delete_zone(self.admin_context, self.zone)

        self.assertIn(
            "Delete Zone <Zone id:'cca7908b-dad4-4c50-adba-fb67d4c556e8' "
            "type:'None' name:'example.test.' pool_id:'None' serial:'None' "
            "action:'None' status:'None' shard:'None'>",
            self.stdlog.logger.output
        )
