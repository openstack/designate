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
import hashlib
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import Table, Column, MetaData
from sqlalchemy.types import String
from designate.openstack.common import log as logging

LOG = logging.getLogger(__name__)
meta = MetaData()


def _build_hash(r):
    md5 = hashlib.md5()
    md5.update("%s:%s:%s:%s:%s" % (r.domain_id, r.name, r.type, r.data,
                                   r.priority))
    return md5.hexdigest()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    records_table = Table('records', meta, autoload=True)

    # Add the hash column, start with allowing NULLs
    hash_column = Column('hash', String(32), nullable=True, default=None,
                         unique=True)
    hash_column.create(records_table, unique_name='unique_record')

    sync_domains = []

    # Fill out the hash values. We need to do this in a way that lets us track
    # which domains need to be re-synced, so having the DB do this directly
    # won't work.
    for record in records_table.select().execute():
        try:
            records_table.update()\
                         .where(records_table.c.id == record.id)\
                         .values(hash=_build_hash(record))\
                         .execute()
        except IntegrityError:
            if record.domain_id not in sync_domains:
                sync_domains.append(record.domain_id)
                LOG.warn("Domain '%s' needs to be synchronised" %
                         record.domain_id)

            records_table.delete()\
                         .where(records_table.c.id == record.id)\
                         .execute()

    # Finally, the column should not be nullable.
    records_table.c.hash.alter(nullable=False)


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    records_table = Table('records', meta, autoload=True)

    hash_column = Column('hash', String(32), nullable=False, unique=True)
    hash_column.drop(records_table)
