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

"""change_managed_column_types

Revision ID: f9f969f9d85e
Revises: bfcfc4a07487
Create Date: 2022-07-29 21:18:35.403634

"""
from alembic import op
import sqlalchemy as sa

from designate.storage.sqlalchemy.alembic import legacy_utils

# revision identifiers, used by Alembic.
revision = 'f9f969f9d85e'
down_revision = 'bfcfc4a07487'
branch_labels = None
depends_on = None

# Equivalent to legacy sqlalchemy-migrate revision
# 083_change_managed_column_types


def upgrade() -> None:
    # Check if the equivalent legacy migration has already run
    if not legacy_utils.is_migration_needed(83):
        return

    with op.batch_alter_table('records') as batch_op:
        batch_op.alter_column('managed_extra', type_=sa.String(100),
                              existing_type=sa.Unicode(100),
                              existing_nullable=True)
        batch_op.alter_column('managed_plugin_type', type_=sa.String(50),
                              existing_type=sa.Unicode(50),
                              existing_nullable=True)
        batch_op.alter_column('managed_plugin_name', type_=sa.String(50),
                              existing_type=sa.Unicode(50),
                              existing_nullable=True)
        batch_op.alter_column('managed_resource_type', type_=sa.String(50),
                              existing_type=sa.Unicode(50),
                              existing_nullable=True)
        batch_op.alter_column('managed_resource_region', type_=sa.String(100),
                              existing_type=sa.Unicode(100),
                              existing_nullable=True)
        batch_op.alter_column('managed_tenant_id', type_=sa.String(36),
                              existing_type=sa.Unicode(36),
                              existing_nullable=True)
