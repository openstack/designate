# Copyright 2016 Hewlett Packard Enterprise Development Company LP
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

"""
Switch managed_* column types from Unicode to String
Bug #276448
"""

from oslo_log import log as logging
from sqlalchemy.schema import MetaData, Table
from sqlalchemy import String

LOG = logging.getLogger()
meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    records = Table('records', meta, autoload=True)

    records.columns.managed_extra.alter(type=String(100))
    records.columns.managed_plugin_type.alter(type=String(50))
    records.columns.managed_plugin_name.alter(type=String(50))
    records.columns.managed_resource_type.alter(type=String(50))
    records.columns.managed_resource_region.alter(type=String(100))
    records.columns.managed_tenant_id.alter(type=String(36))
