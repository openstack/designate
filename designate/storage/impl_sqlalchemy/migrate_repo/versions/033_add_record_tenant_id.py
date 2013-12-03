# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
from designate.openstack.common import log as logging
from sqlalchemy import MetaData, Table, Column, String
from sqlalchemy.sql import select

LOG = logging.getLogger(__name__)
meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    domains_table = Table('domains', meta, autoload=True)
    records_table = Table('records', meta, autoload=True)

    # Add the tenant_id column
    tenant_id = Column('tenant_id', String(36), default=None, nullable=True)
    tenant_id.create(records_table, populate_default=True)

    # Populate the tenant_id column
    inner_select = select([domains_table.c.tenant_id])\
        .where(domains_table.c.id == records_table.c.domain_id)\
        .as_scalar()

    records_table.update()\
        .values(name=inner_select)\
        .execute()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    records_table = Table('records', meta, autoload=True)

    # Drop the tenant_id column
    records_table.c.tenant_id.drop()
