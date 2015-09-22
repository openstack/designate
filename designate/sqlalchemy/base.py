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
from sqlalchemy import select, or_, between

from designate import exceptions
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

    def _apply_tenant_criteria(self, context, table, query):
        if hasattr(table.c, 'tenant_id'):
            if not context.all_tenants:
                # NOTE: The query doesn't work with table.c.tenant_id is None,
                # so I had to force flake8 to skip the check
                query = query.where(or_(table.c.tenant_id == context.tenant,
                                        table.c.tenant_id == None))  # NOQA

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

    def _find_recordsets_with_records(
        self, context, table, cls,
        list_cls, exc_notfound, criterion,
        one=False, marker=None, limit=None, sort_key=None,
        sort_dir=None, query=None, apply_tenant_criteria=True,
        load_relations=False, relation_table=None, relation_cls=None,
            relation_list_cls=None, relation_not_found_exc=None):

        sort_key = sort_key or 'created_at'
        sort_dir = sort_dir or 'asc'

        # Join the 2 required tables
        rjoin = table.outerjoin(
            relation_table,
            relation_table.c.recordset_id == table.c.id)

        inner_q = select([table.c.id])

        if marker is not None:
            marker = utils.check_marker(table, marker, self.session)

        try:
            inner_q = utils.paginate_query(
                inner_q, table, limit,
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

        inner_q = self._apply_criterion(table, inner_q, criterion)
        inner_q = self._apply_deleted_criteria(context, table, inner_q)

        # Get the list of IDs needed.
        # This is a separate call due to
        # http://dev.mysql.com/doc/mysql-reslimits-excerpt/5.6/en/subquery-restrictions.html  # noqa

        inner_rproxy = self.session.execute(inner_q)
        ids = inner_rproxy.fetchall()

        # formatted_ids = [id[0] for id in ids]
        formatted_ids = six.moves.map(operator.itemgetter(0), ids)

        query = select(
            [
                # RS Info
                table.c.id,                                 # 0 - RS ID
                table.c.version,                            # 1 - RS Version
                table.c.created_at,                         # 2 - RS Created
                table.c.updated_at,                         # 3 - RS Updated
                table.c.tenant_id,                          # 4 - RS Tenant
                table.c.domain_id,                          # 5 - RS Domain
                table.c.name,                               # 6 - RS Name
                table.c.type,                               # 7 - RS Type
                table.c.ttl,                                # 8 - RS TTL
                table.c.description,                        # 9 - RS Desc
                # R Info
                relation_table.c.id,                        # 10 - R ID
                relation_table.c.version,                   # 11 - R Version
                relation_table.c.created_at,                # 12 - R Created
                relation_table.c.updated_at,                # 13 - R Updated
                relation_table.c.tenant_id,                 # 14 - R Tenant
                relation_table.c.domain_id,                 # 15 - R Domain
                relation_table.c.recordset_id,              # 16 - R RSet
                relation_table.c.data,                      # 17 - R Data
                relation_table.c.description,               # 18 - R Desc
                relation_table.c.hash,                      # 19 - R Hash
                relation_table.c.managed,                   # 20 - R Mngd Flg
                relation_table.c.managed_plugin_name,       # 21 - R Mngd Plg
                relation_table.c.managed_resource_type,     # 22 - R Mngd Type
                relation_table.c.managed_resource_region,   # 23 - R Mngd Rgn
                relation_table.c.managed_resource_id,       # 24 - R Mngd ID
                relation_table.c.managed_tenant_id,         # 25 - R Mngd T ID
                relation_table.c.status,                    # 26 - R Status
                relation_table.c.action,                    # 27 - R Action
                relation_table.c.serial                     # 28 - R Serial
            ]).\
            select_from(
                rjoin
                       ).\
            where(
                table.c.id.in_(formatted_ids)
                 )

        # These make looking up indexes for the Raw Rows much easier,
        # and maintainable

        rs_map = {
            "id": 0,
            "version": 1,
            "created_at": 2,
            "updated_at": 3,
            "tenant_id": 4,
            "domain_id": 5,
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
            "domain_id": 15,
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

        query, sort_dirs = utils.sort_query(query, table, [sort_key, 'id'],
                                            sort_dir=sort_dir)

        try:
            resultproxy = self.session.execute(query)
            raw_rows = resultproxy.fetchall()

        # Any ValueErrors are propagated back to the user as is.
        # If however central or storage is called directly, invalid values
        # show up as ValueError
        except ValueError as value_error:
            raise exceptions.ValueError(six.text_type(value_error))

        rrsets = list_cls()
        rrset_id = None
        current_rrset = None

        for record in raw_rows:
            # If we're looking at the first, or a new rrset
            if record[0] != rrset_id:
                if current_rrset is not None:
                    # If this isn't the first iteration
                    rrsets.append(current_rrset)
                # Set up a new rrset
                current_rrset = cls()

                rrset_id = record[rs_map['id']]

                # Add all the loaded vars into RecordSet object

                for key, value in rs_map.items():
                    setattr(current_rrset, key, record[value])

                current_rrset.records = relation_list_cls()

                if record[r_map['id']] is not None:
                    rrdata = relation_cls()

                    for key, value in r_map.items():
                        setattr(rrdata, key, record[value])

                    current_rrset.records.append(rrdata)

            else:
                # We've already got an rrset, add the rdata
                if record[r_map['id']] is not None:
                    rrdata = relation_cls()

                    for key, value in r_map.items():
                        setattr(rrdata, key, record[value])

                    current_rrset.records.append(rrdata)

        # If the last record examined was a new rrset, or there is only 1 rrset
        if len(rrsets) == 0 or \
                (len(rrsets) != 0 and rrsets[-1] != current_rrset):
            if current_rrset is not None:
                rrsets.append(current_rrset)

        return rrsets

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
