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
from oslo_log import log as logging

from designate.manage import base
from designate.sqlalchemy import utils


LOG = logging.getLogger(__name__)

REPOSITORY = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
                                          'storage', 'impl_sqlalchemy',
                                          'migrate_repo'))
cfg.CONF.import_opt('connection', 'designate.storage.impl_sqlalchemy',
                    group='storage:sqlalchemy')
CONF = cfg.CONF
INIT_VERSION = 69


def get_manager():
    return utils.get_migration_manager(
        REPOSITORY, CONF['storage:sqlalchemy'].connection, INIT_VERSION)


class DatabaseCommands(base.Commands):
    def version(self):
        current = get_manager().version()
        latest = versioning_api.version(repository=REPOSITORY).value
        print("Current: %s Latest: %s" % (current, latest))

    def sync(self):
        get_manager().upgrade(None)

    @base.args('revision', nargs='?')
    def upgrade(self, revision):
        get_manager().upgrade(revision)
