
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


"""Unit-test backend agent
"""

from mock import MagicMock
from mock import Mock
from mock import patch
from oslotest import base
import dns
import dns.rdataclass
import dns.rdatatype
import mock
import testtools

from designate import exceptions
from designate.tests.unit import RoObject
import designate.backend.agent as agent
import designate.backend.private_codes as pcodes


class SCAgentPoolBackend(agent.AgentPoolBackend):
    def __init__(self):
        pass


@mock.patch.object(agent.mdns_api.MdnsAPI, 'get_instance')
@patch.object(agent.base.Backend, '__init__')
class BackendAgentTest(base.BaseTestCase):

    def setUp(self, *mocks):
        super(BackendAgentTest, self).setUp()
        agent.CONF = RoObject({
            'service:mdns': RoObject(all_tcp=False)
        })
        self.agent = SCAgentPoolBackend()
        self.agent.timeout = 1
        self.agent.host = 2
        self.agent.port = 3
        self.agent.retry_interval = 4
        self.agent.max_retries = 5
        self.agent.delay = 6

    def test_mdns_api(self, *mock):
        assert isinstance(self.agent.mdns_api, MagicMock)

    def test_create_zone(self, *mock):
        self.agent._make_and_send_dns_message = Mock(return_value=(1, 2))

        out = self.agent.create_zone('ctx', RoObject(name='zn'))

        self.agent._make_and_send_dns_message.assert_called_with(
            'zn', 1, 14, pcodes.CREATE, pcodes.SUCCESS, 2, 3)
        self.assertIsNone(out)

    def test_create_zone_exception(self, *mock):
        self.agent._make_and_send_dns_message = Mock(return_value=(None, 2))

        with testtools.ExpectedException(exceptions.Backend):
            self.agent.create_zone('ctx', RoObject(name='zn'))

        self.agent._make_and_send_dns_message.assert_called_with(
            'zn', 1, 14, pcodes.CREATE, pcodes.SUCCESS, 2, 3)

    def test_update_zone(self, *mock):
        self.agent.mdns_api.notify_zone_changed = Mock()
        zone = RoObject(name='zn')

        out = self.agent.update_zone('ctx', zone)

        self.agent.mdns_api.notify_zone_changed.assert_called_with(
            'ctx', zone, 2, 3, 1, 4, 5, 6)
        self.assertIsNone(out)

    def test_delete_zone(self, *mock):
        self.agent._make_and_send_dns_message = Mock(return_value=(1, 2))

        out = self.agent.delete_zone('ctx', RoObject(name='zn'))

        self.agent._make_and_send_dns_message.assert_called_with(
            'zn', 1, 14, pcodes.DELETE, pcodes.SUCCESS, 2, 3)
        self.assertIsNone(out)

    def test_delete_zone_exception(self, *mock):
        self.agent._make_and_send_dns_message = Mock(return_value=(None, 2))

        with testtools.ExpectedException(exceptions.Backend):
            self.agent.delete_zone('ctx', RoObject(name='zn'))

        self.agent._make_and_send_dns_message.assert_called_with(
            'zn', 1, 14, pcodes.DELETE, pcodes.SUCCESS, 2, 3)

    def test_make_and_send_dns_message_timeout(self, *mocks):
        self.agent._make_dns_message = Mock(return_value='')
        self.agent._send_dns_message = Mock(
            return_value=dns.exception.Timeout())

        out = self.agent._make_and_send_dns_message('h', 123, 1, 2, 3, 4, 5)

        self.assertEqual((None, 0), out)

    def test_make_and_send_dns_message_bad_response(self, *mocks):
        self.agent._make_dns_message = Mock(return_value='')
        self.agent._send_dns_message = Mock(
            return_value=agent.dns_query.BadResponse())

        out = self.agent._make_and_send_dns_message('h', 123, 1, 2, 3, 4, 5)

        self.assertEqual((None, 0), out)

    def test_make_and_send_dns_message_missing_AA_flags(self, *mocks):
        self.agent._make_dns_message = Mock(return_value='')
        response = RoObject(
            rcode=Mock(return_value=dns.rcode.NOERROR),
            # rcode is NOERROR but (flags & dns.flags.AA) gives 0
            flags=0,
        )
        self.agent._send_dns_message = Mock(return_value=response)

        out = self.agent._make_and_send_dns_message('h', 123, 1, 2, 3, 4, 5)

        self.assertEqual((None, 0), out)

    def test_make_and_send_dns_message_error_flags(self, *mocks):
        self.agent._make_dns_message = Mock(return_value='')
        response = RoObject(
            rcode=Mock(return_value=dns.rcode.NOERROR),
            # rcode is NOERROR but flags are not NOERROR
            flags=123,
            ednsflags=321
        )
        self.agent._send_dns_message = Mock(return_value=response)

        out = self.agent._make_and_send_dns_message('h', 123, 1, 2, 3, 4, 5)

        self.assertEqual((None, 0), out)

    def test_make_and_send_dns_message(self, *mock):
        self.agent._make_dns_message = Mock(return_value='')
        response = RoObject(
            rcode=Mock(return_value=dns.rcode.NOERROR),
            flags=agent.dns.flags.AA,
            ednsflags=321
        )
        self.agent._send_dns_message = Mock(return_value=response)

        out = self.agent._make_and_send_dns_message('h', 123, 1, 2, 3, 4, 5)

        self.assertEqual((response, 0), out)

    @mock.patch.object(agent.dns_query, 'tcp')
    @mock.patch.object(agent.dns_query, 'udp')
    def test_send_dns_message(self, *mocks):
        mocks[0].return_value = 'mock udp resp'

        out = self.agent._send_dns_message('msg', 'host', 123, 1)

        assert not agent.dns_query.tcp.called
        agent.dns_query.udp.assert_called_with('msg', 'host', port=123,
                                               timeout=1)
        self.assertEqual('mock udp resp', out)

    @mock.patch.object(agent.dns_query, 'tcp')
    @mock.patch.object(agent.dns_query, 'udp')
    def test_send_dns_message_timeout(self, *mocks):
        mocks[0].side_effect = dns.exception.Timeout

        out = self.agent._send_dns_message('msg', 'host', 123, 1)

        agent.dns_query.udp.assert_called_with('msg', 'host', port=123,
                                               timeout=1)
        assert isinstance(out, dns.exception.Timeout)

    @mock.patch.object(agent.dns_query, 'tcp')
    @mock.patch.object(agent.dns_query, 'udp')
    def test_send_dns_message_bad_response(self, *mocks):
        mocks[0].side_effect = agent.dns_query.BadResponse

        out = self.agent._send_dns_message('msg', 'host', 123, 1)

        agent.dns_query.udp.assert_called_with('msg', 'host', port=123,
                                               timeout=1)
        assert isinstance(out, agent.dns_query.BadResponse)

    @mock.patch.object(agent.dns_query, 'tcp')
    @mock.patch.object(agent.dns_query, 'udp')
    def test_send_dns_message_tcp(self, *mocks):
        agent.CONF = RoObject({
            'service:mdns': RoObject(all_tcp=True)
        })
        mocks[1].return_value = 'mock tcp resp'

        out = self.agent._send_dns_message('msg', 'host', 123, 1)

        assert not agent.dns_query.udp.called
        agent.dns_query.tcp.assert_called_with('msg', 'host', port=123,
                                               timeout=1)
        self.assertEqual('mock tcp resp', out)
