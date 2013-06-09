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
from sqlalchemy import ForeignKey, Enum, Integer, String, DateTime, Text
from sqlalchemy.schema import Column, MetaData
from designate.openstack.common import timeutils
from designate.openstack.common.uuidutils import generate_uuid
from designate.storage.impl_sqlalchemy.migrate_repo.utils import Table
from designate.storage.impl_sqlalchemy.migrate_repo.utils import create_tables
from designate.storage.impl_sqlalchemy.migrate_repo.utils import drop_tables
from designate.sqlalchemy.types import Inet
from designate.sqlalchemy.types import UUID

meta = MetaData()

RECORD_TYPES = ['A', 'AAAA', 'CNAME', 'MX', 'SRV', 'TXT', 'NS']

servers = Table('servers', meta,
                Column('id', UUID(), default=generate_uuid, primary_key=True),
                Column('created_at', DateTime(), default=timeutils.utcnow),
                Column('updated_at', DateTime(), onupdate=timeutils.utcnow),
                Column('version', Integer(), default=1, nullable=False),
                Column('name', String(255), nullable=False, unique=True),
                Column('ipv4', Inet(), nullable=False, unique=True),
                Column('ipv6', Inet(), default=None, unique=True))

domains = Table('domains', meta,
                Column('id', UUID(), default=generate_uuid, primary_key=True),
                Column('created_at', DateTime(), default=timeutils.utcnow),
                Column('updated_at', DateTime(), onupdate=timeutils.utcnow),
                Column('version', Integer(), default=1, nullable=False),
                Column('tenant_id', String(36), default=None, nullable=True),
                Column('name', String(255), nullable=False, unique=True),
                Column('email', String(36), nullable=False),
                Column('ttl', Integer(), default=3600, nullable=False),
                Column('refresh', Integer(), default=3600, nullable=False),
                Column('retry', Integer(), default=3600, nullable=False),
                Column('expire', Integer(), default=3600, nullable=False),
                Column('minimum', Integer(), default=3600, nullable=False))

records = Table('records', meta,
                Column('id', UUID(), default=generate_uuid, primary_key=True),
                Column('created_at', DateTime(), default=timeutils.utcnow),
                Column('updated_at', DateTime(), onupdate=timeutils.utcnow),
                Column('version', Integer(), default=1, nullable=False),
                Column('type', Enum(name='record_types', *RECORD_TYPES),
                       nullable=False),
                Column('name', String(255), nullable=False),
                Column('data', Text(), nullable=False),
                Column('priority', Integer(), default=None),
                Column('ttl', Integer(), default=3600, nullable=False),
                Column('domain_id', UUID(), ForeignKey('domains.id'),
                       nullable=False))


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    tables = [domains, servers, records, ]
    create_tables(tables)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    tables = [domains, servers, records, ]
    drop_tables(tables)
