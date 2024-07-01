# Copyright 2016 Hewlett Packard Enterprise Development Company LP
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

"""add_services

Revision ID: 304d41c3847a
Revises: d04819112169
Create Date: 2022-08-01 16:41:55.139558

"""
from alembic import op
from oslo_utils import uuidutils
import sqlalchemy as sa

from designate.storage.sqlalchemy.alembic import legacy_utils
from designate.storage.sqlalchemy.types import UUID

# revision identifiers, used by Alembic.
revision = '304d41c3847a'
down_revision = 'd04819112169'
branch_labels = None
depends_on = None

SERVICE_STATES = ["UP", "DOWN", "WARNING"]

# Equivalent to legacy sqlalchemy-migrate revision 097_add_services


def upgrade() -> None:
    # Check if the equivalent legacy migration has already run
    if not legacy_utils.is_migration_needed(97):
        return

    metadata = sa.MetaData()

    op.create_table(
        'service_statuses', metadata,
        sa.Column('id', UUID,
                  default=uuidutils.generate_uuid, primary_key=True),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('service_name', sa.String(40), nullable=False),
        sa.Column('hostname', sa.String(255), nullable=False),
        sa.Column('heartbeated_at', sa.DateTime, nullable=True),
        sa.Column('status', sa.Enum(name='service_statuses_enum',
                                    *SERVICE_STATES), nullable=False),
        sa.Column('stats', sa.Text, nullable=False),
        sa.Column('capabilities', sa.Text, nullable=False),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )
