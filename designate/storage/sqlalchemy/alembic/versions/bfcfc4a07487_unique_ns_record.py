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

"""unique_ns_record

Revision ID: bfcfc4a07487
Revises: d9a1883e93e9
Create Date: 2022-07-29 21:05:19.276173

"""
import sys

from alembic import op
from oslo_log import log as logging
import sqlalchemy as sa

from designate.storage.sqlalchemy.alembic import legacy_utils

# revision identifiers, used by Alembic.
revision = 'bfcfc4a07487'
down_revision = 'd9a1883e93e9'
branch_labels = None
depends_on = None

LOG = logging.getLogger()

# Equivalent to legacy sqlalchemy-migrate revision 082_unique_ns_record

# Note from the original migration script:
# Add Unique constraint on ('pool_id', 'hostname') in the pool_ns_records
# table Bug #1517389

EXPLANATION = """
You need to manually remove duplicate entries from the database.

The error message was:
%s
"""


def upgrade() -> None:
    # Check if the equivalent legacy migration has already run
    if not legacy_utils.is_migration_needed(82):
        return

    try:
        with op.batch_alter_table('pool_ns_records') as batch_op:
            batch_op.create_unique_constraint('unique_ns_name',
                                              ['pool_id', 'hostname'])
    except sa.exc.IntegrityError as e:
        LOG.error(EXPLANATION, e)
        # Use sys.exit so we don't blow up with a huge trace
        sys.exit(1)
