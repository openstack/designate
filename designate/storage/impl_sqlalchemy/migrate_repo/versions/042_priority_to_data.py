# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hpe.com>
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

from sqlalchemy.sql import select
from sqlalchemy import Integer
from sqlalchemy.schema import Column, MetaData, Table
from migrate.changeset.constraint import UniqueConstraint


meta = MetaData()


def _build_hash(*args):
    md5 = hashlib.md5()
    md5.update(":".join(args))
    return md5.hexdigest()


def _get_recordsets(table):
    return select(columns=[table.c.id, table.c.type])\
        .where((table.c.type == 'MX') | (table.c.type == 'SRV'))\
        .execute().fetchall()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    rs_table = Table('recordsets', meta, autoload=True)
    records_table = Table('records', meta, autoload=True)

    recordsets = _get_recordsets(rs_table)

    record_cols = [
        records_table.c.id,
        records_table.c.priority,
        records_table.c.data]

    for rs in recordsets:
        query = select(columns=record_cols)\
            .where(records_table.c.recordset_id == rs[0])\
            .where(records_table.c.priority != None)  # noqa
        records = query.execute().fetchall()

        for record in records:
            new_data = '%s %s' % (int(record[1]), record[2])
            # New style hashes are <rs_id>:<data> since prio is baked into data
            new_hash = _build_hash(rs[0], new_data)

            update = records_table.update()\
                .where(records_table.c.id == record[0])\
                .values(data=new_data, hash=new_hash)
            migrate_engine.execute(update)

    records_table.c.priority.drop()

    dialect = migrate_engine.url.get_dialect().name
    if dialect.startswith('sqlite'):
        # Add missing unique index
        constraint = UniqueConstraint('hash',
                                      name='unique_recordset',
                                      table=records_table)
        constraint.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    rs_table = Table('recordsets', meta, autoload=True)
    records_table = Table('records', meta, autoload=True)

    recordsets = _get_recordsets(rs_table)

    col = Column('priority', Integer, default=None, nullable=True)
    col.create(records_table)

    record_cols = [
        records_table.c.id,
        records_table.c.priority,
        records_table.c.data]

    for rs in recordsets:
        records = select(columns=record_cols)\
            .where(records_table.c.recordset_id == rs[0])\
            .execute().fetchall()

        for record in records:
            priority, _, data = record[2].partition(" ")

            # Old style hashes are <rs_id>:<data>:<priority>
            new_hash = _build_hash(rs[0], data, priority)

            update = records_table.update()\
                .where(records_table.c.id == record[0])\
                .values(priority=int(priority), data=data, hash=new_hash)
            update.execute()

    dialect = migrate_engine.url.get_dialect().name
    if dialect.startswith('sqlite'):
        # Add missing unique index
        constraint = UniqueConstraint('hash',
                                      name='unique_recordset',
                                      table=records_table)
        constraint.create()
