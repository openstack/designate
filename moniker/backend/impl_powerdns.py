# Copyright 2012 Hewlett-Packard Development Company, L.P. All Rights Reserved.
# Copyright 2012 Managed I.T.
#
# Author: Patrick Galbraith <patg@hp.com>
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
from sqlalchemy import Column, String, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import exc as sqlalchemy_exceptions
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging
from moniker import exceptions
from moniker.backend import base
from moniker.sqlalchemy.session import get_session, SQLOPTS
from moniker.sqlalchemy.models import Base as CommonBase
from moniker.sqlalchemy.types import UUID

LOG = logging.getLogger(__name__)

cfg.CONF.register_group(cfg.OptGroup(
    name='backend:powerdns', title="Configuration for Powerdns Backend"
))

cfg.CONF.register_opts(SQLOPTS, group='backend:powerdns')


class Base(CommonBase):
    id = Column(Integer, primary_key=True, autoincrement=True)


Base = declarative_base(cls=Base)


class Domain(Base):
    __tablename__ = 'domains'

    moniker_id = Column(UUID, nullable=False)

    name = Column(String(255), nullable=False, unique=True)
    master = Column(String(128), nullable=True)
    last_check = Column(Integer, default=None, nullable=True)
    type = Column(String(6), nullable=False)
    notified_serial = Column(Integer, default=None, nullable=True)
    account = Column(String(40), default=None, nullable=True)


class Record(Base):
    __tablename__ = 'records'

    moniker_id = Column(UUID, nullable=False)

    domain_id = Column(Integer, default=None, nullable=True)
    name = Column(String(255), default=None, nullable=True)
    type = Column(String(10), default=None, nullable=True)
    content = Column(Text, default=None, nullable=True)
    ttl = Column(Integer, default=None, nullable=True)
    prio = Column(Integer, default=None, nullable=True)
    change_date = Column(Integer, default=None, nullable=True)


class PowerDNSBackend(base.Backend):
    __plugin_name__ = 'powerdns'

    def start(self):
        super(PowerDNSBackend, self).start()

        self.session = get_session(self.name)

    def create_domain(self, context, domain, servers):
        domain_m = Domain()
        domain_m.update({
            'moniker_id': domain['id'],
            'name': domain['name'].rstrip('.'),
            'master': servers[0]['name'].rstrip('.'),
            'type': 'NATIVE',
            'account': context.tenant_id
        })
        domain_m.save(self.session)

        for server in servers:
            record_m = Record()
            record_m.update({
                'moniker_id': server['id'],
                'domain_id': domain_m.id,
                'name': domain['name'].rstrip('.'),
                'type': 'NS',
                'content': server['name'].rstrip('.')
            })
            record_m.save(self.session)

        # NOTE(kiall): Do the SOA last, ensuring we don't trigger a NOTIFY
        #              before the NS records are in place.
        record_m = Record()
        record_m.update({
            'moniker_id': domain['id'],
            'domain_id': domain_m.id,
            'name': domain['name'].rstrip('.'),
            'type': 'SOA',
            'content': self._build_soa_content(domain, servers)
        })
        record_m.save(self.session)

    def update_domain(self, context, domain, servers):
        domain_m = self._get_domain(domain['id'])

        # TODO: Sync Server List

        soa_record_m = self._get_record(domain=domain_m, type='SOA')

        soa_record_m.update({
            'content': self._build_soa_content(domain, servers)
        })

        soa_record_m.save(self.session)

    def delete_domain(self, context, domain, servers):
        domain_m = self._get_domain(domain['id'])
        domain_m.delete(self.session)

        self.session.query(Record).filter_by(domain_id=domain_m.id).delete()

    def create_record(self, context, domain, record):
        domain_m = self._get_domain(domain['id'])
        record_m = Record()

        record_m.update({
            'moniker_id': record['id'],
            'domain_id': domain_m.id,
            'name': record['name'].rstrip('.'),
            'type': record['type'],
            'content': record['data'],
            'ttl': record['ttl'],
            'prio': record['priority']
        })

        record_m.save(self.session)

    def update_record(self, context, domain, record):
        record_m = self._get_record(record['id'])

        record_m.update({
            'name': record['name'].rstrip('.'),
            'type': record['type'],
            'content': record['data'],
            'ttl': record['ttl'],
            'prio': record['priority']
        })

        record_m.save(self.session)

    def delete_record(self, context, domain, record):
        record_m = self._get_record(record['id'])
        record_m.delete(self.session)

    def _build_soa_content(self, domain, servers):
        return "%s %s. %d %d %d %d %d" % (servers[0]['name'],
                                          domain['email'].replace("@", "."),
                                          domain['serial'],
                                          domain['refresh'],
                                          domain['retry'],
                                          domain['expire'],
                                          domain['minimum'])

    def _get_domain(self, domain_id):
        query = self.session.query(Domain)

        try:
            domain = query.filter_by(moniker_id=domain_id).one()
        except sqlalchemy_exceptions.NoResultFound:
            raise exceptions.Backend('No domain found')
        except sqlalchemy_exceptions.MultipleResultsFound:
            raise exceptions.Backend('Too many domains found')
        else:
            return domain

    def _get_record(self, record_id=None, domain=None, type=None):
        query = self.session.query(Record)

        if record_id:
            query = query.filter_by(moniker_id=record_id)

        if type:
            query = query.filter_by(type=type)

        if domain:
            query = query.filter_by(domain_id=domain.id)

        try:
            record = query.one()
        except sqlalchemy_exceptions.NoResultFound:
            raise exceptions.Backend('No record found')
        except sqlalchemy_exceptions.MultipleResultsFound:
            raise exceptions.Backend('Too many records found')
        else:
            return record
