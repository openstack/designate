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
import threading

import six
from oslo_db.sqlalchemy import utils as oslodb_utils
from oslo_db import exception as oslo_db_exception
from oslo_log import log as logging
from oslo_utils import timeutils
from sqlalchemy import exc as sqlalchemy_exc
from sqlalchemy import select, or_

from designate import exceptions
from designate.sqlalchemy import session
from designate.sqlalchemy import utils


LOG = logging.getLogger(__name__)


def _set_object_from_model(obj, model, **extra):
    """Update a DesignateObject with the values from a SQLA Model"""

    for fieldname in obj.FIELDS.keys():
        if hasattr(model, fieldname):
            if fieldname in extra.keys():
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

    def _apply_criterion(self, table, query, criterion):
        if criterion is not None:
            for name, value in criterion.items():
                column = getattr(table.c, name)

                # Wildcard value: '*'
                if isinstance(value, basestring) and '*' in value:
                    queryval = value.replace('*', '%')
                    query = query.where(column.like(queryval))
                elif isinstance(value, basestring) and value.startswith('!'):
                    queryval = value[1:]
                    query = query.where(column != queryval)
                elif isinstance(value, basestring) and value.startswith('<='):
                    queryval = value[2:]
                    query = query.where(column <= queryval)
                elif isinstance(value, basestring) and value.startswith('<'):
                    queryval = value[1:]
                    query = query.where(column < queryval)
                elif isinstance(value, basestring) and value.startswith('>='):
                    queryval = value[2:]
                    query = query.where(column >= queryval)
                elif isinstance(value, basestring) and value.startswith('>'):
                    queryval = value[1:]
                    query = query.where(column > queryval)
                else:
                    query = query.where(column == value)

        return query

    def _apply_tenant_criteria(self, context, table, query):
        if hasattr(table.c, 'tenant_id'):
            if context.all_tenants:
                LOG.debug('Including all tenants items in query results')
            else:
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
            raise exc_dup()

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
                raise exc_notfound()
            else:
                return _set_object_from_model(cls(), results[0])
        else:
            if marker is not None:
                # If marker is not none and basestring we query it.
                # Otherwise, return all matching records
                marker_query = select([table]).where(table.c.id == marker)

                try:
                    marker_resultproxy = self.session.execute(marker_query)
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

            try:
                query = utils.paginate_query(
                    query, table, limit,
                    [sort_key, 'id', 'created_at'], marker=marker,
                    sort_dir=sort_dir)

                resultproxy = self.session.execute(query)
                results = resultproxy.fetchall()

                return _set_listobject_from_models(list_cls(), results)
            except oslodb_utils.InvalidSortKey as sort_key_error:
                raise exceptions.InvalidSortKey(sort_key_error.message)
            # Any ValueErrors are propagated back to the user as is.
            # Limits, sort_dir and sort_key are checked at the API layer.
            # If however central or storage is called directly, invalid values
            # show up as ValueError
            except ValueError as value_error:
                raise exceptions.ValueError(value_error.message)

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
            raise exc_dup()

        if resultproxy.rowcount != 1:
            raise exc_notfound()

        # Refetch the row, for generated columns etc
        query = select([table]).where(table.c.id == obj.id)
        resultproxy = self.session.execute(query)

        return _set_object_from_model(obj, resultproxy.fetchone())

    def _delete(self, context, table, obj, exc_notfound):
        if hasattr(table.c, 'deleted'):
            # Perform a Soft Delete
            # TODO(kiall): If the object has any changed fields, they will be
            #              persisted here when we don't want that.
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
            raise exc_notfound()

        # Refetch the row, for generated columns etc
        query = select([table]).where(table.c.id == obj.id)
        resultproxy = self.session.execute(query)

        return _set_object_from_model(obj, resultproxy.fetchone())
