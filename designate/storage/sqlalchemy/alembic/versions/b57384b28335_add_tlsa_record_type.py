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

"""add TLSA record type

Revision ID: b57384b28335
Revises: d2a4aea32428
Create Date: 2026-04-05 13:41:33.430641

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b57384b28335'
down_revision = 'd2a4aea32428'
branch_labels = None
depends_on = None


def upgrade() -> None:

    RECORD_TYPES = ['A', 'AAAA', 'CNAME', 'MX', 'SRV', 'TXT', 'SPF', 'NS',
                    'PTR', 'SSHFP', 'SOA', 'NAPTR', 'CAA', 'CERT',
                    'HTTPS', 'SVCB', 'TLSA']

    with op.batch_alter_table('recordsets') as batch_op:
        batch_op.alter_column(
            'type',
            type_=sa.Enum(name='record_types', *RECORD_TYPES),
            existing_type=sa.Enum,
            existing_nullable=False
        )
