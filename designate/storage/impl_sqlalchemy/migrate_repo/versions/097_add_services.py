# Copyright 2016 Hewlett Packard Enterprise Development Company LP
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

"""Add Service Status tables"""


from oslo_log import log as logging
from sqlalchemy import String, DateTime, Enum, Text
from sqlalchemy.schema import Table, Column, MetaData

from designate import utils
from designate.sqlalchemy.types import UUID

LOG = logging.getLogger()

meta = MetaData()

SERVICE_STATES = [
    "UP", "DOWN", "WARNING"
]


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    status_enum = Enum(name='service_statuses_enum', metadata=meta,
                       *SERVICE_STATES)
    status_enum.create(checkfirst=True)

    service_status_table = Table('service_statuses', meta,
        Column('id', UUID(), default=utils.generate_uuid, primary_key=True),
        Column('created_at', DateTime),
        Column('updated_at', DateTime),

        Column('service_name', String(40), nullable=False),
        Column('hostname', String(255), nullable=False),
        Column('heartbeated_at', DateTime, nullable=True),
        Column('status', status_enum, nullable=False),
        Column('stats', Text, nullable=False),
        Column('capabilities', Text, nullable=False),
    )
    service_status_table.create(checkfirst=True)
