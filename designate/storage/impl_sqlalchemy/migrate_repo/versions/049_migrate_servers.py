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

from sqlalchemy.schema import Table, MetaData
from sqlalchemy.sql import select

meta = MetaData()

# Get the default pool_id from the config file
default_pool_id = cfg.CONF['service:central'].default_pool_id.replace('-', '')


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    # Load the database tables
    servers_table = Table('servers', meta, autoload=True)
    pool_attrib_table = Table('pool_attributes', meta, autoload=True)

    # Read in all the servers to migrate to pool_attributes table
    servers = select(
        columns=[
            servers_table.c.id,
            servers_table.c.created_at,
            servers_table.c.updated_at,
            servers_table.c.version,
            servers_table.c.name
        ]
    ).execute().fetchall()

    for server in servers:
        pool_attrib_table.insert().execute(
            id=server.id,
            created_at=server.created_at,
            updated_at=server.updated_at,
            version=server.version,
            key='name_server',
            value=server.name,
            pool_id=default_pool_id
        )


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    # servers_table = Table('servers', meta, autoload=True)
    pool_attrib_table = Table('pool_attributes', meta, autoload=True)

    pool_attributes = select(
        columns=[
            pool_attrib_table.c.key,
            pool_attrib_table.c.pool_id
        ]
    ).execute().fetchall()

    for p in pool_attributes:
        pool_attrib_table.delete().\
            where(p.pool_id == default_pool_id).\
            where(p.key == 'name_server').execute()