# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hp.com>
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
from oslo.utils import timeutils

from sqlalchemy import DateTime, Enum, Integer, String, ForeignKeyConstraint
from sqlalchemy.schema import Column, MetaData, Table
from sqlalchemy.sql import select
from migrate.changeset.constraint import UniqueConstraint

from designate import utils
from designate.sqlalchemy.types import UUID


meta = MetaData()

ZONE_ATTRIBUTE_KEYS = ('master',)

ZONE_TYPES = ('PRIMARY', 'SECONDARY')


meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    keys = Enum(name='key', *ZONE_ATTRIBUTE_KEYS)

    domain_attributes_table = Table(
        'domain_attributes', meta,
        Column('id', UUID(), default=utils.generate_uuid, primary_key=True),
        Column('version', Integer(), default=1, nullable=False),
        Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
        Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

        Column('key', keys),
        Column('value', String(255), nullable=False),
        Column('domain_id', UUID(), nullable=False),

        UniqueConstraint('key', 'value', 'domain_id',
                         name='unique_attributes'),
        ForeignKeyConstraint(['domain_id'], ['domains.id'],
                             ondelete='CASCADE'),

        mysql_engine='INNODB',
        mysql_charset='utf8'
    )

    domains_table = Table('domains', meta, autoload=True)
    types = Enum(name='types', metadata=meta, *ZONE_TYPES)
    types.create()

    # Add type and transferred_at to domains
    type_ = Column('type', types, default='PRIMARY', server_default='PRIMARY')
    transferred_at = Column('transferred_at', DateTime, default=None)

    type_.create(domains_table, populate_default=True)
    transferred_at.create(domains_table, populate_default=True)

    domain_attributes_table.create()

    dialect = migrate_engine.url.get_dialect().name
    if dialect.startswith('sqlite'):
        constraint = UniqueConstraint(
            'name', 'deleted', name='unique_domain_name', table=domains_table)

        # Add missing unique index
        constraint.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    keys = Enum(name='key', metadata=meta, *ZONE_ATTRIBUTE_KEYS)
    types = Enum(name='types', metadata=meta, *ZONE_TYPES)

    domains_attributes_table = Table('domain_attributes', meta, autoload=True)
    domains_table = Table('domains', meta, autoload=True)

    domains = select(columns=[domains_table.c.id, domains_table.c.type])\
        .where(domains_table.c.type == 'SECONDARY')\
        .execute().fetchall()

    for dom in domains:
        delete = domains_table.delete()\
            .where(domains_table.id == dom.id)
        delete.execute()

    domains_table.c.type.drop()
    domains_table.c.transferred_at.drop()

    domains_attributes_table.drop()
    keys.drop()
    types.drop()

    dialect = migrate_engine.url.get_dialect().name
    if dialect.startswith('sqlite'):
        constraint = UniqueConstraint(
            'name', 'deleted', name='unique_domain_name', table=domains_table)

        # Add missing unique index
        constraint.create()
