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
import mock
import oslotest.base
from oslo_config import cfg
from oslo_config import fixture as cfg_fixture

import designate.dnsutils
import designate.rpc
import designate.service
import designate.storage.base
import designate.utils
from designate.mdns import handler
from designate.mdns import service

CONF = cfg.CONF


class MdnsServiceTest(oslotest.base.BaseTestCase):
    @mock.patch.object(designate.rpc, 'get_server')
    def setUp(self, mock_rpc_server):
        super(MdnsServiceTest, self).setUp()
        self.useFixture(cfg_fixture.Config(CONF))

        self.service = service.Service()

    @mock.patch.object(designate.service.DNSService, '_start')
    def test_service_start(self, mock_service_start):
        self.service.start()

        self.assertTrue(mock_service_start.called)

    def test_service_name(self):
        self.assertEqual('mdns', self.service.service_name)

    def test_mdns_rpc_topic(self):
        CONF.set_override('topic', 'test-topic', 'service:mdns')

        self.service = service.Service()

        self.assertEqual('test-topic', self.service._rpc_topic)
        self.assertEqual('mdns', self.service.service_name)

    def test_rpc_endpoints(self):
        endpoints = self.service._rpc_endpoints

        self.assertIsInstance(endpoints[0], service.notify.NotifyEndpoint)
        self.assertIsInstance(endpoints[1], service.xfr.XfrEndpoint)

    @mock.patch.object(designate.storage.base.Storage, 'get_driver')
    def test_storage_driver(self, mock_get_driver):
        mock_driver = mock.MagicMock()
        mock_driver.name = 'noop_driver'
        mock_get_driver.return_value = mock_driver

        self.assertIsInstance(self.service.storage, mock.MagicMock)

        self.assertTrue(mock_get_driver.called)

    @mock.patch.object(handler, 'RequestHandler', name='reqh')
    @mock.patch.object(designate.service.DNSService, '_start')
    @mock.patch.object(designate.utils, 'cache_result')
    @mock.patch.object(designate.storage.base.Storage, 'get_driver')
    def test_dns_application(self, mock_req_handler, mock_cache_result,
                             mock_service_start, mock_get_driver):
        mock_driver = mock.MagicMock()
        mock_driver.name = 'noop_driver'
        mock_get_driver.return_value = mock_driver

        app = self.service._dns_application

        self.assertIsInstance(app, designate.dnsutils.DNSMiddleware)
