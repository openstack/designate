# Copyright 2015 Dyn Inc.
#
# Author: Yasha Bubnov <ybubnov@dyn.com>
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
import dns.zone

from designate.agent import service
from designate.backend import agent_backend
from designate.tests import TestCase
from designate.tests.test_agent.test_backends import BackendTestMixin


class DenominatorAgentBackendTestCase(TestCase, BackendTestMixin):

    def setUp(self):
        super(DenominatorAgentBackendTestCase, self).setUp()
        self.config(port=0, group='service:agent')
        self.backend = agent_backend.get_backend('denominator',
            agent_service=service.Service())

        self.backend.start()

    def tearDown(self):
        super(DenominatorAgentBackendTestCase, self).tearDown()
        self.backend.agent_service.stop()
        self.backend.stop()

    @mock.patch('designate.utils.execute', return_value=(
                'example.org SOA 86400 ns1.designate.com. '
                'hostmaster@example.org. 475 3600 600 604800 1800', None))
    def test_find_zone_serial(self, execute):
        serial = self.backend.find_zone_serial('example.org.')

        # Ensure returned right serial number
        self.assertEqual(475, serial)

        # Ensure called "denominator zone add"
        self.assertIn('record', execute.call_args[0])
        self.assertIn('get', execute.call_args[0])

    @mock.patch('designate.utils.execute', return_value=('', None))
    def test_find_zone_serial_fail(self, execute):
        serial = self.backend.find_zone_serial('example.org.')
        self.assertIsNone(serial)

    @mock.patch('designate.utils.execute', return_value=(None, None))
    def test_create_zone(self, execute):
        zone = self._create_dnspy_zone('example.org.')
        self.backend.create_zone(zone)

        # Ensure denominator called for each record (except SOA)
        # plus one to update zone data
        self.assertEqual(len(list(zone.iterate_rdatas())),
                         execute.call_count)

    @mock.patch('designate.utils.execute')
    def test_update_zone(self, execute):
        # Output from 'designate record list' command
        records = ('example.org SOA 86400 ns1.designate.com. '
        'hostmaster@example.org. 475 3600 600 604800 1800\n'
        'example.org NS 86400 ns1.designator.net.\n'
        'example.org NS 86400 ns2.designator.net.\n'
        'example.org MX 86400 10 mx1.designator.net.')

        # That should force update_zone to delete A and AAAA records
        # from the zone and create a new MX record.
        execute.return_value = (records, None)

        zone = self._create_dnspy_zone('example.org.')
        self.backend.update_zone(zone)

        # Ensure denominator called to:
        # *update zone info
        # *fetch list of zone records
        # *delete one MX record
        # *replace one NS record
        # *create two A and two AAAA records
        # total: 8 calls

        self.assertEqual(8, execute.call_count)

        self.backend.denominator = mock.MagicMock
        methods = ['update_zone',
                   'get_records',
                   'create_record', 'update_record', 'delete_record']
        for method in methods:
            setattr(self.backend.denominator, method, mock.Mock(
                return_value=records))

        self.backend.update_zone(zone)
        self.assertEqual(1, self.backend.denominator.update_zone.call_count)
        self.assertEqual(1, self.backend.denominator.get_records.call_count)
        self.assertEqual(4, self.backend.denominator.create_record.call_count)
        self.assertEqual(1, self.backend.denominator.update_record.call_count)
        self.assertEqual(1, self.backend.denominator.delete_record.call_count)

    @mock.patch('designate.utils.execute', return_value=(None, None))
    def test_delete_zone(self, execute):
        self.backend.delete_zone('example.org.')

        # Ensure called 'denominator zone delete'
        self.assertEqual(1, execute.call_count)
        self.assertIn('zone', execute.call_args[0])
        self.assertIn('delete', execute.call_args[0])

    # Returns dns.zone test object
    def _create_dnspy_zone(self, name):
        zone_text = ('$ORIGIN %(name)s\n'
        '@  3600 IN SOA %(ns)s email.%(name)s 1421777854 3600 600 86400 3600\n'
        '   3600 IN NS %(ns)s\n'
        '   1800 IN A 173.194.123.30\n'
        '   1800 IN A 173.194.123.31\n'
        's  2400 IN AAAA 2001:db8:cafe::1\n'
        's  2400 IN AAAA 2001:db8:cafe::2\n'
        % {'name': name, 'ns': 'ns1.designate.net.'})

        return dns.zone.from_text(zone_text, check_origin=False)
