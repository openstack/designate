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
import testtools
from designateclient import exceptions
from mock import NonCallableMagicMock
from mock import patch
from oslo_log import log as logging

from designate import objects
from designate import tests
from designate.backend import impl_designate

LOG = logging.getLogger(__name__)


class DesignateBackendTestCase(tests.TestCase):
    def setUp(self):
        super(DesignateBackendTestCase, self).setUp()
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
            ],
            'options': [
                {'key': 'username', 'value': 'user'},
                {'key': 'password', 'value': 'secret'},
                {'key': 'project_name', 'value': 'project'},
                {'key': 'project_zone_name', 'value': 'project_zone'},
                {'key': 'user_zone_name', 'value': 'user_zone'},
            ],
        }

        self.backend = impl_designate.DesignateBackend(
            objects.PoolTarget.from_dict(self.target)
        )

        # Mock client
        self.client = NonCallableMagicMock()
        zones = NonCallableMagicMock(spec_set=[
            'create', 'delete'])

        self.client.configure_mock(zones=zones)

    def test_create_zone(self):
        masters = ["%(host)s:%(port)s" % self.target['masters'][0]]
        with patch.object(self.backend, '_get_client',
                          return_value=self.client):
            self.backend.create_zone(self.admin_context, self.zone)
        self.client.zones.create.assert_called_once_with(
            self.zone.name, 'SECONDARY', masters=masters)

    def test_delete_zone(self):
        with patch.object(self.backend, '_get_client',
                          return_value=self.client):
            self.backend.delete_zone(self.admin_context, self.zone)
        self.client.zones.delete.assert_called_once_with(self.zone.name)

    def test_delete_zone_notfound(self):
        self.client.delete.side_effect = exceptions.NotFound
        with patch.object(self.backend, '_get_client',
                          return_value=self.client):
            self.backend.delete_zone(self.admin_context, self.zone)
        self.client.zones.delete.assert_called_once_with(self.zone.name)

    def test_delete_zone_exc(self):
        self.client.zones.delete.side_effect = Exception
        with testtools.ExpectedException(Exception):
            with patch.object(self.backend, '_get_client',
                              return_value=self.client):
                self.backend.delete_zone(self.admin_context, self.zone)
        self.client.zones.delete.assert_called_once_with(self.zone.name)
