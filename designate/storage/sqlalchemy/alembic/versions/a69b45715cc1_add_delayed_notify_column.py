# Copyright 2015 Hewlett-Packard Development Company, L.P.
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

"""add_delayed_notify_column

Revision ID: a69b45715cc1
Revises: f9f969f9d85e
Create Date: 2022-07-29 21:30:12.127816

"""
from alembic import op
import sqlalchemy as sa

from designate.storage.sqlalchemy.alembic import legacy_utils

# revision identifiers, used by Alembic.
revision = 'a69b45715cc1'
down_revision = 'f9f969f9d85e'
branch_labels = None
depends_on = None

# Equivalent to legacy sqlalchemy-migrate revision
# 084_add_delayed_notify_column


def upgrade() -> None:
    # Check if the equivalent legacy migration has already run
    if not legacy_utils.is_migration_needed(84):
        return

    op.add_column('zones',
                  sa.Column('delayed_notify', sa.Boolean, default=False))
    op.create_index('delayed_notify', 'zones', ['delayed_notify'])
