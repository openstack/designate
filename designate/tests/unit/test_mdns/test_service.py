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
import unittest

from oslotest import base
import mock

from designate.tests.unit import RoObject
import designate.mdns.service as mdns

# TODO(Federico): fix skipped tests


@mock.patch.object(mdns.utils, 'cache_result')
@mock.patch.object(mdns.notify, 'NotifyEndpoint')
@mock.patch.object(mdns.xfr, 'XfrEndpoint')
class MdnsServiceTest(base.BaseTestCase):

    @mock.patch.object(mdns.storage, 'get_storage', name='get_storage')
    @mock.patch.object(mdns.Service, '_rpc_endpoints')
    def setUp(self, *mocks):
        super(MdnsServiceTest, self).setUp()
        mdns.CONF = RoObject({
            'service:mdns': RoObject(storage_driver=None)
        })
        # _rpc_endpoints is a property
        mock_rpc_endpoints = mocks[0]
        mock_rpc_endpoints.__get__ = mock.Mock(
            return_value=[mock.MagicMock(), mock.MagicMock()]
        )

        self.mdns = mdns.Service()
        self.mdns.tg = mock.Mock(name='tg')

    def test_service_name(self, mc, mn, mx):
        self.assertEqual('mdns', self.mdns.service_name)

    @unittest.skip("Fails when run together with designate/tests/test_mdns/")
    def test_rpc_endpoints(self, _, mock_notify, mock_xfr):
        out = self.mdns._rpc_endpoints
        self.assertEqual(2, len(out))
        assert isinstance(out[0], mock.MagicMock), out
        assert isinstance(out[1], mock.MagicMock), out

    @unittest.skip("Fails when run together with designate/tests/test_mdns/")
    @mock.patch.object(mdns.handler, 'RequestHandler', name='reqh')
    @mock.patch.object(mdns.dnsutils, 'TsigInfoMiddleware', name='tsig')
    @mock.patch.object(mdns.dnsutils, 'SerializationMiddleware')
    def test_dns_application(self, *mocks):
        mock_serialization, mock_tsiginf, mock_req_handler = mocks[:3]
        mock_req_handler.return_value = mock.Mock(name='app')

        app = self.mdns._dns_application

        assert isinstance(app, mock.MagicMock), repr(app)
        assert mock_req_handler.called
        assert mock_tsiginf.called
        assert mock_serialization.called
