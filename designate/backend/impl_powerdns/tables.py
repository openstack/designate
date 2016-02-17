# Copyright 2012-2014 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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
from sqlalchemy import MetaData, Table, Column, String, Integer

from oslo_config import cfg

from designate.sqlalchemy.types import UUID

CONF = cfg.CONF


metadata = MetaData()

domains = Table(
    'domains', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),

    Column('designate_id', UUID, nullable=False),
    Column('name', String(255), nullable=False, unique=True),
    Column('master', String(255), nullable=True),
    Column('last_check', Integer, default=None, nullable=True),
    Column('type', String(6), nullable=False),
    Column('notified_serial', Integer, default=None, nullable=True),
    Column('account', String(40), default=None, nullable=True),
    mysql_engine='InnoDB',
    mysql_charset='utf8')
