# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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
from sqlalchemy import Integer, String, DateTime, UniqueConstraint
from sqlalchemy.schema import Table, Column, MetaData
from designate.openstack.common import timeutils
from designate.openstack.common.uuidutils import generate_uuid
from designate.sqlalchemy.types import UUID


meta = MetaData()

quotas = Table('quotas', meta,
               Column('id', UUID(), default=generate_uuid, primary_key=True),
               Column('created_at', DateTime(), default=timeutils.utcnow),
               Column('updated_at', DateTime(), onupdate=timeutils.utcnow),
               Column('version', Integer(), default=1, nullable=False),
               Column('tenant_id', String(36), nullable=False),
               Column('resource', String(32), nullable=False),
               Column('hard_limit', Integer(), nullable=False),
               UniqueConstraint('tenant_id', 'resource', name='unique_quota'))


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    quotas.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    quotas.drop()
