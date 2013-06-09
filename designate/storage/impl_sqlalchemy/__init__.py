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
from sqlalchemy.orm import exc
from sqlalchemy import distinct, func
from designate.openstack.common import cfg
from designate.openstack.common import log as logging
from designate import exceptions
from designate.storage import base
from designate.storage.impl_sqlalchemy import models
from designate.sqlalchemy.session import get_session
from designate.sqlalchemy.session import get_engine
from designate.sqlalchemy.session import SQLOPTS

LOG = logging.getLogger(__name__)

cfg.CONF.register_group(cfg.OptGroup(
    name='storage:sqlalchemy', title="Configuration for SQLAlchemy Storage"
))

cfg.CONF.register_opts(SQLOPTS, group='storage:sqlalchemy')


class SQLAlchemyStorage(base.Storage):
    """ SQLAlchemy connection """
    __plugin_name__ = 'sqlalchemy'

    def __init__(self):
        super(SQLAlchemyStorage, self).__init__()

        self.engine = get_engine(self.name)
        self.session = get_session(self.name)

    def setup_schema(self):
        """ Semi-Private Method to create the database schema """
        models.Base.metadata.create_all(self.session.bind)

    def teardown_schema(self):
        """ Semi-Private Method to reset the database schema """
        models.Base.metadata.drop_all(self.session.bind)

    def _apply_criterion(self, model, query, criterion):
        if criterion:
            for name, value in criterion.items():
                column = getattr(model, name)

                if isinstance(value, basestring) and '%' in value:
                    query = query.filter(column.like(value))
                else:
                    query = query.filter(column == value)

        return query

    # Quota Methods
    def create_quota(self, context, values):
        quota = models.Quota()

        quota.update(values)

        try:
            quota.save(self.session)
        except exceptions.Duplicate:
            raise exceptions.DuplicateQuota()

        return dict(quota)

    def get_quotas(self, context, criterion=None):
        query = self.session.query(models.Quota)
        query = self._apply_criterion(models.Quota, query, criterion)

        try:
            result = query.all()
        except exc.NoResultFound:
            LOG.debug('No results found')
            return []
        else:
            return [dict(o) for o in result]

    def _get_quota(self, context, quota_id):
        query = self.session.query(models.Quota)

        quota = query.get(quota_id)

        if not quota:
            raise exceptions.QuotaNotFound(quota_id)
        else:
            return quota

    def get_quota(self, context, quota_id):
        quota = self._get_quota(context, quota_id)

        return dict(quota)

    def _find_quotas(self, context, criterion, one=False):
        query = self.session.query(models.Quota)
        query = self._apply_criterion(models.Quota, query, criterion)

        if one:
            try:
                quota = query.one()
                return dict(quota)
            except (exc.NoResultFound, exc.MultipleResultsFound):
                raise exceptions.QuotaNotFound()
        else:
            quotas = query.all()
            return [dict(q) for q in quotas]

    def find_quotas(self, context, criterion):
        return self._find_quotas(context, criterion)

    def find_quota(self, context, criterion):
        return self._find_quotas(context, criterion, one=True)

    def update_quota(self, context, quota_id, values):
        quota = self._get_quota(context, quota_id)

        quota.update(values)

        try:
            quota.save(self.session)
        except exceptions.Duplicate:
            raise exceptions.DuplicateQuota()

        return dict(quota)

    def delete_quota(self, context, quota_id):
        quota = self._get_quota(context, quota_id)

        quota.delete(self.session)

    # Server Methods
    def create_server(self, context, values):
        server = models.Server()

        server.update(values)

        try:
            server.save(self.session)
        except exceptions.Duplicate:
            raise exceptions.DuplicateServer()

        return dict(server)

    def get_servers(self, context, criterion=None):
        query = self.session.query(models.Server)
        query = self._apply_criterion(models.Server, query, criterion)

        try:
            result = query.all()
        except exc.NoResultFound:
            LOG.debug('No results found')
            return []
        else:
            return [dict(o) for o in result]

    def _get_server(self, context, server_id):
        query = self.session.query(models.Server)

        server = query.get(server_id)

        if not server:
            raise exceptions.ServerNotFound(server_id)
        else:
            return server

    def get_server(self, context, server_id):
        server = self._get_server(context, server_id)

        return dict(server)

    def update_server(self, context, server_id, values):
        server = self._get_server(context, server_id)

        server.update(values)

        try:
            server.save(self.session)
        except exceptions.Duplicate:
            raise exceptions.DuplicateServer()

        return dict(server)

    def delete_server(self, context, server_id):
        server = self._get_server(context, server_id)

        server.delete(self.session)

    # TSIG Key Methods
    def create_tsigkey(self, context, values):
        tsigkey = models.TsigKey()

        tsigkey.update(values)

        try:
            tsigkey.save(self.session)
        except exceptions.Duplicate:
            raise exceptions.DuplicateTsigKey()

        return dict(tsigkey)

    def get_tsigkeys(self, context, criterion=None):
        query = self.session.query(models.TsigKey)
        query = self._apply_criterion(models.TsigKey, query, criterion)

        try:
            result = query.all()
        except exc.NoResultFound:
            LOG.debug('No results found')
            return []
        else:
            return [dict(o) for o in result]

    def _get_tsigkey(self, context, tsigkey_id):
        query = self.session.query(models.TsigKey)

        tsigkey = query.get(tsigkey_id)

        if not tsigkey:
            raise exceptions.TsigKeyNotFound(tsigkey_id)
        else:
            return tsigkey

    def get_tsigkey(self, context, tsigkey_id):
        tsigkey = self._get_tsigkey(context, tsigkey_id)

        return dict(tsigkey)

    def update_tsigkey(self, context, tsigkey_id, values):
        tsigkey = self._get_tsigkey(context, tsigkey_id)

        tsigkey.update(values)

        try:
            tsigkey.save(self.session)
        except exceptions.Duplicate:
            raise exceptions.DuplicateTsigKey()

        return dict(tsigkey)

    def delete_tsigkey(self, context, tsigkey_id):
        tsigkey = self._get_tsigkey(context, tsigkey_id)

        tsigkey.delete(self.session)

    # Tenant Methods
    def get_tenants(self, context):
        query = self.session.query(models.Domain.tenant_id,
                                   func.count(models.Domain.id))
        query = query.group_by(models.Domain.tenant_id)

        return [{'id': t[0], 'domain_count': t[1]} for t in query.all()]

    def get_tenant(self, context, tenant_id):
        query = self.session.query(models.Domain.name)
        query = query.filter(models.Domain.tenant_id == tenant_id)

        result = query.all()

        return {
            'id': tenant_id,
            'domain_count': len(result),
            'domains': [r[0] for r in result]
        }

    def count_tenants(self, context):
        # tenants are the owner of domains, count the number of unique tenants
        # select count(distinct tenant_id) from domains
        return self.session.query(distinct(models.Domain.tenant_id)).count()

    # Domain Methods
    def create_domain(self, context, values):
        domain = models.Domain()

        domain.update(values)

        try:
            domain.save(self.session)
        except exceptions.Duplicate:
            raise exceptions.DuplicateDomain()

        return dict(domain)

    def get_domains(self, context, criterion=None):
        query = self.session.query(models.Domain)
        query = self._apply_criterion(models.Domain, query, criterion)

        try:
            result = query.all()
        except exc.NoResultFound:
            LOG.debug('No results found')
            return []
        else:
            return [dict(o) for o in result]

    def _get_domain(self, context, domain_id):
        query = self.session.query(models.Domain)

        domain = query.get(domain_id)

        if not domain:
            raise exceptions.DomainNotFound(domain_id)
        else:
            return domain

    def get_domain(self, context, domain_id):
        domain = self._get_domain(context, domain_id)

        return dict(domain)

    def _find_domains(self, context, criterion, one=False):
        query = self.session.query(models.Domain)
        query = self._apply_criterion(models.Domain, query, criterion)

        if one:
            try:
                domain = query.one()
                return dict(domain)
            except (exc.NoResultFound, exc.MultipleResultsFound):
                raise exceptions.DomainNotFound()
        else:
            domains = query.all()
            return [dict(d) for d in domains]

    def find_domains(self, context, criterion):
        return self._find_domains(context, criterion)

    def find_domain(self, context, criterion):
        return self._find_domains(context, criterion, one=True)

    def update_domain(self, context, domain_id, values):
        domain = self._get_domain(context, domain_id)

        domain.update(values)

        try:
            domain.save(self.session)
        except exceptions.Duplicate:
            raise exceptions.DuplicateDomain()

        return dict(domain)

    def delete_domain(self, context, domain_id):
        domain = self._get_domain(context, domain_id)

        domain.delete(self.session)

    def count_domains(self, context, criterion=None):
        query = self.session.query(models.Domain)
        query = self._apply_criterion(models.Domain, query, criterion)
        return query.count()

    # Record Methods
    def create_record(self, context, domain_id, values):
        record = models.Record()

        record.update(values)
        record.domain_id = domain_id

        record.save(self.session)

        return dict(record)

    def get_records(self, context, domain_id, criterion=None):
        query = self.session.query(models.Record)
        query = query.filter_by(domain_id=domain_id)
        query = self._apply_criterion(models.Record, query, criterion)

        return [dict(o) for o in query.all()]

    def _get_record(self, context, record_id):
        query = self.session.query(models.Record)

        record = query.get(record_id)

        if not record:
            raise exceptions.RecordNotFound(record_id)
        else:
            return record

    def get_record(self, context, record_id):
        record = self._get_record(context, record_id)

        return dict(record)

    def _find_records(self, context, criterion, one=False):
        query = self.session.query(models.Record)
        query = self._apply_criterion(models.Record, query, criterion)

        if one:
            try:
                record = query.one()
                return dict(record)
            except (exc.NoResultFound, exc.MultipleResultsFound):
                raise exceptions.RecordNotFound()
        else:
            records = query.all()
            return [dict(r) for r in records]

    def find_records(self, context, criterion):
        return self._find_records(context, criterion)

    def find_record(self, context, criterion):
        return self._find_records(context, criterion, one=True)

    def update_record(self, context, record_id, values):
        record = self._get_record(context, record_id)

        record.update(values)

        record.save(self.session)

        return dict(record)

    def delete_record(self, context, record_id):
        record = self._get_record(context, record_id)

        record.delete(self.session)

    def count_records(self, context, criterion=None):
        query = self.session.query(models.Record)
        query = self._apply_criterion(models.Record, query, criterion)
        return query.count()

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
