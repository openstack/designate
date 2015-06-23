# Copyright 2015 Rackspace Inc.
#
# Author: Tim Simmons <tim.simmons@rackspace.com>
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


from sqlalchemy import Integer, String, DateTime, Enum
from sqlalchemy.schema import Table, Column, MetaData

from oslo_utils import timeutils

from designate import utils
from designate.sqlalchemy.types import UUID

meta = MetaData()
TASK_STATUSES = ['ACTIVE', 'PENDING', 'DELETED', 'ERROR', 'COMPLETE']
TASK_TYPES = ['IMPORT']

zone_tasks_table = Table('zone_tasks', meta,
    Column('id', UUID(), default=utils.generate_uuid, primary_key=True),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),
    Column('version', Integer(), default=1, nullable=False),
    Column('tenant_id', String(36), default=None, nullable=True),

    Column('domain_id', UUID(), nullable=True),
    Column('task_type', Enum(name='task_types', *TASK_TYPES), nullable=True),
    Column('message', String(160), nullable=True),
    Column('status', Enum(name='resource_statuses', *TASK_STATUSES),
           nullable=False, server_default='ACTIVE',
           default='ACTIVE'),

    mysql_engine='INNODB',
    mysql_charset='utf8')


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    # Create the table
    zone_tasks_table.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    # Find the table and drop it
    zone_tasks_table = Table('zone_tasks', meta, autoload=True)
    zone_tasks_table.drop()
