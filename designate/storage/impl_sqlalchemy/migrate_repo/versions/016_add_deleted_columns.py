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
from sqlalchemy import MetaData, Table, Column, DateTime
from sqlalchemy.types import CHAR
from migrate.changeset.constraint import UniqueConstraint

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    domains_table = Table('domains', meta, autoload=True)

    # Create the new columns
    deleted_column = Column('deleted', CHAR(32), nullable=False, default="0",
                            server_default="0")
    deleted_column.create(domains_table, populate_default=True)

    deleted_at_column = Column('deleted_at', DateTime, nullable=True,
                               default=None)
    deleted_at_column.create(domains_table, populate_default=True)

    # Drop the old single column unique
    # NOTE(kiall): It appears this does nothing. Miration 17 has been added.
    #              leaving this here for reference.
    domains_table.c.name.alter(unique=False)

    # Add a new multi-column unique index
    constraint = UniqueConstraint('name', 'deleted', name='unique_domain_name',
                                  table=domains_table)
    constraint.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    domains_table = Table('domains', meta, autoload=True)

    # Drop the multi-column unique index
    constraint = UniqueConstraint('name', 'deleted', name='unique_domain_name',
                                  table=domains_table)
    constraint.drop()

    # Revert to single column unique
    # NOTE(kiall): It appears this does nothing. Miration 17 has been added.
    #              leaving this here for reference.
    domains_table.c.name.alter(unique=True)

    # Drop the deleted columns
    deleted_column = Column('deleted', CHAR(32), nullable=True, default=None)
    deleted_column.drop(domains_table)

    deleted_at_column = Column('deleted_at', DateTime, nullable=True,
                               default=None)
    deleted_at_column.drop(domains_table)
