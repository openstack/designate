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
from sqlalchemy.orm.exc import NoResultFound
from moniker.openstack.common import log as logging
from moniker import exceptions
from moniker.database import BaseDatabase
from moniker.database.sqlalchemy import models
from moniker.database.sqlalchemy.session import get_session


LOG = logging.getLogger(__name__)


class Sqlalchemy(BaseDatabase):
    def __init__(self):
        self.session = get_session()
        self._initialize_database()  # HACK: Remove me

    def _initialize_database(self):
        """ Semi-Private Method to create the database schema """
        models.Base.metadata.create_all(self.session.bind)

    # Server Methods
    def create_server(self, context, values):
        server = models.Server()

        server.update(values)

        try:
            server.save()
        except exceptions.Duplicate:
            raise exceptions.DuplicateServer()

        return dict(server)

    def get_servers(self, context):
        query = self.session.query(models.Server)

        try:
            result = query.all()
        except NoResultFound:
            LOG.debug('No results found')
            return []
        else:
            return [dict(o) for o in result]

    def _get_server(self, context, server_id):
        query = self.session.query(models.Server)

        try:
            server = query.filter(models.Server.id == server_id).one()
        except NoResultFound:
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
            server.save()
        except exceptions.Duplicate:
            raise exceptions.DuplicateServer()

        return dict(server)

    def delete_server(self, context, server_id):
        server = self._get_server(context, server_id)

        server.delete()

    # Domain Methods
    def create_domain(self, context, values):
        domain = models.Domain()

        domain.update(values)

        try:
            domain.save()
        except exceptions.Duplicate:
            raise exceptions.DuplicateDomain()

        return dict(domain)

    def get_domains(self, context):
        query = self.session.query(models.Domain)

        try:
            result = query.all()
        except NoResultFound:
            LOG.debug('No results found')
            return []
        else:
            return [dict(o) for o in result]

    def _get_domain(self, context, domain_id):
        query = self.session.query(models.Domain)

        try:
            domain = query.filter(models.Domain.id == domain_id).one()
        except NoResultFound:
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
            domain.save()
        except exceptions.Duplicate:
            raise exceptions.DuplicateDomain()

        return dict(domain)

    def delete_domain(self, context, domain_id):
        domain = self._get_domain(context, domain_id)

        domain.delete()

    # Record Methods
    def create_record(self, context, domain_id, values):
        domain = self._get_domain(context, domain_id)

        record = models.Record()
        record.update(values)

        domain.records.append(record)

        domain.save()

        return dict(record)

    def get_records(self, context, domain_id):
        domain = self._get_domain(context, domain_id)

        return [dict(o) for o in domain.records]

    def _get_record(self, context, record_id):
        query = self.session.query(models.Record)

        try:
            record = query.filter(models.Record.id == record_id).one()
        except NoResultFound:
            raise exceptions.RecordNotFound(record_id)
        else:
            return record

    def get_record(self, context, record_id):
        record = self._get_record(context, record_id)

        return dict(record)

    def update_record(self, context, record_id, values):
        record = self._get_record(context, record_id)

        record.update(values)

        record.save()

        return dict(record)

    def delete_record(self, context, record_id):
        record = self._get_record(context, record_id)

        record.delete()
