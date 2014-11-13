# Copyright (c) 2014 Rackspace Inc.
#
# Author: Tim Simmons <tim.simmons@rackspace.com>
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
from migrate.changeset.constraint import UniqueConstraint
from sqlalchemy import Index, MetaData, Table, Column, String
from sqlalchemy import func

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    connection = migrate_engine.connect()

    dialect = migrate_engine.url.get_dialect().name
    if dialect.startswith('sqlite'):
        connection.connection.create_function("reverse", 1, lambda s: s[::-1])

    # Domains Table
    domains_table = Table('domains', meta, autoload=True)

    reverse_name_col = Column('reverse_name', String(255), nullable=True,
                              server_default='')
    reverse_name_col.create(domains_table)

    update = domains_table.update()\
        .values(reverse_name=func.reverse(domains_table.c.name))
    connection.execute(update)

    domains_table.c.reverse_name.alter(nullable=False, default=None)

    rev_ind = Index('reverse_name_deleted', domains_table.c.reverse_name,
         domains_table.c.deleted)

    rev_ind.create(connection)

    # Recordsets Table
    rsets_table = Table('recordsets', meta, autoload=True)

    reverse_name_col = Column('reverse_name', String(255), nullable=True,
                              server_default='')
    reverse_name_col.create(rsets_table)

    update = rsets_table.update()\
        .values(reverse_name=func.reverse(rsets_table.c.name))
    connection.execute(update)

    rsets_table.c.reverse_name.alter(nullable=False, default=None)

    rev_ind = Index('reverse_name_dom_id', rsets_table.c.reverse_name,
         rsets_table.c.domain_id)

    rev_ind.create(connection)

    # Recreate constraints for SQLite
    if dialect.startswith('sqlite'):
        domains_constraint = UniqueConstraint('name', 'deleted',
                                              name='unique_domain_name',
                                              table=domains_table)
        recordsets_constraint = UniqueConstraint('domain_id', 'name', 'type',
                                                 name='unique_recordset',
                                                 table=rsets_table)
        domains_constraint.create()
        recordsets_constraint.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    # Domains Table
    domains_table = Table('domains', meta, autoload=True)

    rev_ind = Index('reverse_name_deleted', domains_table.c.reverse_name,
         domains_table.c.deleted)
    rev_ind.drop(migrate_engine)

    # Recordsets Table
    rsets_table = Table('recordsets', meta, autoload=True)

    rev_ind = Index('reverse_name_dom_id', rsets_table.c.reverse_name,
         rsets_table.c.domain_id)
    rev_ind.drop(migrate_engine)

    domains_table.c.reverse_name.drop()
    rsets_table.c.reverse_name.drop()

    # Recreate constraints for SQLite
    dialect = migrate_engine.url.get_dialect().name
    if dialect.startswith('sqlite'):
        domains_constraint = UniqueConstraint('name', 'deleted',
                                              name='unique_domain_name',
                                              table=domains_table)
        recordsets_constraint = UniqueConstraint('domain_id', 'name', 'type',
                                                 name='unique_recordset',
                                                 table=rsets_table)
        domains_constraint.create()
        recordsets_constraint.create()
