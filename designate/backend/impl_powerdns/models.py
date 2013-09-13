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
from sqlalchemy import Column, String, Text, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from designate.sqlalchemy.models import Base as CommonBase
from designate.sqlalchemy.types import UUID


class Base(CommonBase):
    id = Column(Integer, primary_key=True, autoincrement=True)


Base = declarative_base(cls=Base)


class TsigKey(Base):
    __tablename__ = 'tsigkeys'

    designate_id = Column(UUID, nullable=False)

    name = Column(String(255), default=None, nullable=True)
    algorithm = Column(String(255), default=None, nullable=True)
    secret = Column(String(255), default=None, nullable=True)


class DomainMetadata(Base):
    __tablename__ = 'domainmetadata'

    domain_id = Column(Integer(), nullable=False)
    kind = Column(String(16), default=None, nullable=True)
    content = Column(Text())


class Domain(Base):
    __tablename__ = 'domains'

    designate_id = Column(UUID, nullable=False)

    name = Column(String(255), nullable=False, unique=True)
    master = Column(String(255), nullable=True)
    last_check = Column(Integer, default=None, nullable=True)
    type = Column(String(6), nullable=False)
    notified_serial = Column(Integer, default=None, nullable=True)
    account = Column(String(40), default=None, nullable=True)


class Record(Base):
    __tablename__ = 'records'

    designate_id = Column(UUID, nullable=False)

    domain_id = Column(Integer, default=None, nullable=True)
    name = Column(String(255), default=None, nullable=True)
    type = Column(String(10), default=None, nullable=True)
    content = Column(Text, default=None, nullable=True)
    ttl = Column(Integer, default=None, nullable=True)
    prio = Column(Integer, default=None, nullable=True)
    change_date = Column(Integer, default=None, nullable=True)
    ordername = Column(String(255), default=None, nullable=True)
    auth = Column(Boolean(), default=None, nullable=True)
    inherit_ttl = Column(Boolean(), default=True)
