# Copyright 2014 eBay Inc.
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
from sqlalchemy import Integer, DateTime, Enum, UniqueConstraint
from sqlalchemy.schema import Table, Column, MetaData

from designate.sqlalchemy.types import UUID

UPDATE_STATUSES = ['SUCCESS', 'ERROR']
UPDATE_ACTIONS = ['CREATE', 'DELETE', 'UPDATE']

meta = MetaData()

pool_manager_statuses = Table(
    'pool_manager_statuses', meta,
    Column('id', UUID(), primary_key=True),
    Column('version', Integer(), nullable=False),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
    Column('server_id', UUID(), nullable=False),
    Column('domain_id', UUID(), nullable=False),
    Column('action', Enum(name='update_actions', *UPDATE_ACTIONS),
           nullable=False),
    Column('status', Enum(name='update_statuses', *UPDATE_STATUSES),
           nullable=True),
    Column('serial_number', Integer, nullable=False),

    UniqueConstraint('server_id', 'domain_id', 'action',
                     name='unique_pool_manager_status'),

    mysql_engine='InnoDB',
    mysql_charset='utf8')


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    with migrate_engine.begin() as conn:
        if migrate_engine.name == "mysql":
            conn.execute("SET foreign_key_checks = 0;")

        elif migrate_engine.name == "postgresql":
            conn.execute("SET CONSTRAINTS ALL DEFERRED;")

        pool_manager_statuses.create(conn)

        if migrate_engine.name == "mysql":
            conn.execute("SET foreign_key_checks = 1;")


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    with migrate_engine.begin() as conn:
        if migrate_engine.name == "mysql":
            conn.execute("SET foreign_key_checks = 0;")

        elif migrate_engine.name == "postgresql":
            conn.execute("SET CONSTRAINTS ALL DEFERRED;")

        pool_manager_statuses.drop()

        if migrate_engine.name == "mysql":
            conn.execute("SET foreign_key_checks = 1;")
