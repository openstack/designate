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
"""Add Unique constraint on ('service_name', 'hostname') in the
service_statuses table for bug #1768824"""

import sys

from migrate.changeset.constraint import UniqueConstraint
from oslo_log import log as logging
from sqlalchemy import exc
from sqlalchemy.schema import MetaData
from sqlalchemy.schema import Table

LOG = logging.getLogger()
EXPLANATION = """
You need to manually remove duplicate entries from the database.

The error message was:
%s
"""


def upgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
    service_statuses_table = Table('service_statuses', meta, autoload=True)

    # Add UniqueConstraint based on service_name and hostname.
    constraint = UniqueConstraint('service_name', 'hostname',
                                  table=service_statuses_table,
                                  name="unique_service_status")
    try:
        constraint.create()
    except exc.IntegrityError as e:
        LOG.error(EXPLANATION, e)
        # Use sys.exit so we don't blow up with a huge trace
        sys.exit(1)
