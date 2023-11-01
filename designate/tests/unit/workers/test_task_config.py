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
from oslo_config import cfg
from oslo_config import fixture as cfg_fixture
import oslotest.base

import designate.conf
from designate.worker.tasks import base

CONF = designate.conf.CONF


class TestTaskConfig(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))
        self.task_config = base.TaskConfig()

    def test_load_config(self):
        self.assertIsInstance(
            self.task_config.config, cfg.ConfigOpts.GroupAttr
        )

    def test_threshold_percentage(self):
        CONF.set_override('threshold_percentage', 51, 'service:worker')

        self.assertIsNone(self.task_config._threshold_percentage)
        self.assertEqual(51, self.task_config.threshold_percentage)
        self.assertIsNotNone(self.task_config._threshold_percentage)
        self.assertEqual(51, self.task_config.threshold_percentage)

    def test_timeout(self):
        CONF.set_override('poll_timeout', 52, 'service:worker')

        self.assertIsNone(self.task_config._timeout)
        self.assertEqual(52, self.task_config.timeout)
        self.assertIsNotNone(self.task_config._timeout)
        self.assertEqual(52, self.task_config.timeout)

    def test_retry_interval(self):
        CONF.set_override('poll_retry_interval', 53, 'service:worker')
        self.assertEqual(53, self.task_config.retry_interval)

    def test_max_retries(self):
        CONF.set_override('poll_max_retries', 54, 'service:worker')
        self.assertEqual(54, self.task_config.max_retries)

    def test_delay(self):
        CONF.set_override('poll_delay', 55, 'service:worker')
        self.assertEqual(55, self.task_config.delay)

    def test_max_prop_time(self):
        CONF.set_override('threshold_percentage', 100, 'service:worker')
        CONF.set_override('poll_timeout', 10, 'service:worker')
        CONF.set_override('poll_retry_interval', 10, 'service:worker')
        CONF.set_override('poll_max_retries', 10, 'service:worker')
        CONF.set_override('poll_delay', 3, 'service:worker')

        self.assertIsNone(self.task_config._max_prop_time)
        self.assertEqual(203, self.task_config.max_prop_time)
        self.assertIsNotNone(self.task_config._max_prop_time)
        self.assertEqual(203, self.task_config.max_prop_time)
