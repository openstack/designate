# Copyright 2012 Hewlett-Packard Development Company, L.P.
# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
# Modified: Patrick Galbraith <patg@hp.com>
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
from uuid import uuid4
from urlparse import urlparse
from sqlalchemy import (Column, DateTime, String, Text, Integer, ForeignKey,
                        Enum)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship, backref, object_mapper
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging
from moniker.openstack.common import timeutils
from moniker import exceptions
from moniker.storage.impl_sqlalchemy.session import get_session
from moniker.storage.impl_sqlalchemy.types import UUID, Inet

LOG = logging.getLogger(__name__)

sql_opts = [
    cfg.IntOpt('mysql_engine', default='InnoDB', help='MySQL engine')
]

cfg.CONF.register_opts(sql_opts)

RECORD_TYPES = ['A', 'AAAA', 'CNAME', 'MX', 'SRV', 'TXT', 'NS']


def table_args():
    engine_name = urlparse(cfg.CONF.database_connection).scheme
    if engine_name == 'mysql':
        return {'mysql_engine': cfg.CONF.mysql_engine}
    return None


class Base(object):
    __abstract__ = True

    id = Column(UUID, default=uuid4, primary_key=True)

    created_at = Column(DateTime, default=timeutils.utcnow)
    updated_at = Column(DateTime, onupdate=timeutils.utcnow)
    version = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        'version_id_col': version
    }

    __table_args__ = table_args()
    __table_initialized__ = False

    def save(self, session):
        """ Save this object """
        session.add(self)

        try:
            session.flush()
        except IntegrityError, e:
            if 'not unique' in str(e):
                raise exceptions.Duplicate(str(e))
            else:
                raise

    def delete(self, session):
        """ Delete this object """
        session.delete(self)
        session.flush()

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def __iter__(self):
        columns = dict(object_mapper(self).columns).keys()
        # NOTE(russellb): Allow models to specify other keys that can be looked
        # up, beyond the actual db columns.  An example would be the 'name'
        # property for an Instance.
        if hasattr(self, '_extra_keys'):
            columns.extend(self._extra_keys())
        self._i = iter(columns)
        return self

    def next(self):
        n = self._i.next()
        return n, getattr(self, n)

    def update(self, values):
        """ Make the model object behave like a dict """
        for k, v in values.iteritems():
            setattr(self, k, v)

    def iteritems(self):
        """
        Make the model object behave like a dict.

        Includes attributes from joins.
        """
        local = dict(self)
        joined = dict([(k, v) for k, v in self.__dict__.iteritems()
                      if not k[0] == '_'])
        local.update(joined)
        return local.iteritems()


Base = declarative_base(cls=Base)


class Server(Base):
    __tablename__ = 'servers'

    name = Column(String(255), nullable=False, unique=True)
    ipv4 = Column(Inet, nullable=False, unique=True)
    ipv6 = Column(Inet, default=None, nullable=True, unique=True)


class Domain(Base):
    __tablename__ = 'domains'

    tenant_id = Column(String(36), default=None, nullable=True)
    name = Column(String(255), nullable=False, unique=True)
    email = Column(String(36), nullable=False)

    ttl = Column(Integer, default=3600, nullable=False)
    refresh = Column(Integer, default=3600, nullable=False)
    retry = Column(Integer, default=3600, nullable=False)
    expire = Column(Integer, default=3600, nullable=False)
    minimum = Column(Integer, default=3600, nullable=False)

    records = relationship('Record', backref=backref('domain', uselist=False))

    @hybrid_property
    def serial(self):
        # TODO: Terrible terrible hack.. Cleanup ;)
        last_change = self.updated_at

        if last_change is None or self.created_at > last_change:
            last_change = self.created_at

        for record in self.records:
            if (record.updated_at is not None
                    and record.updated_at > last_change):
                last_change = record.updated_at
            elif record.created_at > last_change:
                last_change = record.created_at

        return int(last_change.strftime("%s"))

    def _extra_keys(self):
        return ['serial']


class Record(Base):
    __tablename__ = 'records'

    type = Column(Enum(name='record_types', *RECORD_TYPES), nullable=False)
    name = Column(String(255), nullable=False)
    data = Column(Text, nullable=False)
    priority = Column(Integer, default=None)
    ttl = Column(Integer, default=3600, nullable=False)

    domain_id = Column(UUID, ForeignKey('domains.id'), nullable=False)

    @hybrid_property
    def tenant_id(self):
        return self.domain.tenant_id

    def _extra_keys(self):
        return ['tenant_id']
