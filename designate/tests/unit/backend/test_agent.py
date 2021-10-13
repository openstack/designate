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

import dns
import dns.query
import dns.rdataclass
import dns.rdatatype

import designate.backend.agent as agent
import designate.backend.private_codes as pcodes
from designate import dnsutils
from designate import exceptions
from designate.mdns import rpcapi as mdns_api
from designate import objects
from designate import tests
from designate.tests.unit import RoObject


class AgentBackendTestCase(tests.TestCase):
    def setUp(self):
        super(AgentBackendTestCase, self).setUp()
        self.CONF.set_override('poll_timeout', 1, 'service:worker')
        self.CONF.set_override('poll_retry_interval', 4,
                               'service:worker')
        self.CONF.set_override('poll_max_retries', 5, 'service:worker')
        self.CONF.set_override('poll_delay', 6, 'service:worker')

        self.context = self.get_context()
        self.zone = objects.Zone(
            id='e2bed4dc-9d01-11e4-89d3-123b93f75cba',
            name='example.com.',
            email='example@example.com',
        )

        self.target = {
            'id': '4588652b-50e7-46b9-b688-a9bad40a873e',
            'type': 'agent',
            'masters': [],
            'options': [
                {'key': 'host', 'value': 2},
                {'key': 'port', 'value': 3},
            ],
        }

        self.backend = agent.AgentPoolBackend(
            objects.PoolTarget.from_dict(self.target)
        )

    @mock.patch.object(mdns_api.MdnsAPI, 'get_instance')
    def test_mdns_api(self, mock_get_instance):
        self.assertIsInstance(self.backend.mdns_api, mock.Mock)

    @mock.patch.object(mdns_api.MdnsAPI, 'get_instance')
    def test_create_zone(self, mock_get_instance):
        self.backend._make_and_send_dns_message = mock.Mock(
            return_value=(1, 2))

        out = self.backend.create_zone(self.context, self.zone)

        self.backend._make_and_send_dns_message.assert_called_with(
            self.zone.name, 1, 14, pcodes.CREATE, pcodes.SUCCESS, 2, 3)
        self.assertIsNone(out)

    @mock.patch.object(mdns_api.MdnsAPI, 'get_instance')
    def test_create_zone_exception(self, mock_get_instance):
        self.backend._make_and_send_dns_message = mock.Mock(
            return_value=(None, 2))

        self.assertRaisesRegex(
            exceptions.Backend, 'create_zone.* failed',
            self.backend.create_zone, self.context, self.zone,
        )

        self.backend._make_and_send_dns_message.assert_called_with(
            self.zone.name, 1, 14, pcodes.CREATE, pcodes.SUCCESS, 2, 3)

    @mock.patch.object(mdns_api.MdnsAPI, 'get_instance')
    def test_update_zone(self, mock_get_instance):
        self.backend.mdns_api.notify_zone_changed = mock.Mock()

        out = self.backend.update_zone(self.context, self.zone)

        self.backend.mdns_api.notify_zone_changed.assert_called_with(
            self.context, self.zone, 2, 3, 1, 4, 5, 6)
        self.assertIsNone(out)

    @mock.patch.object(mdns_api.MdnsAPI, 'get_instance')
    def test_delete_zone(self, mock_get_instance):
        self.backend._make_and_send_dns_message = mock.Mock(
            return_value=(1, 2))

        out = self.backend.delete_zone(self.context, self.zone)

        self.backend._make_and_send_dns_message.assert_called_with(
            self.zone.name, 1, 14, pcodes.DELETE, pcodes.SUCCESS, 2, 3)
        self.assertIsNone(out)

    @mock.patch.object(mdns_api.MdnsAPI, 'get_instance')
    def test_delete_zone_exception(self, mock_get_instance):
        self.backend._make_and_send_dns_message = mock.Mock(
            return_value=(None, 2))

        self.assertRaisesRegex(
            exceptions.Backend, 'failed delete_zone',
            self.backend.delete_zone, self.context, self.zone,
        )

        self.backend._make_and_send_dns_message.assert_called_with(
            self.zone.name, 1, 14, pcodes.DELETE, pcodes.SUCCESS, 2, 3)

    def test_make_and_send_dns_message_timeout(self):
        self.backend._make_dns_message = mock.Mock(return_value='')
        self.backend._send_dns_message = mock.Mock(
            return_value=dns.exception.Timeout())

        out = self.backend._make_and_send_dns_message('h', 123, 1, 2, 3, 4, 5)

        self.assertEqual((None, 0), out)

    def test_make_and_send_dns_message_bad_response(self):
        self.backend._make_dns_message = mock.Mock(return_value='')
        self.backend._send_dns_message = mock.Mock(
            return_value=dns.query.BadResponse())

        out = self.backend._make_and_send_dns_message('h', 123, 1, 2, 3, 4, 5)

        self.assertEqual((None, 0), out)

    def test_make_and_send_dns_message_missing_AA_flags(self):
        self.backend._make_dns_message = mock.Mock(return_value='')
        response = RoObject(
            rcode=mock.Mock(return_value=dns.rcode.NOERROR),
            # rcode is NOERROR but (flags & dns.flags.AA) gives 0
            flags=0,
        )
        self.backend._send_dns_message = mock.Mock(return_value=response)

        out = self.backend._make_and_send_dns_message('h', 123, 1, 2, 3, 4, 5)

        self.assertEqual((None, 0), out)

    def test_make_and_send_dns_message_error_flags(self):
        self.backend._make_dns_message = mock.Mock(return_value='')
        response = RoObject(
            rcode=mock.Mock(return_value=dns.rcode.NOERROR),
            # rcode is NOERROR but flags are not NOERROR
            flags=123,
            ednsflags=321
        )
        self.backend._send_dns_message = mock.Mock(return_value=response)

        out = self.backend._make_and_send_dns_message('h', 123, 1, 2, 3, 4, 5)

        self.assertEqual((None, 0), out)

    def test_make_and_send_dns_message(self):
        self.backend._make_dns_message = mock.Mock(return_value='')
        response = RoObject(
            rcode=mock.Mock(return_value=dns.rcode.NOERROR),
            flags=agent.dns.flags.AA,
            ednsflags=321
        )
        self.backend._send_dns_message = mock.Mock(return_value=response)

        out = self.backend._make_and_send_dns_message('h', 123, 1, 2, 3, 4, 5)

        self.assertEqual((response, 0), out)

    @mock.patch.object(dnsutils, 'get_ip_address')
    @mock.patch.object(dns.query, 'tcp')
    @mock.patch.object(dns.query, 'udp')
    def test_send_dns_message(self, mock_udp, mock_tcp, mock_get_ip_address):
        mock_udp.return_value = 'mock udp resp'
        mock_get_ip_address.return_value = '10.0.1.39'

        out = self.backend._send_dns_message('msg', '10.0.1.39', 123, 1)

        self.assertFalse(mock_tcp.called)
        mock_udp.assert_called_with('msg', '10.0.1.39', port=123,
                                    timeout=1)
        self.assertEqual('mock udp resp', out)
