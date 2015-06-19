# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hp.com>
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
from oslo_log import log as logging
from sqlalchemy import Column, MetaData, Table, SmallInteger
from sqlalchemy.sql import select, update

from designate import i18n

LOG = logging.getLogger(__name__)

meta = MetaData()


def _add_shards(engine, table, dst_col, src_col):
    dialect = engine.url.get_dialect().name
    if dialect.startswith('mysql'):
        sql = "UPDATE %s SET %s = CONV(SUBSTR(%s, 1, 3), 16, 10)"
        engine.execute(sql % (table.name, dst_col.name, src_col.name))
    elif dialect.startswith('postgres'):
        sql = "UPDATE %s SET %s = ('x'||lpad(substr(%s::text, 1, 3), 8, '0')"\
            ")::bit(32)::int"
        engine.execute(sql % (table.name, dst_col.name, src_col.name))
    else:
        rows = select(columns=[table.c.id]).execute().fetchall()
        for r in rows:
            shard = int(r.id[0:3], 16)
            values = {dst_col.name: shard}
            update(table).where(table.id == r.id).values(values)


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    domains_table = Table('domains', meta, autoload=True)
    recordsets_table = Table('recordsets', meta, autoload=True)
    records_table = Table('records', meta, autoload=True)

    domains_shard_col = Column('shard', SmallInteger(), nullable=True)
    domains_shard_col.create(domains_table)

    recordset_domain_shard_col = Column('domain_shard', SmallInteger(),
                                        nullable=True)
    recordset_domain_shard_col.create(recordsets_table)

    records_domain_shard_col = Column('domain_shard', SmallInteger(),
                                      nullable=True)
    records_domain_shard_col.create(records_table)

    def _set_default():
        _add_shards(
            migrate_engine,
            domains_table,
            domains_shard_col,
            domains_table.c.id)
        _add_shards(
            migrate_engine,
            recordsets_table,
            recordset_domain_shard_col,
            recordsets_table.c.domain_id)
        _add_shards(
            migrate_engine,
            records_table,
            records_domain_shard_col,
            records_table.c.domain_id)

    def _set_nullable():
        domains_table.c.shard.alter(nullable=False)
        recordsets_table.c.domain_shard.alter(nullable=False)
        records_table.c.domain_shard.alter(nullable=False)

    for i in range(0, 5):
        try:
            _set_default()
            _set_nullable()
        except Exception as e:
            # The population default & enforcement of nullable=False failed,
            # try again
            msg = i18n._LW(
                "Updating migration for sharding failed, retrying.")
            LOG.warn(msg)
            if i >= 4:
                # Raise if we've reached max attempts causing migration to
                # fail
                raise e
            else:
                continue
        # It was successful, no exception so we break the loop.
        break
