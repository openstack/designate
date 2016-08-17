# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2010-2011 OpenStack Foundation.
# Copyright 2012 Justin Santa Barbara
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import six
import sqlalchemy
from sqlalchemy import exc as sqlalchemy_exc
from sqlalchemy import select
from oslo_db.sqlalchemy import utils
from oslo_db import exception as oslo_db_exception
from oslo_db.sqlalchemy.migration_cli import manager
from oslo_log import log

from designate.i18n import _
from designate.i18n import _LW
from designate import exceptions


LOG = log.getLogger(__name__)

RRSET_FILTERING_INDEX = {
    'created_at': 'recordset_created_at',
    'updated_at': 'rrset_updated_at',
    'zone_id': 'rrset_zoneid',
    'name': 'recordset_type_name',
    'type': 'rrset_type',
    'ttl': 'rrset_ttl',
    'tenant_id': 'rrset_tenant_id',
}


def get_migration_manager(repo_path, url, init_version=None):
    migration_config = {
        'migration_repo_path': repo_path,
        'db_url': url,
        'init_version': init_version,
    }
    return manager.MigrationManager(migration_config)


# copy from olso/db/sqlalchemy/utils.py
def paginate_query(query, table, limit, sort_keys, marker=None,
                   sort_dir=None, sort_dirs=None):

    # Add sorting
    query, sort_dirs = sort_query(query, table, sort_keys, sort_dir=sort_dir)

    # Add pagination
    if marker is not None:
        marker_values = []
        for sort_key in sort_keys:
            v = marker[sort_key]
            marker_values.append(v)

        # Build up an array of sort criteria as in the docstring
        criteria_list = []
        for i in range(len(sort_keys)):
            crit_attrs = []
            for j in range(i):
                table_attr = getattr(table.c, sort_keys[j])
                crit_attrs.append((table_attr == marker_values[j]))

            table_attr = getattr(table.c, sort_keys[i])
            if sort_dirs[i] == 'desc':
                crit_attrs.append((table_attr < marker_values[i]))
            else:
                crit_attrs.append((table_attr > marker_values[i]))

            criteria = sqlalchemy.sql.and_(*crit_attrs)
            criteria_list.append(criteria)

        f = sqlalchemy.sql.or_(*criteria_list)
        query = query.where(f)

    if limit is not None:
        query = query.limit(limit)

    return query


def sort_query(query, table, sort_keys, sort_dir=None, sort_dirs=None):

    if 'id' not in sort_keys:
        # TODO(justinsb): If this ever gives a false-positive, check
        # the actual primary key, rather than assuming its id
        LOG.warning(_LW('Id not in sort_keys; is sort_keys unique?'))

    assert(not (sort_dir and sort_dirs))

    # Default the sort direction to ascending
    if sort_dirs is None and sort_dir is None:
        sort_dir = 'asc'

    # Ensure a per-column sort direction
    if sort_dirs is None:
        sort_dirs = [sort_dir for _sort_key in sort_keys]

    assert(len(sort_dirs) == len(sort_keys))

    for current_sort_key, current_sort_dir in \
            six.moves.zip(sort_keys, sort_dirs):
        try:
            sort_dir_func = {
                'asc': sqlalchemy.asc,
                'desc': sqlalchemy.desc,
            }[current_sort_dir]
        except KeyError:
            raise ValueError(_("Unknown sort direction, "
                               "must be 'desc' or 'asc'"))
        try:
            sort_key_attr = getattr(table.c, current_sort_key)
        except AttributeError:
            raise utils.InvalidSortKey()
        query = query.order_by(sort_dir_func(sort_key_attr))

    return query, sort_dirs


def check_marker(table, marker, session):

    marker_query = select([table]).where(table.c.id == marker)

    try:
        marker_resultproxy = session.execute(marker_query)
        marker = marker_resultproxy.fetchone()
        if marker is None:
            raise exceptions.MarkerNotFound(
                'Marker %s could not be found' % marker)
    except oslo_db_exception.DBError as e:
        # Malformed UUIDs return StatementError wrapped in a
        # DBError
        if isinstance(e.inner_exception,
                      sqlalchemy_exc.StatementError):
            raise exceptions.InvalidMarker()
        else:
            raise

    return marker


def get_rrset_index(sort_key):
    rrset_index_hint = None
    index = RRSET_FILTERING_INDEX.get(sort_key)

    if index:
        rrset_index_hint = 'USE INDEX (%s)' % index

    return rrset_index_hint
