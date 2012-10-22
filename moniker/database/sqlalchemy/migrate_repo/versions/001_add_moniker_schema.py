# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Hewlett-Packard Development Company, L.P. 
# All Rights Reserved.
#
# Author: Patrick Galbraith <patg@hp.com>
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from migrate import *
from sqlalchemy.schema import (Column, MetaData, Table)
from moniker.database.sqlalchemy.migrate_repo.schema import (
    Boolean, DateTime, Integer, String, Text, create_tables, 
    drop_tables, RECORD_TYPES)

meta = MetaData()

domains = Table('domains',
    Column('tenant_id', String(36), nullable=False),
    Column('name', String(255), nullable=False, unique=True),
    Column('email', String(36), nullable=False),
    Column('ttl', Integer, default=3600, nullable=False),
    Column('refresh', Integer, default=3600, nullable=False),
    Column('retry', Integer, default=3600, nullable=False),
    Column('expire', Integer, default=3600, nullable=False),
    Column('minimum', Integer, default=3600, nullable=False),
    relationship('Record', backref=backref('domain', uselist=False)),
    mysql_engine='InnoDB',
    useexisting=True)
)

servers = Table('servers',
    Column('name', String(255), nullable=False, unique=True),
    Column('ipv4', Inet, nullable=False, unique=True),
    Column('ipv6', Inet, default=None, unique=True),
    mysql_engine='InnoDB',
    useexisting=True)

records =  Table('records',
    Column('type', Enum(name='record_types', *RECORD_TYPES), nullable=False),
    Column('name', String(255), nullable=False),
    Column('data', Text, nullable=False),
    Column('priority', Integer, default=None),
    Column('ttl', Integer, default=3600, nullable=False),
    Column('domain_id', UUID, ForeignKey('domains.id'), nullable=False),
    mysql_engine='InnoDB',
    useexisting=True)


def upgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
    tables = [domains, servers, records, ]
    create_tables(tables)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
    tables = [domains, servers, records, ]
    drop_tables(tables)
