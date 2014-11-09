# Copyright (c) 2014 Rackspace Hosting
#
# Author: Betsy Luzader <betsy.luzader@rackspace.com>
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

from oslo.config import cfg

from sqlalchemy.schema import Table, Column, MetaData
from migrate.changeset.constraint import UniqueConstraint

from designate.sqlalchemy.types import UUID

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    domains_table = Table('domains', meta, autoload=True)

    # Get the default pool_id from the config file
    default_pool_id = cfg.CONF['service:central'].default_pool_id

    # Create the pool_id column
    pool_id_column = Column('pool_id',
                            UUID(),
                            default=default_pool_id,
                            nullable=True)
    pool_id_column.create(domains_table, populate_default=True)

    # Alter the table to drop default value after populating it
    domains_table.c.pool_id.alter(default=None)

    dialect = migrate_engine.url.get_dialect().name
    if dialect.startswith('sqlite'):
        # Add missing unique index
        constraint = UniqueConstraint('name', 'deleted',
                                      name='unique_domain_name',
                                      table=domains_table)
        constraint.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    domains_table = Table('domains', meta, autoload=True)

    domains_table.c.pool_id.drop()
