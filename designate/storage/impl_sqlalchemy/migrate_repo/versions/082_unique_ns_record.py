# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hpe.com>
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

"""Add Unique constraint on ('pool_id', 'hostname') in the pool_ns_records
table Bug #1517389"""

import sys

from migrate.changeset.constraint import UniqueConstraint
from oslo_log import log as logging
from sqlalchemy.schema import MetaData, Table
from sqlalchemy import exc
from sqlalchemy.engine.reflection import Inspector

LOG = logging.getLogger()

meta = MetaData()

CONSTRAINT_NAME = "unique_ns_name"

explanation = """
You need to manually remove duplicate entries from the database.

The error message was:
%s
"""


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    pool_ns_records_table = Table('pool_ns_records', meta, autoload=True)

    # Only apply it if it's not there (It's been backported to L)
    insp = Inspector.from_engine(migrate_engine)
    unique_constraints = insp.get_unique_constraints('pool_ns_records')
    unique_constraint_names = [i['name'] for i in unique_constraints]

    if CONSTRAINT_NAME not in unique_constraint_names:
        # We define the constraint here if not it shows in the list above.
        constraint = UniqueConstraint('pool_id', 'hostname',
                                      name=CONSTRAINT_NAME,
                                      table=pool_ns_records_table)
        try:
            constraint.create()
        except exc.IntegrityError as e:
            LOG.error(explanation, e)
            # Use sys.exit so we don't blow up with a huge trace
            sys.exit(1)
