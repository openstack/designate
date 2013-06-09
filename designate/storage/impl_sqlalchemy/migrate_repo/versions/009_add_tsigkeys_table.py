# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
from sqlalchemy import Enum, Integer, String, DateTime
from sqlalchemy.schema import Table, Column, MetaData
from designate.openstack.common import timeutils
from designate.openstack.common.uuidutils import generate_uuid
from designate.sqlalchemy.types import UUID


meta = MetaData()

TSIG_ALGORITHMS = ['hmac-md5', 'hmac-sha1', 'hmac-sha224', 'hmac-sha256',
                   'hmac-sha384', 'hmac-sha512']

tsigkeys = Table('tsigkeys', meta,
                 Column('id', UUID(), default=generate_uuid, primary_key=True),
                 Column('created_at', DateTime(), default=timeutils.utcnow),
                 Column('updated_at', DateTime(), onupdate=timeutils.utcnow),
                 Column('version', Integer(), default=1, nullable=False),
                 Column('name', String(255), nullable=False, unique=True),
                 Column('algorithm', Enum(name='tsig_algorithms',
                                          *TSIG_ALGORITHMS),
                        nullable=False),
                 Column('secret', String(255), nullable=False))


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    tsigkeys.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    tsigkeys.drop()
