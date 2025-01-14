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

"""shared zones dalmatian merge

Revision ID: 018194635d9e
Revises: 9099de8ae11c
Create Date: 2025-01-06 18:20:01.097227

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '018194635d9e'
down_revision = '9099de8ae11c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # CCloud only, Shared Zones were used since years, therefore
    # we need to make old implementation compatible with Dalmatian release
    #op.drop_constraint('unique_shared_zone', 'shared_zones')

    with op.batch_alter_table('shared_zones') as batch_op:
        batch_op.alter_column('tenant_id',
                              existing_type=sa.String(36),
                              existing_nullable=False,
                              new_column_name='project_id')
        batch_op.alter_column('target_tenant_id',
                              existing_type=sa.String(36),
                              existing_nullable=False,
                              new_column_name='target_project_id')

    #op.create_unique_constraint('unique_shared_zone',
    #                            'shared_zones',
    #                            ['zone_id', 'project_id', 'target_project_id'])