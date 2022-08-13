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

from oslo_config import cfg
from oslo_config import fixture as cfg_fixture
import oslotest.base

import designate.backend.agent as agent
import designate.backend.private_codes as pcodes
from designate import context
from designate import dnsutils
from designate import exceptions
from designate import objects
from designate.tests.unit import RoObject

CONF = cfg.CONF


class AgentBackendTestCase(oslotest.base.BaseTestCase):
    def setUp(self):
        super(AgentBackendTestCase, self).setUp()
        self.useFixture(cfg_fixture.Config(CONF))

        self.context = mock.Mock()
        self.admin_context = mock.Mock()
        mock.patch.object(
            context.DesignateContext, 'get_admin_context',
            return_value=self.admin_context).start()

        CONF.set_override('poll_timeout', 1, 'service:worker')
        CONF.set_override('poll_retry_interval', 4, 'service:worker')
        CONF.set_override('poll_max_retries', 5, 'service:worker')
        CONF.set_override('poll_delay', 6, 'service:worker')

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

    def test_create_zone(self):
        self.backend._make_and_send_dns_message = mock.Mock(
            return_value=1
        )

        out = self.backend.create_zone(self.context, self.zone)

        self.backend._make_and_send_dns_message.assert_called_with(
            self.zone.name, 1, 14, pcodes.CREATE, pcodes.SUCCESS, 2, 3)
        self.assertIsNone(out)

    def test_create_zone_exception(self):
        self.backend._make_and_send_dns_message = mock.Mock(
            return_value=None
        )

        self.assertRaisesRegex(
            exceptions.Backend, 'Failed create_zone()',
            self.backend.create_zone, self.context, self.zone,
        )

        self.backend._make_and_send_dns_message.assert_called_with(
            self.zone.name, 1, 14, pcodes.CREATE, pcodes.SUCCESS, 2, 3)

    def test_update_zone(self):
        self.assertIsNone(self.backend.update_zone(self.context, self.zone))

    def test_delete_zone(self):
        self.backend._make_and_send_dns_message = mock.Mock(
            return_value=(1, 2))

        out = self.backend.delete_zone(self.context, self.zone)

        self.backend._make_and_send_dns_message.assert_called_with(
            self.zone.name, 1, 14, pcodes.DELETE, pcodes.SUCCESS, 2, 3)
        self.assertIsNone(out)

    def test_delete_zone_exception(self):
        self.backend._make_and_send_dns_message = mock.Mock(
            return_value=None
        )

        self.assertRaisesRegex(
            exceptions.Backend, 'Failed delete_zone()',
            self.backend.delete_zone, self.context, self.zone,
        )

        self.backend._make_and_send_dns_message.assert_called_with(
            self.zone.name, 1, 14, pcodes.DELETE, pcodes.SUCCESS, 2, 3)

    @mock.patch.object(dnsutils, 'send_dns_message')
    def test_make_and_send_dns_message_timeout(self, mock_send_dns_message):
        self.backend._make_dns_message = mock.Mock(return_value='')
        mock_send_dns_message.side_effect = dns.exception.Timeout()

        self.assertIsNone(
            self.backend._make_and_send_dns_message('h', 123, 1, 2, 3, 4, 5)
        )

    @mock.patch.object(dnsutils, 'send_dns_message')
    def test_make_and_send_dns_message_bad_response(self,
                                                    mock_send_dns_message):
        self.backend._make_dns_message = mock.Mock(return_value='')
        mock_send_dns_message.side_effect = dns.query.BadResponse()

        self.assertIsNone(
            self.backend._make_and_send_dns_message('h', 123, 1, 2, 3, 4, 5)
        )

    @mock.patch.object(dnsutils, 'send_dns_message')
    def test_make_and_send_dns_message_missing_AA_flags(self,
                                                        mock_send_dns_message):
        self.backend._make_dns_message = mock.Mock(return_value='')
        response = RoObject(
            rcode=mock.Mock(return_value=dns.rcode.NOERROR),
            # rcode is NOERROR but (flags & dns.flags.AA) gives 0
            flags=0,
        )
        mock_send_dns_message.return_value = response

        self.assertIsNone(
            self.backend._make_and_send_dns_message('h', 123, 1, 2, 3, 4, 5)
        )

    @mock.patch.object(dnsutils, 'send_dns_message')
    def test_make_and_send_dns_message_error_flags(self,
                                                   mock_send_dns_message):
        self.backend._make_dns_message = mock.Mock(return_value='')
        response = RoObject(
            rcode=mock.Mock(return_value=dns.rcode.NOERROR),
            # rcode is NOERROR but flags are not NOERROR
            flags=123,
            ednsflags=321
        )
        mock_send_dns_message.return_value = response

        self.assertIsNone(
            self.backend._make_and_send_dns_message('h', 123, 1, 2, 3, 4, 5)
        )

    @mock.patch.object(dnsutils, 'send_dns_message')
    def test_make_and_send_dns_message(self, mock_send_dns_message):
        self.backend._make_dns_message = mock.Mock(return_value='')
        response = RoObject(
            rcode=mock.Mock(return_value=dns.rcode.NOERROR),
            flags=agent.dns.flags.AA,
            ednsflags=321
        )
        mock_send_dns_message.return_value = response

        self.assertEqual(
            response,
            self.backend._make_and_send_dns_message('h', 123, 1, 2, 3, 4, 5)
        )
