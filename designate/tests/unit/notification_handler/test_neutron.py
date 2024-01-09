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
# under the License.mport threading


from unittest import mock

from oslo_config import fixture as cfg_fixture
import oslotest.base

import designate.conf
from designate.notification_handler import neutron
from designate.tests import base_fixtures


CONF = designate.conf.CONF


class TestNeutronHandler(oslotest.base.BaseTestCase):
    @mock.patch('designate.rpc.get_client', mock.Mock())
    def setUp(self):
        super().setUp()

        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(self.stdlog)
        self.useFixture(cfg_fixture.Config(CONF))

        self.zone_id = '09ecb760-efc8-43b9-8aa2-a53f8dec65d3'

        CONF.set_override(
            'enabled_notification_handlers',
            [neutron.NeutronFloatingHandler.__plugin_name__],
            'service:sink'
        )
        CONF.set_override(
            'zone_id', self.zone_id, 'handler:neutron_floatingip'
        )

        self.handler = neutron.NeutronFloatingHandler()
        self.handler._create = mock.Mock()
        self.handler._delete = mock.Mock()

    def test_get_name(self):
        self.assertEqual(
            self.handler.name,
            'handler:neutron_floatingip'
        )

    def test_get_canonical_name(self):
        self.assertEqual(
            self.handler.get_canonical_name(),
            'handler:neutron_floatingip'
        )

    def test_get_exchange_topics(self):
        self.assertEqual(
            self.handler.get_exchange_topics(),
            ('neutron', ['notifications'])
        )

    def test_get_event_types(self):
        self.assertEqual(
            self.handler.get_event_types(),
            [
                'floatingip.update.end',
                'floatingip.delete.start'
            ]
        )

    def test_process_notification_create(self):
        floatingip_id = 'a2a739ce-eae7-4c82-959f-55a105e4ac72'
        payload = {
            'floatingip': {
                'id': floatingip_id,
                'fixed_ip_address': '192.0.2.100',
                'floating_ip_address': '192.0.2.10'
            }
        }
        self.handler.process_notification(
            {}, 'floatingip.update.end', payload
        )

        self.handler._create.assert_called_with(
            addresses=[{'version': 4, 'address': '192.0.2.10'}],
            extra={
                'id': floatingip_id,
                'fixed_ip_address': '192.0.2.100',
                'floating_ip_address': '192.0.2.10',
                'project': None
            },
            zone_id=self.zone_id,
            resource_id=floatingip_id,
            resource_type='floatingip'
        )
        self.handler._delete.assert_not_called()

    def test_process_notification_delete(self):
        floatingip_id = 'a2a739ce-eae7-4c82-959f-55a105e4ac72'
        payload = {
            'floatingip_id': floatingip_id,
        }
        self.handler.process_notification(
            {}, 'floatingip.delete.start', payload
        )

        self.handler._create.assert_not_called()
        self.handler._delete.assert_called_with(
            zone_id=self.zone_id,
            resource_id=floatingip_id,
            resource_type='floatingip'
        )

    def test_process_notification_invalid_event_type(self):
        self.handler.process_notification(
            mock.Mock(), 'compute.instance.delete.end', None
        )

        self.handler._create.assert_not_called()
        self.handler._delete.assert_not_called()

    def test_process_notification_no_zone_id_set(self):
        CONF.set_override('zone_id', None, 'handler:neutron_floatingip')

        self.handler.process_notification(
            mock.Mock(), 'compute.instance.create.end', None
        )

        self.assertIn(
            'NeutronFloatingHandler: zone_id is None, ignore the event.',
            self.stdlog.logger.output
        )

        self.handler._create.assert_not_called()
        self.handler._delete.assert_not_called()
