# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hp.com>
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
import datetime
import time

import mock
from oslo_messaging.notify import notifier

from designate import objects
from designate import utils
from designate.zone_manager import tasks
from designate.tests import TestCase


class TaskTest(TestCase):
    def setUp(self):
        super(TaskTest, self).setUp()
        utils.register_plugin_opts()

    def _enable_tasks(self, tasks):
        self.config(
            enabled_tasks=tasks,
            group="service:zone_manager")


class PeriodicExistsTest(TaskTest):
    def setUp(self):
        super(PeriodicExistsTest, self).setUp()
        self.config(
            interval=2,
            group="zone_manager_task:periodic_exists")
        self._enable_tasks("periodic_exists")

    def _wait_for_cond(self, condition, interval=0.5, max_attempts=20):
        attempts = 0
        while attempts < max_attempts:
            result = condition()
            if result:
                return result
            time.sleep(interval)
            attempts += 1
        raise ValueError

    @mock.patch.object(notifier.Notifier, 'info')
    def test_emit_exists(self, mock_notifier):
        domain = self.create_domain()
        # Clear the create domain notification
        mock_notifier.reset_mock()

        # Install our own period results
        start, end = tasks.PeriodicExistsTask._get_period(2)
        with mock.patch.object(tasks.PeriodicExistsTask, "_get_period",
                               return_value=(start, end,)):

            svc = self.start_service("zone_manager")
            result = self._wait_for_cond(
                lambda: mock_notifier.called is True, .5, 3)
            self.assertEqual(True, result)
            svc.stop()

        # Make some notification data in the same format that the task does
        data = dict(domain)
        del data["attributes"]
        # For some reason domain.created when doing dict(domain) is a datetime
        data["created_at"] = datetime.datetime.isoformat(domain.created_at)
        data["audit_period_beginning"] = str(start)
        data["audit_period_ending"] = str(end)

        # .info(ctxt, event, payload)
        mock_notifier.assert_called_with(mock.ANY, "dns.domain.exists", data)

    @mock.patch.object(notifier.Notifier, 'info')
    def test_emit_exists_no_zones(self, mock_notifier):
        self.start_service("zone_manager")
        # Since the interval is 2 seconds we wait for the call to have been
        # executed for 3 seconds
        time.sleep(2)
        self.assertEqual(False, mock_notifier.called)

    @mock.patch.object(notifier.Notifier, 'info')
    def test_emit_exists_multiple_zones(self, mock_notifier):
        zones = []
        for i in range(0, 10):
            z = self.central_service.create_domain(
                self.admin_context,
                objects.Domain(
                    name="example%s.net." % i,
                    email="foo@example.com"))
            zones.append(z)

        # Clear any notifications from create etc.
        mock_notifier.reset_mock()

        # Start ZM so that the periodic task fires
        self.start_service("zone_manager")
        self._wait_for_cond(lambda: mock_notifier.call_count is 10)
