#    Copyright 2022 Red Hat
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

"""unique_service_status

Revision ID: 93a00a815f07
Revises: 7977deaa5167
Create Date: 2022-08-01 17:17:44.572964

"""
import sys

from alembic import op
from oslo_log import log as logging
import sqlalchemy as sa

from designate.storage.sqlalchemy.alembic import legacy_utils

# revision identifiers, used by Alembic.
revision = '93a00a815f07'
down_revision = '7977deaa5167'
branch_labels = None
depends_on = None

LOG = logging.getLogger()

# Equivalent to legacy sqlalchemy-migrate revision 100_unique_service_status

EXPLANATION = """
You need to manually remove duplicate entries from the database.

The error message was:
%s
"""


def upgrade() -> None:
    # Check if the equivalent legacy migration has already run
    if not legacy_utils.is_migration_needed(100):
        return

    try:
        with op.batch_alter_table('service_statuses') as batch_op:
            batch_op.create_unique_constraint('unique_service_status',
                                              ['service_name', 'hostname'])
    except sa.exc.IntegrityError as e:
        LOG.error(EXPLANATION, e)
        # Use sys.exit so we don't blow up with a huge trace
        sys.exit(1)
