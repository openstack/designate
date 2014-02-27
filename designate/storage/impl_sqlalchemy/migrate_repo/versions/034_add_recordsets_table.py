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
import hashlib
from sqlalchemy import ForeignKey, Enum, Integer, String, DateTime, Unicode
from sqlalchemy import func
from sqlalchemy.sql import select
from sqlalchemy.schema import Table, Column, MetaData
from migrate import ForeignKeyConstraint
from migrate.changeset.constraint import UniqueConstraint
from designate.openstack.common import timeutils
from designate import utils
from designate.sqlalchemy.types import UUID


RECORD_TYPES = ['A', 'AAAA', 'CNAME', 'MX', 'SRV', 'TXT', 'SPF', 'NS', 'PTR',
                'SSHFP']

meta = MetaData()

recordsets_table = Table(
    'recordsets',
    meta,

    Column('id', UUID(), default=utils.generate_uuid, primary_key=True),
    Column('created_at', DateTime(), default=timeutils.utcnow),
    Column('updated_at', DateTime(), onupdate=timeutils.utcnow),
    Column('version', Integer(), default=1, nullable=False),

    Column('tenant_id', String(36), default=None, nullable=True),
    Column('domain_id', UUID, ForeignKey('domains.id'), nullable=False),
    Column('name', String(255), nullable=False),
    Column('type', Enum(name='recordset_types', *RECORD_TYPES),
           nullable=False),
    Column('ttl', Integer, default=None, nullable=True),
    Column('description', Unicode(160), nullable=True),

    UniqueConstraint('domain_id', 'name', 'type', name='unique_recordset'),

    mysql_engine='INNODB',
    mysql_charset='utf8')


def _build_hash(recordset_id, record):
    md5 = hashlib.md5()
    md5.update("%s:%s:%s" % (recordset_id, record.data, record.priority))

    return md5.hexdigest()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    records_table = Table('records', meta, autoload=True)

    # We need to autoload the domains table for the FK to succeed.
    Table('domains', meta, autoload=True)

    # Prepare an empty dict to cache (domain_id, name, type) tuples to
    # RRSet id's
    cache = {}

    # Create the recordsets_table table
    recordsets_table.create()

    # NOTE(kiall): Since we need a unique UUID for each recordset, and need
    #              to maintain cross DB compatibility, we're stuck doing this
    #              in code rather than an
    #              INSERT INTO recordsets_table SELECT (..) FROM records;
    results = select(
        columns=[
            records_table.c.tenant_id,
            records_table.c.domain_id,
            records_table.c.name,
            records_table.c.type,
            func.min(records_table.c.ttl).label('ttl'),
            func.min(records_table.c.created_at).label('created_at'),
            func.max(records_table.c.updated_at).label('updated_at')
        ],
        group_by=[
            records_table.c.tenant_id,
            records_table.c.domain_id,
            records_table.c.name,
            records_table.c.type
        ]
    ).execute()

    for result in results:
        # Create the new RecordSet and remember it's id
        pk = recordsets_table.insert().execute(
            tenant_id=result.tenant_id,
            domain_id=result.domain_id,
            name=result.name,
            type=result.type,
            ttl=result.ttl,
            created_at=result.created_at,
            updated_at=result.updated_at
        ).inserted_primary_key[0]

        # Cache the ID for later
        cache_key = "%s.%s.%s" % (result.domain_id, result.name, result.type)
        cache[cache_key] = pk

    # Add the recordset column to the records table
    record_recordset_id = Column('recordset_id', UUID,
                                 default=None,
                                 nullable=True)
    record_recordset_id.create(records_table, populate_default=True)

    # Fetch all the records
    # TODO(kiall): Batch this..
    results = select(
        columns=[
            records_table.c.id,
            records_table.c.domain_id,
            records_table.c.name,
            records_table.c.type,
            records_table.c.data,
            records_table.c.priority
        ]
    ).execute()

    # Update each result with the approperiate recordset_id, and refresh
    # the hash column to reflect the removal of several fields.
    for result in results:
        cache_key = "%s.%s.%s" % (result.domain_id, result.name,
                                  result.type)

        recordset_id = cache[cache_key]
        new_hash = _build_hash(recordset_id, result)

        records_table.update()\
            .where(records_table.c.id == result.id)\
            .values(recordset_id=cache[cache_key], hash=new_hash)\
            .execute()

    # Now that the records.recordset_id field is populated, lets ensure the
    # column is not nullable and is a FK to the records table.
    records_table.c.recordset_id.alter(nullable=False)
    ForeignKeyConstraint(columns=[records_table.c.recordset_id],
                         refcolumns=[recordsets_table.c.id],
                         ondelete='CASCADE',
                         name='fkey_records_recordset_id').create()

    # Finally, drop the now-defunct columns from the records table
    records_table.c.name.drop()
    records_table.c.type.drop()
    records_table.c.ttl.drop()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    raise Exception('There is no undo')
