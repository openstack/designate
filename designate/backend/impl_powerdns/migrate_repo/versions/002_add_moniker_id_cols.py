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
from designate.sqlalchemy.types import UUID

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    tsigkeys_table = Table('tsigkeys', meta, autoload=True)
    domains_table = Table('domains', meta, autoload=True)
    records_table = Table('records', meta, autoload=True)

    tsigkeys_designate_id = Column('designate_id', UUID())
    tsigkeys_designate_id.create(tsigkeys_table)

    domains_designate_id = Column('designate_id', UUID())
    domains_designate_id.create(domains_table)

    records_designate_id = Column('designate_id', UUID())
    records_designate_id.create(records_table)


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    tsigkeys_table = Table('tsigkeys', meta, autoload=True)
    domains_table = Table('domains', meta, autoload=True)
    records_table = Table('records', meta, autoload=True)

    tsigkeys_designate_id = Column('designate_id', UUID())
    tsigkeys_designate_id.drop(tsigkeys_table)

    domains_designate_id = Column('designate_id', UUID())
    domains_designate_id.drop(domains_table)

    records_designate_id = Column('designate_id', UUID())
    records_designate_id.drop(records_table)
