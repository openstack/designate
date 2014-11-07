# Copyright (c) 2014 eBay Inc.
#
# Author: Ron Rickard <rrickard@ebaysf.com>
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
from sqlalchemy import MetaData, Table, Enum, Column, Integer
from migrate.changeset.constraint import UniqueConstraint

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    RESOURCE_STATUSES = ['ACTIVE', 'PENDING', 'DELETED', 'ERROR']
    ACTIONS = ['CREATE', 'DELETE', 'UPDATE', 'NONE']

    # Get associated database tables
    domains_table = Table('domains', meta, autoload=True)
    records_table = Table('records', meta, autoload=True)

    # Upgrade the domains table.
    domains_table.c.status.alter(
        type=Enum(name='resource_statuses', *RESOURCE_STATUSES),
        default='PENDING', server_default='PENDING')
    action_column = Column('action', Enum(name='actions', *ACTIONS),
                           default='CREATE', server_default='CREATE',
                           nullable=False)
    action_column.create(domains_table)

    # Re-add constraint for sqlite.
    dialect = migrate_engine.url.get_dialect().name
    if dialect.startswith('sqlite'):
        constraint = UniqueConstraint(
            'name', 'deleted', name='unique_domain_name', table=domains_table)
        constraint.create()

    # Upgrade the records table.
    records_table.c.status.alter(
        type=Enum(name='resource_statuses', *RESOURCE_STATUSES),
        default='PENDING', server_default='PENDING')
    action_column = Column('action', Enum(name='actions', *ACTIONS),
                           default='CREATE', server_default='CREATE',
                           nullable=False)
    action_column.create(records_table)
    serial_column = Column('serial', Integer(), server_default='1',
                           nullable=False)
    serial_column.create(records_table)

    # Re-add constraint for sqlite.
    if dialect.startswith('sqlite'):
        constraint = UniqueConstraint(
            'hash', name='unique_record', table=records_table)
        constraint.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    RESOURCE_STATUSES = ['ACTIVE', 'PENDING', 'DELETED']

    # Get associated database tables
    domains_table = Table('domains', meta, autoload=True)
    records_table = Table('records', meta, autoload=True)

    # Downgrade the domains table.
    domains_table.c.status.alter(
        type=Enum(name='resource_statuses', *RESOURCE_STATUSES),
        default='ACTIVE', server_default='ACTIVE')
    domains_table.c.action.drop()

    # Re-add constraint for sqlite.
    dialect = migrate_engine.url.get_dialect().name
    if dialect.startswith('sqlite'):
        constraint = UniqueConstraint(
            'name', 'deleted', name='unique_domain_name', table=domains_table)
        constraint.create()

    # Downgrade the records table.
    records_table.c.status.alter(
        type=Enum(name='resource_statuses', *RESOURCE_STATUSES),
        default='ACTIVE', server_default='ACTIVE')
    records_table.c.action.drop()
    records_table.c.serial.drop()

    # Re-add constraint for sqlite.
    if dialect.startswith('sqlite'):
        constraint = UniqueConstraint(
            'hash', name='unique_record', table=records_table)
        constraint.create()
