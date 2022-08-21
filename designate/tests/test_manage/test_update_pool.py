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

from designate import context
from designate.manage.pool import PoolCommands
from designate import objects
from designate.tests import fixtures
from designate.tests.test_manage import DesignateManageTestCase

LOG = logging.getLogger(__name__)


class UpdatePoolTestCase(DesignateManageTestCase):
    def setUp(self):
        super(DesignateManageTestCase, self).setUp()
        self.stdlog = fixtures.StandardLogging()
        self.useFixture(self.stdlog)

        self.context = context.DesignateContext.get_admin_context(
            request_id='designate-manage'
        )

    def hydrate_pool_targets(self, target_masters):
        pool_targets = objects.PoolTargetList()
        masters = objects.PoolTargetMasterList()
        for target_master in target_masters:
            masters.append(target_master)
        target = objects.PoolTarget(masters=masters)
        target.masters = masters
        pool_targets.append(target)
        return pool_targets

    def test_update_pools_zones(self):
        values = dict(
            name='example.com.',
            email='info@example.com',
            type='PRIMARY'
        )

        zone = self.central_service.create_zone(
            self.admin_context, zone=objects.Zone.from_dict(values))

        # Ensure the correct NS Records are in place
        pool = self.central_service.get_pool(
            self.admin_context, zone.pool_id
        )

        pool.targets = self.hydrate_pool_targets([objects.PoolTargetMaster(
            pool_target_id=pool.id,
            host='192.0.2.2',
            port='53')]
        )

        command = PoolCommands()
        command.context = self.context
        command.central_api = self.central_service

        with mock.patch.object(
                self.central_service, 'update_zone') as mock_update_zone:
            command._update_zones(pool)
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
        pool = self.central_service.get_pool(
            self.admin_context, zone.pool_id
        )

        targets1 = self.hydrate_pool_targets([
            objects.PoolTargetMaster(
                pool_target_id=pool.id,
                host='192.0.2.3',
                port='53')
        ])
        targets2 = self.hydrate_pool_targets([
            objects.PoolTargetMaster(
                pool_target_id=pool.id,
                host='192.0.2.4',
                port='53')
        ])
        pool.targets = objects.PoolTargetList()
        pool.targets.extend(targets1.objects + targets2.objects)

        command = PoolCommands()
        command.context = self.context
        command.central_api = self.central_service

        command._update_zones(pool)

    def test_create_new_pool(self):
        pool = {
            'name': 'new_pool',
            'description': 'New PowerDNS Pool',
            'attributes': {},
            'ns_records': [
                {'hostname': 'ns1-1.example.org.', 'priority': 1},
                {'hostname': 'ns1-2.example.org.', 'priority': 2}
            ],
            'nameservers': [
                {'host': '192.0.2.2', 'port': 53}
            ],
            'targets': [
                {
                    'type': 'powerdns',
                    'description': 'PowerDNS Database Cluster',
                    'masters': [
                        {'host': '192.0.2.1', 'port': 5354}
                    ],
                    'options': {
                        'host': '192.0.2.2', 'port': 53,
                        'connection': 'connection'
                    }
                }
            ],
            'also_notifies': [
                {'host': '192.0.2.4', 'port': 53}
            ]
        }

        command = PoolCommands()
        command.context = self.context
        command.central_api = self.central_service

        command._create_pool(pool, dry_run=False)

        pool = self.central_service.find_pool(
            self.admin_context, {'name': 'new_pool'}
        )

        self.assertEqual('new_pool', pool.name)
        self.assertEqual('New PowerDNS Pool', pool.description)
