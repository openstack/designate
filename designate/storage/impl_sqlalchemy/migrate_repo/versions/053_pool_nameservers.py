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


from sqlalchemy import Integer, String, DateTime, ForeignKeyConstraint
from sqlalchemy.schema import Table, Column, MetaData
from sqlalchemy.sql import select
from oslo_config import cfg

from designate import utils
from designate.sqlalchemy.types import UUID

meta = MetaData()

# Get the default pool_id from the config file
default_pool_id = cfg.CONF['service:central'].default_pool_id.replace('-', '')

pool_ns_records_table = Table('pool_ns_records', meta,
    Column('id', UUID(), default=utils.generate_uuid, primary_key=True),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
    Column('version', Integer(), default=1, nullable=False),

    Column('pool_id', UUID(), nullable=False),
    Column('priority', Integer(), nullable=False),
    Column('hostname', String(255), nullable=False),

    ForeignKeyConstraint(['pool_id'], ['pools.id'], ondelete='CASCADE'),

    mysql_engine='INNODB',
    mysql_charset='utf8')


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    # Load the pool_attributes_table table schema
    pool_attributes_table = Table('pool_attributes', meta, autoload=True)

    # Create the pool_ns_records DB table
    pool_ns_records_table.create()

    # Find the existing name server entries
    pool_ns_records = select(
        columns=[
            pool_attributes_table.c.id,
            pool_attributes_table.c.key,
            pool_attributes_table.c.value,
            pool_attributes_table.c.created_at,
            pool_attributes_table.c.updated_at,
            pool_attributes_table.c.version
        ]
    ).where(pool_attributes_table.c.key == 'name_server').execute().fetchall()

    # Create matching entries in the new table.
    for pool_ns_record in pool_ns_records:
        pool_ns_records_table.insert().execute(
            id=pool_ns_record.id,
            created_at=pool_ns_record.created_at,
            updated_at=pool_ns_record.updated_at,
            version=pool_ns_record.version,

            pool_id=default_pool_id,
            priority=1,
            hostname=pool_ns_record.value,
        )

    # Delete the old nameserver attr rows from the Database
    pool_attributes_table.delete()\
                         .where(pool_attributes_table.c.key == 'name_server')\
                         .execute()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    # Load the pool_attributes and pool_ns_records table schema
    pool_attributes_table = Table('pool_attributes', meta, autoload=True)
    pool_ns_records_table = Table('pool_ns_records', meta, autoload=True)

    # Find the nameservers for the default_pool_id
    pool_ns_records = select(
        columns=[
            pool_ns_records_table.c.id,
            pool_ns_records_table.c.created_at,
            pool_ns_records_table.c.updated_at,
            pool_ns_records_table.c.version,

            pool_ns_records_table.c.hostname,
        ]
    ).where(pool_attributes_table.c.pool_id == default_pool_id)\
     .execute().fetchall()

    # Create matching entries in the new table.
    for pool_ns_record in pool_ns_records:
        pool_attributes_table.insert().execute(
            id=pool_ns_record.id,
            created_at=pool_ns_record.created_at,
            updated_at=pool_ns_record.updated_at,
            version=pool_ns_record.version,

            key='name_server',
            value=pool_ns_record.hostname,
        )

    # Delete the pool_ns_records table from the DB
    pool_ns_records_table.drop()
