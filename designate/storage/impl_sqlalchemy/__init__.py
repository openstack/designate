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
import time
import threading
import hashlib

from oslo.config import cfg
from oslo.db.sqlalchemy import utils as oslo_utils
from oslo.db import options
from oslo.db import exception as oslo_db_exception
from sqlalchemy import exc as sqlalchemy_exc
from sqlalchemy import select, distinct, func

from designate.openstack.common import log as logging
from designate.openstack.common import timeutils
from designate import exceptions
from designate import objects
from designate.sqlalchemy import session
from designate.sqlalchemy import utils
from designate.storage import base
from designate.storage.impl_sqlalchemy import tables


LOG = logging.getLogger(__name__)

cfg.CONF.register_group(cfg.OptGroup(
    name='storage:sqlalchemy', title="Configuration for SQLAlchemy Storage"
))

cfg.CONF.register_opts(options.database_opts, group='storage:sqlalchemy')


def _set_object_from_model(obj, model, **extra):
    """Update a DesignateObject with the values from a SQLA Model"""

    for fieldname in obj.FIELDS:
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


class SQLAlchemyStorage(base.Storage):
    """SQLAlchemy connection"""
    __plugin_name__ = 'sqlalchemy'

    def __init__(self):
        super(SQLAlchemyStorage, self).__init__()

        self.engine = session.get_engine(self.name)

        self.local_store = threading.local()

    @property
    def session(self):
        # NOTE: This uses a thread local store, allowing each greenthread to
        #       have it's own session stored correctly. Without this, each
        #       greenthread may end up using a single global session, which
        #       leads to bad things happening.

        if not hasattr(self.local_store, 'session'):
            self.local_store.session = session.get_session(self.name)

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
                else:
                    query = query.where(column == value)

        return query

    def _apply_tenant_criteria(self, context, table, query):
        if hasattr(table.c, 'tenant_id'):
            if context.all_tenants:
                LOG.debug('Including all tenants items in query results')
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

    def _create(self, table, obj, exc_dup, skip_values=None):
        values = obj.obj_get_changes()

        if skip_values is not None:
            for skip_value in skip_values:
                values.pop(skip_value, None)

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
              sort_dir=None, query=None):
        sort_key = sort_key or 'created_at'
        sort_dir = sort_dir or 'asc'

        # Build the query
        if query is None:
            query = select([table])
        query = self._apply_criterion(table, query, criterion)
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
            except oslo_utils.InvalidSortKey as sort_key_error:
                raise exceptions.InvalidSortKey(sort_key_error.message)
            # Any ValueErrors are propagated back to the user as is.
            # Limits, sort_dir and sort_key are checked at the API layer.
            # If however central or storage is called directly, invalid values
            # show up as ValueError
            except ValueError as value_error:
                raise exceptions.ValueError(value_error.message)

    def _update(self, context, table, obj, exc_dup, exc_notfound,
                skip_values=None):
        values = obj.obj_get_changes()

        if skip_values is not None:
            for skip_value in skip_values:
                values.pop(skip_value, None)

        query = table.update()\
                     .where(table.c.id == obj.id)\
                     .values(**values)

        query = self._apply_tenant_criteria(context, table, query)
        query = self._apply_deleted_criteria(context, table, query)

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

    # CRUD for our resources (quota, server, tsigkey, tenant, domain & record)
    # R - get_*, find_*s
    #
    # Standard Arguments
    # self      - python object for the class
    # context   - a dictionary of details about the request (http etc),
    #             provided by flask.
    # criterion - dictionary of filters to be applied
    #

    # Quota Methods
    def _find_quotas(self, context, criterion, one=False, marker=None,
                     limit=None, sort_key=None, sort_dir=None):
        return self._find(
            context, tables.quotas, objects.Quota, objects.QuotaList,
            exceptions.QuotaNotFound, criterion, one, marker, limit,
            sort_key, sort_dir)

    def create_quota(self, context, quota):
        if not isinstance(quota, objects.Quota):
            # TODO(kiall): Quotas should always use Objects
            quota = objects.Quota(**quota)

        return self._create(
            tables.quotas, quota, exceptions.DuplicateQuota)

    def get_quota(self, context, quota_id):
        return self._find_quotas(context, {'id': quota_id}, one=True)

    def find_quotas(self, context, criterion=None, marker=None, limit=None,
                    sort_key=None, sort_dir=None):
        return self._find_quotas(context, criterion, marker=marker,
                                 limit=limit, sort_key=sort_key,
                                 sort_dir=sort_dir)

    def find_quota(self, context, criterion):
        return self._find_quotas(context, criterion, one=True)

    def update_quota(self, context, quota):
        return self._update(
            context, tables.quotas, quota, exceptions.DuplicateQuota,
            exceptions.QuotaNotFound)

    def delete_quota(self, context, quota_id):
        # Fetch the existing quota, we'll need to return it.
        quota = self._find_quotas(context, {'id': quota_id}, one=True)
        return self._delete(context, tables.quotas, quota,
                            exceptions.QuotaNotFound)

    # Server Methods
    def _find_servers(self, context, criterion, one=False, marker=None,
                     limit=None, sort_key=None, sort_dir=None):
        return self._find(
            context, tables.servers, objects.Server, objects.ServerList,
            exceptions.ServerNotFound, criterion, one, marker, limit,
            sort_key, sort_dir)

    def create_server(self, context, server):
        return self._create(
            tables.servers, server, exceptions.DuplicateServer)

    def get_server(self, context, server_id):
        return self._find_servers(context, {'id': server_id}, one=True)

    def find_servers(self, context, criterion=None, marker=None, limit=None,
                     sort_key=None, sort_dir=None):
        return self._find_servers(context, criterion, marker=marker,
                                  limit=limit, sort_key=sort_key,
                                  sort_dir=sort_dir)

    def find_server(self, context, criterion):
        return self._find_servers(context, criterion, one=True)

    def update_server(self, context, server):
        return self._update(
            context, tables.servers, server, exceptions.DuplicateServer,
            exceptions.ServerNotFound)

    def delete_server(self, context, server_id):
        # Fetch the existing server, we'll need to return it.
        server = self._find_servers(context, {'id': server_id}, one=True)
        return self._delete(context, tables.servers, server,
                            exceptions.ServerNotFound)

    # TLD Methods
    def _find_tlds(self, context, criterion, one=False, marker=None,
                   limit=None, sort_key=None, sort_dir=None):
        return self._find(
            context, tables.tlds, objects.Tld, objects.TldList,
            exceptions.TldNotFound, criterion, one, marker, limit,
            sort_key, sort_dir)

    def create_tld(self, context, tld):
        return self._create(
            tables.tlds, tld, exceptions.DuplicateTld)

    def get_tld(self, context, tld_id):
        return self._find_tlds(context, {'id': tld_id}, one=True)

    def find_tlds(self, context, criterion=None, marker=None, limit=None,
                  sort_key=None, sort_dir=None):
        return self._find_tlds(context, criterion, marker=marker, limit=limit,
                               sort_key=sort_key, sort_dir=sort_dir)

    def find_tld(self, context, criterion):
        return self._find_tlds(context, criterion, one=True)

    def update_tld(self, context, tld):
        return self._update(
            context, tables.tlds, tld, exceptions.DuplicateTld,
            exceptions.TldNotFound)

    def delete_tld(self, context, tld_id):
        # Fetch the existing tld, we'll need to return it.
        tld = self._find_tlds(context, {'id': tld_id}, one=True)
        return self._delete(context, tables.tlds, tld, exceptions.TldNotFound)

    # TSIG Key Methods
    def _find_tsigkeys(self, context, criterion, one=False, marker=None,
                       limit=None, sort_key=None, sort_dir=None):
        return self._find(
            context, tables.tsigkeys, objects.TsigKey, objects.TsigKeyList,
            exceptions.TsigKeyNotFound, criterion, one, marker, limit,
            sort_key, sort_dir)

    def create_tsigkey(self, context, tsigkey):
        return self._create(
            tables.tsigkeys, tsigkey, exceptions.DuplicateTsigKey)

    def get_tsigkey(self, context, tsigkey_id):
        return self._find_tsigkeys(context, {'id': tsigkey_id}, one=True)

    def find_tsigkeys(self, context, criterion=None, marker=None, limit=None,
                      sort_key=None, sort_dir=None):
        return self._find_tsigkeys(context, criterion, marker=marker,
                                   limit=limit, sort_key=sort_key,
                                   sort_dir=sort_dir)

    def find_tsigkey(self, context, criterion):
        return self._find_tsigkeys(context, criterion, one=True)

    def update_tsigkey(self, context, tsigkey):
        return self._update(
            context, tables.tsigkeys, tsigkey, exceptions.DuplicateTsigKey,
            exceptions.TsigKeyNotFound)

    def delete_tsigkey(self, context, tsigkey_id):
        # Fetch the existing tsigkey, we'll need to return it.
        tsigkey = self._find_tsigkeys(context, {'id': tsigkey_id}, one=True)
        return self._delete(context, tables.tsigkeys, tsigkey,
                            exceptions.TsigKeyNotFound)

    ##
    # Tenant Methods
    ##
    def find_tenants(self, context):
        # returns an array of tenant_id & count of their domains
        query = select([tables.domains.c.tenant_id,
                        func.count(tables.domains.c.id)])
        query = self._apply_tenant_criteria(context, tables.domains, query)
        query = self._apply_deleted_criteria(context, tables.domains, query)
        query = query.group_by(tables.domains.c.tenant_id)

        resultproxy = self.session.execute(query)
        results = resultproxy.fetchall()

        tenant_list = objects.TenantList(
            objects=[objects.Tenant(id=t[0], domain_count=t[1]) for t in
                     results])

        tenant_list.obj_reset_changes()

        return tenant_list

    def get_tenant(self, context, tenant_id):
        # get list list & count of all domains owned by given tenant_id
        query = select([tables.domains.c.name])
        query = self._apply_tenant_criteria(context, tables.domains, query)
        query = self._apply_deleted_criteria(context, tables.domains, query)
        query = query.where(tables.domains.c.tenant_id == tenant_id)

        resultproxy = self.session.execute(query)
        results = resultproxy.fetchall()

        return objects.Tenant(
            id=tenant_id,
            domain_count=len(results),
            domains=[r[0] for r in results])

    def count_tenants(self, context):
        # tenants are the owner of domains, count the number of unique tenants
        # select count(distinct tenant_id) from domains
        query = select([func.count(distinct(tables.domains.c.tenant_id))])
        query = self._apply_tenant_criteria(context, tables.domains, query)
        query = self._apply_deleted_criteria(context, tables.domains, query)

        resultproxy = self.session.execute(query)
        result = resultproxy.fetchone()

        if result is None:
            return 0

        return result[0]

    ##
    # Domain Methods
    ##
    def _find_domains(self, context, criterion, one=False, marker=None,
                      limit=None, sort_key=None, sort_dir=None):
        return self._find(
            context, tables.domains, objects.Domain, objects.DomainList,
            exceptions.DomainNotFound, criterion, one, marker, limit,
            sort_key, sort_dir)

    def create_domain(self, context, domain):
        return self._create(
            tables.domains, domain, exceptions.DuplicateDomain)

    def get_domain(self, context, domain_id):
        return self._find_domains(context, {'id': domain_id}, one=True)

    def find_domains(self, context, criterion=None, marker=None, limit=None,
                     sort_key=None, sort_dir=None):
        return self._find_domains(context, criterion, marker=marker,
                                  limit=limit, sort_key=sort_key,
                                  sort_dir=sort_dir)

    def find_domain(self, context, criterion):
        return self._find_domains(context, criterion, one=True)

    def update_domain(self, context, domain):
        return self._update(
            context, tables.domains, domain, exceptions.DuplicateDomain,
            exceptions.DomainNotFound)

    def delete_domain(self, context, domain_id):
        # Fetch the existing domain, we'll need to return it.
        domain = self._find_domains(context, {'id': domain_id}, one=True)
        return self._delete(context, tables.domains, domain,
                            exceptions.DomainNotFound)

    def count_domains(self, context, criterion=None):
        query = select([func.count(tables.domains.c.id)])
        query = self._apply_criterion(tables.domains, query, criterion)
        query = self._apply_tenant_criteria(context, tables.domains, query)
        query = self._apply_deleted_criteria(context, tables.domains, query)

        resultproxy = self.session.execute(query)
        result = resultproxy.fetchone()

        if result is None:
            return 0

        return result[0]

    # RecordSet Methods
    def _find_recordsets(self, context, criterion, one=False, marker=None,
                         limit=None, sort_key=None, sort_dir=None):
        query = None
        if criterion is not None \
                and not criterion.get('domains_deleted', True):
            # Ensure that we return only active recordsets
            rjoin = tables.recordsets.join(
                tables.domains,
                tables.recordsets.c.domain_id == tables.domains.c.id)
            query = select([tables.recordsets]).select_from(rjoin).\
                where(tables.domains.c.deleted == '0')

            # remove 'domains_deleted' from the criterion, as _apply_criterion
            # assumes each key in criterion to be a column name.
            del criterion['domains_deleted']
        return self._find(
            context, tables.recordsets, objects.RecordSet,
            objects.RecordSetList, exceptions.RecordSetNotFound, criterion,
            one, marker, limit, sort_key, sort_dir, query)

    def create_recordset(self, context, domain_id, recordset):
        # Fetch the domain as we need the tenant_id
        domain = self._find_domains(context, {'id': domain_id}, one=True)

        recordset.tenant_id = domain.tenant_id
        recordset.domain_id = domain_id

        recordset = self._create(
            tables.recordsets, recordset, exceptions.DuplicateRecordSet,
            ['records'])

        if recordset.obj_attr_is_set('records'):
            for record in recordset.records:
                # NOTE: Since we're dealing with a mutable object, the return
                #       value is not needed. The original item will be mutated
                #       in place on the input "recordset.records" list.
                self.create_record(context, domain_id, recordset.id, record)
        else:
            recordset.records = objects.RecordList()

        recordset.obj_reset_changes('records')

        return recordset

    def get_recordset(self, context, recordset_id):
        recordset = self._find_recordsets(
            context, {'id': recordset_id}, one=True)

        recordset.records = self._find_records(
            context, {'recordset_id': recordset.id})

        recordset.obj_reset_changes('records')

        return recordset

    def find_recordsets(self, context, criterion=None, marker=None, limit=None,
                        sort_key=None, sort_dir=None):
        recordsets = self._find_recordsets(context, criterion, marker=marker,
                                           limit=limit, sort_key=sort_key,
                                           sort_dir=sort_dir)

        for recordset in recordsets:
            recordset.records = self._find_records(
                context, {'recordset_id': recordset.id})

            recordset.obj_reset_changes('records')

        return recordsets

    def find_recordset(self, context, criterion):
        recordset = self._find_recordsets(context, criterion, one=True)

        recordset.records = self._find_records(
            context, {'recordset_id': recordset.id})

        recordset.obj_reset_changes('records')

        return recordset

    def update_recordset(self, context, recordset):
        recordset = self._update(
            context, tables.recordsets, recordset,
            exceptions.DuplicateRecordSet, exceptions.RecordSetNotFound,
            ['records'])

        if recordset.obj_attr_is_set('records'):
            # Gather the Record ID's we have
            have_records = set([r.id for r in self._find_records(
                context, {'recordset_id': recordset.id})])

            # Prep some lists of changes
            keep_records = set([])
            create_records = []
            update_records = []

            # Determine what to change
            for record in recordset.records:
                keep_records.add(record.id)
                try:
                    record.obj_get_original_value('id')
                except KeyError:
                    create_records.append(record)
                else:
                    update_records.append(record)

            # NOTE: Since we're dealing with mutable objects, the return value
            #       of create/update/delete record is not needed. The original
            #       item will be mutated in place on the input
            #       "recordset.records" list.

            # Delete Records
            for record_id in have_records - keep_records:
                self.delete_record(context, record_id)

            # Update Records
            for record in update_records:
                self.update_record(context, record)

            # Create Records
            for record in create_records:
                self.create_record(
                    context, recordset.domain_id, recordset.id, record)

        return recordset

    def delete_recordset(self, context, recordset_id):
        # Fetch the existing recordset, we'll need to return it.
        recordset = self._find_recordsets(
            context, {'id': recordset_id}, one=True)

        return self._delete(context, tables.recordsets, recordset,
                            exceptions.RecordSetNotFound)

    def count_recordsets(self, context, criterion=None):
        query = select([func.count(tables.recordsets.c.id)])
        query = self._apply_criterion(tables.recordsets, query, criterion)
        query = self._apply_tenant_criteria(context, tables.recordsets, query)
        query = self._apply_deleted_criteria(context, tables.recordsets, query)

        resultproxy = self.session.execute(query)
        result = resultproxy.fetchone()

        if result is None:
            return 0

        return result[0]

    # Record Methods
    def _find_records(self, context, criterion, one=False, marker=None,
                      limit=None, sort_key=None, sort_dir=None):
        return self._find(
            context, tables.records, objects.Record, objects.RecordList,
            exceptions.RecordNotFound, criterion, one, marker, limit,
            sort_key, sort_dir)

    def _recalculate_record_hash(self, record):
        """
        Calculates the hash of the record, used to ensure record uniqueness.
        """
        md5 = hashlib.md5()
        md5.update("%s:%s:%s" % (record.recordset_id, record.data,
                                 record.priority))

        return md5.hexdigest()

    def create_record(self, context, domain_id, recordset_id, record):
        # Fetch the domain as we need the tenant_id
        domain = self._find_domains(context, {'id': domain_id}, one=True)

        record.tenant_id = domain.tenant_id
        record.domain_id = domain_id
        record.recordset_id = recordset_id
        record.hash = self._recalculate_record_hash(record)

        return self._create(
            tables.records, record, exceptions.DuplicateRecord)

    def get_record(self, context, record_id):
        return self._find_records(context, {'id': record_id}, one=True)

    def find_records(self, context, criterion=None, marker=None, limit=None,
                     sort_key=None, sort_dir=None):
        return self._find_records(context, criterion, marker=marker,
                                  limit=limit, sort_key=sort_key,
                                  sort_dir=sort_dir)

    def find_record(self, context, criterion):
        return self._find_records(context, criterion, one=True)

    def update_record(self, context, record):
        if record.obj_what_changed():
            record.hash = self._recalculate_record_hash(record)

        return self._update(
            context, tables.records, record, exceptions.DuplicateRecord,
            exceptions.RecordNotFound)

    def delete_record(self, context, record_id):
        # Fetch the existing record, we'll need to return it.
        record = self._find_records(context, {'id': record_id}, one=True)
        return self._delete(context, tables.records, record,
                            exceptions.RecordNotFound)

    def count_records(self, context, criterion=None):
        query = select([func.count(tables.records.c.id)])
        query = self._apply_criterion(tables.records, query, criterion)
        query = self._apply_tenant_criteria(context, tables.records, query)
        query = self._apply_deleted_criteria(context, tables.records, query)

        resultproxy = self.session.execute(query)
        result = resultproxy.fetchone()

        if result is None:
            return 0

        return result[0]

    # Blacklist Methods
    def _find_blacklists(self, context, criterion, one=False, marker=None,
                         limit=None, sort_key=None, sort_dir=None):
        return self._find(
            context, tables.blacklists, objects.Blacklist,
            objects.BlacklistList, exceptions.BlacklistNotFound, criterion,
            one, marker, limit, sort_key, sort_dir)

    def create_blacklist(self, context, blacklist):
        return self._create(
            tables.blacklists, blacklist, exceptions.DuplicateBlacklist)

    def get_blacklist(self, context, blacklist_id):
        return self._find_blacklists(context, {'id': blacklist_id}, one=True)

    def find_blacklists(self, context, criterion=None, marker=None, limit=None,
                        sort_key=None, sort_dir=None):
        return self._find_blacklists(context, criterion, marker=marker,
                                     limit=limit, sort_key=sort_key,
                                     sort_dir=sort_dir)

    def find_blacklist(self, context, criterion):
        return self._find_blacklists(context, criterion, one=True)

    def update_blacklist(self, context, blacklist):
        return self._update(
            context, tables.blacklists, blacklist,
            exceptions.DuplicateBlacklist, exceptions.BlacklistNotFound)

    def delete_blacklist(self, context, blacklist_id):
        # Fetch the existing blacklist, we'll need to return it.
        blacklist = self._find_blacklists(
            context, {'id': blacklist_id}, one=True)

        return self._delete(context, tables.blacklists, blacklist,
                            exceptions.BlacklistNotFound)

    # diagnostics
    def ping(self, context):
        start_time = time.time()

        try:
            result = self.engine.execute('SELECT 1').first()
        except Exception:
            status = False
        else:
            status = True if result[0] == 1 else False

        return {
            'status': status,
            'rtt': "%f" % (time.time() - start_time)
        }
