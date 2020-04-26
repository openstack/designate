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

"""shared_zones

Revision ID: b20189fd288e
Revises: e5e2199ed76e
Create Date: 2022-09-22 20:50:03.056609

"""
from alembic import op
import sqlalchemy as sa

from designate.sqlalchemy.types import UUID
from designate import utils

# revision identifiers, used by Alembic.
revision = 'b20189fd288e'
down_revision = 'e5e2199ed76e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    meta = sa.MetaData()

    op.create_table(
        'shared_zones', meta,
        sa.Column('id', UUID, default=utils.generate_uuid, primary_key=True),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('zone_id', UUID, nullable=False),
        sa.Column('project_id', sa.String(36), nullable=False),
        sa.Column('target_project_id', sa.String(36), nullable=False),

        sa.UniqueConstraint('zone_id', 'project_id', 'target_project_id',
                         name='unique_shared_zone'),
        sa.ForeignKeyConstraint(['zone_id'], ['zones.id'], ondelete='CASCADE'),
    )
