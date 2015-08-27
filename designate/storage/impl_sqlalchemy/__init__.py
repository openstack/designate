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
import hashlib

from oslo_config import cfg
from oslo_log import log as logging
from oslo_db import options
from sqlalchemy import select, distinct, func
from sqlalchemy.sql.expression import or_

from designate import exceptions
from designate import objects
from designate.sqlalchemy import base as sqlalchemy_base
from designate.storage import base as storage_base
from designate.storage.impl_sqlalchemy import tables


LOG = logging.getLogger(__name__)

cfg.CONF.register_group(cfg.OptGroup(
    name='storage:sqlalchemy', title="Configuration for SQLAlchemy Storage"
))

cfg.CONF.register_opts(options.database_opts, group='storage:sqlalchemy')


class SQLAlchemyStorage(sqlalchemy_base.SQLAlchemy, storage_base.Storage):
    """SQLAlchemy connection"""
    __plugin_name__ = 'sqlalchemy'

    def __init__(self):
        super(SQLAlchemyStorage, self).__init__()

    def get_name(self):
        return self.name

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
        # Check to see if the criterion can use the reverse_name column
        criterion = self._rname_check(criterion)

        domains = self._find(
            context, tables.domains, objects.Domain, objects.DomainList,
            exceptions.DomainNotFound, criterion, one, marker, limit,
            sort_key, sort_dir)

        def _load_relations(domain):
            if domain.type == 'SECONDARY':
                domain.masters = self._find_domain_masters(
                    context, {'domain_id': domain.id})
            else:
                # This avoids an extra DB call per primary zone. This will
                # always have 0 results for a PRIMARY zone.
                domain.masters = objects.DomainMasterList()

            domain.attributes = self._find_domain_masters(
                context, {'domain_id': domain.id})

            domain.obj_reset_changes(['masters', 'attributes'])

        if one:
            _load_relations(domains)
        else:
            domains.total_count = self.count_domains(context, criterion)
            for d in domains:
                _load_relations(d)

        return domains

    def create_domain(self, context, domain):
        # Patch in the reverse_name column
        extra_values = {"reverse_name": domain.name[::-1]}

        # Don't handle recordsets for now
        domain = self._create(
            tables.domains, domain, exceptions.DuplicateDomain,
            ['attributes', 'recordsets', 'masters'],
            extra_values=extra_values)

        if domain.obj_attr_is_set('attributes'):
            for attrib in domain.attributes:
                self.create_domain_attribute(context, domain.id, attrib)
        else:
            domain.attributes = objects.DomainAttributeList()
        if domain.obj_attr_is_set('masters'):
            for master in domain.masters:
                self.create_domain_master(context, domain.id, master)
        else:
            domain.masters = objects.DomainMasterList()
        domain.obj_reset_changes(['masters', 'attributes'])

        return domain

    def get_domain(self, context, domain_id):
        domain = self._find_domains(context, {'id': domain_id}, one=True)
        return domain

    def find_domains(self, context, criterion=None, marker=None, limit=None,
                     sort_key=None, sort_dir=None):
        domains = self._find_domains(context, criterion, marker=marker,
                                     limit=limit, sort_key=sort_key,
                                     sort_dir=sort_dir)
        return domains

    def find_domain(self, context, criterion):
        domain = self._find_domains(context, criterion, one=True)
        return domain

    def update_domain(self, context, domain):
        tenant_id_changed = False
        if 'tenant_id' in domain.obj_what_changed():
            tenant_id_changed = True

        # Don't handle recordsets for now
        updated_domain = self._update(
            context, tables.domains, domain, exceptions.DuplicateDomain,
            exceptions.DomainNotFound,
            ['attributes', 'recordsets', 'masters'])

        if domain.obj_attr_is_set('attributes'):
            # Gather the Attribute ID's we have
            have = set([r.id for r in self._find_domain_attributes(
                context, {'domain_id': domain.id})])

            # Prep some lists of changes
            keep = set([])
            create = []
            update = []

            # Determine what to change
            for i in domain.attributes:
                keep.add(i.id)
                try:
                    i.obj_get_original_value('id')
                except KeyError:
                    create.append(i)
                else:
                    update.append(i)

            # NOTE: Since we're dealing with mutable objects, the return value
            #       of create/update/delete attribute is not needed.
            #       The original item will be mutated in place on the input
            #       "domain.attributes" list.

            # Delete Attributes
            for i_id in have - keep:
                attr = self._find_domain_attributes(
                    context, {'id': i_id}, one=True)
                self.delete_domain_attribute(context, attr.id)

            # Update Attributes
            for i in update:
                self.update_domain_attribute(context, i)

            # Create Attributes
            for attr in create:
                attr.domain_id = domain.id
                self.create_domain_attribute(context, domain.id, attr)

        if domain.obj_attr_is_set('masters'):
            # Gather the Attribute ID's we have
            have = set([r.id for r in self._find_domain_masters(
                context, {'domain_id': domain.id})])

            # Prep some lists of changes
            keep = set([])
            create = []
            update = []

            # Determine what to change
            for i in domain.masters:
                keep.add(i.id)
                try:
                    i.obj_get_original_value('id')
                except KeyError:
                    create.append(i)
                else:
                    update.append(i)

            # NOTE: Since we're dealing with mutable objects, the return value
            #       of create/update/delete attribute is not needed.
            #       The original item will be mutated in place on the input
            #       "domain.attributes" list.

            # Delete Attributes
            for i_id in have - keep:
                attr = self._find_domain_masters(
                    context, {'id': i_id}, one=True)
                self.delete_domain_master(context, attr.id)

            # Update Attributes
            for i in update:
                self.update_domain_master(context, i)

            # Create Attributes
            for attr in create:
                attr.domain_id = domain.id
                self.create_domain_master(context, domain.id, attr)

        if domain.obj_attr_is_set('recordsets'):
            existing = self.find_recordsets(context, {'domain_id': domain.id})

            data = {}
            for rrset in existing:
                data[rrset.name, rrset.type] = rrset

            keep = set()
            for rrset in domain.recordsets:
                current = data.get((rrset.name, rrset.type))

                if current:
                    current.update(rrset)
                    current.records = rrset.records
                    self.update_recordset(context, current)
                    keep.add(current.id)
                else:
                    self.create_recordset(context, domain.id, rrset)
                    keep.add(rrset.id)

            if domain.type == 'SECONDARY':
                # Purge anything that shouldn't be there :P
                for i in set([i.id for i in data.values()]) - keep:
                    self.delete_recordset(context, i)

        if tenant_id_changed:
            recordsets_query = tables.recordsets.update().\
                where(tables.recordsets.c.domain_id == domain.id)\
                .values({'tenant_id': domain.tenant_id})

            records_query = tables.records.update().\
                where(tables.records.c.domain_id == domain.id).\
                values({'tenant_id': domain.tenant_id})

            self.session.execute(records_query)
            self.session.execute(recordsets_query)

        return updated_domain

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

    # Domain attribute methods
    def _find_domain_attributes(self, context, criterion, one=False,
                                marker=None, limit=None, sort_key=None,
                                sort_dir=None):
        return self._find(context, tables.domain_attributes,
                          objects.DomainAttribute, objects.DomainAttributeList,
                          exceptions.DomainAttributeNotFound, criterion, one,
                          marker, limit, sort_key, sort_dir)

    def create_domain_attribute(self, context, domain_id, domain_attribute):
        domain_attribute.domain_id = domain_id
        return self._create(tables.domain_attributes, domain_attribute,
                            exceptions.DuplicateDomainAttribute)

    def get_domain_attributes(self, context, domain_attribute_id):
        return self._find_domain_attributes(
            context, {'id': domain_attribute_id}, one=True)

    def find_domain_attributes(self, context, criterion=None, marker=None,
                   limit=None, sort_key=None, sort_dir=None):
        return self._find_domain_attributes(context, criterion, marker=marker,
                                            limit=limit, sort_key=sort_key,
                                            sort_dir=sort_dir)

    def find_domain_attribute(self, context, criterion):
        return self._find_domain_attributes(context, criterion, one=True)

    def update_domain_attribute(self, context, domain_attribute):
        return self._update(context, tables.domain_attributes,
                            domain_attribute,
                            exceptions.DuplicateDomainAttribute,
                            exceptions.DomainAttributeNotFound)

    def delete_domain_attribute(self, context, domain_attribute_id):
        domain_attribute = self._find_domain_attributes(
            context, {'id': domain_attribute_id}, one=True)
        deleted_domain_attribute = self._delete(
            context, tables.domain_attributes, domain_attribute,
            exceptions.DomainAttributeNotFound)

        return deleted_domain_attribute

    # Domain master methods
    def _find_domain_masters(self, context, criterion, one=False,
                             marker=None, limit=None, sort_key=None,
                             sort_dir=None):

        criterion['key'] = 'master'

        attribs = self._find(context, tables.domain_attributes,
                             objects.DomainAttribute,
                             objects.DomainAttributeList,
                             exceptions.DomainMasterNotFound,
                             criterion, one,
                             marker, limit, sort_key, sort_dir)

        masters = objects.DomainMasterList()

        for attrib in attribs:
            masters.append(objects.DomainMaster().from_data(attrib.value))

        return masters

    def create_domain_master(self, context, domain_id, domain_master):

        domain_attribute = objects.DomainAttribute()
        domain_attribute.domain_id = domain_id
        domain_attribute.key = 'master'
        domain_attribute.value = domain_master.to_data()

        return self._create(tables.domain_attributes, domain_attribute,
                            exceptions.DuplicateDomainAttribute)

    def get_domain_masters(self, context, domain_attribute_id):
        return self._find_domain_masters(
            context, {'id': domain_attribute_id}, one=True)

    def find_domain_masters(self, context, criterion=None, marker=None,
                   limit=None, sort_key=None, sort_dir=None):
        return self._find_domain_masters(context, criterion, marker=marker,
                                         limit=limit, sort_key=sort_key,
                                         sort_dir=sort_dir)

    def find_domain_master(self, context, criterion):
        return self._find_domain_master(context, criterion, one=True)

    def update_domain_master(self, context, domain_master):

        domain_attribute = objects.DomainAttribute()
        domain_attribute.domain_id = domain_master.domain_id
        domain_attribute.key = 'master'
        domain_attribute.value = domain_master.to_data()

        return self._update(context, tables.domain_attributes,
                            domain_attribute,
                            exceptions.DuplicateDomainAttribute,
                            exceptions.DomainAttributeNotFound)

    def delete_domain_master(self, context, domain_master_id):
        domain_attribute = self._find_domain_attributes(
            context, {'id': domain_master_id}, one=True)
        deleted_domain_attribute = self._delete(
            context, tables.domain_attributes, domain_attribute,
            exceptions.DomainAttributeNotFound)

        return deleted_domain_attribute

    # RecordSet Methods
    def _find_recordsets(self, context, criterion, one=False, marker=None,
                         limit=None, sort_key=None, sort_dir=None):

        # Check to see if the criterion can use the reverse_name column
        criterion = self._rname_check(criterion)

        if criterion is not None \
                and not criterion.get('domains_deleted', True):
            # remove 'domains_deleted' from the criterion, as _apply_criterion
            # assumes each key in criterion to be a column name.
            del criterion['domains_deleted']

        if one:
            rjoin = tables.recordsets.join(
                tables.domains,
                tables.recordsets.c.domain_id == tables.domains.c.id)
            query = select([tables.recordsets]).select_from(rjoin).\
                where(tables.domains.c.deleted == '0')

            recordsets = self._find(
                context, tables.recordsets, objects.RecordSet,
                objects.RecordSetList, exceptions.RecordSetNotFound, criterion,
                one, marker, limit, sort_key, sort_dir, query)

            recordsets.records = self._find_records(
                context, {'recordset_id': recordsets.id})

            recordsets.obj_reset_changes(['records'])

        else:
            recordsets = self._find_recordsets_with_records(
                context, tables.recordsets, objects.RecordSet,
                objects.RecordSetList, exceptions.RecordSetNotFound, criterion,
                load_relations=True, relation_table=tables.records,
                relation_cls=objects.Record,
                relation_list_cls=objects.RecordList, limit=limit,
                marker=marker, sort_key=sort_key, sort_dir=sort_dir)

            recordsets.total_count = self.count_recordsets(context, criterion)

        return recordsets

    def find_recordsets_axfr(self, context, criterion=None):
        query = None

        # Check to see if the criterion can use the reverse_name column
        criterion = self._rname_check(criterion)

        rjoin = tables.records.join(
            tables.recordsets,
            tables.records.c.recordset_id == tables.recordsets.c.id)

        query = select([tables.recordsets.c.id, tables.recordsets.c.type,
                        tables.recordsets.c.ttl, tables.recordsets.c.name,
                        tables.records.c.data, tables.records.c.action]).\
            select_from(rjoin).where(tables.records.c.action != 'DELETE')

        query = query.order_by(tables.recordsets.c.id)

        raw_rows = self._select_raw(
            context, tables.recordsets, criterion, query)

        return raw_rows

    def create_recordset(self, context, domain_id, recordset):
        # Fetch the domain as we need the tenant_id
        domain = self._find_domains(context, {'id': domain_id}, one=True)

        recordset.tenant_id = domain.tenant_id
        recordset.domain_id = domain_id

        # Patch in the reverse_name column
        extra_values = {"reverse_name": recordset.name[::-1]}

        recordset = self._create(
            tables.recordsets, recordset, exceptions.DuplicateRecordSet,
            ['records'], extra_values=extra_values)

        if recordset.obj_attr_is_set('records'):
            for record in recordset.records:
                # NOTE: Since we're dealing with a mutable object, the return
                #       value is not needed. The original item will be mutated
                #       in place on the input "recordset.records" list.
                self.create_record(context, domain_id, recordset.id, record)
        else:
            recordset.records = objects.RecordList()

        recordset.obj_reset_changes(['records'])

        return recordset

    def find_recordsets_export(self, context, criterion=None):
        query = None

        rjoin = tables.records.join(
            tables.recordsets,
            tables.records.c.recordset_id == tables.recordsets.c.id)

        query = select([tables.recordsets.c.name, tables.recordsets.c.ttl,
                        tables.recordsets.c.type, tables.records.c.data]).\
            select_from(rjoin)

        query = query.order_by(tables.recordsets.c.created_at)

        raw_rows = self._select_raw(
            context, tables.recordsets, criterion, query)

        return raw_rows

    def get_recordset(self, context, recordset_id):
        return self._find_recordsets(context, {'id': recordset_id}, one=True)

    def find_recordsets(self, context, criterion=None, marker=None, limit=None,
                        sort_key=None, sort_dir=None):
        return self._find_recordsets(context, criterion, marker=marker,
                                     limit=limit, sort_key=sort_key,
                                     sort_dir=sort_dir)

    def find_recordset(self, context, criterion):
        return self._find_recordsets(context, criterion, one=True)

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
        # Ensure that we return only active recordsets
        rjoin = tables.recordsets.join(
            tables.domains,
            tables.recordsets.c.domain_id == tables.domains.c.id)

        query = select([func.count(tables.recordsets.c.id)]).\
            select_from(rjoin).\
            where(tables.domains.c.deleted == '0')

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
        md5.update(("%s:%s" % (record.recordset_id,
                               record.data)).encode('utf-8'))

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
        # Ensure that we return only active records
        rjoin = tables.records.join(
            tables.domains,
            tables.records.c.domain_id == tables.domains.c.id)

        query = select([func.count(tables.records.c.id)]).\
            select_from(rjoin).\
            where(tables.domains.c.deleted == '0')

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

    # Pool methods
    def _find_pools(self, context, criterion, one=False, marker=None,
                    limit=None, sort_key=None, sort_dir=None):
        pools = self._find(context, tables.pools, objects.Pool,
                           objects.PoolList, exceptions.PoolNotFound,
                           criterion, one, marker, limit, sort_key,
                           sort_dir)

        # Load Relations
        def _load_relations(pool):
            pool.attributes = self._find_pool_attributes(
                context, {'pool_id': pool.id})

            pool.ns_records = self._find_pool_ns_records(
                context, {'pool_id': pool.id})

            pool.obj_reset_changes(['attributes', 'ns_records'])

        if one:
            _load_relations(pools)
        else:
            for pool in pools:
                _load_relations(pool)

        return pools

    def create_pool(self, context, pool):
        pool = self._create(
            tables.pools, pool, exceptions.DuplicatePool,
            ['attributes', 'ns_records'])

        if pool.obj_attr_is_set('attributes'):
            for pool_attribute in pool.attributes:
                self.create_pool_attribute(context, pool.id, pool_attribute)
        else:
            pool.attributes = objects.PoolAttributeList()

        if pool.obj_attr_is_set('ns_records'):
            for ns_record in pool.ns_records:
                self.create_pool_ns_record(context, pool.id, ns_record)
        else:
            pool.ns_records = objects.PoolNsRecordList()

        pool.obj_reset_changes(['attributes', 'ns_records'])

        return pool

    def get_pool(self, context, pool_id):
        return self._find_pools(context, {'id': pool_id}, one=True)

    def find_pools(self, context, criterion=None, marker=None,
                   limit=None, sort_key=None, sort_dir=None):
        return self._find_pools(context, criterion, marker=marker,
                                limit=limit, sort_key=sort_key,
                                sort_dir=sort_dir)

    def find_pool(self, context, criterion):
        return self._find_pools(context, criterion, one=True)

    def update_pool(self, context, pool):
        pool = self._update(context, tables.pools, pool,
                            exceptions.DuplicatePool, exceptions.PoolNotFound,
                            ['attributes', 'ns_records'])

        # TODO(kiall): These two sections below are near identical, we should
        #              refactor into a single reusable method.
        if pool.obj_attr_is_set('attributes'):
            # Gather the pool ID's we have
            have_attributes = set([r.id for r in self._find_pool_attributes(
                context, {'pool_id': pool.id})])

            # Prep some lists of changes
            keep_attributes = set([])
            create_attributes = []
            update_attributes = []

            attributes = []
            if pool.obj_attr_is_set('attributes'):
                for r in pool.attributes.objects:
                    attributes.append(r)

            # Determine what to change
            for attribute in attributes:
                keep_attributes.add(attribute.id)
                try:
                    attribute.obj_get_original_value('id')
                except KeyError:
                    create_attributes.append(attribute)
                else:
                    update_attributes.append(attribute)

            # NOTE: Since we're dealing with mutable objects, the return value
            #       of create/update/delete attribute is not needed. The
            #       original item will be mutated in place on the input
            #       "pool.attributes" list.

            # Delete attributes
            for attribute_id in have_attributes - keep_attributes:
                self.delete_pool_attribute(context, attribute_id)

            # Update attributes
            for attribute in update_attributes:
                self.update_pool_attribute(context, attribute)

            # Create attributes
            for attribute in create_attributes:
                self.create_pool_attribute(
                    context, pool.id, attribute)

        if pool.obj_attr_is_set('ns_records'):
            # Gather the pool ID's we have
            have_ns_records = set([r.id for r in self._find_pool_ns_records(
                context, {'pool_id': pool.id})])

            # Prep some lists of changes
            keep_ns_records = set([])
            create_ns_records = []
            update_ns_records = []

            ns_records = []
            if pool.obj_attr_is_set('ns_records'):
                for r in pool.ns_records.objects:
                    ns_records.append(r)

            # Determine what to change
            for ns_record in ns_records:
                keep_ns_records.add(ns_record.id)
                try:
                    ns_record.obj_get_original_value('id')
                except KeyError:
                    create_ns_records.append(ns_record)
                else:
                    update_ns_records.append(ns_record)

            # NOTE: Since we're dealing with mutable objects, the return value
            #       of create/update/delete ns_record is not needed. The
            #       original item will be mutated in place on the input
            #       "pool.ns_records" list.

            # Delete ns_records
            for ns_record_id in have_ns_records - keep_ns_records:
                self.delete_pool_ns_record(context, ns_record_id)

            # Update ns_records
            for ns_record in update_ns_records:
                self.update_pool_ns_record(context, ns_record)

            # Create ns_records
            for ns_record in create_ns_records:
                self.create_pool_ns_record(
                    context, pool.id, ns_record)

        # Call get_pool to get the ids of all the attributes/ns_records
        # refreshed in the pool object
        updated_pool = self.get_pool(context, pool.id)

        return updated_pool

    def delete_pool(self, context, pool_id):
        pool = self._find_pools(context, {'id': pool_id}, one=True)

        return self._delete(context, tables.pools, pool,
                            exceptions.PoolNotFound)

    # Pool attribute methods
    def _find_pool_attributes(self, context, criterion, one=False, marker=None,
                    limit=None, sort_key=None, sort_dir=None):
        return self._find(context, tables.pool_attributes,
                          objects.PoolAttribute, objects.PoolAttributeList,
                          exceptions.PoolAttributeNotFound, criterion, one,
                          marker, limit, sort_key, sort_dir)

    def create_pool_attribute(self, context, pool_id, pool_attribute):
        pool_attribute.pool_id = pool_id

        return self._create(tables.pool_attributes, pool_attribute,
                            exceptions.DuplicatePoolAttribute)

    def get_pool_attribute(self, context, pool_attribute_id):
        return self._find_pool_attributes(
            context, {'id': pool_attribute_id}, one=True)

    def find_pool_attributes(self, context, criterion=None, marker=None,
                   limit=None, sort_key=None, sort_dir=None):
        return self._find_pool_attributes(context, criterion, marker=marker,
                                          limit=limit, sort_key=sort_key,
                                          sort_dir=sort_dir)

    def find_pool_attribute(self, context, criterion):
        return self._find_pool_attributes(context, criterion, one=True)

    def update_pool_attribute(self, context, pool_attribute):
        return self._update(context, tables.pool_attributes, pool_attribute,
                            exceptions.DuplicatePoolAttribute,
                            exceptions.PoolAttributeNotFound)

    def delete_pool_attribute(self, context, pool_attribute_id):
        pool_attribute = self._find_pool_attributes(
            context, {'id': pool_attribute_id}, one=True)
        deleted_pool_attribute = self._delete(
            context, tables.pool_attributes, pool_attribute,
            exceptions.PoolAttributeNotFound)

        return deleted_pool_attribute

    # Pool ns_record methods
    def _find_pool_ns_records(self, context, criterion, one=False, marker=None,
                    limit=None, sort_key=None, sort_dir=None):
        return self._find(context, tables.pool_ns_records,
                          objects.PoolNsRecord, objects.PoolNsRecordList,
                          exceptions.PoolNsRecordNotFound, criterion, one,
                          marker, limit, sort_key, sort_dir)

    def create_pool_ns_record(self, context, pool_id, pool_ns_record):
        pool_ns_record.pool_id = pool_id

        return self._create(tables.pool_ns_records, pool_ns_record,
                            exceptions.DuplicatePoolNsRecord)

    def get_pool_ns_record(self, context, pool_ns_record_id):
        return self._find_pool_ns_records(
            context, {'id': pool_ns_record_id}, one=True)

    def find_pool_ns_records(self, context, criterion=None, marker=None,
                   limit=None, sort_key=None, sort_dir=None):
        return self._find_pool_ns_records(context, criterion, marker=marker,
                                          limit=limit, sort_key=sort_key,
                                          sort_dir=sort_dir)

    def find_pool_ns_record(self, context, criterion):
        return self._find_pool_ns_records(context, criterion, one=True)

    def update_pool_ns_record(self, context, pool_ns_record):
        return self._update(context, tables.pool_ns_records, pool_ns_record,
                            exceptions.DuplicatePoolNsRecord,
                            exceptions.PoolNsRecordNotFound)

    def delete_pool_ns_record(self, context, pool_ns_record_id):
        pool_ns_record = self._find_pool_ns_records(
            context, {'id': pool_ns_record_id}, one=True)
        deleted_pool_ns_record = self._delete(
            context, tables.pool_ns_records, pool_ns_record,
            exceptions.PoolNsRecordNotFound)

        return deleted_pool_ns_record

    # Zone Transfer Methods
    def _find_zone_transfer_requests(self, context, criterion, one=False,
                                     marker=None, limit=None, sort_key=None,
                                     sort_dir=None):

        table = tables.zone_transfer_requests

        ljoin = tables.zone_transfer_requests.join(
            tables.domains,
            tables.zone_transfer_requests.c.domain_id == tables.domains.c.id)

        query = select(
            [table, tables.domains.c.name.label("domain_name")]
        ).select_from(ljoin)

        if not context.all_tenants:
            query = query.where(or_(
                table.c.tenant_id == context.tenant,
                table.c.target_tenant_id == context.tenant))

        return self._find(
            context, table, objects.ZoneTransferRequest,
            objects.ZoneTransferRequestList,
            exceptions.ZoneTransferRequestNotFound,
            criterion,
            one=one, marker=marker, limit=limit, sort_dir=sort_dir,
            sort_key=sort_key, query=query, apply_tenant_criteria=False
        )

    def create_zone_transfer_request(self, context, zone_transfer_request):

        try:
            criterion = {"domain_id": zone_transfer_request.domain_id,
                         "status": "ACTIVE"}
            self.find_zone_transfer_request(
                context, criterion)
        except exceptions.ZoneTransferRequestNotFound:
            return self._create(
                tables.zone_transfer_requests,
                zone_transfer_request,
                exceptions.DuplicateZoneTransferRequest)
        else:
            raise exceptions.DuplicateZoneTransferRequest()

    def find_zone_transfer_requests(self, context, criterion=None,
                                    marker=None, limit=None, sort_key=None,
                                    sort_dir=None):

        return self._find_zone_transfer_requests(
            context, criterion, marker=marker,
            limit=limit, sort_key=sort_key,
            sort_dir=sort_dir)

    def get_zone_transfer_request(self, context, zone_transfer_request_id):
        request = self._find_zone_transfer_requests(
            context,
            {'id': zone_transfer_request_id},
            one=True)

        return request

    def find_zone_transfer_request(self, context, criterion):

        return self._find_zone_transfer_requests(context, criterion, one=True)

    def update_zone_transfer_request(self, context, zone_transfer_request):

        zone_transfer_request.obj_reset_changes(('domain_name'))

        updated_zt_request = self._update(
            context,
            tables.zone_transfer_requests,
            zone_transfer_request,
            exceptions.DuplicateZoneTransferRequest,
            exceptions.ZoneTransferRequestNotFound,
            skip_values=['domain_name'])

        return updated_zt_request

    def delete_zone_transfer_request(self, context, zone_transfer_request_id):

        zone_transfer_request = self._find_zone_transfer_requests(
            context,
            {'id': zone_transfer_request_id},
            one=True)

        return self._delete(
            context,
            tables.zone_transfer_requests,
            zone_transfer_request,
            exceptions.ZoneTransferRequestNotFound)

    def _find_zone_transfer_accept(self, context, criterion, one=False,
                                   marker=None, limit=None, sort_key=None,
                                   sort_dir=None):

            return self._find(
                context, tables.zone_transfer_accepts,
                objects.ZoneTransferAccept,
                objects.ZoneTransferAcceptList,
                exceptions.ZoneTransferAcceptNotFound, criterion,
                one, marker, limit, sort_key, sort_dir)

    def create_zone_transfer_accept(self, context, zone_transfer_accept):

        return self._create(
            tables.zone_transfer_accepts,
            zone_transfer_accept,
            exceptions.DuplicateZoneTransferAccept)

    def find_zone_transfer_accepts(self, context, criterion=None,
                                   marker=None, limit=None, sort_key=None,
                                   sort_dir=None):
        return self._find_zone_transfer_accept(
            context, criterion, marker=marker, limit=limit, sort_key=sort_key,
            sort_dir=sort_dir)

    def get_zone_transfer_accept(self, context, zone_transfer_accept_id):
        return self._find_zone_transfer_accept(
            context,
            {'id': zone_transfer_accept_id},
            one=True)

    def find_zone_transfer_accept(self, context, criterion):
        return self._find_zone_transfer_accept(
            context,
            criterion,
            one=True)

    def update_zone_transfer_accept(self, context, zone_transfer_accept):

        return self._update(
            context,
            tables.zone_transfer_accepts,
            zone_transfer_accept,
            exceptions.DuplicateZoneTransferAccept,
            exceptions.ZoneTransferAcceptNotFound)

    def delete_zone_transfer_accept(self, context, zone_transfer_accept_id):

        zone_transfer_accept = self._find_zone_transfer_accept(
            context,
            {'id': zone_transfer_accept_id},
            one=True)

        return self._delete(
            context,
            tables.zone_transfer_accepts,
            zone_transfer_accept,
            exceptions.ZoneTransferAcceptNotFound)

    # Zone Import Methods
    def _find_zone_imports(self, context, criterion, one=False, marker=None,
                   limit=None, sort_key=None, sort_dir=None):
        if not criterion:
            criterion = {}
        criterion['task_type'] = 'IMPORT'
        return self._find(
            context, tables.zone_tasks, objects.ZoneImport,
            objects.ZoneImportList, exceptions.ZoneImportNotFound, criterion,
            one, marker, limit, sort_key, sort_dir)

    def create_zone_import(self, context, zone_import):
        return self._create(
            tables.zone_tasks, zone_import, exceptions.DuplicateZoneImport)

    def get_zone_import(self, context, zone_import_id):
        return self._find_zone_imports(context, {'id': zone_import_id},
                                     one=True)

    def find_zone_imports(self, context, criterion=None, marker=None,
                  limit=None, sort_key=None, sort_dir=None):
        return self._find_zone_imports(context, criterion, marker=marker,
                               limit=limit, sort_key=sort_key,
                               sort_dir=sort_dir)

    def find_zone_import(self, context, criterion):
        return self._find_zone_imports(context, criterion, one=True)

    def update_zone_import(self, context, zone_import):
        return self._update(
            context, tables.zone_tasks, zone_import,
            exceptions.DuplicateZoneImport, exceptions.ZoneImportNotFound)

    def delete_zone_import(self, context, zone_import_id):
        # Fetch the existing zone_import, we'll need to return it.
        zone_import = self._find_zone_imports(context, {'id': zone_import_id},
                                one=True)
        return self._delete(context, tables.zone_tasks, zone_import,
                    exceptions.ZoneImportNotFound)

    # Zone Export Methods
    def _find_zone_exports(self, context, criterion, one=False, marker=None,
                   limit=None, sort_key=None, sort_dir=None):
        if not criterion:
            criterion = {}
        criterion['task_type'] = 'EXPORT'
        return self._find(
            context, tables.zone_tasks, objects.ZoneExport,
            objects.ZoneExportList, exceptions.ZoneExportNotFound, criterion,
            one, marker, limit, sort_key, sort_dir)

    def create_zone_export(self, context, zone_export):
        return self._create(
            tables.zone_tasks, zone_export, exceptions.DuplicateZoneExport)

    def get_zone_export(self, context, zone_export_id):
        return self._find_zone_exports(context, {'id': zone_export_id},
                                     one=True)

    def find_zone_exports(self, context, criterion=None, marker=None,
                  limit=None, sort_key=None, sort_dir=None):
        return self._find_zone_exports(context, criterion, marker=marker,
                               limit=limit, sort_key=sort_key,
                               sort_dir=sort_dir)

    def find_zone_export(self, context, criterion):
        return self._find_zone_exports(context, criterion, one=True)

    def update_zone_export(self, context, zone_export):
        return self._update(
            context, tables.zone_tasks, zone_export,
            exceptions.DuplicateZoneExport, exceptions.ZoneExportNotFound)

    def delete_zone_export(self, context, zone_export_id):
        # Fetch the existing zone_export, we'll need to return it.
        zone_export = self._find_zone_exports(context, {'id': zone_export_id},
                                one=True)
        return self._delete(context, tables.zone_tasks, zone_export,
                    exceptions.ZoneExportNotFound)

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

    # Reverse Name utils
    def _rname_check(self, criterion):
        # If the criterion has 'name' in it, switch it out for reverse_name
        if criterion is not None and criterion.get('name', "").startswith('*'):
                criterion['reverse_name'] = criterion.pop('name')[::-1]
        return criterion
