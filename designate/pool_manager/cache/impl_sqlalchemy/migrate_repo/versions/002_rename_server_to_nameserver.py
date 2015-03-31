# Copyright 2014 eBay Inc.
#
# Author: Ron Rickard <rrickard@ebaysf.com>
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


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    pms_table = Table('pool_manager_statuses', meta, autoload=True)
    pms_table.c.server_id.alter(name='nameserver_id')


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    pms_table = Table('pool_manager_statuses', meta, autoload=True)
    pms_table.c.nameserver_id.alter(name='server_id')
