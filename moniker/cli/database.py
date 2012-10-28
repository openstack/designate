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
from moniker import storage  # Import for database_connection cfg def.
from moniker.cli import utils

LOG = logging.getLogger(__name__)

REPOSITORY = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
                                          'storage', 'impl_sqlalchemy',
                                          'migrate_repo'))


class InitCommand(Command):
    "Init database"

    def take_action(self, parsed_args):
        utils.read_config('moniker-central')

        url = cfg.CONF.database_connection

        if not os.path.exists(REPOSITORY):
            raise Exception('Migration Respository Not Found')

        try:
            LOG.info('Attempting to initialize database')
            versioning_api.version_control(url=url, repository=REPOSITORY)
            LOG.info('Database initialized sucessfully')
        except DatabaseAlreadyControlledError:
            raise Exception('Database already initialized')


class SyncCommand(Command):
    "Sync database"

    def take_action(self, parsed_args):
        # TODO: Support specifying version
        utils.read_config('moniker-central')

        url = cfg.CONF.database_connection

        if not os.path.exists(REPOSITORY):
            raise Exception('Migration Respository Not Found')

        LOG.info('Attempting to synchronize database')
        versioning_api.upgrade(url=url, repository=REPOSITORY,
                               version=None)
        LOG.info('Database synchronized sucessfully')
