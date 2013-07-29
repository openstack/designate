# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Patrick Galbraith <patg@hp.com>
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
import logging
from sqlalchemy import MetaData, Table
from migrate.changeset.constraint import UniqueConstraint

LOG = logging.getLogger(__name__)
meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    dialect = migrate_engine.url.get_dialect().name

    if dialect.startswith('sqlite'):
        domains_table = Table('domains', meta, autoload=True)
        servers_table = Table('servers', meta, autoload=True)

        # Add missing multi-column unique index
        constraint = UniqueConstraint('name', 'deleted',
                                      name='unique_domain_name',
                                      table=domains_table)
        constraint.create()

        # Add a missing unique index
        constraint = UniqueConstraint('name',
                                      name='unique_server_name',
                                      table=servers_table)
        constraint.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    dialect = migrate_engine.url.get_dialect().name

    if dialect.startswith('sqlite'):
        domains_table = Table('domains', meta, autoload=True)
        servers_table = Table('servers', meta, autoload=True)

        # Add a new multi-column unique index
        constraint = UniqueConstraint('name', 'deleted',
                                      name='unique_domain_name',
                                      table=domains_table)
        constraint.drop()

        # Add a missing unique index
        constraint = UniqueConstraint('name',
                                      name='unique_server_name',
                                      table=servers_table)
        constraint.drop()
