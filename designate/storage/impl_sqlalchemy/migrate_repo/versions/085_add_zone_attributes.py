# Copyright 2015 Hewlett-Packard Development Company, L.P.
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

"""Move zone masters to their own table, and allow for abstract keys in the
attributes table"""

from migrate.changeset.constraint import UniqueConstraint
from oslo_log import log as logging
from oslo_utils import timeutils
from sqlalchemy.schema import MetaData, Table, Column, ForeignKeyConstraint
from sqlalchemy import DateTime, Integer, String, select

from designate import utils
from designate.sqlalchemy.types import UUID

LOG = logging.getLogger()

meta = MetaData()

zone_masters_table = Table('zone_masters', meta,
    Column('id', UUID(), default=utils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('host', String(32), nullable=False),
    Column('port', Integer(), nullable=False),
    Column('zone_id', UUID(), nullable=False),

    UniqueConstraint('host', 'port', 'zone_id', name='unique_masters'),
    ForeignKeyConstraint(['zone_id'], ['zones.id'], ondelete='CASCADE'),

    mysql_engine='InnoDB',
    mysql_charset='utf8'
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    zone_attibutes_table = Table('zone_attributes', meta, autoload=True)

    connection = migrate_engine.connect()

    transaction = connection.begin()
    try:

        zone_masters_table.create()

        masters = select(
            [
                zone_attibutes_table.c.id,
                zone_attibutes_table.c.version,
                zone_attibutes_table.c.created_at,
                zone_attibutes_table.c.updated_at,
                zone_attibutes_table.c.value,
                zone_attibutes_table.c.zone_id
            ]
        ).where(
            zone_attibutes_table.c.key == 'master'
        ).execute().fetchall()

        masters_input = []

        for master in masters:
            host, port = utils.split_host_port(
                master[zone_attibutes_table.c.value])
            masters_input.append({
                'id': master[zone_attibutes_table.c.id],
                'version': master[zone_attibutes_table.c.version],
                'created_at': master[zone_attibutes_table.c.created_at],
                'updated_at': master[zone_attibutes_table.c.updated_at],
                'zone_id': master[zone_attibutes_table.c.zone_id],
                'host': host,
                'port': port
            })

        zone_attibutes_table.insert(masters_input)

        zone_attibutes_table.delete().where(
            zone_attibutes_table.c.key == 'master')

        zone_attibutes_table.c.key.alter(type=String(50))
        transaction.commit()
    except Exception:
        transaction.rollback()
        raise
