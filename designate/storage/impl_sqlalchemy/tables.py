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
from sqlalchemy import (Table, MetaData, Column, String, Text, Integer, CHAR,
                        DateTime, Enum, Boolean, Unicode, UniqueConstraint,
                        ForeignKeyConstraint)

from oslo.config import cfg

from designate import utils
from designate.openstack.common import timeutils
from designate.sqlalchemy.types import UUID


CONF = cfg.CONF

RESOURCE_STATUSES = ['ACTIVE', 'PENDING', 'DELETED']
RECORD_TYPES = ['A', 'AAAA', 'CNAME', 'MX', 'SRV', 'TXT', 'SPF', 'NS', 'PTR',
                'SSHFP']
TSIG_ALGORITHMS = ['hmac-md5', 'hmac-sha1', 'hmac-sha224', 'hmac-sha256',
                   'hmac-sha384', 'hmac-sha512']

metadata = MetaData()

quotas = Table('quotas', metadata,
    Column('id', UUID, default=utils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('tenant_id', String(36), default=None, nullable=True),
    Column('resource', String(32), nullable=False),
    Column('hard_limit', Integer(), nullable=False),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

servers = Table('servers', metadata,
    Column('id', UUID, default=utils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('name', String(255), nullable=False, unique=True),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

tlds = Table('tlds', metadata,
    Column('id', UUID, default=utils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('name', String(255), nullable=False, unique=True),
    Column('description', Unicode(160), nullable=True),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

domains = Table('domains', metadata,
    Column('id', UUID, default=utils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('deleted', CHAR(32), nullable=False, default='0',
           server_default='0'),
    Column('deleted_at', DateTime, nullable=True, default=None),

    Column('tenant_id', String(36), default=None, nullable=True),
    Column('name', String(255), nullable=False),
    Column('email', String(255), nullable=False),
    Column('description', Unicode(160), nullable=True),
    Column('ttl', Integer, default=CONF.default_ttl, nullable=False),
    Column('serial', Integer, default=timeutils.utcnow_ts, nullable=False),
    Column('refresh', Integer, default=CONF.default_soa_refresh,
           nullable=False),
    Column('retry', Integer, default=CONF.default_soa_retry, nullable=False),
    Column('expire', Integer, default=CONF.default_soa_expire, nullable=False),
    Column('minimum', Integer, default=CONF.default_soa_minimum,
           nullable=False),
    Column('status', Enum(name='resource_statuses', *RESOURCE_STATUSES),
           nullable=False, server_default='ACTIVE', default='ACTIVE'),
    Column('parent_domain_id', UUID, default=None, nullable=True),

    UniqueConstraint('name', 'deleted', name='unique_domain_name'),
    ForeignKeyConstraint(['parent_domain_id'],
                         ['domains.id'],
                         ondelete='SET NULL'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

recordsets = Table('recordsets', metadata,
    Column('id', UUID, default=utils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('tenant_id', String(36), default=None, nullable=True),
    Column('domain_id', UUID, nullable=False),
    Column('name', String(255), nullable=False),
    Column('type', Enum(name='record_types', *RECORD_TYPES), nullable=False),
    Column('ttl', Integer, default=None, nullable=True),
    Column('description', Unicode(160), nullable=True),

    UniqueConstraint('domain_id', 'name', 'type', name='unique_recordset'),
    ForeignKeyConstraint(['domain_id'], ['domains.id'], ondelete='CASCADE'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

records = Table('records', metadata,
    Column('id', UUID, default=utils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('tenant_id', String(36), default=None, nullable=True),
    Column('domain_id', UUID, nullable=False),
    Column('recordset_id', UUID, nullable=False),
    Column('data', Text, nullable=False),
    Column('priority', Integer, default=None, nullable=True),
    Column('description', Unicode(160), nullable=True),
    Column('hash', String(32), nullable=False, unique=True),
    Column('managed', Boolean, default=False),
    Column('managed_extra', Unicode(100), default=None, nullable=True),
    Column('managed_plugin_type', Unicode(50), default=None, nullable=True),
    Column('managed_plugin_name', Unicode(50), default=None, nullable=True),
    Column('managed_resource_type', Unicode(50), default=None, nullable=True),
    Column('managed_resource_region', Unicode(100), default=None,
           nullable=True),
    Column('managed_resource_id', UUID, default=None, nullable=True),
    Column('managed_tenant_id', Unicode(36), default=None, nullable=True),
    Column('status', Enum(name='resource_statuses', *RESOURCE_STATUSES),
           nullable=False, server_default='ACTIVE', default='ACTIVE'),

    ForeignKeyConstraint(['domain_id'], ['domains.id'], ondelete='CASCADE'),
    ForeignKeyConstraint(['recordset_id'], ['recordsets.id'],
                         ondelete='CASCADE'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

tsigkeys = Table('tsigkeys', metadata,
    Column('id', UUID, default=utils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('name', String(255), nullable=False, unique=True),
    Column('algorithm', Enum(name='tsig_algorithms', *TSIG_ALGORITHMS),
           nullable=False),
    Column('secret', String(255), nullable=False),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

blacklists = Table('blacklists', metadata,
    Column('id', UUID, default=utils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('pattern', String(255), nullable=False, unique=True),
    Column('description', Unicode(160), nullable=True),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)
