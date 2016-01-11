# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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
from sqlalchemy import MetaData, Table
from migrate.changeset.constraint import ForeignKeyConstraint

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    domains_table = Table('domains', meta, autoload=True)

    domainmetadata_table = Table('domainmetadata', meta, autoload=True)
    records_table = Table('records', meta, autoload=True)

    records_fk = ForeignKeyConstraint(
        [records_table.c.domain_id],
        [domains_table.c.id],
        ondelete="CASCADE")

    records_fk.create()

    domainmetadata_fk = ForeignKeyConstraint(
        [domainmetadata_table.c.domain_id],
        [domains_table.c.id],
        ondelete="CASCADE")

    domainmetadata_fk.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    domains_table = Table('domains', meta, autoload=True)

    domainmetadata_table = Table('domainmetadata', meta, autoload=True)
    records_table = Table('records', meta, autoload=True)

    records_fk = ForeignKeyConstraint(
        [records_table.c.domain_id],
        [domains_table.c.id],
        ondelete="CASCADE")
    records_fk.drop()

    domainmetadata_fk = ForeignKeyConstraint(
        [domainmetadata_table.c.domain_id],
        [domains_table.c.id],
        ondelete="CASCADE")
    domainmetadata_fk.drop()
