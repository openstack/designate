# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    tsigkeys_table = Table('tsigkeys', meta, autoload=True)
    domains_table = Table('domains', meta, autoload=True)
    records_table = Table('records', meta, autoload=True)

    tsigkeys_table.c.moniker_id.alter(name='designate_id')
    domains_table.c.moniker_id.alter(name='designate_id')
    records_table.c.moniker_id.alter(name='designate_id')


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    tsigkeys_table = Table('tsigkeys', meta, autoload=True)
    domains_table = Table('domains', meta, autoload=True)
    records_table = Table('records', meta, autoload=True)

    tsigkeys_table.c.designate_id.alter(name='moniker_id')
    domains_table.c.designate_id.alter(name='moniker_id')
    records_table.c.designate_id.alter(name='moniker_id')
