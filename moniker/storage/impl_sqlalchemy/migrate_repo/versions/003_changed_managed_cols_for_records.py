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
from sqlalchemy import MetaData, Table, Column, Unicode

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    records_table = Table('records', meta, autoload=True)

    records_table.c.managed_resource.alter(name='managed')

    managed_plugin_name = Column('managed_plugin_name', Unicode(50))
    managed_plugin_name.create(records_table, populate_default=True)

    managed_plugin_type = Column('managed_plugin_type', Unicode(50))
    managed_plugin_type.create(records_table, populate_default=True)


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    records_table = Table('records', meta, autoload=True)

    records_table.c.managed.alter(name='managed_resource')

    managed_plugin_name = Column('managed_resource_name', Unicode(50))
    managed_plugin_name.drop(records_table)

    managed_plugin_type = Column('managed_resource_type', Unicode(50))
    managed_plugin_type.drop(records_table)
