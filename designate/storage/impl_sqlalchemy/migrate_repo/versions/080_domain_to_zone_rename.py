# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Graham Hayes <graham.hayes@hpe.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# See https://blueprints.launchpad.net/nova/+spec/backportable-db-migrations
# http://lists.openstack.org/pipermail/openstack-dev/2013-March/006827.html
from sqlalchemy.schema import MetaData, Table, Index
from migrate.changeset.constraint import UniqueConstraint, \
    ForeignKeyConstraint, PathNotFoundError


# This migration removes all references to domain from our Database.
# We rename the domains and domain_attribute tables, and rename any columns
# that had "domain" in the name.as
# There is a follow on patch to recreate the FKs for the newly renamed
# tables as the lib we use doesn't seem to like creating FKs on renamed
# tables until after the migration is complete.

meta = MetaData()


def index_exists(index):
    table = index[1]._get_table()
    cols = sorted([str(x).split('.')[1] for x in index[1:]])

    for idx in table.indexes:
        if sorted(idx.columns.keys()) == cols:
            return True
    return False


def drop_index(index):
    if index_exists(index):
        index = Index(*index)
        index.drop()


def drop_foreign_key(fk_def):

    table = fk_def[0]._get_table()

    col = fk_def[0]
    ref_col = fk_def[1]

    # Use .copy() to avoid the set changing during the for operation
    for fk in table.foreign_keys.copy():
        # Check if the fk is the one we want
        if fk.column == col and fk.parent == ref_col:

            fkc = ForeignKeyConstraint([fk.column], [fk.parent],
                                       name=fk.constraint.name)
            fkc.drop()
        # Check if the fk is the one we want (sometimes it seems the parent
        # / col is switched
        if fk.parent == col and fk.column == ref_col:

            fkc = ForeignKeyConstraint([fk.parent], [fk.column],
                                       name=fk.constraint.name)
            fkc.drop()


def drop_unique_constraint(uc_def):
    uc = UniqueConstraint(*uc_def[2], table=uc_def[0], name=uc_def[1])
    try:
        uc.drop()
    except PathNotFoundError:
        pass


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    # Get all the tables
    domains_table = Table('domains', meta, autoload=True)
    domain_attrib_table = Table('domain_attributes', meta, autoload=True)
    recordsets_table = Table('recordsets', meta, autoload=True)
    records_table = Table('records', meta, autoload=True)
    ztr_table = Table('zone_transfer_requests', meta, autoload=True)
    zta_table = Table('zone_transfer_accepts', meta, autoload=True)
    zt_table = Table('zone_tasks', meta, autoload=True)

    # Remove the affected FKs
    # Define FKs
    fks = [
        [domains_table.c.id, domains_table.c.parent_domain_id],
        [domain_attrib_table.c.domain_id,
         domains_table.c.id],
        [recordsets_table.c.domain_id, domains_table.c.id],
        [records_table.c.domain_id, domains_table.c.id],
        [ztr_table.c.domain_id, domains_table.c.id],
        [zta_table.c.domain_id, domains_table.c.id]
    ]

    # Drop FKs
    for fk in fks:
        drop_foreign_key(fk)

    # Change the table structures

    # Domains Table changes
    domains_table.c.parent_domain_id.alter(name='parent_zone_id')
    domains_table.rename('zones')

    # Domain Attributes
    domain_attrib_table.c.domain_id.alter(name='zone_id')
    domain_attrib_table.rename('zone_attributes')

    # Recordsets
    recordsets_table.c.domain_id.alter(name='zone_id')
    recordsets_table.c.domain_shard.alter(name='zone_shard')

    # Records
    records_table.c.domain_id.alter(name="zone_id")
    records_table.c.domain_shard.alter(name="zone_shard")

    # Zone Transfer Requests
    ztr_table.c.domain_id.alter(name='zone_id')

    # Zone Transfer Requests
    zta_table.c.domain_id.alter(name='zone_id')

    # Zone Tasks
    zt_table.c.domain_id.alter(name='zone_id')


def downgrade(migration_engine):
    pass
