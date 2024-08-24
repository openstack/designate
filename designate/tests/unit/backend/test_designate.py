# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hpe.com>
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

from designateclient import exceptions
from designateclient.v2 import client
from oslo_log import log as logging
import oslotest.base

from designate.backend import impl_designate
from designate import context
from designate import objects
from designate.tests import base_fixtures


LOG = logging.getLogger(__name__)


class DesignateBackendTestCase(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(self.stdlog)

        self.admin_context = mock.Mock()
        mock.patch.object(
            context.DesignateContext, 'get_admin_context',
            return_value=self.admin_context).start()

        self.zone = objects.Zone(
            id='e2bed4dc-9d01-11e4-89d3-123b93f75cba',
            name='example.com.',
            email='example@example.com',
        )
        self.target = {
            'id': '4588652b-50e7-46b9-b688-a9bad40a873e',
            'type': 'designate',
            'masters': [
                {'host': '192.0.2.1', 'port': 53},
                {'host': '::1', 'port': 53},
                {'host': 'mdns.designate.example.com.', 'port': 53},
            ],
            'options': [
                {'key': 'auth_url', 'value': 'auth_url'},
                {'key': 'username', 'value': 'user'},
                {'key': 'password', 'value': 'secret'},
                {'key': 'project_name', 'value': 'project'},
                {'key': 'project_domain_name', 'value': 'project_domain'},
                {'key': 'user_domain_name', 'value': 'user_domain'},
                {'key': 'region_name', 'value': 'RegionOne'},
            ],
        }

        self.backend = impl_designate.DesignateBackend(
            objects.PoolTarget.from_dict(self.target)
        )

        # Mock client
        self.client = mock.NonCallableMagicMock()
        zones = mock.NonCallableMagicMock(spec_set=['create', 'delete'])

        self.client.configure_mock(zones=zones)

        self.backend._client = self.client

    def test_get_options(self):
        self.assertEqual('auth_url', self.backend.auth_url)
        self.assertEqual('user', self.backend.username)
        self.assertEqual('secret', self.backend.password)
        self.assertEqual('project', self.backend.project_name)
        self.assertEqual('project_domain', self.backend.project_domain_name)
        self.assertEqual('user_domain', self.backend.user_domain_name)
        self.assertEqual('dns', self.backend.service_type)
        self.assertEqual('RegionOne', self.backend.region_name)

    def test_get_client(self):
        self.backend._client = None

        self.assertIsInstance(self.backend.client, client.Client)

    def test_create_zone(self):
        masters = ["192.0.2.1:53", "[::1]:53",
                   "mdns.designate.example.com.:53"]
        self.backend.create_zone(self.admin_context, self.zone)
        self.client.zones.create.assert_called_once_with(
            self.zone.name, 'SECONDARY', masters=masters)

        self.assertIn(
            'Creating zone e2bed4dc-9d01-11e4-89d3-123b93f75cba / '
            'example.com.',
            self.stdlog.logger.output
        )

    def test_delete_zone(self):
        self.backend.delete_zone(self.admin_context, self.zone)
        self.client.zones.delete.assert_called_once_with(self.zone.name)

        self.assertIn(
            'Deleting zone e2bed4dc-9d01-11e4-89d3-123b93f75cba / '
            'example.com.',
            self.stdlog.logger.output
        )

    def test_delete_zone_notfound(self):
        self.client.delete.side_effect = exceptions.NotFound
        self.backend.delete_zone(self.admin_context, self.zone)
        self.client.zones.delete.assert_called_once_with(self.zone.name)

    def test_delete_zone_exc(self):
        self.client.zones.delete.side_effect = exceptions.RemoteError

        self.assertRaises(
            exceptions.RemoteError,
            self.backend.delete_zone, self.admin_context, self.zone,
        )
        self.client.zones.delete.assert_called_once_with(self.zone.name)

    def test_delete_zone_exc_not_found(self):
        self.client.zones.delete.side_effect = exceptions.NotFound

        self.backend.delete_zone(self.admin_context, self.zone)

        self.assertIn(
            'Zone e2bed4dc-9d01-11e4-89d3-123b93f75cba not found on remote '
            'Designate, Ignoring',
            self.stdlog.logger.output
        )
