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

"""domain_to_zone_rename

Revision ID: 867a331ce1fc
Revises: c9f427f7180a
Create Date: 2022-07-29 18:41:19.427853

"""
from alembic import op
import sqlalchemy as sa

from designate.storage.sqlalchemy.alembic import legacy_utils
from designate.storage.sqlalchemy.types import UUID

# revision identifiers, used by Alembic.
revision = '867a331ce1fc'
down_revision = 'c9f427f7180a'
branch_labels = None
depends_on = None

# Equivalent to legacy sqlalchemy-migrate revision 080_domain_to_zone_rename

# Notes from the original migration file:
# This migration removes all references to domain from our Database.
# We rename the domains and domain_attribute tables, and rename any columns
# that had "domain" in the name.as
# There is a follow on patch to recreate the FKs for the newly renamed
# tables as the lib we use doesn't seem to like creating FKs on renamed
# tables until after the migration is complete.


def _drop_foreign_key(fk_def):

    table = fk_def[0].table

    col = fk_def[0]
    ref_col = fk_def[1]

    # We need a naming convention to find unnamed foreign keys on sqlite
    naming_convention = {
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"}

    # Use .copy() to avoid the set changing during the for operation
    # We need to search for the foreign keys as they may be named differently
    # between different dialects (mysql, sqlite, etc.)
    for fk in table.foreign_keys.copy():
        # We must use batch mode because the unit tests use sqlite
        with op.batch_alter_table(
                table.name, naming_convention=naming_convention) as batch_op:

            # Check if the fk is the one we want
            if fk.column == col and fk.parent == ref_col:
                batch_op.drop_constraint(fk.constraint.name,
                                         type_='foreignkey')

            # Check if the fk is the one we want (sometimes it seems the parent
            # / col is switched
            if fk.parent == col and fk.column == ref_col:
                batch_op.drop_constraint(fk.constraint.name,
                                         type_='foreignkey')


def upgrade() -> None:
    # Check if the equivalent legacy migration has already run
    if not legacy_utils.is_migration_needed(80):
        return

    convention = {
        "ix": 'ix_%(column_0_label)s',
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }

    metadata = sa.MetaData(naming_convention=convention)
    metadata.bind = op.get_bind()

    # Get all the tables
    domains_table = sa.Table('domains', metadata,
                             autoload_with=op.get_bind())
    domain_attrib_table = sa.Table('domain_attributes', metadata,
                                   autoload_with=op.get_bind())
    recordsets_table = sa.Table('recordsets', metadata,
                                autoload_with=op.get_bind())
    records_table = sa.Table('records', metadata, autoload_with=op.get_bind())
    ztr_table = sa.Table('zone_transfer_requests', metadata,
                         autoload_with=op.get_bind())
    zta_table = sa.Table('zone_transfer_accepts', metadata,
                         autoload_with=op.get_bind())

    # Remove the affected FKs
    # Define FKs
    fks = [
        [domains_table.c.id, domains_table.c.parent_domain_id],
        [domain_attrib_table.c.domain_id, domains_table.c.id],
        [recordsets_table.c.domain_id, domains_table.c.id],
        [records_table.c.domain_id, domains_table.c.id],
        [ztr_table.c.domain_id, domains_table.c.id],
        [zta_table.c.domain_id, domains_table.c.id]
    ]

    # Drop FKs
    for fk in fks:
        _drop_foreign_key(fk)

    with op.batch_alter_table('domains') as batch_op:
        batch_op.alter_column('parent_domain_id',
                              new_column_name='parent_zone_id',
                              existing_type=UUID)
    op.rename_table('domains', 'zones')

    with op.batch_alter_table('domain_attributes') as batch_op:
        batch_op.alter_column('domain_id', new_column_name='zone_id',
                              existing_type=UUID)
    op.rename_table('domain_attributes', 'zone_attributes')

    with op.batch_alter_table('recordsets') as batch_op:
        batch_op.alter_column('domain_id', new_column_name='zone_id',
                              existing_type=UUID)
        batch_op.alter_column('domain_shard', new_column_name='zone_shard',
                              existing_type=sa.SmallInteger)

    with op.batch_alter_table('records') as batch_op:
        batch_op.alter_column('domain_id', new_column_name='zone_id',
                              existing_type=UUID)
        batch_op.alter_column('domain_shard', new_column_name='zone_shard',
                              existing_type=sa.SmallInteger)

    with op.batch_alter_table('zone_transfer_requests') as batch_op:
        batch_op.alter_column('domain_id', new_column_name='zone_id',
                              existing_type=UUID)

    with op.batch_alter_table('zone_transfer_accepts') as batch_op:
        batch_op.alter_column('domain_id', new_column_name='zone_id',
                              existing_type=UUID)

    with op.batch_alter_table('zone_tasks') as batch_op:
        batch_op.alter_column('domain_id', new_column_name='zone_id',
                              existing_type=UUID)
