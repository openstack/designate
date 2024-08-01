# Copyright 2015 Hewlett-Packard Development Company, L.P.
# Copyright 2022 Red Hat
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""add_zone_attributes

Revision ID: 0bcf910ea823
Revises: a69b45715cc1
Create Date: 2022-07-29 21:36:15.117658

"""
from alembic import op
from oslo_utils import timeutils
from oslo_utils import uuidutils
import sqlalchemy as sa

from designate.storage.sqlalchemy.alembic import legacy_utils
from designate.storage.sqlalchemy.types import UUID
from designate import utils

# revision identifiers, used by Alembic.
revision = '0bcf910ea823'
down_revision = 'a69b45715cc1'
branch_labels = None
depends_on = None

# Equivalent to legacy sqlalchemy-migrate revision 085_add_zone_attributes

# Note from original migration file:
# Move zone masters to their own table, and allow for abstract keys in the
# attributes table


def upgrade() -> None:
    # Check if the equivalent legacy migration has already run
    if not legacy_utils.is_migration_needed(85):
        return

    metadata = sa.MetaData()

    zone_masters_table = op.create_table(
        'zone_masters', metadata,
        sa.Column('id', UUID,
                  default=uuidutils.generate_uuid, primary_key=True),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime,
                  default=lambda: timeutils.utcnow()),
        sa.Column('updated_at', sa.DateTime,
                  onupdate=lambda: timeutils.utcnow()),
        sa.Column('host', sa.String(32), nullable=False),
        sa.Column('port', sa.Integer, nullable=False),
        sa.Column('zone_id', UUID, nullable=False),
        sa.UniqueConstraint('host', 'port', 'zone_id', name='unique_masters'),
        sa.ForeignKeyConstraint(['zone_id'], ['zones.id'], ondelete='CASCADE'),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )

    zone_attr_sql = sa.text(
        'SELECT id, version, created_at, updated_at, value, zone_id FROM '
        'zone_attributes WHERE \'key\' = \'master\';')

    masters = op.get_bind().execute(zone_attr_sql).fetchall()

    masters_input = []

    for master in masters:
        host, port = utils.split_host_port(
            master['value'])
        masters_input.append({
            'id': master['id'],
            'version': master['version'],
            'created_at': master['created_at'],
            'updated_at': master['updated_at'],
            'zone_id': master['zone_id'],
            'host': host,
            'port': port
        })

    op.bulk_insert(zone_masters_table, masters_input)

    master_delete_sql = sa.text(
        'DELETE FROM zone_attributes WHERE \'key\' = \'master\';')

    op.get_bind().execute(master_delete_sql)

    with op.batch_alter_table('zone_attributes') as batch_op:
        batch_op.alter_column('key', type_=sa.String(50),
                              existing_type=sa.Enum)
