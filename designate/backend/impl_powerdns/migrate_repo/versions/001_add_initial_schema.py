# Copyright 2012 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
# Author: Patrick Galbraith <patg@hp.com>
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from sqlalchemy import Integer, String, Text, Boolean
from sqlalchemy.schema import Table, Column, MetaData, Index

meta = MetaData()

domains = Table('domains', meta,
                Column('id', Integer(), autoincrement=True,
                       primary_key=True, nullable=False),
                Column('name', String(255), nullable=False, unique=True),
                Column('master', String(20), default=None, nullable=True),
                Column('last_check', Integer(), default=None,
                       nullable=True),
                Column('type', String(6), nullable=False),
                Column('notified_serial', Integer(), default=None,
                       nullable=True),
                Column('account', String(40), default=None, nullable=True))

records = Table('records', meta,
                Column('id', Integer(), autoincrement=True,
                       primary_key=True, nullable=False),
                Column('domain_id', Integer(), default=None, nullable=True),
                Column('name', String(255), default=None, nullable=True),
                Column('type', String(10), default=None, nullable=True),
                Column('content', String(255), default=None, nullable=True),
                Column('ttl', Integer(), default=None, nullable=True),
                Column('prio', Integer(), default=None, nullable=True),
                Column('change_date', Integer(), default=None,
                       nullable=True),
                Column('ordername', String(255), default=None, nullable=True),
                Column('auth', Boolean(), default=None, nullable=True))

Index('rec_name_index', records.c.name)
Index('nametype_index', records.c.name, records.c.type)
Index('domain_id', records.c.domain_id)
Index('orderindex', records.c.ordername)

cryptokeys = Table('cryptokeys', meta,
                   Column('id', Integer(), autoincrement=True,
                          primary_key=True, nullable=False),
                   Column('domain_id', Integer(), nullable=False),
                   Column('flags', Integer(), nullable=False),
                   Column('active', Boolean(), default=None, nullable=True),
                   Column('content', Text()))

domainmetadata = Table('domainmetadata', meta,
                       Column('id', Integer(), autoincrement=True,
                              primary_key=True, nullable=False),
                       Column('domain_id', Integer(), nullable=False),
                       Column('kind', String(16), default=None, nullable=True),
                       Column('content', Text()))

supermasters = Table('supermasters', meta,
                     Column('ip', String(25), nullable=False),
                     Column('nameserver', String(255), nullable=False),
                     Column('account', String(40), default=None,
                            nullable=True))

tsigkeys = Table('tsigkeys', meta,
                 Column('id', Integer(), autoincrement=True,
                        primary_key=True, nullable=False),
                 Column('name', String(255), default=None, nullable=True),
                 Column('algorithm', String(255), default=None, nullable=True),
                 Column('secret', String(255), default=None, nullable=True))

Index('namealgoindex', tsigkeys.c.name, tsigkeys.c.algorithm, unique=True)


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    domains.create()
    records.create()
    cryptokeys.create()
    domainmetadata.create()
    supermasters.create()
    tsigkeys.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    tsigkeys.drop()
    supermasters.drop()
    domainmetadata.drop()
    cryptokeys.drop()
    records.drop()
    domains.drop()
