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
from oslo_log import log as logging

from designate import objects
import designate.tests.functional


LOG = logging.getLogger(__name__)


class ProducerServiceTest(designate.tests.functional.TestCase):
    def setUp(self):
        super().setUp()
        self.producer_service = self.start_service('producer')

    def test_stop(self):
        self.producer_service.stop()

    def test_validate_partition_range(self):
        self.producer_service.start()

        min_partition = objects.Zone.fields['shard'].min
        max_partition = objects.Zone.fields['shard'].max

        self.assertIn(min_partition, self.producer_service.partition_range)
        self.assertIn(max_partition, self.producer_service.partition_range)
