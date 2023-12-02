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

import dns.message

import designate.conf
from designate import dnsmiddleware
from designate import exceptions
import oslotest.base

CONF = designate.conf.CONF


@mock.patch('designate.context.DesignateContext.get_admin_context',
            mock.Mock())
class TestSerializationMiddleware(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.message = dns.message.Message()
        self.application = mock.Mock()
        self.application.return_value = [None, self.message]
        self.dns_middleware = dnsmiddleware.SerializationMiddleware(
            self.application
        )

    @mock.patch.object(dns.message, 'from_wire')
    def test_unknown_tsig_key(self, mock_from_wire):
        mock_from_wire.side_effect = dns.message.UnknownTSIGKey()
        next(self.dns_middleware(
            {'payload': 'payload', 'addr': ['192.0.2.1', 5353]})
        )

    @mock.patch.object(dns.message, 'from_wire')
    def test_bad_signature(self, mock_from_wire):
        mock_from_wire.side_effect = dns.tsig.BadSignature()
        next(self.dns_middleware(
            {'payload': 'payload', 'addr': ['192.0.2.1', 5353]})
        )

    @mock.patch.object(dns.message, 'from_wire')
    def test_dns_exception(self, mock_from_wire):
        mock_from_wire.side_effect = dns.exception.DNSException()
        next(self.dns_middleware(
            {'payload': 'payload', 'addr': ['192.0.2.1', 5353]})
        )

    @mock.patch.object(dns.message, 'from_wire')
    def test_general_exception(self, mock_from_wire):
        mock_from_wire.side_effect = Exception()
        next(self.dns_middleware(
            {'payload': 'payload', 'addr': ['192.0.2.1', 5353]})
        )

    @mock.patch.object(dns.message, 'from_wire', mock.Mock())
    def test_message_to_wire(self):
        self.assertEqual(
            self.message.to_wire(max_size=65535),
            next(self.dns_middleware(
                {'payload': 'payload', 'addr': ['192.0.2.1', 5353]})
            ))

    @mock.patch.object(dns.message, 'from_wire', mock.Mock())
    def test_renderer_to_wire(self):
        self.message = dns.renderer.Renderer()
        self.application.return_value = [self.message]

        self.assertEqual(
            self.message.get_wire(),
            next(self.dns_middleware(
                {'payload': 'payload', 'addr': ['192.0.2.1', 5353]})
            ))


@mock.patch('designate.context.get_current', mock.Mock())
class TestTsigInfoMiddleware(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.application = mock.Mock()
        self.storage = mock.Mock()
        self.dns_middleware = dnsmiddleware.TsigInfoMiddleware(
            self.application, self.storage
        )

    def test_process_request(self):
        mock_context = mock.Mock()
        mock_request = mock.Mock()
        mock_request.keyname.to_text.return_value = 'test'
        mock_request.environ = {'context': mock_context}

        self.assertIsNone(self.dns_middleware.process_request(mock_request))

        self.storage.find_tsigkey.assert_called_with(
            mock.ANY, {'name': 'test'}
        )

    def test_process_request_tsig_key_not_found(self):
        mock_context = mock.Mock()
        mock_request = mock.Mock()
        mock_request.environ = {'context': mock_context}

        self.storage.find_tsigkey.side_effect = exceptions.TsigKeyNotFound()
        self.dns_middleware._build_error_response = mock.Mock()

        self.assertEqual(
            self.dns_middleware._build_error_response(),
            self.dns_middleware.process_request(mock_request)
        )


class TestDNSMiddleware(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.application = mock.Mock(name='application')
        self.dns_application = dnsmiddleware.DNSMiddleware(self.application)

    @mock.patch.object(dnsmiddleware.DNSMiddleware, 'process_request')
    def test_call(self, mock_process_request):
        request = mock.Mock()
        self.dns_application(request)

        mock_process_request.assert_called_with(request)

    @mock.patch.object(dnsmiddleware.DNSMiddleware, 'process_response')
    @mock.patch.object(dnsmiddleware.DNSMiddleware, 'process_request')
    def test_call_with_none(self, mock_process_request, mock_process_response):
        mock_process_request.return_value = None

        self.dns_application(None)

        mock_process_request.assert_called_with(None)
        mock_process_response.assert_called_with(self.application())

    def test_process_request(self):
        self.assertIsNone(self.dns_application.process_request(mock.Mock()))

    def test_process_response(self):
        response = mock.Mock()
        self.assertEqual(
            response, self.dns_application.process_response(response)
        )

    def test_build_error_response(self):
        self.assertIsInstance(
            self.dns_application._build_error_response(), dns.message.Message
        )
