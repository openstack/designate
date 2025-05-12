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

from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_utils import timeutils

from designate.manage import service
from designate import objects
from designate.tests import base_fixtures
import designate.tests.functional

CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class ManageServiceTestCase(designate.tests.functional.TestCase):
    def setUp(self):
        super().setUp()
        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(self.stdlog)
        self.command = service.ServiceCommands()

    @mock.patch.object(service, 'LOG')
    def test_service_clean(self, m_log):
        values = self.get_service_status_fixture()
        service_status = objects.ServiceStatus.from_dict(values)
        service_status.heartbeated_at = timeutils.datetime.datetime(
            2024, 5, 8, 14, 46, 38, 314323)
        self.storage.create_service_status(
            self.admin_context, service_status)

        values_new = self.get_service_status_fixture(fixture=1)
        service_status_new = objects.ServiceStatus.from_dict(values_new)
        self.storage.create_service_status(
            self.admin_context, service_status_new)
        self.assertEqual(
            len(self.storage.find_service_statuses(self.admin_context)), 2
        )
        self.command.clean()
        self.assertIn(
            service_status.service_name,
            m_log.warning.call_args_list[0].args[1]['service_name']
        )
        statuses = self.storage.find_service_statuses(self.admin_context)
        self.assertEqual(len(statuses), 1)

        # Make sure the remaining service is not the one who expired
        self.assertEqual(service_status_new.service_name,
                         statuses[0].service_name)
        self.assertNotEqual(service_status.service_name,
                            statuses[0].service_name)

    @mock.patch.object(service, 'LOG')
    def test_service_clean_no_dead_service(self, m_log):
        values = self.get_service_status_fixture()
        service_status = objects.ServiceStatus.from_dict(values)
        self.storage.create_service_status(
            self.admin_context, service_status)

        values_new = self.get_service_status_fixture(fixture=1)
        service_status_new = objects.ServiceStatus.from_dict(values_new)
        self.storage.create_service_status(
            self.admin_context, service_status_new)
        self.assertEqual(
            len(self.storage.find_service_statuses(self.admin_context)), 2
        )
        self.command.clean()
        self.assertEqual(
            len(m_log.warning.call_args_list), 0
        )
        statuses = self.storage.find_service_statuses(self.admin_context)
        self.assertEqual(len(statuses), 2)

    @mock.patch.object(service, 'LOG')
    def test_service_clean_message_timeout(self, m_log):
        self.command.storage.find_service_statuses = mock.Mock(
            side_effect=messaging.exceptions.MessagingTimeout
        )
        self.assertRaises(SystemExit, self.command.clean)
        self.assertEqual(
            len(m_log.critical.call_args_list), 1
        )
