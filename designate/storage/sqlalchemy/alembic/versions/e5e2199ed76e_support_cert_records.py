# Copyright 2021 Cloudification GmbH
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

"""support_cert_records

Revision ID: e5e2199ed76e
Revises: 91eb1eb7c882
Create Date: 2022-08-01 17:34:45.569101

"""
from alembic import op
import sqlalchemy as sa

from designate.storage.sqlalchemy.alembic import legacy_utils

# revision identifiers, used by Alembic.
revision = 'e5e2199ed76e'
down_revision = '91eb1eb7c882'
branch_labels = None
depends_on = None

# Equivalent to legacy sqlalchemy-migrate revision 103_support_cert_records


def upgrade() -> None:
    # Check if the equivalent legacy migration has already run
    if not legacy_utils.is_migration_needed(103):
        return

    RECORD_TYPES = ['A', 'AAAA', 'CNAME', 'MX', 'SRV', 'TXT', 'SPF', 'NS',
                    'PTR', 'SSHFP', 'SOA', 'NAPTR', 'CAA', 'CERT']

    with op.batch_alter_table('recordsets') as batch_op:
        batch_op.alter_column('type', type_=sa.Enum(name='record_types',
                                                    *RECORD_TYPES),
                              existing_type=sa.Enum, existing_nullable=False)
