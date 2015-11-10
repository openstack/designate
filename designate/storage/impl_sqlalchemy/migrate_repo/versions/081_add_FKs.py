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

from migrate.changeset.constraint import ForeignKeyConstraint
from sqlalchemy.schema import MetaData, Table

# This migration adds back the FKs removed in migration 80, as sqlalchemy
# migrate seems to need to wait to add FKs to renamed tables.

meta = MetaData()


def upgrade(migrate_engine):

    meta.bind = migrate_engine

    # Get all the tables
    zones_table = Table('zones', meta, autoload=True)
    zone_attrib_table = Table('zone_attributes', meta, autoload=True)
    recordsets_table = Table('recordsets', meta, autoload=True)
    records_table = Table('records', meta, autoload=True)
    ztr_table = Table('zone_transfer_requests', meta, autoload=True)
    zta_table = Table('zone_transfer_accepts', meta, autoload=True)
    zt_table = Table('zone_tasks', meta, autoload=True)

    # Create new FKs

    fks = []

    fks.append(ForeignKeyConstraint([zones_table.c.parent_zone_id],
                                    [zones_table.c.id], ondelete='SET NULL'))
    fks.append(ForeignKeyConstraint([zone_attrib_table.c.zone_id],
                                    [zones_table.c.id], ondelete='CASCADE'))
    fks.append(ForeignKeyConstraint([recordsets_table.c.zone_id],
                                    [zones_table.c.id], ondelete='CASCADE'))
    fks.append(ForeignKeyConstraint([records_table.c.zone_id],
                                    [zones_table.c.id], ondelete='CASCADE'))
    fks.append(ForeignKeyConstraint([ztr_table.c.zone_id],
                                    [zones_table.c.id], ondelete='CASCADE'))
    fks.append(ForeignKeyConstraint([zta_table.c.zone_id],
                                    [zones_table.c.id], ondelete='CASCADE'))
    fks.append(ForeignKeyConstraint([zt_table.c.zone_id],
                                    [zones_table.c.id], ondelete='CASCADE'))

    for fk in fks:
        fk.create()


def downgrade(migration_engine):
    pass
