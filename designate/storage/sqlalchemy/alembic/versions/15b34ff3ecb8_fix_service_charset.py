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

"""fix_service_charset

Revision ID: 15b34ff3ecb8
Revises: 304d41c3847a
Create Date: 2022-08-01 16:53:34.612019

"""
from alembic import op

from designate.storage.sqlalchemy.alembic import legacy_utils

# revision identifiers, used by Alembic.
revision = '15b34ff3ecb8'
down_revision = '304d41c3847a'
branch_labels = None
depends_on = None

# Equivalent to legacy sqlalchemy-migrate revision 098_fix_service_charset


def upgrade() -> None:
    # Check if the equivalent legacy migration has already run
    if not legacy_utils.is_migration_needed(98):
        return

    current_bind = op.get_bind()
    if current_bind.dialect.name != 'mysql':
        return

    op.execute('SET foreign_key_checks = 0;')
    op.execute('ALTER TABLE service_statuses CONVERT TO CHARACTER SET utf8;')
    op.execute('SET foreign_key_checks = 1;')
    op.execute('ALTER DATABASE DEFAULT CHARACTER SET utf8;')
