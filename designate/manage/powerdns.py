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
from oslo.config import cfg
from designate.manage import base

LOG = logging.getLogger(__name__)
REPOSITORY = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
                                          'backend', 'impl_powerdns',
                                          'migrate_repo'))
cfg.CONF.import_opt('database_connection', 'designate.backend.impl_powerdns',
                    group='backend:powerdns')


class DatabaseInitCommand(base.Command):
    """ Init PowerDNS database """

    def execute(self, parsed_args):
        url = cfg.CONF['backend:powerdns'].database_connection

        if not os.path.exists(REPOSITORY):
            raise Exception('Migration Respository Not Found')

        try:
            LOG.info('Attempting to initialize PowerDNS database')
            versioning_api.version_control(url=url, repository=REPOSITORY)
            LOG.info('PowerDNS database initialized sucessfully')
        except DatabaseAlreadyControlledError:
            raise Exception('PowerDNS Database already initialized')


class DatabaseSyncCommand(base.Command):
    """ Sync PowerDNS database """

    def get_parser(self, prog_name):
        parser = super(DatabaseSyncCommand, self).get_parser(prog_name)

        parser.add_argument('--to-version', help="Migrate to version",
                            default=None, type=int)

        return parser

    def execute(self, parsed_args):
        url = cfg.CONF['backend:powerdns'].database_connection

        if not os.path.exists(REPOSITORY):
            raise Exception('Migration Respository Not Found')

        try:
            target_version = int(parsed_args.to_version) \
                if parsed_args.to_version else None

            current_version = versioning_api.db_version(url=url,
                                                        repository=REPOSITORY)
        except DatabaseNotControlledError:
            raise Exception('PowerDNS database not yet initialized')

        LOG.info("Attempting to synchronize PowerDNS database from version "
                 "'%s' to '%s'",
                 current_version,
                 target_version if target_version is not None else "latest")

        if target_version and target_version < current_version:
            versioning_api.downgrade(url=url, repository=REPOSITORY,
                                     version=parsed_args.to_version)
        else:
            versioning_api.upgrade(url=url, repository=REPOSITORY,
                                   version=parsed_args.to_version)

        LOG.info('PowerDNS database synchronized sucessfully')
