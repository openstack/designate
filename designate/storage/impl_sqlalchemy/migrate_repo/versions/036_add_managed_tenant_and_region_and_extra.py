# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hp.com>
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
# This is a placeholder for Havana backports.
# Do not use this number for new Icehouse work. New Icehouse work starts after
# all the placeholders.
#
# See https://blueprints.launchpad.net/nova/+spec/backportable-db-migrations
# http://lists.openstack.org/pipermail/openstack-dev/2013-March/006827.html
from designate.openstack.common import log as logging
from sqlalchemy import MetaData, Table, Column, Unicode


LOG = logging.getLogger(__name__)
meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    records_table = Table('records', meta, autoload=True)
    record_managed_tenant_id = Column(
        'managed_tenant_id', Unicode(36), default=None, nullable=True)
    record_managed_tenant_id.create(records_table, populate_default=True)

    record_managed_resource_region = Column(
        'managed_resource_region', Unicode(100), default=None, nullable=True)
    record_managed_resource_region.create(records_table, populate_default=True)

    record_managed_extra = Column(
        'managed_extra', Unicode(100), default=None, nullable=True)
    record_managed_extra.create(records_table, populate_default=True)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    records_table = Table('records', meta, autoload=True)

    record_managed_tenant_id = Column(
        'managed_tenant_id', Unicode(36), default=None, nullable=True)
    record_managed_tenant_id.drop(records_table)

    record_managed_resource_region = Column(
        'managed_resource_region', Unicode(100), default=None, nullable=True)
    record_managed_resource_region.drop(records_table)

    record_extra = Column(
        'managed_extra', Unicode(100), default=None, nullable=True)
    record_extra.drop(records_table)
