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
import stevedore.exception

from designate import backend
from designate.backend import impl_pdns4
from designate import context
from designate import objects


class BaseBackendTestCase(oslotest.base.BaseTestCase):
    def setUp(self):
        super(BaseBackendTestCase, self).setUp()

        self.context = mock.Mock()
        self.admin_context = mock.Mock()
        mock.patch.object(
            context.DesignateContext, 'get_admin_context',
            return_value=self.admin_context).start()

        self.target = {
            'type': 'pdns4',
            'masters': [
            ],
            'options': [
            ],
        }

    def test_get_backend(self):
        pool_target = objects.PoolTarget.from_dict(self.target)
        self.assertIsInstance(
            backend.get_backend(pool_target),
            impl_pdns4.PDNS4Backend
        )

    def test_get_backend_does_not_exist(self):
        self.target['type'] = 'unknown'
        pool_target = objects.PoolTarget.from_dict(self.target)
        self.assertRaises(
            stevedore.exception.NoMatches,
            backend.get_backend, pool_target
        )
