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
from sqlalchemy import (Table, MetaData, Column, String, Text, Integer,
                        SmallInteger, CHAR, DateTime, Enum, Boolean, Unicode,
                        UniqueConstraint, ForeignKeyConstraint)

from oslo_db.sqlalchemy import types
from oslo_utils import timeutils
from oslo_utils import uuidutils

import designate.conf
from designate.storage.sqlalchemy.types import UUID


CONF = designate.conf.CONF

RESOURCE_STATUSES = ['ACTIVE', 'PENDING', 'DELETED', 'ERROR']
RECORD_TYPES = ['A', 'AAAA', 'CNAME', 'MX', 'SRV', 'TXT', 'SPF', 'NS', 'PTR',
                'SSHFP', 'SOA', 'NAPTR', 'CAA', 'CERT']

TASK_STATUSES = ['ACTIVE', 'PENDING', 'DELETED', 'ERROR', 'COMPLETE']
TSIG_ALGORITHMS = ['hmac-md5', 'hmac-sha1', 'hmac-sha224', 'hmac-sha256',
                   'hmac-sha384', 'hmac-sha512']
TSIG_SCOPES = ['POOL', 'ZONE']
POOL_PROVISIONERS = ['UNMANAGED']
ACTIONS = ['CREATE', 'DELETE', 'UPDATE', 'NONE']

ZONE_TYPES = ('PRIMARY', 'SECONDARY', 'CATALOG')
ZONE_TASK_TYPES = ['IMPORT', 'EXPORT']

SERVICE_STATES = [
    "UP", "DOWN", "WARNING"
]

metadata = MetaData()

# TODO(Federico) some default column values are not needed because we
# explicitly set the value on record insertion. Having default values could
# hide bugs.


def default_shard(context, id_col):
    return int(context.current_parameters[id_col][0:3], 16)


service_status = Table("service_statuses", metadata,
    Column('id', UUID, default=uuidutils.generate_uuid, primary_key=True),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('service_name', String(40), nullable=False),
    Column('hostname', String(255), nullable=False),
    Column('heartbeated_at', DateTime, nullable=True),

    Column('status', Enum(name='service_statuses', *SERVICE_STATES),
           nullable=False),
    Column('stats', types.JsonEncodedDict, nullable=False),
    Column('capabilities', types.JsonEncodedDict, nullable=False),

    UniqueConstraint('service_name', 'hostname', name="unique_service_status"),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)


quotas = Table('quotas', metadata,
    Column('id', UUID, default=uuidutils.generate_uuid, primary_key=True),
    Column('version', Integer, default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('tenant_id', String(36), default=None, nullable=True),
    Column('resource', String(32), nullable=False),
    Column('hard_limit', Integer, nullable=False),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

tlds = Table('tlds', metadata,
    Column('id', UUID, default=uuidutils.generate_uuid, primary_key=True),
    Column('version', Integer, default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('name', String(255), nullable=False, unique=True),
    Column('description', Unicode(160), nullable=True),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

zones = Table('zones', metadata,
    Column('id', UUID, default=uuidutils.generate_uuid, primary_key=True),
    Column('version', Integer, default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('deleted', CHAR(32), nullable=False, default='0',
           server_default='0'),
    Column('deleted_at', DateTime, nullable=True, default=None),
    Column('shard', SmallInteger, nullable=False,
           default=lambda ctxt: default_shard(ctxt, 'id')),

    Column('tenant_id', String(36), default=None, nullable=True),
    Column('name', String(255), nullable=False),
    Column('email', String(255), nullable=False),
    Column('description', Unicode(160), nullable=True),
    Column("type", Enum(name='type', *ZONE_TYPES), nullable=False),
    Column('transferred_at', DateTime, default=None),
    Column('ttl', Integer, default=lambda: CONF.default_ttl, nullable=False),
    Column('serial', Integer, default=timeutils.utcnow_ts, nullable=False),
    # The refresh interval is randomized by _generate_soa_refresh_interval
    Column('refresh', Integer, default=lambda: CONF.default_soa_refresh_min,
           nullable=False),
    Column('retry', Integer, default=lambda: CONF.default_soa_retry,
           nullable=False),
    Column('expire', Integer, default=lambda: CONF.default_soa_expire,
           nullable=False),
    Column('minimum', Integer, default=lambda: CONF.default_soa_minimum,
           nullable=False),
    Column('status', Enum(name='zones_resource_statuses', *RESOURCE_STATUSES),
           nullable=False, server_default='PENDING', default='PENDING'),
    Column('parent_zone_id', UUID, default=None, nullable=True),
    Column('action', Enum(name='actions', *ACTIONS),
           default='CREATE', server_default='CREATE', nullable=False),
    Column('pool_id', UUID, default=None, nullable=True),
    Column('reverse_name', String(255), nullable=False),
    Column('delayed_notify', Boolean, default=False),
    Column('increment_serial', Boolean, default=False),

    UniqueConstraint('name', 'deleted', 'pool_id', name='unique_zone_name'),
    ForeignKeyConstraint(['parent_zone_id'],
                         ['zones.id'],
                         ondelete='SET NULL'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

zone_attributes = Table('zone_attributes', metadata,
    Column('id', UUID, default=uuidutils.generate_uuid, primary_key=True),
    Column('version', Integer, default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('key', String(50)),
    Column('value', String(255), nullable=False),
    Column('zone_id', UUID, nullable=False),

    UniqueConstraint('key', 'value', 'zone_id', name='unique_attributes'),
    ForeignKeyConstraint(['zone_id'], ['zones.id'], ondelete='CASCADE'),

    mysql_engine='InnoDB',
    mysql_charset='utf8'
)

zone_masters = Table('zone_masters', metadata,
    Column('id', UUID(), default=uuidutils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('host', String(32), nullable=False),
    Column('port', Integer(), nullable=False),
    Column('zone_id', UUID(), nullable=False),

    UniqueConstraint('host', 'port', 'zone_id', name='unique_masters'),
    ForeignKeyConstraint(['zone_id'], ['zones.id'], ondelete='CASCADE'),

    mysql_engine='InnoDB',
    mysql_charset='utf8'
)

shared_zones = Table(
    'shared_zones', metadata,
    Column('id', UUID, default=uuidutils.generate_uuid, primary_key=True),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),
    Column('zone_id', UUID, nullable=False),
    Column('project_id', String(36), nullable=False),
    Column('target_project_id', String(36), nullable=False),

    UniqueConstraint('zone_id', 'project_id', 'target_project_id',
                     name='unique_shared_zone'),
    ForeignKeyConstraint(('zone_id',), ['zones.id'], ondelete='CASCADE'),

    mysql_engine='InnoDB',
    mysql_charset='utf8'
)

recordsets = Table('recordsets', metadata,
    Column('id', UUID, default=uuidutils.generate_uuid, primary_key=True),
    Column('version', Integer, default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),
    Column('zone_shard', SmallInteger, nullable=False,
           default=lambda ctxt: default_shard(ctxt, 'zone_id')),

    Column('tenant_id', String(36), default=None, nullable=True),
    Column('zone_id', UUID, nullable=False),
    Column('name', String(255), nullable=False),
    Column('type', Enum(name='record_types', *RECORD_TYPES), nullable=False),
    Column('ttl', Integer, default=None, nullable=True),
    Column('description', Unicode(160), nullable=True),
    Column('reverse_name', String(255), nullable=False, default=''),

    UniqueConstraint('zone_id', 'name', 'type', name='unique_recordset'),
    ForeignKeyConstraint(['zone_id'], ['zones.id'], ondelete='CASCADE'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

records = Table('records', metadata,
    Column('id', UUID, default=uuidutils.generate_uuid, primary_key=True),
    Column('version', Integer, default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),
    Column('zone_shard', SmallInteger, nullable=False,
           default=lambda ctxt: default_shard(ctxt, 'zone_id')),

    Column('tenant_id', String(36), default=None, nullable=True),
    Column('zone_id', UUID, nullable=False),
    Column('recordset_id', UUID, nullable=False),
    Column('data', Text, nullable=False),
    Column('description', Unicode(160), nullable=True),
    Column('hash', String(32), nullable=False, unique=True),
    Column('managed', Boolean, default=False),
    Column('managed_extra', String(100), default=None, nullable=True),
    Column('managed_plugin_type', String(50), default=None, nullable=True),
    Column('managed_plugin_name', String(50), default=None, nullable=True),
    Column('managed_resource_type', String(50), default=None, nullable=True),
    Column('managed_resource_region', String(100), default=None,
           nullable=True),
    Column('managed_resource_id', UUID, default=None, nullable=True),
    Column('managed_tenant_id', String(36), default=None, nullable=True),
    Column('status', Enum(name='records_resource_statuses',
                          *RESOURCE_STATUSES),
           server_default='PENDING', default='PENDING', nullable=False),
    Column('action', Enum(name='actions', *ACTIONS),
           default='CREATE', server_default='CREATE', nullable=False),
    Column('serial', Integer, server_default='1', nullable=False),

    UniqueConstraint('hash', name='unique_record'),
    ForeignKeyConstraint(['zone_id'], ['zones.id'], ondelete='CASCADE'),
    ForeignKeyConstraint(['recordset_id'], ['recordsets.id'],
                         ondelete='CASCADE'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

tsigkeys = Table('tsigkeys', metadata,
    Column('id', UUID, default=uuidutils.generate_uuid, primary_key=True),
    Column('version', Integer, default=1, nullable=False),
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
    Column('id', UUID, default=uuidutils.generate_uuid, primary_key=True),
    Column('version', Integer, default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('pattern', String(255), nullable=False, unique=True),
    Column('description', Unicode(160), nullable=True),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

pools = Table('pools', metadata,
    Column('id', UUID, default=uuidutils.generate_uuid, primary_key=True),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),
    Column('version', Integer, default=1, nullable=False),

    Column('name', String(50), nullable=False, unique=True),
    Column('description', Unicode(160), nullable=True),
    Column('tenant_id', String(36), nullable=True),
    Column('provisioner', Enum(name='pool_provisioner', *POOL_PROVISIONERS),
           nullable=False, server_default='UNMANAGED'),

    UniqueConstraint('name', name='unique_pool_name'),

    mysql_engine='InnoDB',
    mysql_charset='utf8'
)

pool_attributes = Table('pool_attributes', metadata,
    Column('id', UUID, default=uuidutils.generate_uuid, primary_key=True),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),
    Column('version', Integer, default=1, nullable=False),

    Column('key', String(255), nullable=False),
    Column('value', String(255), nullable=False),
    Column('pool_id', UUID, nullable=False),

    ForeignKeyConstraint(['pool_id'], ['pools.id'], ondelete='CASCADE'),

    mysql_engine='InnoDB',
    mysql_charset='utf8'
)

pool_ns_records = Table('pool_ns_records', metadata,
    Column('id', UUID, default=uuidutils.generate_uuid, primary_key=True),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),
    Column('version', Integer, default=1, nullable=False),

    Column('pool_id', UUID, nullable=False),
    Column('priority', Integer, nullable=False),
    Column('hostname', String(255), nullable=False),

    ForeignKeyConstraint(['pool_id'], ['pools.id'], ondelete='CASCADE'),
    UniqueConstraint('pool_id', 'hostname', name='unique_ns_name'),

    mysql_engine='InnoDB',
    mysql_charset='utf8')

pool_nameservers = Table('pool_nameservers', metadata,
    Column('id', UUID, default=uuidutils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('pool_id', UUID(), nullable=False),
    Column('host', String(255), nullable=False),
    Column('port', Integer(), nullable=False),

    ForeignKeyConstraint(['pool_id'], ['pools.id'], ondelete='CASCADE'),
    UniqueConstraint('pool_id', 'host', 'port', name='unique_pool_host_port'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

pool_targets = Table('pool_targets', metadata,
    Column('id', UUID, default=uuidutils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('pool_id', UUID(), nullable=False),
    Column('type', String(50), nullable=False),
    Column('tsigkey_id', UUID(), nullable=True),
    Column('description', Unicode(160), nullable=True),

    ForeignKeyConstraint(['pool_id'], ['pools.id'], ondelete='CASCADE'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

pool_target_masters = Table('pool_target_masters', metadata,
    Column('id', UUID, default=uuidutils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('pool_target_id', UUID(), nullable=False),
    Column('host', String(255), nullable=False),
    Column('port', Integer(), nullable=False),

    ForeignKeyConstraint(['pool_target_id'], ['pool_targets.id'],
                         ondelete='CASCADE'),
    UniqueConstraint('pool_target_id', 'host', 'port',
                     name='unique_pool_target_host_port'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

pool_target_options = Table('pool_target_options', metadata,
    Column('id', UUID, default=uuidutils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('pool_target_id', UUID(), nullable=False),
    Column('key', String(255), nullable=False),
    Column('value', String(255), nullable=False),

    ForeignKeyConstraint(['pool_target_id'], ['pool_targets.id'],
                         ondelete='CASCADE'),
    UniqueConstraint('pool_target_id', 'key', name='unique_pool_target_key'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

pool_also_notifies = Table('pool_also_notifies', metadata,
    Column('id', UUID, default=uuidutils.generate_uuid, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('pool_id', UUID(), nullable=False),
    Column('host', String(255), nullable=False),
    Column('port', Integer(), nullable=False),

    ForeignKeyConstraint(['pool_id'], ['pools.id'], ondelete='CASCADE'),
    UniqueConstraint('pool_id', 'host', 'port', name='unique_pool_host_port'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

zone_transfer_requests = Table('zone_transfer_requests', metadata,
    Column('id', UUID, default=uuidutils.generate_uuid, primary_key=True),
    Column('version', Integer, default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('zone_id', UUID, nullable=False),
    Column("key", String(255), nullable=False),
    Column("description", String(255), nullable=False),
    Column("tenant_id", String(36), default=None, nullable=False),
    Column("target_tenant_id", String(36), default=None, nullable=True),
    Column("status", Enum(name='zone_transfer_requests_resource_statuses',
                          *TASK_STATUSES),
           nullable=False, server_default='ACTIVE',
           default='ACTIVE'),

    ForeignKeyConstraint(['zone_id'], ['zones.id'], ondelete='CASCADE'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

zone_transfer_accepts = Table('zone_transfer_accepts', metadata,
    Column('id', UUID, default=uuidutils.generate_uuid, primary_key=True),
    Column('version', Integer, default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('zone_id', UUID, nullable=False),
    Column('zone_transfer_request_id', UUID, nullable=False),
    Column("tenant_id", String(36), default=None, nullable=False),
    Column("status", Enum(name='zone_transfer_accepts_resource_statuses',
                          *TASK_STATUSES),
           nullable=False, server_default='ACTIVE',
           default='ACTIVE'),

    ForeignKeyConstraint(['zone_id'], ['zones.id'], ondelete='CASCADE'),
    ForeignKeyConstraint(
        ['zone_transfer_request_id'],
        ['zone_transfer_requests.id'],
        ondelete='CASCADE'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

zone_tasks = Table('zone_tasks', metadata,
    Column('id', UUID, default=uuidutils.generate_uuid, primary_key=True),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),
    Column('version', Integer, default=1, nullable=False),
    Column('tenant_id', String(36), default=None, nullable=True),

    Column('zone_id', UUID, nullable=True),
    Column('task_type', Enum(name='task_types', *ZONE_TASK_TYPES),
           nullable=True),
    Column('message', String(160), nullable=True),
    Column('status', Enum(name='zone_tasks_resource_statuses', *TASK_STATUSES),
           nullable=False, server_default='ACTIVE',
           default='ACTIVE'),
    Column('location', String(160), nullable=True),

    mysql_engine='InnoDB',
    mysql_charset='utf8')
