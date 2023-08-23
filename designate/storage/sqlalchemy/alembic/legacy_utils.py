# Copyright 2022 Red Hat
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

from alembic import op
from oslo_log import log as logging
import sqlalchemy as sa

LOG = logging.getLogger(__name__)


def is_migration_needed(equivalent_revision):
    metadata = sa.MetaData()
    metadata.reflect(bind=op.get_bind())

    if 'migrate_version' not in metadata.tables.keys():
        return True

    version_sql = sa.text("SELECT version FROM migrate_version;")
    legacy_db_rev = None
    try:
        legacy_db_rev = op.get_bind().execute(version_sql).scalar_one_or_none()
    except Exception as e:
        LOG.debug("Unable to query the database for the legacy revision "
                  "number. Assuming there is no legacy migration revision "
                  "or the migration is running in offline mode. Error: %s",
                  str(e))

    # Check if this migration was already run by the legacy sqlalchemy-migrate
    # migrations.
    if legacy_db_rev and int(legacy_db_rev) >= equivalent_revision:
        return False
    return True
