# Copyright (c) 2014 Rackspace Inc.
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
from sqlalchemy import Index, MetaData, Table

meta = MetaData()


def index_exists(index):
    table = index[1]._get_table()
    cols = sorted([str(x).split('.')[1] for x in index[1:]])

    for idx in table.indexes:
        if sorted(idx.columns.keys()) == cols:
            return True
    return False


def upgrade(migrate_engine):

    meta.bind = migrate_engine

    zones_table = Table('domains', meta, autoload=True)
    recordsets_table = Table('recordsets', meta, autoload=True)
    records_table = Table('records', meta, autoload=True)

    indices = [
        ['zone_created_at', zones_table.c.created_at],
        ['recordset_created_at', recordsets_table.c.created_at],
        ['record_created_at', records_table.c.created_at]
    ]

    for ind in indices:
        if not index_exists(ind):
            index = Index(*ind)
            index.create(migrate_engine)
