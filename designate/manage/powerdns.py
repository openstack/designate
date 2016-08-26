# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
import os

from migrate.versioning import api as versioning_api
from oslo_config import cfg
from oslo_db.sqlalchemy.migration_cli import manager as migration_manager

from designate.manage import base
from designate import rpc
from designate import utils
from designate.central import rpcapi as central_rpcapi


REPOSITORY = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
                                          'backend', 'impl_powerdns',
                                          'migrate_repo'))
CONF = cfg.CONF
utils.register_plugin_opts()


def get_manager(pool_target):
    connection = pool_target.options.get('connection', None)

    migration_config = {
        'migration_repo_path': REPOSITORY,
        'db_url': connection}

    return migration_manager.MigrationManager(migration_config)


class DatabaseCommands(base.Commands):
    def __init__(self):
        super(DatabaseCommands, self).__init__()
        rpc.init(cfg.CONF)
        self.central_api = central_rpcapi.CentralAPI()

    @base.args('pool-id', help="Pool to Migrate", type=str)
    def version(self, pool_id):
        pool = self.central_api.find_pool(self.context, {"id": pool_id})

        for pool_target in pool.targets:
            current = get_manager(pool_target).version()
            latest = versioning_api.version(repository=REPOSITORY).value
            print("Current: %s Latest: %s" % (current, latest))

    @base.args('pool-id', help="Pool to Migrate", type=str)
    def sync(self, pool_id):
        pool = self.central_api.find_pool(self.context, {"id": pool_id})

        for pool_target in pool.targets:
            get_manager(pool_target).upgrade(None)

    @base.args('pool-id', help="Pool to Migrate", type=str)
    @base.args('revision', nargs='?')
    def upgrade(self, pool_id, revision):
        pool = self.central_api.find_pool(self.context, {"id": pool_id})

        for pool_target in pool.targets:
            get_manager(pool_target).upgrade(revision)

    @base.args('pool-id', help="Pool to Migrate", type=str)
    @base.args('revision', nargs='?')
    def downgrade(self, pool_id, revision):
        pool = self.central_api.find_pool(self.context, {"id": pool_id})

        for pool_target in pool.targets:
            get_manager(pool_target).downgrade(revision)
