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

"""add stopped service status

Revision ID: f49c4409c8ba
Revises: a005af3aa38e
Create Date: 2023-03-21 12:28:15.381864

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f49c4409c8ba'
down_revision = 'a005af3aa38e'
branch_labels = None
depends_on = None


OLD_SERVICE_STATES = ["UP", "DOWN", "WARNING"]
NEW_SERVICE_STATES = OLD_SERVICE_STATES + ["STOPPED"]


def upgrade():
    with op.batch_alter_table('service_statuses') as batch_op:
        batch_op.alter_column(
            'status',
            type_=sa.Enum(
                name='service_statuses', *NEW_SERVICE_STATES),
            existing_type=sa.Enum(
                name='service_statuses', *OLD_SERVICE_STATES))
