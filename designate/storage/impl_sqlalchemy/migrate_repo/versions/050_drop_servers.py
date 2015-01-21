# Copyright (c) 2015 Rackspace Hosting
#
# Author: Betsy Luzader <betsy.luzader@rackspace.com>
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


from sqlalchemy.schema import Table, MetaData

meta = MetaData()

# No downgrade is possible because once the table is dropped, because there is
# no way to recreate the table with the original data. All data was migrated
# to the PoolAttributes table in the previous migration, however a database
# backup should still be done before the migration


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    # Load the database tables
    servers_table = Table('servers', meta, autoload=True)
    servers_table.drop()


def downgrade(migrate_engine):
    pass