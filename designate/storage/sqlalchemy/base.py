# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
import abc
import operator
import threading

from oslo_db import exception as oslo_db_exception
from oslo_db.sqlalchemy import utils as oslodb_utils
from oslo_log import log as logging
from oslo_utils import timeutils
from sqlalchemy import select, or_, between, func, distinct

from designate import exceptions
from designate import objects
from designate.storage import sql
from designate.storage.sqlalchemy import tables
from designate.storage.sqlalchemy import utils


LOG = logging.getLogger(__name__)

RECORDSET_QUERY_TABLES = (
    # RS Info
    tables.recordsets.c.id,                    # 0 - RS ID
    tables.recordsets.c.version,               # 1 - RS Version
    tables.recordsets.c.created_at,            # 2 - RS Created
    tables.recordsets.c.updated_at,            # 3 - RS Updated
    tables.recordsets.c.tenant_id,             # 4 - RS Tenant
    tables.recordsets.c.zone_id,               # 5 - RS Zone
    tables.recordsets.c.name,                  # 6 - RS Name
    tables.recordsets.c.type,                  # 7 - RS Type
    tables.recordsets.c.ttl,                   # 8 - RS TTL
    tables.recordsets.c.description,           # 9 - RS Desc
    # R Info
    tables.records.c.id,                       # 10 - R ID
    tables.records.c.version,                  # 11 - R Version
    tables.records.c.created_at,               # 12 - R Created
    tables.records.c.updated_at,               # 13 - R Updated
    tables.records.c.tenant_id,                # 14 - R Tenant
    tables.records.c.zone_id,                  # 15 - R Zone
    tables.records.c.recordset_id,             # 16 - R RSet
    tables.records.c.data,                     # 17 - R Data
    tables.records.c.description,              # 18 - R Desc
    tables.records.c.hash,                     # 19 - R Hash
    tables.records.c.managed,                  # 20 - R Mngd Flg
    tables.records.c.managed_plugin_name,      # 21 - R Mngd Plg
    tables.records.c.managed_resource_type,    # 22 - R Mngd Type
    tables.records.c.managed_resource_region,  # 23 - R Mngd Rgn
    tables.records.c.managed_resource_id,      # 24 - R Mngd ID
    tables.records.c.managed_tenant_id,        # 25 - R Mngd T ID
    tables.records.c.status,                   # 26 - R Status
    tables.records.c.action,                   # 27 - R Action
    tables.records.c.serial                    # 28 - R Serial
)
RECORDSET_MAP = {
    'id': 0,
    'version': 1,
    'created_at': 2,
    'updated_at': 3,
    'tenant_id': 4,
    'zone_id': 5,
    'name': 6,
    'type': 7,
    'ttl': 8,
    'description': 9,
}
RECORD_MAP = {
    'id': 10,
    'version': 11,
    'created_at': 12,
    'updated_at': 13,
    'tenant_id': 14,
    'zone_id': 15,
    'recordset_id': 16,
    'data': 17,
    'description': 18,
    'hash': 19,
    'managed': 20,
    'managed_plugin_name': 21,
    'managed_resource_type': 22,
    'managed_resource_region': 23,
    'managed_resource_id': 24,
    'managed_tenant_id': 25,
    'status': 26,
    'action': 27,
    'serial': 28,
}


def _set_object_from_model(obj, model):
    """Update a DesignateObject with the values from a SQLA Model"""

    for field_name in obj.FIELDS.keys():
        if hasattr(model, field_name):
            obj[field_name] = getattr(model, field_name)

    obj.obj_reset_changes()
    return obj


def _set_listobject_from_models(obj, models):
    for model in models:
        obj.objects.append(_set_object_from_model(obj.LIST_ITEM_TYPE(), model))

    obj.obj_reset_changes()
    return obj


class SQLAlchemy(metaclass=abc.ABCMeta):

    def __init__(self):
        super().__init__()
        self.local_store = threading.local()

    @staticmethod
    def _apply_criterion(table, query, criterion):
        if criterion is None:
            return query

        for name, value in criterion.items():
            column = getattr(table.c, name)

            if isinstance(value, str):
                # Wildcard value: '%'
                if '%' in value:
                    query = query.where(column.like(value))
                elif value.startswith('!'):
                    query = query.where(column != value[1:])
                elif value.startswith('<='):
                    query = query.where(column <= value[2:])
                elif value.startswith('<'):
                    query = query.where(column < value[1:])
                elif value.startswith('>='):
                    query = query.where(column >= value[2:])
                elif value.startswith('>'):
                    query = query.where(column > value[1:])
                elif value.startswith('BETWEEN'):
                    elements = [i.strip(' ') for i in
                                value.split(' ', 1)[1].strip(' ').split(',')]
                    query = query.where(
                        between(column, elements[0], elements[1])
                    )
                else:
                    query = query.where(column == value)
            elif isinstance(value, list):
                query = query.where(column.in_(value))
            else:
                query = query.where(column == value)

        return query

    def _apply_tenant_criteria(self, context, table, query,
                               include_null_tenant=True,
                               include_shared=False):
        shared_zone_project_id = tables.shared_zones.c.target_project_id
        if hasattr(table.c, 'tenant_id'):
            if not context.all_tenants:
                # NOTE: The query doesn't work with table.c.tenant_id is None,
                # so I had to force flake8 to skip the check
                if include_null_tenant:
                    # Account for scoped tokens with no project_id
                    if include_shared and context.project_id is not None:
                        query = query.where(or_(
                                table.c.tenant_id == context.project_id,
                                shared_zone_project_id == context.project_id,
                                table.c.tenant_id == None))  # NOQA
                    else:
                        query = query.where(or_(
                                table.c.tenant_id == context.project_id,
                                table.c.tenant_id == None))  # NOQA
                else:
                    if include_shared and context.project_id is not None:
                        query = query.where(or_(
                            table.c.tenant_id == context.project_id,
                            shared_zone_project_id == context.project_id
                        ))
                    else:
                        query = query.where(
                            table.c.tenant_id == context.project_id
                        )

        return query

    def _apply_deleted_criteria(self, context, table, query):
        if hasattr(table.c, 'deleted'):
            if context.show_deleted:
                LOG.debug('Including deleted items in query results')
            else:
                query = query.where(table.c.deleted == "0")

        return query

    def _apply_version_increment(self, context, table, query):
        """
        Apply Version Incrementing SQL fragment a Query

        This should be called on all UPDATE queries, as it will ensure the
        version column is correctly incremented.
        """
        if hasattr(table.c, 'version'):
            # NOTE(kiall): This will translate into a true SQL increment.
            query = query.values({'version': table.c.version + 1})

        return query

    def _create(self, table, obj, exc_dup, skip_values=None,
                extra_values=None):
        # TODO(graham): Re Enable this
        # This was disabled as all the tests generate invalid Objects

        # Ensure the Object is valid
        # obj.validate()

        values = dict(obj)

        if skip_values is not None:
            for skip_value in skip_values:
                values.pop(skip_value, None)

        if extra_values is not None:
            for key in extra_values:
                values[key] = extra_values[key]

        query = table.insert()

        with sql.get_write_session() as session:
            try:
                resultproxy = session.execute(query, [values])
            except oslo_db_exception.DBDuplicateEntry:
                raise exc_dup("Duplicate %s" % obj.obj_name())

            # Refetch the row, for generated columns etc
            query = select(table).where(
                table.c.id == resultproxy.inserted_primary_key[0])
            resultproxy = session.execute(query)

            return _set_object_from_model(obj, resultproxy.fetchone())

    def _find(self, context, table, cls, list_cls, exc_notfound, criterion,
              one=False, marker=None, limit=None, sort_key=None,
              sort_dir=None, query=None, apply_tenant_criteria=True,
              include_shared=False):

        sort_key = sort_key or 'created_at'
        sort_dir = sort_dir or 'asc'

        # Build the query
        if query is None:
            query = select(table)
        query = self._apply_criterion(table, query, criterion)
        if apply_tenant_criteria:
            query = self._apply_tenant_criteria(context, table, query,
                                                include_shared=include_shared)
        query = self._apply_deleted_criteria(context, table, query)

        # Execute the Query
        if one:
            # NOTE(kiall): If we expect one value, and two rows match, we raise
            #              a NotFound. Limiting to 2 allows us to determine
            #              when we need to raise, while selecting the minimal
            #              number of rows.
            with sql.get_read_session() as session:
                resultproxy = session.execute(query.limit(2))
                results = resultproxy.fetchall()

            if len(results) != 1:
                raise exc_notfound("Could not find %s" % cls.obj_name())
            else:
                return _set_object_from_model(cls(), results[0])
        else:
            if marker is not None:
                marker = utils.check_marker(table, marker)

            try:
                query = utils.paginate_query(
                    query, table, limit,
                    [sort_key, 'id'], marker=marker,
                    sort_dir=sort_dir)

                with sql.get_read_session() as session:
                    resultproxy = session.execute(query)
                    results = resultproxy.fetchall()

                return _set_listobject_from_models(list_cls(), results)
            except oslodb_utils.InvalidSortKey as sort_key_error:
                raise exceptions.InvalidSortKey(str(sort_key_error))
            # Any ValueErrors are propagated back to the user as is.
            # Limits, sort_dir and sort_key are checked at the API layer.
            # If however central or storage is called directly, invalid values
            # show up as ValueError
            except ValueError as value_error:
                raise exceptions.ValueError(str(value_error))

    def _find_recordsets_with_records(self, context, criterion,
                                      marker=None, limit=None,
                                      sort_key=None, sort_dir=None,
                                      apply_tenant_criteria=True,
                                      force_index=False):
        sort_key = sort_key or 'created_at'
        sort_dir = sort_dir or 'asc'
        data = criterion.pop('data', None)
        status = criterion.pop('status', None)
        filtering_records = data or status

        # sort key will be used for the ORDER BY key in query,
        # needs to use the correct table index for different sort keys
        index_hint = utils.get_rrset_index(sort_key) if force_index else None

        rzjoin = tables.recordsets.join(
                tables.zones,
                tables.recordsets.c.zone_id == tables.zones.c.id
        )

        if filtering_records:
            rzjoin = rzjoin.join(
                    tables.records,
                    tables.recordsets.c.id == tables.records.c.recordset_id
            )

        inner_q = (
            select(tables.recordsets.c.id,     # 0 - RS ID
                   tables.zones.c.name).       # 1 - ZONE NAME
            select_from(rzjoin).
            where(tables.zones.c.deleted == '0')
        )

        count_q = (
            select(func.count(distinct(tables.recordsets.c.id))).
            select_from(rzjoin).where(tables.zones.c.deleted == '0')
        )

        if index_hint:
            inner_q = inner_q.with_hint(tables.recordsets, index_hint,
                                        dialect_name='mysql')

        if marker is not None:
            marker = utils.check_marker(tables.recordsets, marker)

        try:
            inner_q = utils.paginate_query(
                inner_q, tables.recordsets, limit,
                [sort_key, 'id'], marker=marker,
                sort_dir=sort_dir)

        except oslodb_utils.InvalidSortKey as sort_key_error:
            raise exceptions.InvalidSortKey(str(sort_key_error))
        # Any ValueErrors are propagated back to the user as is.
        # Limits, sort_dir and sort_key are checked at the API layer.
        # If however central or storage is called directly, invalid values
        # show up as ValueError
        except ValueError as value_error:
            raise exceptions.ValueError(str(value_error))

        if apply_tenant_criteria:
            inner_q = self._apply_tenant_criteria(
                    context, tables.recordsets, inner_q,
                    include_null_tenant=False)
            count_q = self._apply_tenant_criteria(context, tables.recordsets,
                                                  count_q,
                                                  include_null_tenant=False)

        inner_q = self._apply_criterion(tables.recordsets, inner_q, criterion)
        count_q = self._apply_criterion(tables.recordsets, count_q, criterion)

        if filtering_records:
            records_criterion = {k: v for k, v in (
                ('data', data), ('status', status)) if v is not None}
            inner_q = self._apply_criterion(tables.records, inner_q,
                                            records_criterion)
            count_q = self._apply_criterion(tables.records, count_q,
                                            records_criterion)

        inner_q = self._apply_deleted_criteria(context, tables.recordsets,
                                               inner_q)
        count_q = self._apply_deleted_criteria(context, tables.recordsets,
                                               count_q)

        # Get the list of IDs needed.
        # This is a separate call due to
        # http://dev.mysql.com/doc/mysql-reslimits-excerpt/5.6/en/subquery-restrictions.html  # noqa

        with sql.get_read_session() as session:
            inner_rproxy = session.execute(inner_q)
            rows = inner_rproxy.fetchall()
        if len(rows) == 0:
            return 0, objects.RecordSetList()
        id_zname_map = {}
        for r in rows:
            id_zname_map[r[0]] = r[1]
        formatted_ids = map(operator.itemgetter(0), rows)

        # Count query does not scale well for large amount of recordsets,
        # don't do it if the header 'OpenStack-DNS-Hide-Counts: True' exists
        if context.hide_counts:
            total_count = None
        else:
            with sql.get_read_session() as session:
                resultproxy = session.execute(count_q)
                result = resultproxy.fetchone()
            total_count = 0 if result is None else result[0]

        # Join the 2 required tables
        rjoin = tables.recordsets.outerjoin(
            tables.records,
            tables.records.c.recordset_id == tables.recordsets.c.id
        )

        query = select(*RECORDSET_QUERY_TABLES).select_from(rjoin)

        query = query.where(
            tables.recordsets.c.id.in_(formatted_ids)
        )

        query, sort_dirs = utils.sort_query(query, tables.recordsets,
                                            [sort_key, 'id'],
                                            sort_dir=sort_dir)

        try:
            with sql.get_read_session() as session:
                resultproxy = session.execute(query)
                raw_rows = resultproxy.fetchall()

        # Any ValueErrors are propagated back to the user as is.
        # If however central or storage is called directly, invalid values
        # show up as ValueError
        except ValueError as value_error:
            raise exceptions.ValueError(str(value_error))

        rrsets = objects.RecordSetList()
        rrset_id = None
        current_rrset = None

        for record in raw_rows:
            # If we're looking at the first, or a new rrset
            if record[0] != rrset_id:
                if current_rrset is not None:
                    # If this isn't the first iteration
                    rrsets.append(current_rrset)
                # Set up a new rrset
                current_rrset = objects.RecordSet()

                rrset_id = record[RECORDSET_MAP['id']]

                # Add all the loaded vars into RecordSet object

                for key, value in RECORDSET_MAP.items():
                    setattr(current_rrset, key, record[value])

                current_rrset.zone_name = id_zname_map[current_rrset.id]
                current_rrset.obj_reset_changes(['zone_name'])

                current_rrset.records = objects.RecordList()

                if record[RECORD_MAP['id']] is not None:
                    rrdata = objects.Record()

                    for key, value in RECORD_MAP.items():
                        setattr(rrdata, key, record[value])

                    current_rrset.records.append(rrdata)

            else:
                # We've already got a rrset, add the rdata
                if record[RECORD_MAP['id']] is not None:
                    rrdata = objects.Record()

                    for key, value in RECORD_MAP.items():
                        setattr(rrdata, key, record[value])

                    current_rrset.records.append(rrdata)

        # If the last record examined was a new rrset, or there is only 1 rrset
        if (len(rrsets) == 0 or
                (len(rrsets) != 0 and rrsets[-1] != current_rrset)):
            if current_rrset is not None:
                rrsets.append(current_rrset)

        return total_count, rrsets

    def _update(self, context, table, obj, exc_dup, exc_notfound,
                skip_values=None):
        # TODO(graham): Re Enable this

        # This was disabled as all the tests generate invalid Objects

        # Ensure the Object is valid
        # obj.validate()

        values = obj.obj_get_changes()

        if skip_values is not None:
            for skip_value in skip_values:
                values.pop(skip_value, None)

        query = (
            table.update().
            where(table.c.id == obj.id).
            values(**values)
        )

        query = self._apply_tenant_criteria(context, table, query)
        query = self._apply_deleted_criteria(context, table, query)
        query = self._apply_version_increment(context, table, query)

        with sql.get_write_session() as session:
            try:
                resultproxy = session.execute(query)
            except oslo_db_exception.DBDuplicateEntry:
                raise exc_dup("Duplicate %s" % obj.obj_name())

            if resultproxy.rowcount != 1:
                raise exc_notfound("Could not find %s" % obj.obj_name())

            # Refetch the row, for generated columns etc
            query = select(table).where(table.c.id == obj.id)
            resultproxy = session.execute(query)

            return _set_object_from_model(obj, resultproxy.fetchone())

    def _delete(self, context, table, obj, exc_notfound, hard_delete=False):
        """Perform item deletion or soft-delete.
        """

        if hasattr(table.c, 'deleted') and not hard_delete:
            # Perform item soft-delete.
            # Set the "status" column to "DELETED" and populate
            # the "deleted_at" column

            # TODO(kiall): If the object has any changed fields, they will be
            #              persisted here when we don't want that.

            # "deleted" is populated with the object id (rather than being a
            # boolean) to keep (name, deleted) unique
            obj.deleted = obj.id.replace('-', '')
            obj.deleted_at = timeutils.utcnow()

            # TODO(vinod): Change the action to be null
            # update the action and status before deleting the object
            obj.action = 'NONE'
            obj.status = 'DELETED'

            # NOTE(kiall): It should be impossible for a duplicate exception to
            #              be raised in this call, therefore, it is OK to pass
            #              in "None" as the exc_dup param.
            return self._update(context, table, obj, None, exc_notfound)

        # Delete the quota.
        query = table.delete().where(table.c.id == obj.id)
        query = self._apply_tenant_criteria(context, table, query)
        query = self._apply_deleted_criteria(context, table, query)

        with sql.get_write_session() as session:
            resultproxy = session.execute(query)

            if resultproxy.rowcount != 1:
                raise exc_notfound("Could not find %s" % obj.obj_name())

            # Refetch the row, for generated columns etc
            query = select(table).where(table.c.id == obj.id)
            resultproxy = session.execute(query)

            return _set_object_from_model(obj, resultproxy.fetchone())

    def _select_raw(self, context, table, criterion, query=None):
        # Build the query
        if query is None:
            query = select(table)

        query = self._apply_criterion(table, query, criterion)
        query = self._apply_deleted_criteria(context, table, query)

        try:
            with sql.get_read_session() as session:
                resultproxy = session.execute(query)
                return resultproxy.fetchall()
        # Any ValueErrors are propagated back to the user as is.
        # If however central or storage is called directly, invalid values
        # show up as ValueError
        except ValueError as value_error:
            raise exceptions.ValueError(str(value_error))
