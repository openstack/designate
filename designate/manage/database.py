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

from migrate.exceptions import (DatabaseAlreadyControlledError,
                                DatabaseNotControlledError)
from migrate.versioning import api as versioning_api
from designate.openstack.common import log as logging
from designate.openstack.common.gettextutils import _LI
from oslo.config import cfg
from designate.manage import base


LOG = logging.getLogger(__name__)
REPOSITORY = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
                                          'storage', 'impl_sqlalchemy',
                                          'migrate_repo'))
cfg.CONF.import_opt('database_connection', 'designate.storage.impl_sqlalchemy',
                    group='storage:sqlalchemy')


class DatabaseCommands(base.Commands):
    def init(self):
        url = cfg.CONF['storage:sqlalchemy'].database_connection

        try:
            LOG.info(_LI('Attempting to initialize database'))
            versioning_api.version_control(url=url, repository=REPOSITORY)
            LOG.info(_LI('Database initialized successfully'))
        except DatabaseAlreadyControlledError:
            raise Exception('Database already initialized')

    @base.args('--version', metavar='<version>', help="Database version")
    def sync(self, version=None):
        url = cfg.CONF['storage:sqlalchemy'].database_connection

        if not os.path.exists(REPOSITORY):
            raise Exception('Migration Repository Not Found')

        try:
            target_version = int(version) if version else None

            current_version = versioning_api.db_version(url=url,
                                                        repository=REPOSITORY)
        except DatabaseNotControlledError:
            raise Exception('Database not yet initialized')

        LOG.info(_LI("Attempting to synchronize database from version "
                     "'%(curr_version)s' to '%(tgt_version)s'"),
                 {'curr_version': current_version,
                  'tgt_version': target_version if
                  target_version is not None else "latest"})

        if target_version and target_version < current_version:
            versioning_api.downgrade(url=url, repository=REPOSITORY,
                                     version=version)
        else:
            versioning_api.upgrade(url=url, repository=REPOSITORY,
                                   version=version)

        LOG.info(_LI('Database synchronized successfully'))

    def version(self):
        url = cfg.CONF['storage:sqlalchemy'].database_connection

        current = versioning_api.db_version(url=url, repository=REPOSITORY)
        latest = versioning_api.version(repository=REPOSITORY).value

        print("Current: %s Latest: %s" % (current, latest))
