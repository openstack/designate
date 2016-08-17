# Copyright 2016 Rackspace
#
# Author: James Li <james.li@rackspace.com>
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
#

from oslo_log import log as logging
from sqlalchemy.schema import MetaData, Table, Index

LOG = logging.getLogger(__name__)
meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    recordsets_table = Table('recordsets', meta, autoload=True)

    Index('rrset_updated_at', recordsets_table.c.updated_at
          ).create(migrate_engine)
    Index('rrset_zoneid', recordsets_table.c.zone_id
          ).create(migrate_engine)
    Index('rrset_type', recordsets_table.c.type).create(migrate_engine)
    Index('rrset_ttl', recordsets_table.c.ttl).create(migrate_engine)
    Index('rrset_tenant_id', recordsets_table.c.tenant_id
          ).create(migrate_engine)
