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


from oslo_log import log as logging

import designate.conf
from designate import objects
from designate.tests.functional.api import v2

CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class ZoneExportsTest(v2.ApiV2TestCase):
    def setUp(self):
        super().setUp()
        self.zone = self.create_zone()

    def create_zone_export(self, location='designate://'):
        return self.storage.create_zone_export(
            self.admin_context,
            objects.ZoneExport(
                status='ACTIVE',
                task_type='EXPORT',
                location=location,
                zone_id=self.zone['id']
            )
        )

    def test_export(self):
        zone_export = self.create_zone_export()
        response = self.client.get(
            '/zones/tasks/exports/%s/export' % zone_export['id'],
            headers={'X-Test-Role': 'member'}
        )

        self.assertEqual(200, response.status_int)
        self.assertEqual('text/dns', response.content_type)

    def test_export_cannot_be_exported_synchronously(self):
        zone_export = self.create_zone_export(location=None)

        self._assert_exception(
            'bad_request', 400, self.client.get,
            '/zones/tasks/exports/%s/export' % zone_export['id'],
            headers={'X-Test-Role': 'member'}
        )
