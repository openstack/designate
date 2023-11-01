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
import oslotest.base


CONF = designate.conf.CONF


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
