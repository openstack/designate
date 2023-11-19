# Copyright 2015 Hewlett-Packard Development Company, L.P.
# Copyright 2022 Red Hat
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

"""liberty

Revision ID: c9f427f7180a
Revises:
Create Date: 2022-07-28 23:06:40.731452

"""
from alembic import op
from oslo_utils import timeutils
import sqlalchemy as sa

import designate.conf
from designate.conf import central
from designate.storage.sqlalchemy.alembic import legacy_utils
from designate.storage.sqlalchemy.types import UUID

# revision identifiers, used by Alembic.
revision = 'c9f427f7180a'
down_revision = None
branch_labels = None
depends_on = None

# Equivalent to legacy sqlalchemy-migrate revision 070_liberty

CONF = designate.conf.CONF
central.register_opts(CONF)

ACTIONS = ('CREATE', 'DELETE', 'UPDATE', 'NONE')
POOL_PROVISIONERS = ('UNMANAGED',)
RECORD_TYPES = ('A', 'AAAA', 'CNAME', 'MX', 'SRV', 'TXT', 'SPF', 'NS', 'PTR',
                'SSHFP', 'SOA')
RESOURCE_STATUSES = ('ACTIVE', 'PENDING', 'DELETED', 'ERROR')
TASK_STATUSES = ('ACTIVE', 'PENDING', 'DELETED', 'ERROR', 'COMPLETE')
TSIG_ALGORITHMS = ('hmac-md5', 'hmac-sha1', 'hmac-sha224', 'hmac-sha256',
                   'hmac-sha384', 'hmac-sha512')
TSIG_SCOPES = ('POOL', 'ZONE')
ZONE_ATTRIBUTE_KEYS = ('master',)
ZONE_TASK_TYPES = ('IMPORT', 'EXPORT')
ZONE_TYPES = ('PRIMARY', 'SECONDARY')


def upgrade() -> None:
    # Check if the equivalent legacy migration has already run
    if not legacy_utils.is_migration_needed(70):
        return

    metadata = sa.MetaData()

    pools_table = op.create_table(
        'pools', metadata,
        sa.Column('id', UUID, primary_key=True),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.Unicode(160), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('provisioner', sa.Enum(name='pool_provisioner',
                                         *POOL_PROVISIONERS),
                  nullable=False, server_default='UNMANAGED'),
        sa.UniqueConstraint('name', name='unique_pool_name'),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )

    op.bulk_insert(
        pools_table,
        [{'id': CONF['service:central'].default_pool_id,
          'name': 'default',
          'version': 1}])

    op.create_table(
        'pool_ns_records', metadata,
        sa.Column('id', UUID, primary_key=True),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('pool_id', UUID, nullable=False),
        sa.Column('priority', sa.Integer, nullable=False),
        sa.Column('hostname', sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(['pool_id'], ['pools.id'], ondelete='CASCADE'),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )

    op.create_table(
        'pool_attributes', metadata,
        sa.Column('id', UUID, primary_key=True),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('value', sa.String(255), nullable=False),
        sa.Column('pool_id', UUID, nullable=False),
        sa.UniqueConstraint('pool_id', 'key', 'value',
                            name='unique_pool_attribute'),
        sa.ForeignKeyConstraint(['pool_id'], ['pools.id'], ondelete='CASCADE'),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )

    op.create_table(
        'domains', metadata,
        sa.Column('id', UUID, primary_key=True),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('version', sa.Integer, nullable=False),
        sa.Column('tenant_id', sa.String(36), default=None, nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('ttl', sa.Integer, default=lambda: CONF.default_ttl,
                  nullable=False),
        sa.Column('refresh', sa.Integer, nullable=False),
        sa.Column('retry', sa.Integer, nullable=False),
        sa.Column('expire', sa.Integer, nullable=False),
        sa.Column('minimum', sa.Integer, nullable=False),
        sa.Column('parent_domain_id', UUID, default=None, nullable=True),
        sa.Column('serial', sa.Integer, nullable=False, server_default='1'),
        sa.Column('deleted', sa.CHAR(32), nullable=False, default='0',
                  server_default='0'),
        sa.Column('deleted_at', sa.DateTime, nullable=True, default=None),
        sa.Column('description', sa.Unicode(160), nullable=True),
        sa.Column('status', sa.Enum(name='domains_resource_statuses',
                                    *RESOURCE_STATUSES),
                  nullable=False, server_default='PENDING', default='PENDING'),
        sa.Column('action', sa.Enum(name='domain_actions', *ACTIONS),
                  default='CREATE', server_default='CREATE', nullable=False),
        sa.Column('pool_id', UUID, default=None, nullable=True),
        sa.Column('reverse_name', sa.String(255), nullable=False,
                  server_default=''),
        sa.Column("type", sa.Enum(name='type', *ZONE_TYPES),
                  server_default='PRIMARY', default='PRIMARY'),
        sa.Column('transferred_at', sa.DateTime, default=None),
        sa.Column('shard', sa.SmallInteger, nullable=False),
        sa.UniqueConstraint('name', 'deleted', 'pool_id',
                            name='unique_domain_name'),
        sa.ForeignKeyConstraint(['parent_domain_id'],
                                ['domains.id'],
                                ondelete='SET NULL'),
        sa.Index('zone_deleted', 'deleted'),
        sa.Index('zone_tenant_deleted', 'tenant_id', 'deleted'),
        sa.Index('reverse_name_deleted', 'reverse_name', 'deleted'),
        sa.Index('zone_created_at', 'created_at'),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )

    op.create_table(
        'domain_attributes', metadata,
        sa.Column('id', UUID, primary_key=True),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('key', sa.Enum(name='key', *ZONE_ATTRIBUTE_KEYS)),
        sa.Column('value', sa.String(255), nullable=False),
        sa.Column('domain_id', UUID, nullable=False),
        sa.UniqueConstraint('key', 'value', 'domain_id',
                            name='unique_attributes'),
        sa.ForeignKeyConstraint(['domain_id'], ['domains.id'],
                                ondelete='CASCADE'),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )
    op.create_table(
        'recordsets', metadata,
        sa.Column('id', UUID, primary_key=True),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('domain_shard', sa.SmallInteger, nullable=False),
        sa.Column('tenant_id', sa.String(36), default=None, nullable=True),
        sa.Column('domain_id', UUID, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.Enum(name='record_types', *RECORD_TYPES),
                  nullable=False),
        sa.Column('ttl', sa.Integer, default=None, nullable=True),
        sa.Column('description', sa.Unicode(160), nullable=True),
        sa.Column('reverse_name', sa.String(255), nullable=False,
                  server_default=''),
        sa.UniqueConstraint('domain_id', 'name', 'type',
                            name='unique_recordset'),
        sa.ForeignKeyConstraint(['domain_id'], ['domains.id'],
                                ondelete='CASCADE'),
        sa.Index('rrset_type_domainid', 'type', 'domain_id'),
        sa.Index('recordset_type_name', 'type', 'name'),
        sa.Index('reverse_name_dom_id', 'reverse_name', 'domain_id'),
        sa.Index('recordset_created_at', 'created_at'),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )

    op.create_table(
        'records', metadata,
        sa.Column('id', UUID, primary_key=True),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('data', sa.Text, nullable=False),
        sa.Column('domain_id', UUID, nullable=False),
        sa.Column('managed', sa.Boolean, default=False),
        sa.Column('managed_resource_type', sa.Unicode(50), default=None,
                  nullable=True),
        sa.Column('managed_resource_id', UUID, default=None, nullable=True),
        sa.Column('managed_plugin_type', sa.Unicode(50), default=None,
                  nullable=True),
        sa.Column('managed_plugin_name', sa.Unicode(50), default=None,
                  nullable=True),
        sa.Column('hash', sa.String(32), nullable=False),
        sa.Column('description', sa.Unicode(160), nullable=True),
        sa.Column('status', sa.Enum(name='record_resource_statuses',
                                    *RESOURCE_STATUSES),
                  server_default='PENDING', default='PENDING', nullable=False),
        sa.Column('tenant_id', sa.String(36), default=None, nullable=True),
        sa.Column('recordset_id', UUID, nullable=False),
        sa.Column('managed_tenant_id', sa.Unicode(36), default=None,
                  nullable=True),
        sa.Column('managed_resource_region', sa.Unicode(100), default=None,
                  nullable=True),
        sa.Column('managed_extra', sa.Unicode(100), default=None,
                  nullable=True),
        sa.Column('action', sa.Enum(name='record_actions', *ACTIONS),
                  default='CREATE', server_default='CREATE', nullable=False),
        sa.Column('serial', sa.Integer, server_default='1', nullable=False),
        sa.Column('domain_shard', sa.SmallInteger, nullable=False),
        sa.UniqueConstraint('hash', name='unique_record'),
        sa.ForeignKeyConstraint(['domain_id'], ['domains.id'],
                                ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recordset_id'], ['recordsets.id'],
                                ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['domain_id'], ['domains.id'],
                                ondelete='CASCADE',
                                name='fkey_records_domain_id'),
        sa.ForeignKeyConstraint(['recordset_id'], ['recordsets.id'],
                                ondelete='CASCADE',
                                name='fkey_records_recordset_id'),
        sa.Index('records_tenant', 'tenant_id'),
        sa.Index('record_created_at', 'created_at'),
        sa.Index('update_status_index', 'status', 'domain_id', 'tenant_id',
                 'created_at', 'serial'),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )

    op.create_table(
        'quotas', metadata,
        sa.Column('id', UUID, primary_key=True),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime,
                  default=lambda: timeutils.utcnow()),
        sa.Column('updated_at', sa.DateTime,
                  onupdate=lambda: timeutils.utcnow()),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('resource', sa.String(32), nullable=False),
        sa.Column('hard_limit', sa.Integer, nullable=False),
        sa.UniqueConstraint('tenant_id', 'resource', name='unique_quota'),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )

    op.create_table(
        'tsigkeys', metadata,
        sa.Column('id', UUID, primary_key=True),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('algorithm',
                  sa.Enum(name='tsig_algorithms', *TSIG_ALGORITHMS),
                  nullable=False),
        sa.Column('secret', sa.String(255), nullable=False),
        sa.Column('scope', sa.Enum(name='tsig_scopes', *TSIG_SCOPES),
                  nullable=False, server_default='POOL'),
        sa.Column('resource_id', UUID, nullable=False),
        sa.UniqueConstraint('name', name='unique_tsigkey_name'),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )

    op.create_table(
        'tlds', metadata,
        sa.Column('id', UUID, primary_key=True),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime,
                  default=lambda: timeutils.utcnow()),
        sa.Column('updated_at', sa.DateTime,
                  onupdate=lambda: timeutils.utcnow()),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Unicode(160), nullable=True),
        sa.UniqueConstraint('name', name='unique_tld_name'),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )

    op.create_table(
        'zone_transfer_requests', metadata,
        sa.Column('id', UUID, primary_key=True),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('domain_id', UUID, nullable=False),
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("description", sa.String(255)),
        sa.Column("tenant_id", sa.String(36), default=None, nullable=False),
        sa.Column("target_tenant_id", sa.String(36), default=None,
                  nullable=True),
        sa.Column("status",
                  sa.Enum(name='zone_transfer_requests_resource_statuses',
                          *TASK_STATUSES),
                  nullable=False, server_default='ACTIVE', default='ACTIVE'),
        sa.ForeignKeyConstraint(['domain_id'], ['domains.id'],
                                ondelete='CASCADE'),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )

    op.create_table(
        'zone_transfer_accepts', metadata,
        sa.Column('id', UUID, primary_key=True),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('domain_id', UUID, nullable=False),
        sa.Column('zone_transfer_request_id', UUID, nullable=False),
        sa.Column("tenant_id", sa.String(36), default=None, nullable=False),
        sa.Column("status",
                  sa.Enum(name='zone_transfer_accepts_resource_statuses',
                          *TASK_STATUSES),
                  nullable=False, server_default='ACTIVE', default='ACTIVE'),
        sa.ForeignKeyConstraint(['domain_id'], ['domains.id'],
                                ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['zone_transfer_request_id'],
                                ['zone_transfer_requests.id'],
                                ondelete='CASCADE'),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )

    op.create_table(
        'zone_tasks', metadata,
        sa.Column('id', UUID, primary_key=True),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('tenant_id', sa.String(36), default=None, nullable=True),
        sa.Column('domain_id', UUID, nullable=True),
        sa.Column('task_type', sa.Enum(name='task_types', *ZONE_TASK_TYPES),
                  nullable=True),
        sa.Column('message', sa.String(160), nullable=True),
        sa.Column('status', sa.Enum(name='zone_tasks_resource_statuses',
                                    *TASK_STATUSES),
                  nullable=False, server_default='ACTIVE', default='ACTIVE'),
        sa.Column('location', sa.String(160), nullable=True),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )

    op.create_table(
        'blacklists', metadata,
        sa.Column('id', UUID, primary_key=True),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime),
        sa.Column('pattern', sa.String(255), nullable=False),
        sa.Column('description', sa.Unicode(160), nullable=True),
        sa.UniqueConstraint('pattern', name='pattern'),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )
