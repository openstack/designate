# Copyright 2013 Rackspace Hosting
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
from designate.openstack.common import log as logging
from sqlalchemy import MetaData, Table, Column, Unicode

LOG = logging.getLogger(__name__)
meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    domains_table = Table('domains', meta, autoload=True)
    records_table = Table('records', meta, autoload=True)

    #Add in description columns in domain/record databases
    domain_description = Column('description', Unicode(160),
                                nullable=True)
    domain_description.create(domains_table, populate_default=True)

    record_description = Column('description', Unicode(160),
                                nullable=True)
    record_description.create(records_table, populate_default=True)


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    domains_table = Table('domains', meta, autoload=True)
    domains_table.c.description.drop()

    record_table = Table('records', meta, autoload=True)
    record_table.c.description.drop()
