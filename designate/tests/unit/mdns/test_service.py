# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Federico Ceratto <federico.ceratto@hpe.com>
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

import oslotest.base

import designate.conf
from designate import dnsmiddleware
from designate.mdns import service
from designate import policy
from designate import rpc
import designate.service
from designate import storage
from designate.tests import base_fixtures
import designate.utils


CONF = designate.conf.CONF


class MdnsServiceTest(oslotest.base.BaseTestCase):
    @mock.patch.object(storage, 'get_storage', mock.Mock())
    @mock.patch.object(policy, 'init')
    @mock.patch.object(rpc, 'init')
    @mock.patch.object(rpc, 'initialized')
    def setUp(self, mock_rpc_initialized, mock_rpc_init, mock_policy_init):
        super().setUp()
        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(self.stdlog)

        mock_rpc_initialized.return_value = False

        self.service = service.Service()

        mock_policy_init.assert_called_once()
        mock_rpc_initialized.assert_called_once()
        mock_rpc_init.assert_called_once()

    @mock.patch.object(designate.service.DNSService, 'start')
    def test_service_start(self, mock_dns_start):
        self.service.start()

        mock_dns_start.assert_called()

    def test_service_stop(self):
        self.service.dns_service.stop = mock.Mock()

        self.service.stop()

        self.service.dns_service.stop.assert_called()

        self.assertIn('Stopping mdns service', self.stdlog.logger.output)

    def test_service_name(self):
        self.assertEqual('mdns', self.service.service_name)

    def test_dns_application(self):
        app = self.service.dns_application
        self.assertIsInstance(app, dnsmiddleware.DNSMiddleware)
