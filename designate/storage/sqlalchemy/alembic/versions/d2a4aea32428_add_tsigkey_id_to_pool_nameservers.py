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

"""add tsigkey_id to pool_nameservers

Revision ID: d2a4aea32428
Revises: f828412479ee
Create Date: 2026-02-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

from designate.storage.sqlalchemy.types import UUID


# revision identifiers, used by Alembic.
revision = 'd2a4aea32428'
down_revision = 'f828412479ee'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'pool_nameservers',
        sa.Column('tsigkey_id', UUID, nullable=True)
    )
