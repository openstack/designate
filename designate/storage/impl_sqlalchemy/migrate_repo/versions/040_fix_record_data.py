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
from sqlalchemy import Text
from sqlalchemy.schema import Table, MetaData


meta = MetaData()


# No downgrade possible - MySQL may have performed an implicit conversion from
# text -> mediumtext depending on the particular deployments server-wide
# default charset during migration 21's conversion to utf-8.


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    if migrate_engine.name == "mysql":
        records_table = Table('records', meta, autoload=True)
        records_table.c.data.alter(type=Text())


def downgrade(migrate_engine):
    pass
