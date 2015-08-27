# Copyright 2015 Rackspace Inc.
#
# Author: Tim Simmons <tim.simmons@rackspace.com>
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
from sqlalchemy import Enum, String
from sqlalchemy.schema import Column, MetaData, Table

meta = MetaData()
TASK_TYPES = ['IMPORT', 'EXPORT']


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    dialect = migrate_engine.url.get_dialect().name

    zone_tasks_table = Table('zone_tasks', meta, autoload=True)

    dialect = migrate_engine.url.get_dialect().name

    if dialect.startswith("postgresql"):
        with migrate_engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT")
            conn.execute(
                "ALTER TYPE task_types ADD VALUE 'EXPORT' "
                "AFTER 'IMPORT'")
            conn.close()

    zone_tasks_table.c.task_type.alter(type=Enum(name='task_type',
                                            *TASK_TYPES))

    location = Column('location', String(160), nullable=True)
    location.create(zone_tasks_table)
