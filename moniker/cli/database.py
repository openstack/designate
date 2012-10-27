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
from migrate.exceptions import DatabaseAlreadyControlledError
from migrate.versioning import api as versioning_api
from cliff.command import Command
from moniker.openstack.common import log as logging
from moniker.openstack.common import cfg
import moniker.database  # Import for database_connection cfg def.

LOG = logging.getLogger(__name__)

URL = cfg.CONF.database_connection
REPOSITORY = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
                                          'database', 'sqlalchemy',
                                          'migrate_repo'))


class InitCommand(Command):
    "Init database"

    def take_action(self, parsed_args):
        try:
            LOG.info('Attempting to initialize database')
            versioning_api.version_control(url=URL, repository=REPOSITORY)
            LOG.info('Database initialize sucessfully')
        except DatabaseAlreadyControlledError:
            LOG.error('Database already initialized')


class SyncCommand(Command):
    "Sync database"

    def take_action(self, parsed_args):
        # TODO: Support specifying version
        try:
            LOG.info('Attempting to synchronize database')
            versioning_api.upgrade(url=URL, repository=REPOSITORY,
                                   version=None)
            LOG.info('Database synchronized sucessfully')
        except DatabaseAlreadyControlledError:
            LOG.error('Database synchronize failed')
