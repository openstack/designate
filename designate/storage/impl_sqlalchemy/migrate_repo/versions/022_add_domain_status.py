# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Graham Hayes <graham.hayes@hp.com>
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
from sqlalchemy import MetaData, Table, Column, Enum

LOG = logging.getLogger(__name__)
RESOURCE_STATUSES = ['ACTIVE', 'PENDING', 'DELETED']
meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    domains_table = Table('domains', meta, autoload=True)
    records_table = Table('records', meta, autoload=True)

    # Add a domain & record creation status for async backends

    domain_status = Column('status', Enum(name='domain_statuses',
                           *RESOURCE_STATUSES), nullable=False,
                           server_default='ACTIVE', default='ACTIVE')

    record_status = Column('status', Enum(name='record_statuses',
                           *RESOURCE_STATUSES), nullable=False,
                           server_default='ACTIVE', default='ACTIVE')

    domain_status.create(domains_table, populate_default=True)
    record_status.create(records_table, populate_default=True)


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    domains_table = Table('domains', meta, autoload=True)
    records_table = Table('records', meta, autoload=True)

    domains_table.c.status.drop()
    records_table.c.status.drop()
