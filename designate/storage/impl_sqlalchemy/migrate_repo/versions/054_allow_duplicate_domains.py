# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hp.com>
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
from migrate.changeset.constraint import UniqueConstraint

meta = MetaData()

CONSTRAINT_NAME = "unique_domain_name"


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    # Load the database tables
    domains_table = Table('domains', meta, autoload=True)

    constraint = UniqueConstraint('name', 'deleted',
                                  name=CONSTRAINT_NAME,
                                  table=domains_table)
    constraint.drop()

    constraint = UniqueConstraint('name', 'deleted', 'pool_id',
                                  name=CONSTRAINT_NAME,
                                  table=domains_table)
    constraint.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    domains_table = Table('domains', meta, autoload=True)

    constraint = UniqueConstraint('name', 'deleted', 'pool_id',
                                  name=CONSTRAINT_NAME,
                                  table=domains_table)
    constraint.drop()

    constraint = UniqueConstraint('name', 'deleted',
                                  name=CONSTRAINT_NAME,
                                  table=domains_table)
    constraint.create()
