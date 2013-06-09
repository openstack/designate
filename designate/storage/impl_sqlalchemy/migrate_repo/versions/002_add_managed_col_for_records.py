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
from sqlalchemy import MetaData, Table, Column, Boolean, Unicode
from designate.sqlalchemy.types import UUID

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    records_table = Table('records', meta, autoload=True)

    managed_resource = Column('managed_resource', Boolean(), default=False)
    managed_resource.create(records_table, populate_default=True)

    managed_resource_type = Column('managed_resource_type', Unicode(50),
                                   default=None, nullable=True)
    managed_resource_type.create(records_table, populate_default=True)

    managed_resource_id = Column('managed_resource_id', UUID(), default=None,
                                 nullable=True)
    managed_resource_id.create(records_table, populate_default=True)


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    records_table = Table('records', meta, autoload=True)

    managed_resource_id = Column('managed_resource_id', UUID(), default=None,
                                 nullable=True)
    managed_resource_id.drop(records_table)

    managed_resource_type = Column('managed_resource_type', Unicode(50),
                                   default=None, nullable=True)
    managed_resource_type.drop(records_table)

    managed_resource = Column('managed_resource', Boolean(), default=False)
    managed_resource.drop(records_table)
