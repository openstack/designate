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
from designate.openstack.common import timeutils
from designate.openstack.common import log as logging
from sqlalchemy import MetaData, Table, Column, Integer

LOG = logging.getLogger(__name__)
meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    domains_table = Table('domains', meta, autoload=True)

    serial = Column('serial', Integer(), default=timeutils.utcnow_ts,
                    nullable=False, server_default="1")
    serial.create(domains_table, populate_default=True)

    # Do we have any domains?
    domain_count = domains_table.count().execute().first()[0]

    if domain_count > 0:
        LOG.warn('A sync-domains is now required in order for the API '
                 'provided, and backend provided serial numbers to align')


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    domains_table = Table('domains', meta, autoload=True)
    domains_table.c.serial.drop()
