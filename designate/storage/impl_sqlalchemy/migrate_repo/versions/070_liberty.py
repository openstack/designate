# Copyright 2015 Hewlett-Packard Development Company, L.P.
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
#
from sqlalchemy import (Table, MetaData, Column, String, Text, Integer,
                        SmallInteger, CHAR, DateTime, Enum, Boolean, Unicode,
                        UniqueConstraint, ForeignKeyConstraint, Index)

from oslo_config import cfg
from oslo_utils import timeutils

from designate.sqlalchemy.types import UUID


CONF = cfg.CONF

RESOURCE_STATUSES = ['ACTIVE', 'PENDING', 'DELETED', 'ERROR']
RECORD_TYPES = ['A', 'AAAA', 'CNAME', 'MX', 'SRV', 'TXT', 'SPF', 'NS', 'PTR',
                'SSHFP', 'SOA']
TASK_STATUSES = ['ACTIVE', 'PENDING', 'DELETED', 'ERROR', 'COMPLETE']
TSIG_ALGORITHMS = ['hmac-md5', 'hmac-sha1', 'hmac-sha224', 'hmac-sha256',
                   'hmac-sha384', 'hmac-sha512']
TSIG_SCOPES = ['POOL', 'ZONE']
POOL_PROVISIONERS = ['UNMANAGED']
ACTIONS = ['CREATE', 'DELETE', 'UPDATE', 'NONE']

ZONE_ATTRIBUTE_KEYS = ('master',)

ZONE_TYPES = ('PRIMARY', 'SECONDARY',)
ZONE_TASK_TYPES = ['IMPORT', 'EXPORT']


metadata = MetaData()

quotas = Table('quotas', metadata,
    Column('id', UUID, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('tenant_id', String(36), nullable=False),
    Column('resource', String(32), nullable=False),
    Column('hard_limit', Integer(), nullable=False),

    UniqueConstraint('tenant_id', 'resource', name='unique_quota'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

tlds = Table('tlds', metadata,
    Column('id', UUID, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime, default=lambda: timeutils.utcnow()),
    Column('updated_at', DateTime, onupdate=lambda: timeutils.utcnow()),

    Column('name', String(255), nullable=False),
    Column('description', Unicode(160), nullable=True),

    UniqueConstraint('name', name='unique_tld_name'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

domains = Table('domains', metadata,
    Column('id', UUID, primary_key=True),
    Column('created_at', DateTime),
    Column('updated_at', DateTime),
    Column('version', Integer(), nullable=False),
    Column('tenant_id', String(36), default=None, nullable=True),
    Column('name', String(255), nullable=False),
    Column('email', String(255), nullable=False),
    Column('ttl', Integer, default=CONF.default_ttl, nullable=False),
    Column('refresh', Integer, nullable=False),
    Column('retry', Integer, nullable=False),
    Column('expire', Integer, nullable=False),
    Column('minimum', Integer, nullable=False),
    Column('parent_domain_id', UUID, default=None, nullable=True),
    Column('serial', Integer, nullable=False, server_default='1'),
    Column('deleted', CHAR(32), nullable=False, default='0',
           server_default='0'),
    Column('deleted_at', DateTime, nullable=True, default=None),
    Column('description', Unicode(160), nullable=True),
    Column('status', Enum(name='domains_resource_statuses',
                          *RESOURCE_STATUSES),
           nullable=False, server_default='PENDING', default='PENDING'),
    Column('action', Enum(name='domain_actions', *ACTIONS),
           default='CREATE', server_default='CREATE', nullable=False),
    Column('pool_id', UUID, default=None, nullable=True),
    Column('reverse_name', String(255), nullable=False, server_default=''),
    Column("type", Enum(name='type', *ZONE_TYPES),
           server_default='PRIMARY', default='PRIMARY'),
    Column('transferred_at', DateTime, default=None),
    Column('shard', SmallInteger(), nullable=False),

    UniqueConstraint('name', 'deleted', 'pool_id', name='unique_domain_name'),
    ForeignKeyConstraint(['parent_domain_id'],
                         ['domains.id'],
                         ondelete='SET NULL'),

    Index('zone_deleted', 'deleted'),
    Index('zone_tenant_deleted', 'tenant_id', 'deleted'),
    Index('reverse_name_deleted', 'reverse_name', 'deleted'),
    Index('zone_created_at', 'created_at'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

domain_attributes = Table('domain_attributes', metadata,
    Column('id', UUID(), primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime),
    Column('updated_at', DateTime),

    Column('key', Enum(name='key', *ZONE_ATTRIBUTE_KEYS)),
    Column('value', String(255), nullable=False),
    Column('domain_id', UUID(), nullable=False),

    UniqueConstraint('key', 'value', 'domain_id', name='unique_attributes'),
    ForeignKeyConstraint(['domain_id'], ['domains.id'], ondelete='CASCADE'),

    mysql_engine='INNODB',
    mysql_charset='utf8'
)

recordsets = Table('recordsets', metadata,
    Column('id', UUID, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime),
    Column('updated_at', DateTime),
    Column('domain_shard', SmallInteger(), nullable=False),

    Column('tenant_id', String(36), default=None, nullable=True),
    Column('domain_id', UUID, nullable=False),
    Column('name', String(255), nullable=False),
    Column('type', Enum(name='record_types', *RECORD_TYPES), nullable=False),
    Column('ttl', Integer, default=None, nullable=True),
    Column('description', Unicode(160), nullable=True),
    Column('reverse_name', String(255), nullable=False, server_default=''),

    UniqueConstraint('domain_id', 'name', 'type', name='unique_recordset'),
    ForeignKeyConstraint(['domain_id'], ['domains.id'], ondelete='CASCADE'),

    Index('rrset_type_domainid', 'type', 'domain_id'),
    Index('recordset_type_name', 'type', 'name'),
    Index('reverse_name_dom_id', 'reverse_name', 'domain_id'),
    Index('recordset_created_at', 'created_at'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

records = Table('records', metadata,
    Column('id', UUID, primary_key=True),
    Column('created_at', DateTime),
    Column('updated_at', DateTime),
    Column('version', Integer(), default=1, nullable=False),
    Column('data', Text, nullable=False),
    Column('domain_id', UUID, nullable=False),
    Column('managed', Boolean, default=False),
    Column('managed_resource_type', Unicode(50), default=None, nullable=True),
    Column('managed_resource_id', UUID, default=None, nullable=True),
    Column('managed_plugin_type', Unicode(50), default=None, nullable=True),
    Column('managed_plugin_name', Unicode(50), default=None, nullable=True),
    Column('hash', String(32), nullable=False),
    Column('description', Unicode(160), nullable=True),
    Column('status', Enum(name='record_resource_statuses', *RESOURCE_STATUSES),
           server_default='PENDING', default='PENDING', nullable=False),
    Column('tenant_id', String(36), default=None, nullable=True),
    Column('recordset_id', UUID, nullable=False),
    Column('managed_tenant_id', Unicode(36), default=None, nullable=True),
    Column('managed_resource_region', Unicode(100), default=None,
           nullable=True),
    Column('managed_extra', Unicode(100), default=None, nullable=True),
    Column('action', Enum(name='record_actions', *ACTIONS),
           default='CREATE', server_default='CREATE', nullable=False),
    Column('serial', Integer(), server_default='1', nullable=False),
    Column('domain_shard', SmallInteger(), nullable=False),

    UniqueConstraint('hash', name='unique_record'),
    ForeignKeyConstraint(['domain_id'], ['domains.id'], ondelete='CASCADE'),
    ForeignKeyConstraint(['recordset_id'], ['recordsets.id'],
                         ondelete='CASCADE'),
    ForeignKeyConstraint(['domain_id'], ['domains.id'], ondelete='CASCADE',
                         name='fkey_records_domain_id'),
    ForeignKeyConstraint(['recordset_id'], ['recordsets.id'],
                         ondelete='CASCADE', name='fkey_records_recordset_id'),
    Index('records_tenant', 'tenant_id'),
    Index('record_created_at', 'created_at'),
    Index('update_status_index', 'status', 'domain_id', 'tenant_id',
          'created_at', 'serial'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

tsigkeys = Table('tsigkeys', metadata,
    Column('id', UUID, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime),
    Column('updated_at', DateTime),

    Column('name', String(255), nullable=False),
    Column('algorithm', Enum(name='tsig_algorithms', *TSIG_ALGORITHMS),
           nullable=False),
    Column('secret', String(255), nullable=False),
    Column('scope', Enum(name='tsig_scopes', *TSIG_SCOPES), nullable=False,
           server_default='POOL'),
    Column('resource_id', UUID, nullable=False),

    UniqueConstraint('name', name='unique_tsigkey_name'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

blacklists = Table('blacklists', metadata,
    Column('id', UUID, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('updated_at', DateTime),
    Column('created_at', DateTime),

    Column('pattern', String(255), nullable=False),
    Column('description', Unicode(160), nullable=True),

    UniqueConstraint('pattern', name='pattern'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

pools = Table('pools', metadata,
    Column('id', UUID, primary_key=True),
    Column('created_at', DateTime),
    Column('updated_at', DateTime),
    Column('version', Integer(), default=1, nullable=False),

    Column('name', String(50), nullable=False),
    Column('description', Unicode(160), nullable=True),
    Column('tenant_id', String(36), nullable=True),
    Column('provisioner', Enum(name='pool_provisioner', *POOL_PROVISIONERS),
           nullable=False, server_default='UNMANAGED'),

    UniqueConstraint('name', name='unique_pool_name'),

    mysql_engine='INNODB',
    mysql_charset='utf8'
)

pool_attributes = Table('pool_attributes', metadata,
    Column('id', UUID(), primary_key=True),
    Column('created_at', DateTime),
    Column('updated_at', DateTime),
    Column('version', Integer(), default=1, nullable=False),

    Column('key', String(255), nullable=False),
    Column('value', String(255), nullable=False),
    Column('pool_id', UUID(), nullable=False),

    UniqueConstraint('pool_id', 'key', 'value', name='unique_pool_attribute'),

    ForeignKeyConstraint(['pool_id'], ['pools.id'], ondelete='CASCADE'),

    mysql_engine='INNODB',
    mysql_charset='utf8'
)

pool_ns_records = Table('pool_ns_records', metadata,
    Column('id', UUID(), primary_key=True),
    Column('created_at', DateTime),
    Column('updated_at', DateTime),
    Column('version', Integer(), default=1, nullable=False),

    Column('pool_id', UUID(), nullable=False),
    Column('priority', Integer(), nullable=False),
    Column('hostname', String(255), nullable=False),

    ForeignKeyConstraint(['pool_id'], ['pools.id'], ondelete='CASCADE'),

    mysql_engine='INNODB',
    mysql_charset='utf8')

zone_transfer_requests = Table('zone_transfer_requests', metadata,
    Column('id', UUID, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime),
    Column('updated_at', DateTime),

    Column('domain_id', UUID, nullable=False),
    Column("key", String(255), nullable=False),
    Column("description", String(255)),
    Column("tenant_id", String(36), default=None, nullable=False),
    Column("target_tenant_id", String(36), default=None, nullable=True),
    Column("status", Enum(name='zone_transfer_requests_resource_statuses',
                          *TASK_STATUSES),
           nullable=False, server_default='ACTIVE',
           default='ACTIVE'),

    ForeignKeyConstraint(['domain_id'], ['domains.id'], ondelete='CASCADE'),

    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

zone_transfer_accepts = Table('zone_transfer_accepts', metadata,
    Column('id', UUID, primary_key=True),
    Column('version', Integer(), default=1, nullable=False),
    Column('created_at', DateTime),
    Column('updated_at', DateTime),

    Column('domain_id', UUID, nullable=False),
    Column('zone_transfer_request_id', UUID, nullable=False),
    Column("tenant_id", String(36), default=None, nullable=False),
    Column("status", Enum(name='zone_transfer_accepts_resource_statuses',
                          *TASK_STATUSES),
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
    Column('id', UUID(), primary_key=True),
    Column('created_at', DateTime),
    Column('updated_at', DateTime),
    Column('version', Integer(), default=1, nullable=False),
    Column('tenant_id', String(36), default=None, nullable=True),

    Column('domain_id', UUID(), nullable=True),
    Column('task_type', Enum(name='task_types', *ZONE_TASK_TYPES),
           nullable=True),
    Column('message', String(160), nullable=True),
    Column('status', Enum(name='zone_tasks_resource_statuses', *TASK_STATUSES),
           nullable=False, server_default='ACTIVE',
           default='ACTIVE'),
    Column('location', String(160), nullable=True),

    mysql_engine='INNODB',
    mysql_charset='utf8')


def default_shard(context, id_col):
    return int(context.current_parameters[id_col][0:3], 16)


def upgrade(migrate_engine):
    metadata.bind = migrate_engine

    default_pool_id = cfg.CONF['service:central'].default_pool_id

    with migrate_engine.begin() as conn:
        if migrate_engine.name == "mysql":
            conn.execute("SET foreign_key_checks = 0;")

        pools.create()
        pool_ns_records.create()
        pool_attributes.create()
        domains.create()
        domain_attributes.create()
        recordsets.create()
        records.create()
        quotas.create()
        tsigkeys.create()
        tlds.create()
        zone_transfer_requests.create()
        zone_transfer_accepts.create()
        zone_tasks.create()
        blacklists.create()

        pools.insert().execute(
            id=default_pool_id,
            name='default',
            version=1
        )

        if migrate_engine.name == "mysql":
            conn.execute("SET foreign_key_checks = 1;")
