# Copyright (c) 2014 Rackspace Hosting
# All Rights Reserved.
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
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.schema import Table, Column, MetaData
from designate.openstack.common import timeutils
from designate import utils
from designate.sqlalchemy.types import UUID

meta = MetaData()

blacklists = Table(
    'blacklists',
    meta,
    Column('id', UUID(), default=utils.generate_uuid,
           primary_key=True),
    Column('created_at', DateTime(),
           default=timeutils.utcnow),
    Column('updated_at', DateTime(),
           onupdate=timeutils.utcnow),
    Column('version', Integer(), default=1,
           nullable=False),
    Column('pattern', String(255), nullable=False,
           unique=True),
    Column('description', String(160),
           nullable=True),

    mysql_engine='INNODB',
    mysql_charset='utf8')


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    blacklists.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    blacklists.drop()
