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

from designate.manage import base
from designate.manage import pool
from designate import objects
from designate.tests import base_fixtures
import designate.tests.functional


LOG = logging.getLogger(__name__)


def hydrate_pool_targets(target_masters):
    pool_targets = objects.PoolTargetList()
    masters = objects.PoolTargetMasterList()
    for target_master in target_masters:
        masters.append(target_master)
    target = objects.PoolTarget(masters=masters)
    target.masters = masters
    pool_targets.append(target)
    return pool_targets


class UpdatePoolTestCase(designate.tests.functional.TestCase):
    def setUp(self):
        super().setUp()
        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(self.stdlog)

        self.print_result = mock.patch.object(
            base.Commands, '_print_result').start()

    def test_update_pools_zones(self):
        values = dict(
            name='example.com.',
            email='info@example.com',
            type='PRIMARY'
        )

        zone = self.central_service.create_zone(
            self.admin_context, zone=objects.Zone.from_dict(values))

        # Ensure the correct NS Records are in place
        new_pool = self.central_service.get_pool(
            self.admin_context, zone.pool_id
        )

        new_pool.targets = hydrate_pool_targets([objects.PoolTargetMaster(
            pool_target_id=new_pool.id,
            host='192.0.2.2',
            port='53')]
        )

        command = pool.PoolCommands()
        command._setup()

        with mock.patch.object(
                self.central_service, 'update_zone') as mock_update_zone:
            command._update_zones(new_pool)
            mock_update_zone.assert_called_once()

    def test_update_pools_zones_multiple_masters(self):
        values = dict(
            name='example.com.',
            email='info@example.com',
            type='PRIMARY'
        )

        zone = self.central_service.create_zone(
            self.admin_context, zone=objects.Zone.from_dict(values))

        # Ensure the correct NS Records are in place
        new_pool = self.central_service.get_pool(
            self.admin_context, zone.pool_id
        )

        targets1 = hydrate_pool_targets([
            objects.PoolTargetMaster(
                pool_target_id=new_pool.id,
                host='192.0.2.3',
                port='53')
        ])
        targets2 = hydrate_pool_targets([
            objects.PoolTargetMaster(
                pool_target_id=new_pool.id,
                host='192.0.2.4',
                port='53')
        ])
        new_pool.targets = objects.PoolTargetList()
        new_pool.targets.extend(targets1.objects + targets2.objects)

        command = pool.PoolCommands()
        command._setup()

        command._update_zones(new_pool)
