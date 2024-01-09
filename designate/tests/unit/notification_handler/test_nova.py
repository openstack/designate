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
from designate.notification_handler import nova
from designate.tests import base_fixtures


CONF = designate.conf.CONF


class TestNovaHandler(oslotest.base.BaseTestCase):
    @mock.patch('designate.rpc.get_client', mock.Mock())
    def setUp(self):
        super().setUp()

        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(self.stdlog)
        self.useFixture(cfg_fixture.Config(CONF))

        self.zone_id = 'b0dc7c26-f605-41c0-b8aa-65d7c086495f'

        CONF.set_override(
            'enabled_notification_handlers',
            [nova.NovaFixedHandler.__plugin_name__],
            'service:sink'
        )
        CONF.set_override(
            'zone_id', self.zone_id, 'handler:nova_fixed'
        )

        self.handler = nova.NovaFixedHandler()
        self.handler._create = mock.Mock()
        self.handler._delete = mock.Mock()

    def test_get_name(self):
        self.assertEqual(
            self.handler.name,
            'handler:nova_fixed'
        )

    def test_get_canonical_name(self):
        self.assertEqual(
            self.handler.get_canonical_name(),
            'handler:nova_fixed'
        )

    def test_get_exchange_topics(self):
        self.assertEqual(
            self.handler.get_exchange_topics(),
            ('nova', ['notifications'])
        )

    def test_get_event_types(self):
        self.assertEqual(
            self.handler.get_event_types(),
            [
                'compute.instance.create.end',
                'compute.instance.delete.start'
            ]
        )

    def test_process_notification_create(self):
        payload = {
            'fixed_ips': mock.Mock(),
            'instance_id': mock.Mock(),
        }
        self.handler.process_notification(
            {}, 'compute.instance.create.end', payload
        )

        self.handler._create.assert_called_with(
            addresses=mock.ANY,
            extra={
                'fixed_ips': mock.ANY,
                'instance_id': mock.ANY,
                'project': None
            },
            zone_id=self.zone_id,
            resource_id=mock.ANY,
            resource_type='instance'
        )
        self.handler._delete.assert_not_called()

    def test_process_notification_delete(self):
        payload = {
            'instance_id': mock.Mock(),
        }
        self.handler.process_notification(
            {}, 'compute.instance.delete.start', payload
        )

        self.handler._create.assert_not_called()
        self.handler._delete.assert_called_with(
            zone_id=self.zone_id,
            resource_id=mock.ANY,
            resource_type='instance'
        )

    def test_process_notification_invalid_event_type(self):
        self.handler.process_notification(
            mock.Mock(), 'compute.instance.delete.end', None
        )

        self.handler._create.assert_not_called()
        self.handler._delete.assert_not_called()

    def test_process_notification_no_zone_id_set(self):
        CONF.set_override('zone_id', None, 'handler:nova_fixed')

        self.handler.process_notification(
            mock.Mock(), 'compute.instance.create.end', None
        )

        self.assertIn(
            'NovaFixedHandler: zone_id is None, ignore the event.',
            self.stdlog.logger.output
        )

        self.handler._create.assert_not_called()
        self.handler._delete.assert_not_called()
