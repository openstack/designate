# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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
from sqlalchemy.schema import MetaData

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    if migrate_engine.name == "mysql":
        tables = ['domains', 'quotas', 'records', 'servers', 'tsigkeys']

        migrate_engine.execute("SET foreign_key_checks = 0")

        for table in tables:
            migrate_engine.execute(
                "ALTER TABLE %s ENGINE=InnoDB" % table)
            migrate_engine.execute(
                "ALTER TABLE %s CONVERT TO CHARACTER SET utf8" % table)

        migrate_engine.execute("SET foreign_key_checks = 1")
        migrate_engine.execute(
            "ALTER DATABASE %s DEFAULT CHARACTER SET utf8" %
            migrate_engine.url.database)


def downgrade(migrate_engine):
    # utf8/InnoDB tables are backward compatible.. No need to revert.
    pass
