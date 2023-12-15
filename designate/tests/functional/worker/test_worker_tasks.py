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
from oslo_utils import timeutils

import designate.conf
from designate.tests import base_fixtures
import designate.tests.functional
from designate.worker import processing
from designate.worker.tasks import zone


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class RecoverShardTest(designate.tests.functional.TestCase):
    def setUp(self):
        super().setUp()
        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(self.stdlog)
        self.executor = processing.Executor()

    def test_recover_error_create(self):
        new_zone = self.create_zone(shard=9)
        new_zone.status = 'ERROR'
        self.storage.update_zone(self.admin_context, new_zone)
        self.create_zone(fixture=1, shard=10)

        self.task = zone.RecoverShard(
            self.executor, self.admin_context, 0, new_zone.shard
        )

        self.task._worker_api = mock.Mock()

        self.task()

        self.task.worker_api.create_zone.assert_called()
        self.task.worker_api.update_zone.assert_not_called()
        self.task.worker_api.delete_zone.assert_not_called()

    def test_recover_error_update(self):
        new_zone = self.create_zone(shard=9)
        new_zone.action = 'UPDATE'
        new_zone.status = 'ERROR'
        self.storage.update_zone(self.admin_context, new_zone)
        self.create_zone(fixture=1, shard=10)

        self.task = zone.RecoverShard(
            self.executor, self.admin_context, 0, new_zone.shard
        )

        self.task._worker_api = mock.Mock()

        self.task()

        self.task.worker_api.create_zone.assert_not_called()
        self.task.worker_api.update_zone.assert_called()
        self.task.worker_api.delete_zone.assert_not_called()

    def test_recover_error_delete(self):
        new_zone = self.create_zone(shard=9)
        new_zone.action = 'DELETE'
        new_zone.status = 'ERROR'
        self.storage.update_zone(self.admin_context, new_zone)

        second_zone = self.create_zone(fixture=1, shard=10)
        second_zone.action = 'DELETE'
        second_zone.status = 'ERROR'
        self.storage.update_zone(self.admin_context, second_zone)

        self.task = zone.RecoverShard(
            self.executor, self.admin_context, 0, new_zone.shard
        )

        self.task._worker_api = mock.Mock()

        self.task()

        self.task.worker_api.create_zone.assert_not_called()
        self.task.worker_api.update_zone.assert_not_called()
        self.task.worker_api.delete_zone.assert_called()

    def test_recover_stale(self):
        new_zone = self.create_zone(
            shard=9,
        )
        new_zone.serial = timeutils.utcnow_ts() - 1000
        new_zone.action = 'DELETE'
        new_zone.status = 'PENDING'
        self.storage.update_zone(self.admin_context, new_zone)
        self.create_zone(fixture=1, shard=5)

        self.task = zone.RecoverShard(
            self.executor, self.admin_context, 0, new_zone.shard
        )

        self.task._worker_api = mock.Mock()

        self.task()

        self.task.worker_api.create_zone.assert_not_called()
        self.task.worker_api.update_zone.assert_not_called()
        self.task.worker_api.delete_zone.assert_called()

    def test_recover_nothing_to_do(self):
        self.create_zone(shard=0)
        self.create_zone(fixture=1, shard=2048)
        self.create_zone(fixture=2, shard=4095)

        self.task = zone.RecoverShard(
            self.executor, self.admin_context, 0, 4095
        )

        self.task._worker_api = mock.Mock()

        self.task()

        self.task.worker_api.create_zone.assert_not_called()
        self.task.worker_api.update_zone.assert_not_called()
        self.task.worker_api.delete_zone.assert_not_called()

    def test_recover_no_valid_actions(self):
        new_zone = self.create_zone(shard=9)
        new_zone.action = 'NONE'
        new_zone.status = 'ERROR'
        self.storage.update_zone(self.admin_context, new_zone)
        self.create_zone(fixture=1, shard=2048)
        self.create_zone(fixture=2, shard=4095)

        self.task = zone.RecoverShard(
            self.executor, self.admin_context, 0, 4095
        )

        self.task._worker_api = mock.Mock()

        self.task()

        self.task.worker_api.create_zone.assert_not_called()
        self.task.worker_api.update_zone.assert_not_called()
        self.task.worker_api.delete_zone.assert_not_called()
