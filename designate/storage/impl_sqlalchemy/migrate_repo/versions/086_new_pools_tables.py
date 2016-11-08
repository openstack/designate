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

from oslo_utils import timeutils
from sqlalchemy import (Integer, String, Unicode, DateTime,
                        ForeignKeyConstraint, UniqueConstraint)
from sqlalchemy.schema import Table, Column, MetaData

from designate import utils
from designate.sqlalchemy.types import UUID

meta = MetaData()

pool_nameservers = Table('pool_nameservers', meta,
    Column('id', UUID, default=utils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('pool_id', UUID(), nullable=False),
    Column('host', String(255), nullable=False),
    Column('port', Integer(), nullable=False),

    ForeignKeyConstraint(['pool_id'], ['pools.id'], ondelete='CASCADE'),
    UniqueConstraint('pool_id', 'host', 'port', name='unique_pool_host_port'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

pool_targets = Table('pool_targets', meta,
    Column('id', UUID, default=utils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('pool_id', UUID(), nullable=False),
    Column('type', String(50), nullable=False),
    Column('tsigkey_id', UUID(), nullable=True),
    Column('description', Unicode(160), nullable=True),

    ForeignKeyConstraint(['pool_id'], ['pools.id'], ondelete='CASCADE'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

pool_target_masters = Table('pool_target_masters', meta,
    Column('id', UUID, default=utils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('pool_target_id', UUID(), nullable=False),
    Column('host', String(255), nullable=False),
    Column('port', Integer(), nullable=False),

    ForeignKeyConstraint(['pool_target_id'], ['pool_targets.id'],
                         ondelete='CASCADE'),
    UniqueConstraint('pool_target_id', 'host', 'port',
                     name='unique_pool_target_host_port'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

pool_target_options = Table('pool_target_options', meta,
    Column('id', UUID, default=utils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('pool_target_id', UUID(), nullable=False),
    Column('key', String(255), nullable=False),
    Column('value', String(255), nullable=False),

    ForeignKeyConstraint(['pool_target_id'], ['pool_targets.id'],
                         ondelete='CASCADE'),
    UniqueConstraint('pool_target_id', 'key', name='unique_pool_target_key'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

pool_also_notifies = Table('pool_also_notifies', meta,
    Column('id', UUID, default=utils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('pool_id', UUID(), nullable=False),
    Column('host', String(255), nullable=False),
    Column('port', Integer(), nullable=False),

    ForeignKeyConstraint(['pool_id'], ['pools.id'], ondelete='CASCADE'),
    UniqueConstraint('pool_id', 'host', 'port',
                     name='unique_pool_also_notifies_pool0host0port'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    # Load the pool_attributes_table table schema for relations
    Table('pools', meta, autoload=True)

    pool_nameservers.create(checkfirst=True)
    pool_targets.create(checkfirst=True)
    pool_target_options.create(checkfirst=True)
    pool_target_masters.create(checkfirst=True)
    pool_also_notifies.create(checkfirst=True)
