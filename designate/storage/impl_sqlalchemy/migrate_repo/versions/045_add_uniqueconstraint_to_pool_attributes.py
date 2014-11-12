# Copyright (c) 2014 Rackspace Hosting
#
# Author: Betsy Luzader <betsy.luzader@rackspace.com>
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

from sqlalchemy.schema import Table, MetaData
from migrate.changeset.constraint import UniqueConstraint, ForeignKeyConstraint

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    pool_attributes_table = Table('pool_attributes', meta, autoload=True)

    # Create UniqueConstraint
    constraint = UniqueConstraint('pool_id', 'key', 'value',
                                  name='unique_pool_attribute',
                                  table=pool_attributes_table)

    constraint.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    pool_attributes_table = Table('pool_attributes', meta, autoload=True)
    # pools = Table('pools', meta, autoload=True)

    constraint = UniqueConstraint('pool_id', 'key', 'value',
                                  name='unique_pool_attribute',
                                  table=pool_attributes_table)

    fk_constraint = ForeignKeyConstraint(columns=['pool_id'],
                                         refcolumns=['pools.id'],
                                         ondelete='CASCADE',
                                         table=pool_attributes_table)

    # First have to drop the ForeignKeyConstraint
    fk_constraint.drop()

    # Then drop the UniqueConstraint
    constraint.drop()

    # Then recreate the ForeignKeyConstraint
    fk_constraint.create()
