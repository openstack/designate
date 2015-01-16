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
from oslo_utils import timeutils

from sqlalchemy import Integer, String, DateTime, Unicode, UniqueConstraint, \
                       Enum, ForeignKeyConstraint
from sqlalchemy.schema import Table, Column, MetaData

from designate import utils
from designate.sqlalchemy.types import UUID

POOL_PROVISIONERS = ['UNMANAGED']

meta = MetaData()

pools = Table("pools", meta,
    Column('id', UUID(), default=utils.generate_uuid, primary_key=True),
    Column('created_at', DateTime(), default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime(), onupdate=lambda: timeutils.utcnow()),
    Column('version', Integer(), default=1, nullable=False),

    Column('name', String(50), nullable=False),
    Column('description', Unicode(160)),
    Column('tenant_id', String(36), nullable=True),
    Column('provisioner', Enum(name='pool_provisioner', *POOL_PROVISIONERS),
           nullable=False, server_default='UNMANAGED'),

    UniqueConstraint('name', name='unique_pool_name'),

    mysql_engine='INNODB',
    mysql_charset='utf8')

pool_attributes = Table('pool_attributes', meta,
    Column('id', UUID(), default=utils.generate_uuid, primary_key=True),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
    Column('version', Integer(), default=1, nullable=False),

    Column('key', String(255), nullable=False),
    Column('value', String(255), nullable=False),
    Column('pool_id', UUID(), nullable=False),

    ForeignKeyConstraint(['pool_id'], ['pools.id'], ondelete='CASCADE'),

    mysql_engine='INNODB',
    mysql_charset='utf8')


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    pools.create()
    pool_attributes.create()

    # Get the default pool_id from the config file
    default_pool_id = cfg.CONF['service:central'].default_pool_id

    # Create the default pool with hard-coded name, which can be changed
    # later via the api, and the default_pool_id from the config file
    pools_table = Table('pools', meta, autoload=True)
    pools_table.insert().execute(
        id=default_pool_id,
        name='default',
        version=1
    )


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    with migrate_engine.begin() as conn:
        if migrate_engine.name == "mysql":
            conn.execute("SET foreign_key_checks = 0;")

        pool_attributes.drop()
        pools.drop()

        if migrate_engine.name == "mysql":
            conn.execute("SET foreign_key_checks = 1;")
