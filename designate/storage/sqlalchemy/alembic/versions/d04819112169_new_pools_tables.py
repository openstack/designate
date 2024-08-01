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

"""new_pools_tables

Revision ID: d04819112169
Revises: 0bcf910ea823
Create Date: 2022-08-01 16:20:17.440784

"""
from alembic import op
from oslo_utils import timeutils
from oslo_utils import uuidutils
import sqlalchemy as sa

from designate.storage.sqlalchemy.alembic import legacy_utils
from designate.storage.sqlalchemy.types import UUID

# revision identifiers, used by Alembic.
revision = 'd04819112169'
down_revision = '0bcf910ea823'
branch_labels = None
depends_on = None

# Equivalent to legacy sqlalchemy-migrate revision 086_new_pools_tables


def upgrade() -> None:
    # Check if the equivalent legacy migration has already run
    if not legacy_utils.is_migration_needed(86):
        return

    metadata = sa.MetaData()

    op.create_table(
        'pool_nameservers', metadata,
        sa.Column('id', UUID,
                  default=uuidutils.generate_uuid, primary_key=True),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime,
                  default=lambda: timeutils.utcnow()),
        sa.Column('updated_at', sa.DateTime,
                  onupdate=lambda: timeutils.utcnow()),
        sa.Column('pool_id', UUID, nullable=False),
        sa.Column('host', sa.String(255), nullable=False),
        sa.Column('port', sa.Integer, nullable=False),
        sa.ForeignKeyConstraint(['pool_id'], ['pools.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('pool_id', 'host', 'port',
                            name='unique_pool_host_port'),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )

    op.create_table(
        'pool_targets', metadata,
        sa.Column('id', UUID,
                  default=uuidutils.generate_uuid, primary_key=True),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime,
                  default=lambda: timeutils.utcnow()),
        sa.Column('updated_at', sa.DateTime,
                  onupdate=lambda: timeutils.utcnow()),
        sa.Column('pool_id', UUID, nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('tsigkey_id', UUID, nullable=True),
        sa.Column('description', sa.Unicode(160), nullable=True),
        sa.ForeignKeyConstraint(['pool_id'], ['pools.id'], ondelete='CASCADE'),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )

    op.create_table(
        'pool_target_masters', metadata,
        sa.Column('id', UUID,
                  default=uuidutils.generate_uuid, primary_key=True),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime,
                  default=lambda: timeutils.utcnow()),
        sa.Column('updated_at', sa.DateTime,
                  onupdate=lambda: timeutils.utcnow()),
        sa.Column('pool_target_id', UUID, nullable=False),
        sa.Column('host', sa.String(255), nullable=False),
        sa.Column('port', sa.Integer, nullable=False),
        sa.ForeignKeyConstraint(['pool_target_id'], ['pool_targets.id'],
                                ondelete='CASCADE'),
        sa.UniqueConstraint('pool_target_id', 'host', 'port',
                            name='unique_pool_target_host_port'),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )

    op.create_table(
        'pool_target_options', metadata,
        sa.Column('id', UUID,
                  default=uuidutils.generate_uuid, primary_key=True),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime,
                  default=lambda: timeutils.utcnow()),
        sa.Column('updated_at', sa.DateTime,
                  onupdate=lambda: timeutils.utcnow()),
        sa.Column('pool_target_id', UUID, nullable=False),
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('value', sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(['pool_target_id'], ['pool_targets.id'],
                                ondelete='CASCADE'),
        sa.UniqueConstraint('pool_target_id', 'key',
                            name='unique_pool_target_key'),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )

    op.create_table(
        'pool_also_notifies', metadata,
        sa.Column('id', UUID,
                  default=uuidutils.generate_uuid, primary_key=True),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime,
                  default=lambda: timeutils.utcnow()),
        sa.Column('updated_at', sa.DateTime,
                  onupdate=lambda: timeutils.utcnow()),
        sa.Column('pool_id', UUID, nullable=False),
        sa.Column('host', sa.String(255), nullable=False),
        sa.Column('port', sa.Integer, nullable=False),
        sa.ForeignKeyConstraint(['pool_id'], ['pools.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('pool_id', 'host', 'port',
                            name='unique_pool_also_notifies_pool0host0port'),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )
