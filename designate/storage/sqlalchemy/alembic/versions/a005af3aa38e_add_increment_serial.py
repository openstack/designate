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

"""Add increment serial

Revision ID: a005af3aa38e
Revises: b20189fd288e
Create Date: 2023-01-21 17:39:00.822775

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a005af3aa38e'
down_revision = 'b20189fd288e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'zones',
        sa.Column('increment_serial', sa.Boolean, default=False)
    )
    op.create_index(
        'increment_serial', 'zones', ['increment_serial']
    )
