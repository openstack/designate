# Copyright 2014 Hewlett-Packard Development Company, L.P.
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
from sqlalchemy import Integer, String, DateTime, Unicode, UniqueConstraint, \
                       CHAR, Enum, ForeignKeyConstraint, Text, Boolean
from sqlalchemy.schema import Table, Column, MetaData

from designate.sqlalchemy.types import UUID

RESOURCE_STATUSES = ['ACTIVE', 'PENDING', 'DELETED']
RECORD_TYPES = ['A', 'AAAA', 'CNAME', 'MX', 'SRV', 'TXT', 'SPF', 'NS', 'PTR',
                'SSHFP']
TSIG_ALGORITHMS = ['hmac-md5', 'hmac-sha1', 'hmac-sha224', 'hmac-sha256',
                   'hmac-sha384', 'hmac-sha512']

meta = MetaData()


blacklists = Table('blacklists', meta,
    Column('id', UUID(), primary_key=True),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
    Column('version', Integer(), nullable=False),

    Column('pattern', String(255), nullable=False),
    Column('description', Unicode(160)),

    UniqueConstraint('pattern', name='pattern'),

    mysql_engine='INNODB',
    mysql_charset='utf8')

domains = Table('domains', meta,
    Column('id', UUID(), primary_key=True),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
    Column('version', Integer(), nullable=False),

    Column('tenant_id', String(36)),
    Column('name', String(255), nullable=False),
    Column('email', String(255), nullable=False),
    Column('ttl', Integer(), nullable=False),
    Column('refresh', Integer(), nullable=False),
    Column('retry', Integer(), nullable=False),
    Column('expire', Integer(), nullable=False),
    Column('minimum', Integer(), nullable=False),
    Column('parent_domain_id', UUID()),
    Column('serial', Integer(), nullable=False, server_default="1"),
    Column('deleted', CHAR(32), nullable=False, server_default='0'),
    Column('deleted_at', DateTime),
    Column('description', Unicode(160)),
    Column('status', Enum(name='domain_statuses', *RESOURCE_STATUSES),
           nullable=False, server_default='ACTIVE'),

    UniqueConstraint('name', 'deleted', name='unique_domain_name'),
    ForeignKeyConstraint(['parent_domain_id'], ['domains.id']),

    mysql_engine='INNODB',
    mysql_charset='utf8')


quotas = Table('quotas', meta,
    Column('id', UUID(), primary_key=True),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
    Column('version', Integer(), nullable=False),

    Column('tenant_id', String(36), nullable=False),
    Column('resource', String(32), nullable=False),
    Column('hard_limit', Integer(), nullable=False),

    UniqueConstraint('tenant_id', 'resource', name='unique_quota'),

    mysql_engine='INNODB',
    mysql_charset='utf8')


records = Table('records', meta,
    Column('id', UUID(), primary_key=True),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
    Column('version', Integer(), nullable=False),

    Column('data', Text(), nullable=False),
    Column('priority', Integer()),
    Column('domain_id', UUID(), nullable=False),
    Column('managed', Boolean()),
    Column('managed_resource_type', String(50)),
    Column('managed_resource_id', UUID()),
    Column('managed_plugin_name', String(50)),
    Column('managed_plugin_type', String(50)),
    Column('hash', String(32), nullable=False),
    Column('description', Unicode(160)),
    Column('status', Enum(name='record_statuses', *RESOURCE_STATUSES),
           nullable=False, server_default='ACTIVE'),
    Column('tenant_id', String(36)),
    Column('recordset_id', UUID(), nullable=False),
    Column('managed_tenant_id', String(36)),
    Column('managed_resource_region', String(100)),
    Column('managed_extra', String(100)),

    UniqueConstraint('hash', name='unique_record'),
    ForeignKeyConstraint(['domain_id'], ['domains.id'], ondelete='CASCADE',
                         name='fkey_records_domain_id'),
    ForeignKeyConstraint(['recordset_id'], ['recordsets.id'],
                         ondelete='CASCADE', name='fkey_records_recordset_id'),

    mysql_engine='INNODB',
    mysql_charset='utf8')

recordsets = Table('recordsets', meta,
    Column('id', UUID(), primary_key=True),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
    Column('version', Integer(), nullable=False),

    Column('tenant_id', String(36)),
    Column('domain_id', UUID(), nullable=False),
    Column('name', String(255), nullable=False),
    Column('type', Enum(name='recordset_types', *RECORD_TYPES),
           nullable=False),
    Column('ttl', Integer()),
    Column('description', Unicode(160)),

    UniqueConstraint('domain_id', 'name', 'type', name='unique_recordset'),
    ForeignKeyConstraint(['domain_id'], ['domains.id']),

    mysql_engine='INNODB',
    mysql_charset='utf8')

servers = Table('servers', meta,
    Column('id', UUID(), primary_key=True),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
    Column('version', Integer(), nullable=False),

    Column('name', String(255), nullable=False),

    UniqueConstraint('name', name='unique_server_name'),

    mysql_engine='INNODB',
    mysql_charset='utf8')

tlds = Table('tlds', meta,
    Column('id', UUID(), primary_key=True),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
    Column('version', Integer(), nullable=False),

    Column('name', String(255), nullable=False),
    Column('description', Unicode(160)),

    UniqueConstraint('name', name='unique_tld_name'),

    mysql_engine='INNODB',
    mysql_charset='utf8')


tsigkeys = Table('tsigkeys', meta,
    Column('id', UUID(), primary_key=True),
    Column('created_at', DateTime()),
    Column('updated_at', DateTime()),
    Column('version', Integer(), nullable=False),

    Column('name', String(255), nullable=False),
    Column('algorithm', Enum(name='tsig_algorithms', *TSIG_ALGORITHMS),
           nullable=False),
    Column('secret', String(255), nullable=False),

    UniqueConstraint('name', name='unique_tsigkey_name'),

    mysql_engine='INNODB',
    mysql_charset='utf8')


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    with migrate_engine.begin() as conn:
        if migrate_engine.name == "mysql":
            conn.execute("SET foreign_key_checks = 0;")

        elif migrate_engine.name == "postgresql":
            conn.execute("SET CONSTRAINTS ALL DEFERRED;")

        domains.create(conn)
        recordsets.create(conn)
        records.create(conn)
        blacklists.create(conn)
        quotas.create(conn)
        servers.create(conn)
        tlds.create(conn)
        tsigkeys.create(conn)

        if migrate_engine.name == "mysql":
            conn.execute("SET foreign_key_checks = 1;")


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    with migrate_engine.begin() as conn:
        if migrate_engine.name == "mysql":
            conn.execute("SET foreign_key_checks = 0;")

        elif migrate_engine.name == "postgresql":
            conn.execute("SET CONSTRAINTS ALL DEFERRED;")

        tsigkeys.drop()
        tlds.drop()
        servers.drop()
        quotas.drop()
        blacklists.drop()
        records.drop()
        recordsets.drop()
        domains.drop()

        if migrate_engine.name == "mysql":
            conn.execute("SET foreign_key_checks = 1;")
