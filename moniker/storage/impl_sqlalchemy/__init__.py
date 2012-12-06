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
from sqlalchemy.orm import exc
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging
from moniker import exceptions
from moniker.storage import base
from moniker.storage.impl_sqlalchemy import models
from moniker.sqlalchemy.session import get_session

LOG = logging.getLogger(__name__)

cfg.CONF.register_group(cfg.OptGroup(
    name='storage:sqlalchemy', title="Configuration for SQLAlchemy Storage"
))

cfg.CONF.register_opts([
    cfg.StrOpt('database_connection',
               default='sqlite:///$state_path/moniker.sqlite',
               help='The database driver to use'),
    cfg.IntOpt('connection_debug', default=0,
               help='Verbosity of SQL debugging information. 0=None,'
               ' 100=Everything'),
    cfg.BoolOpt('connection_trace', default=False,
                help='Add python stack traces to SQL as comment strings'),
    cfg.BoolOpt('sqlite_synchronous', default=True,
                help='If passed, use synchronous mode for sqlite'),
    cfg.IntOpt('idle_timeout', default=3600,
               help='timeout before idle sql connections are reaped'),
    cfg.IntOpt('max_retries', default=10,
               help='maximum db connection retries during startup. '
               '(setting -1 implies an infinite retry count)'),
    cfg.IntOpt('retry_interval', default=10,
               help='interval between retries of opening a sql connection')
], group='storage:sqlalchemy')


class SQLAlchemyStorage(base.StorageEngine):
    __plugin_name__ = 'sqlalchemy'

    def get_connection(self):
        return Connection(self.name)


class Connection(base.Connection):
    """
    SQLAlchemy connection
    """
    def __init__(self, config_group):
        self.session = self._get_connection(config_group)

    def _get_connection(self, config_group):
        """
        Return a connection to the database.
        """
        return get_session(config_group)

    def setup_schema(self):
        """ Semi-Private Method to create the database schema """
        models.Base.metadata.create_all(self.session.bind)

    def teardown_schema(self):
        """ Semi-Private Method to reset the database schema """
        models.Base.metadata.drop_all(self.session.bind)

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

        if criterion:
            query = query.filter_by(**criterion)

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

        if criterion:
            query = query.filter_by(**criterion)

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

    # Record Methods
    def create_record(self, context, domain_id, values):
        domain = self._get_domain(context, domain_id)

        record = models.Record()
        record.update(values)

        domain.records.append(record)

        domain.save(self.session)

        return dict(record)

    def get_records(self, context, domain_id, criterion=None):
        domain = self._get_domain(context, domain_id)

        query = domain.records

        if criterion:
            query = query.filter_by(**criterion)

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

    def update_record(self, context, record_id, values):
        record = self._get_record(context, record_id)

        record.update(values)

        record.save(self.session)

        return dict(record)

    def delete_record(self, context, record_id):
        record = self._get_record(context, record_id)

        record.delete(self.session)
