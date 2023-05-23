# Copyright 2016 Rackspace
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

"""add_rrset_indexes_for_filtering_perf

Revision ID: 7977deaa5167
Revises: 15b34ff3ecb8
Create Date: 2022-08-01 17:13:01.429689

"""
from alembic import op

from designate.storage.sqlalchemy.alembic import legacy_utils

# revision identifiers, used by Alembic.
revision = '7977deaa5167'
down_revision = '15b34ff3ecb8'
branch_labels = None
depends_on = None

# Equivalent to legacy sqlalchemy-migrate revision
# 099_add_rrset_indexes_for_filtering_perf


def upgrade() -> None:
    # Check if the equivalent legacy migration has already run
    if not legacy_utils.is_migration_needed(99):
        return

    op.create_index('rrset_updated_at', 'recordsets', ['updated_at'])
    op.create_index('rrset_zoneid', 'recordsets', ['zone_id'])
    op.create_index('rrset_type', 'recordsets', ['type'])
    op.create_index('rrset_ttl', 'recordsets', ['ttl'])
    op.create_index('rrset_tenant_id', 'recordsets', ['tenant_id'])
