# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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
from oslo_config import cfg
from sqlalchemy import Enum
from sqlalchemy.schema import Table, MetaData, Column
from migrate.changeset.constraint import UniqueConstraint

from designate.sqlalchemy.types import UUID

meta = MetaData()

# Get the default pool_id from the config file
default_pool_id = cfg.CONF['service:central'].default_pool_id.replace('-', '')

TSIG_SCOPES = ['POOL', 'ZONE']


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    # Load the TSIG Keys tables
    tsigkeys_table = Table('tsigkeys', meta, autoload=True)

    scopes = Enum(name='tsig_scopes', metadata=meta, *TSIG_SCOPES)
    scopes.create()

    # Create the scope and resource columns
    scope_col = Column('scope', scopes, nullable=False, server_default='POOL')
    scope_col.create(tsigkeys_table)

    # Start with nullable=True and populate_default=True, then convert
    # to nullable=False once all rows have been populted with a resource_id
    resource_id_col = Column('resource_id', UUID, default=default_pool_id,
                             nullable=True)
    resource_id_col.create(tsigkeys_table, populate_default=True)

    # Now that we've populated the default pool id in existing rows, MySQL
    # will let us convert this over to nullable=False
    tsigkeys_table.c.resource_id.alter(nullable=False)

    dialect = migrate_engine.url.get_dialect().name
    if dialect.startswith('sqlite'):
        # Add missing unique index
        constraint = UniqueConstraint('name', name='unique_tsigkey_name',
                                      table=tsigkeys_table)
        constraint.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    # Load the TSIG Keys tables
    tsigkeys_table = Table('tsigkeys', meta, autoload=True)
    scopes = Enum(name='tsig_scopes', metadata=meta, *TSIG_SCOPES)

    # Create the scope and resource columns
    tsigkeys_table.c.scope.drop()
    tsigkeys_table.c.resource_id.drop()
    scopes.drop()

    dialect = migrate_engine.url.get_dialect().name
    if dialect.startswith('sqlite'):
        # Add missing unique index
        constraint = UniqueConstraint('name', name='unique_tsigkey_name',
                                      table=tsigkeys_table)
        constraint.create()
