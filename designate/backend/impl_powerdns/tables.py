# Copyright 2012-2014 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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
from sqlalchemy import MetaData, Table, Column, String, Text, Integer, Boolean


from oslo.config import cfg

from designate.sqlalchemy.types import UUID

CONF = cfg.CONF


metadata = MetaData()

tsigkeys = Table(
    'tsigkeys', metadata,
    Column('id', Integer(), primary_key=True, autoincrement=True),

    Column('designate_id', UUID(), nullable=False),
    Column('name', String(255), default=None, nullable=True),
    Column('algorithm', String(255), default=None, nullable=True),
    Column('secret', String(255), default=None, nullable=True),
    mysql_engine='InnoDB',
    mysql_charset='utf8')

domain_metadata = Table(
    'domainmetadata', metadata,
    Column('id', Integer(), primary_key=True, autoincrement=True),

    Column('domain_id', Integer(), nullable=False),
    Column('kind', String(16), default=None, nullable=True),
    Column('content', Text()),
    mysql_engine='InnoDB',
    mysql_charset='utf8')

domains = Table(
    'domains', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),

    Column('designate_id', UUID(), nullable=False),
    Column('name', String(255), nullable=False, unique=True),
    Column('master', String(255), nullable=True),
    Column('last_check', Integer(), default=None, nullable=True),
    Column('type', String(6), nullable=False),
    Column('notified_serial', Integer(), default=None, nullable=True),
    Column('account', String(40), default=None, nullable=True),
    mysql_engine='InnoDB',
    mysql_charset='utf8')

records = Table(
    'records', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),

    Column('designate_id', UUID(), nullable=False),
    Column('designate_recordset_id', UUID(), default=None, nullable=True),
    Column('domain_id', Integer(), default=None, nullable=True),
    Column('name', String(255), default=None, nullable=True),
    Column('type', String(10), default=None, nullable=True),
    Column('content', Text(), default=None, nullable=True),
    Column('ttl', Integer(), default=None, nullable=True),
    Column('prio', Integer(), default=None, nullable=True),
    Column('change_date', Integer(), default=None, nullable=True),
    Column('ordername', String(255), default=None, nullable=True),
    Column('auth', Boolean(), default=None, nullable=True),
    Column('inherit_ttl', Boolean(), default=True),
    mysql_engine='InnoDB',
    mysql_charset='utf8')
