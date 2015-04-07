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

ACTIONS = ['CREATE', 'DELETE', 'UPDATE', 'NONE']


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    RESOURCE_STATUSES = ['ACTIVE', 'PENDING', 'DELETED', 'ERROR']

    # Get associated database tables
    domains_table = Table('domains', meta, autoload=True)
    records_table = Table('records', meta, autoload=True)

    dialect = migrate_engine.url.get_dialect().name
    if dialect.startswith("postgresql"):
        migrate_engine.execute(
            "ALTER TYPE domain_statuses RENAME TO resource_statuses;")

        with migrate_engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT")
            conn.execute(
                "ALTER TYPE resource_statuses ADD VALUE 'ERROR' "
                "AFTER 'DELETED'")
            conn.close()

    actions = Enum(name='actions', metadata=meta, *ACTIONS)
    actions.create()

    resource_statuses = Enum(name='resource_statuses', metadata=meta,
                             *RESOURCE_STATUSES)

    # Upgrade the domains table.
    domains_table.c.status.alter(
        type=resource_statuses,
        default='PENDING', server_default='PENDING')

    action_column = Column('action', actions,
                           default='CREATE', server_default='CREATE',
                           nullable=False)
    action_column.create(domains_table)

    # Re-add constraint for sqlite.
    if dialect.startswith('sqlite'):
        constraint = UniqueConstraint(
            'name', 'deleted', name='unique_domain_name', table=domains_table)
        constraint.create()

    # Upgrade the records table.
    if dialect.startswith("postgresql"):
        sql = "ALTER TABLE records ALTER COLUMN status DROP DEFAULT, " \
              "ALTER COLUMN status TYPE resource_statuses USING " \
              "records::text::resource_statuses, ALTER COLUMN status " \
              "SET DEFAULT 'PENDING';"
        migrate_engine.execute(sql)
        record_statuses = Enum(name='record_statuses', metadata=meta,
                               *RESOURCE_STATUSES)
        record_statuses.drop()
    else:
        records_table.c.status.alter(
            type=resource_statuses,
            default='PENDING', server_default='PENDING')

    action_column = Column('action', actions,
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
    pass
