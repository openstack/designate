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

"""Add catalog zones

Revision ID: 9099de8ae11c
Revises: a005af3aa38e
Create Date: 2023-05-15 09:30:11.476307

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9099de8ae11c'
down_revision = 'a005af3aa38e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    ZONE_TYPES = ['PRIMARY', 'SECONDARY', 'CATALOG']

    with op.batch_alter_table('zones') as batch_op:
        batch_op.alter_column('type', type_=sa.Enum(name='type',
                                                    *ZONE_TYPES),
                              existing_type=sa.Enum, existing_nullable=False)
