# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Federico Ceratto <federico.ceratto@hpe.com>
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
# See https://blueprints.launchpad.net/nova/+spec/backportable-db-migrations
# http://lists.openstack.org/pipermail/openstack-dev/2013-March/006827.html

from oslo_log import log as logging
from sqlalchemy import Boolean
from sqlalchemy.schema import Column, MetaData, Table, Index

from designate.i18n import _LI

LOG = logging.getLogger(__name__)
meta = MetaData()


def upgrade(migrate_engine):
    LOG.info(_LI("Adding boolean column delayed_notify to table 'zones'"))
    meta.bind = migrate_engine
    zones_table = Table('zones', meta, autoload=True)
    col = Column('delayed_notify', Boolean(), default=False)
    col.create(zones_table)
    index = Index('delayed_notify', zones_table.c.delayed_notify)
    index.create(migrate_engine)
