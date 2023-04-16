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

"""add_FKs

Revision ID: d9a1883e93e9
Revises: 867a331ce1fc
Create Date: 2022-07-29 20:41:51.855014

"""
from alembic import op

from designate.storage.sqlalchemy.alembic import legacy_utils

# revision identifiers, used by Alembic.
revision = 'd9a1883e93e9'
down_revision = '867a331ce1fc'
branch_labels = None
depends_on = None

# Equivalent to legacy sqlalchemy-migrate revision 081_add_FKs


def upgrade() -> None:
    # Check if the equivalent legacy migration has already run
    if not legacy_utils.is_migration_needed(81):
        return

    # We must use batch mode because the unit tests use sqlite
    with op.batch_alter_table('zones') as batch_op:
        batch_op.create_foreign_key('fk_zones_id_parent_zone_id', 'zones',
                                    ['parent_zone_id'], ['id'],
                                    ondelete='SET NULL')
    with op.batch_alter_table('zone_attributes') as batch_op:
        batch_op.create_foreign_key('fk_zone_attributes_zones_id_zone_id',
                                    'zones', ['zone_id'], ['id'],
                                    ondelete='CASCADE')
    with op.batch_alter_table('recordsets') as batch_op:
        batch_op.create_foreign_key('fk_recordsets_zones_id_zone_id', 'zones',
                                    ['zone_id'], ['id'], ondelete='CASCADE')
    with op.batch_alter_table('records') as batch_op:
        batch_op.create_foreign_key('fk_records_zones_id_zone_id', 'zones',
                                    ['zone_id'], ['id'], ondelete='CASCADE')
    with op.batch_alter_table('zone_transfer_requests') as batch_op:
        batch_op.create_foreign_key('fk_ztr_zones_id_zone_id', 'zones',
                                    ['zone_id'], ['id'], ondelete='CASCADE')
    with op.batch_alter_table('zone_transfer_accepts') as batch_op:
        batch_op.create_foreign_key('fk_zta_zones_id_zone_id', 'zones',
                                    ['zone_id'], ['id'], ondelete='CASCADE')
    with op.batch_alter_table('zone_tasks') as batch_op:
        batch_op.create_foreign_key('fk_zone_tasks_zones_id_zone_id', 'zones',
                                    ['zone_id'], ['id'], ondelete='CASCADE')
