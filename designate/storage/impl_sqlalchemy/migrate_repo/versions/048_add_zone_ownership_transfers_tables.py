# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Graham Hayes <graham.hayes@hpe.com>
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
from sqlalchemy import Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.schema import Table, Column, MetaData

from designate.sqlalchemy.types import UUID

TASK_STATUSES = ['ACTIVE', 'PENDING', 'DELETED', 'ERROR', 'COMPLETE']

meta = MetaData()


zone_transfer_requests = Table(
    'zone_transfer_requests',
    meta,
    Column('id', UUID(), primary_key=True),
    Column('domain_id', UUID, ForeignKey('domains.id'), nullable=False),
    Column('key', String(255), nullable=False),
    Column('description', String(255), nullable=True),
    Column('tenant_id', String(36), nullable=False),
    Column('target_tenant_id', String(36), nullable=True),
    Column('status',
           Enum(name='task_statuses_ztr', metadata=meta, *TASK_STATUSES),
           nullable=False, server_default='ACTIVE',),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
    Column('version', Integer(), nullable=False),
    mysql_engine='INNODB',
    mysql_charset='utf8'
)

zone_transfer_accepts = Table(
    'zone_transfer_accepts',
    meta,
    Column('id', UUID(), primary_key=True),
    Column('domain_id', UUID, ForeignKey('domains.id'), nullable=False),
    Column('zone_transfer_request_id', UUID,
           ForeignKey('zone_transfer_requests.id',
                      ondelete='CASCADE'),
           nullable=False),
    Column('status',
           Enum(name='task_statuses_zta', metadata=meta, *TASK_STATUSES),
           nullable=False, server_default='ACTIVE'),
    Column('tenant_id', String(36), nullable=False),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
    Column('version', Integer(), nullable=False),
    mysql_engine='INNODB',
    mysql_charset='utf8'
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    Table('domains', meta, autoload=True)

    zone_transfer_requests.create()
    zone_transfer_accepts.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    zone_transfer_accepts.drop()
    zone_transfer_requests.drop()
