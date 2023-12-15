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
from designate.backend import base
from designate.backend import impl_pdns4
from designate import context
from designate import objects
from designate.tests import base_fixtures


class BaseBackendTestCase(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(self.stdlog)

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

    @mock.patch.object(base.Backend, 'get_driver')
    def test_untested_backend(self, mock_get_driver):
        driver = mock.Mock()
        driver.__backend_status__ = 'untested'
        mock_get_driver.return_value = driver

        self.target['type'] = 'test'
        pool_target = objects.PoolTarget.from_dict(self.target)

        backend.get_backend(pool_target)

        self.assertIn('WARNING', self.stdlog.logger.output)
        self.assertIn(
            "Backend Driver 'test' loaded. Has status of 'untested'",
            self.stdlog.logger.output
        )

    @mock.patch.object(base.Backend, 'get_driver')
    def test_tested_backend(self, mock_get_driver):
        driver = mock.Mock()
        driver.__backend_status__ = 'integrated'
        mock_get_driver.return_value = driver

        self.target['type'] = 'test'
        pool_target = objects.PoolTarget.from_dict(self.target)

        backend.get_backend(pool_target)

        self.assertNotIn('WARNING', self.stdlog.logger.output)
        self.assertIn(
            "Backend Driver 'test' loaded. Has status of 'integrated'",
            self.stdlog.logger.output
        )

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
