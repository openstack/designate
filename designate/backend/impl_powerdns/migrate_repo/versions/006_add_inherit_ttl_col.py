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
from oslo_log import log as logging
from sqlalchemy import MetaData, Table, Column, Boolean

from designate.i18n import _LW


LOG = logging.getLogger(__name__)
meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    records_table = Table('records', meta, autoload=True)

    # Create the new inherit_ttl column
    inherit_ttl = Column('inherit_ttl', Boolean(), default=True)
    inherit_ttl.create(records_table)

    # Semi-Populate the new inherit_ttl column. We'll need to do a cross-db
    # join from powerdns.records -> powerdns.domains -> designate.domains, so
    # we can't perform the second half here.
    query = records_table.update().values(inherit_ttl=False)
    query = query.where(records_table.c.ttl is not None)
    query.execute()

    # If there are records without an explicity configured TTL, we'll need
    # a manual post-migration step.
    query = records_table.select()
    query = query.where(records_table.c.ttl is None)
    c = query.count()

    if c > 0:
        pmq = ('UPDATE powerdns.records JOIN powerdns.domains ON powerdns.reco'
               'rds.domain_id = powerdns.domains.id JOIN designate.domains ON '
               'powerdns.domains.designate_id = designate.domains.id SET power'
               'dns.records.ttl = designate.domains.ttl WHERE powerdns.records'
               '.inherit_ttl = 1;')

        LOG.warning(_LW('**** A manual post-migration step is required ****'))
        LOG.warning(_LW('Please issue this query: %s') % pmq)


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    records_table = Table('records', meta, autoload=True)
    records_table.c.inherit_ttl.drop()
