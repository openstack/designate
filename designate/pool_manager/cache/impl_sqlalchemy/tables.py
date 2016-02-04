# Copyright 2014 eBay Inc.
#
# Author: Ron rickard <rrickard@ebaysf.com>
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
from sqlalchemy import (Table, MetaData, Column, Integer, DateTime, Enum,
                        UniqueConstraint, ForeignKeyConstraint)

from oslo_utils import timeutils

from designate import utils
from designate.sqlalchemy.types import UUID

UPDATE_STATUSES = ['SUCCESS', 'ERROR']
UPDATE_ACTIONS = ['CREATE', 'DELETE', 'UPDATE']

metadata = MetaData()

pool_manager_statuses = Table(
    'pool_manager_statuses', metadata,
    Column('id', UUID, default=utils.generate_uuid, primary_key=True),
    Column('version', Integer, default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),
    Column('nameserver_id', UUID, nullable=False),
    Column('zone_id', UUID, nullable=False),
    Column('action', Enum(name='update_actions', *UPDATE_ACTIONS),
           nullable=False),
    Column('status', Enum(name='update_statuses', *UPDATE_STATUSES),
           nullable=True),
    Column('serial_number', Integer, nullable=False),


    UniqueConstraint('nameserver_id', 'zone_id', 'action',
                     name='unique_pool_manager_status'),
    ForeignKeyConstraint(['zone_id'], ['zones.id']),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)
