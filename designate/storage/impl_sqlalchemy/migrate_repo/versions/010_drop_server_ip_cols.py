# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
from sqlalchemy import MetaData, Table, Column
from designate.sqlalchemy.types import Inet

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    servers_table = Table('servers', meta, autoload=True)

    servers_table.c.ipv4.drop()
    servers_table.c.ipv6.drop()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    servers_table = Table('servers', meta, autoload=True)

    ipv4 = Column('ipv4', Inet(), nullable=False, unique=True)
    ipv6 = Column('ipv6', Inet(), default=None, unique=True)

    ipv4.create(servers_table, populate_default=True)
    ipv6.create(servers_table, populate_default=True)
