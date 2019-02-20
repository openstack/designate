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


"""Unit-test MiniDNS service
"""
from oslotest import base
import mock

import designate.rpc
import designate.mdns.service as mdns
import designate.storage.base as storage


class MdnsServiceTest(base.BaseTestCase):
    @mock.patch.object(mdns.service.DNSService, '_start')
    @mock.patch.object(designate.rpc, 'get_server')
    def test_service_start(self, mock_service_start, mock_rpc_server):
        self.mdns = mdns.Service()
        self.mdns.start()

        self.assertTrue(mock_service_start.called)
        self.assertTrue(mock_rpc_server.called)

    def test_service_name(self):
        self.mdns = mdns.Service()

        self.assertEqual('mdns', self.mdns.service_name)

    def test_rpc_endpoints(self):
        self.mdns = mdns.Service()

        endpoints = self.mdns._rpc_endpoints

        self.assertIsInstance(endpoints[0], mdns.notify.NotifyEndpoint)
        self.assertIsInstance(endpoints[1], mdns.xfr.XfrEndpoint)

    @mock.patch.object(storage.Storage, 'get_driver')
    def test_storage_driver(self, mock_get_driver):
        mock_driver = mock.MagicMock()
        mock_driver.name = 'noop_driver'
        mock_get_driver.return_value = mock_driver

        self.mdns = mdns.Service()

        self.assertIsInstance(self.mdns.storage, mock.MagicMock)

        self.assertTrue(mock_get_driver.called)

    @mock.patch.object(mdns.handler, 'RequestHandler', name='reqh')
    @mock.patch.object(mdns.service.DNSService, '_start')
    @mock.patch.object(mdns.utils, 'cache_result')
    @mock.patch.object(storage.Storage, 'get_driver')
    def test_dns_application(self, mock_req_handler, mock_cache_result,
                             mock_service_start, mock_get_driver):
        mock_driver = mock.MagicMock()
        mock_driver.name = 'noop_driver'
        mock_get_driver.return_value = mock_driver

        self.mdns = mdns.Service()

        app = self.mdns._dns_application

        self.assertIsInstance(app, mdns.dnsutils.DNSMiddleware)
