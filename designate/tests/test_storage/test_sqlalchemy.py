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
import tempfile
from migrate.versioning import api as versioning_api
from migrate.versioning import repository
import sqlalchemy
from designate.openstack.common import log as logging
from designate import storage
from designate.tests import TestCase
from designate.tests.test_storage import StorageTestCase

LOG = logging.getLogger(__name__)
REPOSITORY = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
                                          '..', 'storage', 'impl_sqlalchemy',
                                          'migrate_repo'))


class SqlalchemyStorageTest(StorageTestCase, TestCase):
    def setUp(self):
        self.config(database_connection='sqlite://',
                    group='storage:sqlalchemy')
        super(SqlalchemyStorageTest, self).setUp()
        self.storage = storage.get_storage()
        self.REPOSITORY = repository.Repository(REPOSITORY)

    # Migration Test Stuff
    def _init_database(self, url):
        LOG.debug('Building Engine')
        engine = sqlalchemy.create_engine(url)
        LOG.debug('Initializing database')
        versioning_api.version_control(engine, repository=self.REPOSITORY)

        return engine

    def _migrate_up(self, engine, version):
        versioning_api.upgrade(engine, repository=self.REPOSITORY,
                               version=version)

    def _migrate_down(self, engine, version):
        versioning_api.downgrade(engine, repository=self.REPOSITORY,
                                 version=version)

    def test_migrations_walk(self):
        # Init the Database
        engine = self._init_database("sqlite:///%s" % tempfile.mktemp())

        LOG.debug('Latest version is %s' % self.REPOSITORY.latest)

        for version in range(1, self.REPOSITORY.latest):
            LOG.debug('Upgrading to %s' % version)
            self._migrate_up(engine, version)
