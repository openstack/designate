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

import six
from oslo_db.sqlalchemy import utils as oslodb_utils
from oslo_db import exception as oslo_db_exception
from oslo_log import log as logging
from oslo_utils import timeutils
from sqlalchemy import select, or_, between, func, distinct

from designate import exceptions
from designate import objects
from designate.sqlalchemy import session
from designate.sqlalchemy import utils


LOG = logging.getLogger(__name__)


def _set_object_from_model(obj, model, **extra):
    """Update a DesignateObject with the values from a SQLA Model"""

    for fieldname in six.iterkeys(obj.FIELDS):
        if hasattr(model, fieldname):
            if fieldname in six.iterkeys(extra):
                obj[fieldname] = extra[fieldname]
            else:
                obj[fieldname] = getattr(model, fieldname)

    obj.obj_reset_changes()

    return obj


def _set_listobject_from_models(obj, models, map_=None):
        for model in models:
            extra = {}

            if map_ is not None:
                extra = map_(model)

            obj.objects.append(
                _set_object_from_model(obj.LIST_ITEM_TYPE(), model, **extra))

        obj.obj_reset_changes()

        return obj


@six.add_metaclass(abc.ABCMeta)
class SQLAlchemy(object):

    def __init__(self):
        super(SQLAlchemy, self).__init__()

        self.engine = session.get_engine(self.get_name())

        self.local_store = threading.local()

    @abc.abstractmethod
    def get_name(self):
        """Get the name."""

    @property
    def session(self):
        # NOTE: This uses a thread local store, allowing each greenthread to
        #       have it's own session stored correctly. Without this, each
        #       greenthread may end up using a single global session, which
        #       leads to bad things happening.

        if not hasattr(self.local_store, 'session'):
            self.local_store.session = session.get_session(self.get_name())

        return self.local_store.session

    def begin(self):
        self.session.begin(subtransactions=True)

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    @staticmethod
    def _apply_criterion(table, query, criterion):
        if criterion is not None:
            for name, value in criterion.items():
                column = getattr(table.c, name)

                # Wildcard value: '%'
                if isinstance(value, six.string_types) and '%' in value:
                    query = query.where(column.like(value))

                elif (isinstance(value, six.string_types) and
                        value.startswith('!')):
                    queryval = value[1:]
                    query = query.where(column != queryval)

                elif (isinstance(value, six.string_types) and
                        value.startswith('<=')):
                    queryval = value[2:]
                    query = query.where(column <= queryval)

                elif (isinstance(value, six.string_types) and
                        value.startswith('<')):
                    queryval = value[1:]
                    query = query.where(column < queryval)

                elif (isinstance(value, six.string_types) and
                        value.startswith('>=')):
                    queryval = value[2:]
                    query = query.where(column >= queryval)

                elif (isinstance(value, six.string_types) and
                        value.startswith('>')):
                    queryval = value[1:]
                    query = query.where(column > queryval)

                elif (isinstance(value, six.string_types) and
                        value.startswith('BETWEEN')):
                    elements = [i.strip(" ") for i in
                                value.split(" ", 1)[1].strip(" ").split(",")]
                    query = query.where(between(
                        column, elements[0], elements[1]))

                elif isinstance(value, list):
                    query = query.where(column.in_(value))

                else:
                    query = query.where(column == value)

        return query

    def _apply_tenant_criteria(self, context, table, query,
                               include_null_tenant=True):
        if hasattr(table.c, 'tenant_id'):
            if not context.all_tenants:
                # NOTE: The query doesn't work with table.c.tenant_id is None,
                # so I had to force flake8 to skip the check
                if include_null_tenant:
                    query = query.where(or_(
                            table.c.tenant_id == context.tenant,
                            table.c.tenant_id == None))  # NOQA
                else:
                    query = query.where(table.c.tenant_id == context.tenant)

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

        values = obj.obj_get_changes()

        if skip_values is not None:
            for skip_value in skip_values:
                values.pop(skip_value, None)

        if extra_values is not None:
            for key in extra_values:
                values[key] = extra_values[key]

        query = table.insert()

        try:
            resultproxy = self.session.execute(query, [dict(values)])
        except oslo_db_exception.DBDuplicateEntry:
            msg = "Duplicate %s" % obj.obj_name()
            raise exc_dup(msg)

        # Refetch the row, for generated columns etc
        query = select([table]).where(
            table.c.id == resultproxy.inserted_primary_key[0])
        resultproxy = self.session.execute(query)

        return _set_object_from_model(obj, resultproxy.fetchone())

    def _find(self, context, table, cls, list_cls, exc_notfound, criterion,
              one=False, marker=None, limit=None, sort_key=None,
              sort_dir=None, query=None, apply_tenant_criteria=True):

        sort_key = sort_key or 'created_at'
        sort_dir = sort_dir or 'asc'

        # Build the query
        if query is None:
            query = select([table])
        query = self._apply_criterion(table, query, criterion)
        if apply_tenant_criteria:
            query = self._apply_tenant_criteria(context, table, query)

        query = self._apply_deleted_criteria(context, table, query)

        # Execute the Query
        if one:
            # NOTE(kiall): If we expect one value, and two rows match, we raise
            #              a NotFound. Limiting to 2 allows us to determine
            #              when we need to raise, while selecting the minimal
            #              number of rows.
            resultproxy = self.session.execute(query.limit(2))
            results = resultproxy.fetchall()

            if len(results) != 1:
                msg = "Could not find %s" % cls.obj_name()
                raise exc_notfound(msg)
            else:
                return _set_object_from_model(cls(), results[0])
        else:
            if marker is not None:
                marker = utils.check_marker(table, marker, self.session)

            try:
                query = utils.paginate_query(
                    query, table, limit,
                    [sort_key, 'id'], marker=marker,
                    sort_dir=sort_dir)

                resultproxy = self.session.execute(query)
                results = resultproxy.fetchall()

                return _set_listobject_from_models(list_cls(), results)
            except oslodb_utils.InvalidSortKey as sort_key_error:
                raise exceptions.InvalidSortKey(six.text_type(sort_key_error))
            # Any ValueErrors are propagated back to the user as is.
            # Limits, sort_dir and sort_key are checked at the API layer.
            # If however central or storage is called directly, invalid values
            # show up as ValueError
            except ValueError as value_error:
                raise exceptions.ValueError(six.text_type(value_error))

    def _find_recordsets_with_records(self, context, criterion, zones_table,
                                      recordsets_table, records_table,
                                      one=False, marker=None, limit=None,
                                      sort_key=None, sort_dir=None, query=None,
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

        rzjoin = recordsets_table.join(
                zones_table,
                recordsets_table.c.zone_id == zones_table.c.id)

        if filtering_records:
            rzjoin = rzjoin.join(
                    records_table,
                    recordsets_table.c.id == records_table.c.recordset_id)

        inner_q = select([recordsets_table.c.id,      # 0 - RS ID
                          zones_table.c.name]         # 1 - ZONE NAME
                         ).select_from(rzjoin).\
            where(zones_table.c.deleted == '0')

        count_q = select([func.count(distinct(recordsets_table.c.id))]).\
            select_from(rzjoin).where(zones_table.c.deleted == '0')

        if index_hint:
            inner_q = inner_q.with_hint(recordsets_table, index_hint,
                                        dialect_name='mysql')

        if marker is not None:
            marker = utils.check_marker(recordsets_table, marker,
                                        self.session)

        try:
            inner_q = utils.paginate_query(
                inner_q, recordsets_table, limit,
                [sort_key, 'id'], marker=marker,
                sort_dir=sort_dir)

        except oslodb_utils.InvalidSortKey as sort_key_error:
            raise exceptions.InvalidSortKey(six.text_type(sort_key_error))
        # Any ValueErrors are propagated back to the user as is.
        # Limits, sort_dir and sort_key are checked at the API layer.
        # If however central or storage is called directly, invalid values
        # show up as ValueError
        except ValueError as value_error:
            raise exceptions.ValueError(six.text_type(value_error))

        if apply_tenant_criteria:
            inner_q = self._apply_tenant_criteria(
                    context, recordsets_table, inner_q,
                    include_null_tenant=False)
            count_q = self._apply_tenant_criteria(context, recordsets_table,
                                                  count_q,
                                                  include_null_tenant=False)

        inner_q = self._apply_criterion(recordsets_table, inner_q, criterion)
        count_q = self._apply_criterion(recordsets_table, count_q, criterion)

        if filtering_records:
            records_criterion = dict((k, v) for k, v in (
                ('data', data), ('status', status)) if v is not None)
            inner_q = self._apply_criterion(records_table, inner_q,
                                            records_criterion)
            count_q = self._apply_criterion(records_table, count_q,
                                            records_criterion)

        inner_q = self._apply_deleted_criteria(context, recordsets_table,
                                               inner_q)
        count_q = self._apply_deleted_criteria(context, recordsets_table,
                                               count_q)

        # Get the list of IDs needed.
        # This is a separate call due to
        # http://dev.mysql.com/doc/mysql-reslimits-excerpt/5.6/en/subquery-restrictions.html  # noqa

        inner_rproxy = self.session.execute(inner_q)
        rows = inner_rproxy.fetchall()
        if len(rows) == 0:
            return 0, objects.RecordSetList()
        id_zname_map = {}
        for r in rows:
            id_zname_map[r[0]] = r[1]
        formatted_ids = six.moves.map(operator.itemgetter(0), rows)

        # Count query does not scale well for large amount of recordsets,
        # don't do it if the header 'OpenStack-DNS-Hide-Counts: True' exists
        if context.hide_counts:
            total_count = None
        else:
            resultproxy = self.session.execute(count_q)
            result = resultproxy.fetchone()
            total_count = 0 if result is None else result[0]

        # Join the 2 required tables
        rjoin = recordsets_table.outerjoin(
            records_table,
            records_table.c.recordset_id == recordsets_table.c.id)

        query = select(
            [
                # RS Info
                recordsets_table.c.id,                     # 0 - RS ID
                recordsets_table.c.version,                # 1 - RS Version
                recordsets_table.c.created_at,             # 2 - RS Created
                recordsets_table.c.updated_at,             # 3 - RS Updated
                recordsets_table.c.tenant_id,              # 4 - RS Tenant
                recordsets_table.c.zone_id,                # 5 - RS Zone
                recordsets_table.c.name,                   # 6 - RS Name
                recordsets_table.c.type,                   # 7 - RS Type
                recordsets_table.c.ttl,                    # 8 - RS TTL
                recordsets_table.c.description,            # 9 - RS Desc
                # R Info
                records_table.c.id,                        # 10 - R ID
                records_table.c.version,                   # 11 - R Version
                records_table.c.created_at,                # 12 - R Created
                records_table.c.updated_at,                # 13 - R Updated
                records_table.c.tenant_id,                 # 14 - R Tenant
                records_table.c.zone_id,                   # 15 - R Zone
                records_table.c.recordset_id,              # 16 - R RSet
                records_table.c.data,                      # 17 - R Data
                records_table.c.description,               # 18 - R Desc
                records_table.c.hash,                      # 19 - R Hash
                records_table.c.managed,                   # 20 - R Mngd Flg
                records_table.c.managed_plugin_name,       # 21 - R Mngd Plg
                records_table.c.managed_resource_type,     # 22 - R Mngd Type
                records_table.c.managed_resource_region,   # 23 - R Mngd Rgn
                records_table.c.managed_resource_id,       # 24 - R Mngd ID
                records_table.c.managed_tenant_id,         # 25 - R Mngd T ID
                records_table.c.status,                    # 26 - R Status
                records_table.c.action,                    # 27 - R Action
                records_table.c.serial                     # 28 - R Serial
            ]).select_from(rjoin)

        query = query.where(
            recordsets_table.c.id.in_(formatted_ids)
        )

        # These make looking up indexes for the Raw Rows much easier,
        # and maintainable

        rs_map = {
            "id": 0,
            "version": 1,
            "created_at": 2,
            "updated_at": 3,
            "tenant_id": 4,
            "zone_id": 5,
            "name": 6,
            "type": 7,
            "ttl": 8,
            "description": 9,
        }

        r_map = {
            "id": 10,
            "version": 11,
            "created_at": 12,
            "updated_at": 13,
            "tenant_id": 14,
            "zone_id": 15,
            "recordset_id": 16,
            "data": 17,
            "description": 18,
            "hash": 19,
            "managed": 20,
            "managed_plugin_name": 21,
            "managed_resource_type": 22,
            "managed_resource_region": 23,
            "managed_resource_id": 24,
            "managed_tenant_id": 25,
            "status": 26,
            "action": 27,
            "serial": 28,
        }

        query, sort_dirs = utils.sort_query(query, recordsets_table,
                                            [sort_key, 'id'],
                                            sort_dir=sort_dir)

        try:
            resultproxy = self.session.execute(query)
            raw_rows = resultproxy.fetchall()

        # Any ValueErrors are propagated back to the user as is.
        # If however central or storage is called directly, invalid values
        # show up as ValueError
        except ValueError as value_error:
            raise exceptions.ValueError(six.text_type(value_error))

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

                rrset_id = record[rs_map['id']]

                # Add all the loaded vars into RecordSet object

                for key, value in rs_map.items():
                    setattr(current_rrset, key, record[value])

                current_rrset.zone_name = id_zname_map[current_rrset.id]
                current_rrset.obj_reset_changes(['zone_name'])

                current_rrset.records = objects.RecordList()

                if record[r_map['id']] is not None:
                    rrdata = objects.Record()

                    for key, value in r_map.items():
                        setattr(rrdata, key, record[value])

                    current_rrset.records.append(rrdata)

            else:
                # We've already got an rrset, add the rdata
                if record[r_map['id']] is not None:
                    rrdata = objects.Record()

                    for key, value in r_map.items():
                        setattr(rrdata, key, record[value])

                    current_rrset.records.append(rrdata)

        # If the last record examined was a new rrset, or there is only 1 rrset
        if len(rrsets) == 0 or \
                (len(rrsets) != 0 and rrsets[-1] != current_rrset):
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

        query = table.update()\
                     .where(table.c.id == obj.id)\
                     .values(**values)

        query = self._apply_tenant_criteria(context, table, query)
        query = self._apply_deleted_criteria(context, table, query)
        query = self._apply_version_increment(context, table, query)

        try:
            resultproxy = self.session.execute(query)
        except oslo_db_exception.DBDuplicateEntry:
            msg = "Duplicate %s" % obj.obj_name()
            raise exc_dup(msg)

        if resultproxy.rowcount != 1:
            msg = "Could not find %s" % obj.obj_name()
            raise exc_notfound(msg)

        # Refetch the row, for generated columns etc
        query = select([table]).where(table.c.id == obj.id)
        resultproxy = self.session.execute(query)

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

        resultproxy = self.session.execute(query)

        if resultproxy.rowcount != 1:
            msg = "Could not find %s" % obj.obj_name()
            raise exc_notfound(msg)

        # Refetch the row, for generated columns etc
        query = select([table]).where(table.c.id == obj.id)
        resultproxy = self.session.execute(query)

        return _set_object_from_model(obj, resultproxy.fetchone())

    def _select_raw(self, context, table, criterion, query=None):
        # Build the query
        if query is None:
            query = select([table])

        query = self._apply_criterion(table, query, criterion)
        query = self._apply_deleted_criteria(context, table, query)

        try:
            resultproxy = self.session.execute(query)
            return resultproxy.fetchall()
        # Any ValueErrors are propagated back to the user as is.
        # If however central or storage is called directly, invalid values
        # show up as ValueError
        except ValueError as value_error:
            raise exceptions.ValueError(six.text_type(value_error))
