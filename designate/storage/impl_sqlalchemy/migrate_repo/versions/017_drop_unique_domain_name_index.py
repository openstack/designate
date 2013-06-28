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
import logging
from sqlalchemy import MetaData, Table, Column, String
from sqlalchemy.sql import update
from migrate.changeset.constraint import UniqueConstraint

LOG = logging.getLogger(__name__)
meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    dialect = migrate_engine.url.get_dialect().name

    domains_table = Table('domains', meta, autoload=True)

    if not dialect.startswith('sqlite'):
        constraint = UniqueConstraint('name', name='name', table=domains_table)
        constraint.drop()
    else:
        # SQLite can't drop a constraint. Yay. This will be fun..

        # Create a new name column without the unique index
        name_tmp_column = Column('name_tmp', String(255))
        name_tmp_column.create(domains_table)

        # Copy the data over.
        query = update(domains_table).values(name_tmp=domains_table.c.name)
        migrate_engine.execute(query)

        # Delete the name column
        domains_table.c.name.drop()

        # Rename the name_tmp column to name
        domains_table.c.name_tmp.alter(name='name')


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    domains_table = Table('domains', meta, autoload=True)

    constraint = UniqueConstraint('name', name='name', table=domains_table)
    constraint.create()
