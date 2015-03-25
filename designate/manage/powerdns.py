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
from oslo.config import cfg
from oslo_db.sqlalchemy.migration_cli import manager as migration_manager
from oslo_log import log as logging

from designate.manage import base
from designate import utils

LOG = logging.getLogger(__name__)

REPOSITORY = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
                                          'backend', 'impl_powerdns',
                                          'migrate_repo'))
CONF = cfg.CONF
utils.register_plugin_opts()


def get_manager(pool_target_id):
    pool_target_options = CONF['pool_target:%s' % pool_target_id].options
    connection = pool_target_options['connection']

    migration_config = {
        'migration_repo_path': REPOSITORY,
        'db_url': connection}
    return migration_manager.MigrationManager(migration_config)


class DatabaseCommands(base.Commands):
    @base.args('pool-target-id', help="Pool Target to Migrate", type=str)
    def version(self, pool_target_id):
        current = get_manager(pool_target_id).version()
        latest = versioning_api.version(repository=REPOSITORY).value
        print("Current: %s Latest: %s" % (current, latest))

    @base.args('pool-target-id', help="Pool Target to Migrate", type=str)
    def sync(self, pool_target_id):
        get_manager(pool_target_id).upgrade(None)

    @base.args('pool-target-id', help="Pool Target to Migrate", type=str)
    @base.args('revision', nargs='?')
    def upgrade(self, pool_target_id, revision):
        get_manager(pool_target_id).upgrade(revision)

    @base.args('pool-target-id', help="Pool Target to Migrate", type=str)
    @base.args('revision', nargs='?')
    def downgrade(self, pool_target_id, revision):
        get_manager(pool_target_id).downgrade(revision)
