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
from sqlalchemy import (Table, MetaData, Column, String, Text, Integer,
                        SmallInteger, CHAR, DateTime, Enum, Boolean, Unicode,
                        UniqueConstraint, ForeignKeyConstraint)

from oslo_config import cfg
from oslo_utils import timeutils

from designate import utils
from designate.sqlalchemy.types import UUID


CONF = cfg.CONF

RESOURCE_STATUSES = ['ACTIVE', 'PENDING', 'DELETED', 'ERROR']
RECORD_TYPES = ['A', 'AAAA', 'CNAME', 'MX', 'SRV', 'TXT', 'SPF', 'NS', 'PTR',
                'SSHFP']
TASK_STATUSES = ['ACTIVE', 'PENDING', 'DELETED', 'ERROR', 'COMPLETE']
TSIG_ALGORITHMS = ['hmac-md5', 'hmac-sha1', 'hmac-sha224', 'hmac-sha256',
                   'hmac-sha384', 'hmac-sha512']
TSIG_SCOPES = ['POOL', 'ZONE']
POOL_PROVISIONERS = ['UNMANAGED']
ACTIONS = ['CREATE', 'DELETE', 'UPDATE', 'NONE']

ZONE_ATTRIBUTE_KEYS = ('master',)

ZONE_TYPES = ('PRIMARY', 'SECONDARY',)
ZONE_TASK_TYPES = ['IMPORT']


metadata = MetaData()


def default_shard(context, id_col):
    return int(context.current_parameters[id_col][0:3], 16)


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
    Column('shard', SmallInteger(), nullable=False,
           default=lambda ctxt: default_shard(ctxt, 'id')),

    Column('tenant_id', String(36), default=None, nullable=True),
    Column('name', String(255), nullable=False),
    Column('email', String(255), nullable=False),
    Column('description', Unicode(160), nullable=True),
    Column("type", Enum(name='type', *ZONE_TYPES), nullable=False),
    Column('transferred_at', DateTime, default=None),
    Column('ttl', Integer, default=CONF.default_ttl, nullable=False),
    Column('serial', Integer, default=timeutils.utcnow_ts, nullable=False),
    Column('refresh', Integer, default=CONF.default_soa_refresh,
           nullable=False),
    Column('retry', Integer, default=CONF.default_soa_retry, nullable=False),
    Column('expire', Integer, default=CONF.default_soa_expire, nullable=False),
    Column('minimum', Integer, default=CONF.default_soa_minimum,
           nullable=False),
    Column('status', Enum(name='resource_statuses', *RESOURCE_STATUSES),
           nullable=False, server_default='PENDING', default='PENDING'),
    Column('parent_domain_id', UUID, default=None, nullable=True),
    Column('action', Enum(name='actions', *ACTIONS),
           default='CREATE', server_default='CREATE', nullable=False),
    Column('pool_id', UUID, default=None, nullable=True),
    Column('reverse_name', String(255), nullable=False),

    UniqueConstraint('name', 'deleted', 'pool_id', name='unique_domain_name'),
    ForeignKeyConstraint(['parent_domain_id'],
                         ['domains.id'],
                         ondelete='SET NULL'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

domain_attributes = Table('domain_attributes', metadata,
    Column('id', UUID(), default=utils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('key', Enum(name='key', *ZONE_ATTRIBUTE_KEYS)),
    Column('value', String(255), nullable=False),
    Column('domain_id', UUID(), nullable=False),

    UniqueConstraint('key', 'value', 'domain_id', name='unique_attributes'),
    ForeignKeyConstraint(['domain_id'], ['domains.id'], ondelete='CASCADE'),

    mysql_engine='INNODB',
    mysql_charset='utf8'
)

recordsets = Table('recordsets', metadata,
    Column('id', UUID, default=utils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),
    Column('domain_shard', SmallInteger(), nullable=False,
           default=lambda ctxt: default_shard(ctxt, 'domain_id')),

    Column('tenant_id', String(36), default=None, nullable=True),
    Column('domain_id', UUID, nullable=False),
    Column('name', String(255), nullable=False),
    Column('type', Enum(name='record_types', *RECORD_TYPES), nullable=False),
    Column('ttl', Integer, default=None, nullable=True),
    Column('description', Unicode(160), nullable=True),
    Column('reverse_name', String(255), nullable=False, default=''),

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
    Column('domain_shard', SmallInteger(), nullable=False,
           default=lambda ctxt: default_shard(ctxt, 'domain_id')),

    Column('tenant_id', String(36), default=None, nullable=True),
    Column('domain_id', UUID, nullable=False),
    Column('recordset_id', UUID, nullable=False),
    Column('data', Text, nullable=False),
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
           server_default='PENDING', default='PENDING', nullable=False),
    Column('action', Enum(name='actions', *ACTIONS),
           default='CREATE', server_default='CREATE', nullable=False),
    Column('serial', Integer(), server_default='1', nullable=False),

    UniqueConstraint('hash', name='unique_record'),
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
    Column('scope', Enum(name='tsig_scopes', *TSIG_SCOPES), nullable=False),
    Column('resource_id', UUID, nullable=False),

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

pools = Table('pools', metadata,
    Column('id', UUID, default=utils.generate_uuid, primary_key=True),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),
    Column('version', Integer(), default=1, nullable=False),

    Column('name', String(50), nullable=False, unique=True),
    Column('description', Unicode(160), nullable=True),
    Column('tenant_id', String(36), nullable=True),
    Column('provisioner', Enum(name='pool_provisioner', *POOL_PROVISIONERS),
           nullable=False, server_default='UNMANAGED'),

    UniqueConstraint('name', name='unique_pool_name'),

    mysql_engine='INNODB',
    mysql_charset='utf8'
)

pool_attributes = Table('pool_attributes', metadata,
    Column('id', UUID(), default=utils.generate_uuid, primary_key=True),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),
    Column('version', Integer(), default=1, nullable=False),

    Column('key', String(255), nullable=False),
    Column('value', String(255), nullable=False),
    Column('pool_id', UUID(), nullable=False),

    ForeignKeyConstraint(['pool_id'], ['pools.id'], ondelete='CASCADE'),

    mysql_engine='INNODB',
    mysql_charset='utf8'
)

pool_ns_records = Table('pool_ns_records', metadata,
    Column('id', UUID(), default=utils.generate_uuid, primary_key=True),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),
    Column('version', Integer(), default=1, nullable=False),

    Column('pool_id', UUID(), nullable=False),
    Column('priority', Integer(), nullable=False),
    Column('hostname', String(255), nullable=False),

    ForeignKeyConstraint(['pool_id'], ['pools.id'], ondelete='CASCADE'),

    mysql_engine='INNODB',
    mysql_charset='utf8')

zone_transfer_requests = Table('zone_transfer_requests', metadata,
    Column('id', UUID, default=utils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('domain_id', UUID, nullable=False),
    Column("key", String(255), nullable=False),
    Column("description", String(255), nullable=False),
    Column("tenant_id", String(36), default=None, nullable=False),
    Column("target_tenant_id", String(36), default=None, nullable=True),
    Column("status", Enum(name='resource_statuses', *TASK_STATUSES),
           nullable=False, server_default='ACTIVE',
           default='ACTIVE'),

    ForeignKeyConstraint(['domain_id'], ['domains.id'], ondelete='CASCADE'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

zone_transfer_accepts = Table('zone_transfer_accepts', metadata,
    Column('id', UUID, default=utils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('domain_id', UUID, nullable=False),
    Column('zone_transfer_request_id', UUID, nullable=False),
    Column("tenant_id", String(36), default=None, nullable=False),
    Column("status", Enum(name='resource_statuses', *TASK_STATUSES),
           nullable=False, server_default='ACTIVE',
           default='ACTIVE'),

    ForeignKeyConstraint(['domain_id'], ['domains.id'], ondelete='CASCADE'),
    ForeignKeyConstraint(
        ['zone_transfer_request_id'],
        ['zone_transfer_requests.id'],
        ondelete='CASCADE'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

zone_tasks = Table('zone_tasks', metadata,
    Column('id', UUID(), default=utils.generate_uuid, primary_key=True),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),
    Column('version', Integer(), default=1, nullable=False),
    Column('tenant_id', String(36), default=None, nullable=True),

    Column('domain_id', UUID(), nullable=True),
    Column('task_type', Enum(name='task_types', *ZONE_TASK_TYPES),
           nullable=True),
    Column('message', String(160), nullable=True),
    Column('status', Enum(name='resource_statuses', *TASK_STATUSES),
           nullable=False, server_default='ACTIVE',
           default='ACTIVE'),

    mysql_engine='INNODB',
    mysql_charset='utf8')
