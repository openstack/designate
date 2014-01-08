# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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
        records_table = Table('records', meta, autoload=True)

        # Add missing unique index
        constraint = UniqueConstraint('hash',
                                      name='unique_recordset',
                                      table=records_table)
        constraint.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    dialect = migrate_engine.url.get_dialect().name

    if dialect.startswith('sqlite'):
        records_table = Table('records', meta, autoload=True)

        # Drop the unique index
        constraint = UniqueConstraint('hash',
                                      name='unique_recordset',
                                      table=records_table)
        constraint.drop()
