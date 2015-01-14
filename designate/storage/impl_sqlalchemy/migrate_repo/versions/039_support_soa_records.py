# Copyright (c) 2014 Rackspace Hosting
#
# Author: Betsy Luzader <betsy.luzader@rackspace.com>
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
import hashlib

from sqlalchemy import MetaData, Table, Enum
from sqlalchemy.sql import select
from migrate.changeset.constraint import UniqueConstraint
from oslo_db import exception

from designate import utils

meta = MetaData()


def _build_soa_record(zone, servers):
    return "%s %s. %d %d %d %d %d" % (servers[0]['name'],
                                      zone['email'].replace("@", "."),
                                      zone['serial'],
                                      zone['refresh'],
                                      zone['retry'],
                                      zone['expire'],
                                      zone['minimum'])


def _build_hash(recordset_id, data):
    md5 = hashlib.md5()
    md5.update("%s:%s:%s" % (recordset_id, data, None))

    return md5.hexdigest()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    # Get associated database tables
    servers_table = Table('servers', meta, autoload=True)
    zones_table = Table('domains', meta, autoload=True)
    records_table = Table('records', meta, autoload=True)
    dialect = migrate_engine.url.get_dialect().name

    RECORD_TYPES = ['A', 'AAAA', 'CNAME', 'MX', 'SRV', 'TXT', 'SPF', 'NS',
                    'PTR', 'SSHFP', 'SOA']

    recordsets_table = Table('recordsets', meta, autoload=True)
    recordsets_table.c.type.alter(type=Enum(name='recordset_types',
                                            *RECORD_TYPES))

    # Re-add constraint for sqlite
    if dialect.startswith('sqlite'):
        constraint = UniqueConstraint('domain_id', 'name', 'type',
                                      name='unique_recordset',
                                      table=recordsets_table)
        constraint.create()

    # Get the server names which are used to create NS & SOA records
    servers = select(
        columns=[
            servers_table.c.name
        ]
    ).execute().fetchall()

    # Get all the zones
    zones = select(
        columns=[
            zones_table.c.id,
            zones_table.c.created_at,
            zones_table.c.tenant_id,
            zones_table.c.name,
            zones_table.c.email,
            zones_table.c.serial,
            zones_table.c.refresh,
            zones_table.c.retry,
            zones_table.c.expire,
            zones_table.c.minimum
        ]
    ).execute().fetchall()

    # NOTE(per kiall): Since we need a unique UUID for each recordset etc, and
    #              need to maintain cross DB compatibility, we're stuck doing
    #              this in code
    for zone in zones:
        # Create the SOA Recordset, returning the UUID primary key to be used
        # in creating the associated SOA Record
        soa_pk = recordsets_table.insert().execute(
            id=utils.generate_uuid().replace('-', ''),
            created_at=zone.created_at,
            domain_id=zone.id,
            tenant_id=zone.tenant_id,
            name=zone.name,
            type='SOA',
            version=1
        ).inserted_primary_key[0]

        # Create the SOA Record
        soa_data = _build_soa_record(zone, servers)
        records_table.insert().execute(
            id=utils.generate_uuid().replace('-', ''),
            created_at=zone.created_at,
            domain_id=zone.id,
            tenant_id=zone.tenant_id,
            recordset_id=soa_pk,
            data=soa_data,
            hash=_build_hash(soa_pk, soa_data),
            managed=True,
            version=1
        )

        # Create the NS Recorset, returning the UUID primary key to be used
        # in creating the associated NS record
        # NS records could already exist, so check for duplicates
        try:
            ns_pk = recordsets_table.insert().execute(
                id=utils.generate_uuid().replace('-', ''),
                created_at=zone.created_at,
                domain_id=zone.id,
                tenant_id=zone.tenant_id,
                name=zone.name,
                type='NS',
                version=1
            ).inserted_primary_key[0]
        except exception.DBDuplicateEntry:
            # If there's already an NS recordset, retrieve it
            ns_pk = select([recordsets_table.c.id])\
                .where(recordsets_table.c.domain_id == zone.id)\
                .where(recordsets_table.c.tenant_id == zone.tenant_id)\
                .where(recordsets_table.c.name == zone.name)\
                .where(recordsets_table.c.type == 'NS')\
                .execute().scalar()

        # Create the NS records, one for each server
        for server in servers:
            records_table.insert().execute(
                id=utils.generate_uuid().replace('-', ''),
                created_at=zone.created_at,
                domain_id=zone.id,
                tenant_id=zone.tenant_id,
                recordset_id=ns_pk,
                data=server.name,
                hash=_build_hash(ns_pk, server.name),
                managed=True,
                version=1
            )


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    dialect = migrate_engine.url.get_dialect().name
    zones_table = Table('domains', meta, autoload=True)
    records_table = Table('records', meta, autoload=True)

    RECORD_TYPES = ['A', 'AAAA', 'CNAME', 'MX', 'SRV', 'TXT', 'SPF', 'NS',
                    'PTR', 'SSHFP']

    recordsets_table = Table('recordsets', meta, autoload=True)

    # Delete all SOA records
    recordsets_table.delete().where(recordsets_table.c.type == 'SOA').execute()

    # Remove SOA from the ENUM
    recordsets_table.c.type.alter(type=Enum(name='recordset_types',
                                            *RECORD_TYPES))

    # Remove non-delegated NS records
    # Get all the zones
    zones = select(
        columns=[
            zones_table.c.id,
            zones_table.c.created_at,
            zones_table.c.tenant_id,
            zones_table.c.name,
            zones_table.c.email,
            zones_table.c.serial,
            zones_table.c.refresh,
            zones_table.c.retry,
            zones_table.c.expire,
            zones_table.c.minimum
        ]
    ).execute().fetchall()

    for zone in zones:
        # for each zone, get all non-delegated NS recordsets
        results = recordsets_table.select().\
            where(recordsets_table.c.type == 'NS').\
            where(recordsets_table.c.name == zone.name).execute()
        for r in results:
            records_table.delete().\
                where(records_table.c.recordset_id == r.id).\
                where(records_table.c.managed == 1).execute()
        # NOTE: The value 1 is used instead of True because flake8 complains

    # Re-add the constraint for sqlite
    if dialect.startswith('sqlite'):
        constraint = UniqueConstraint('domain_id', 'name', 'type',
                                      name='unique_recordset',
                                      table=recordsets_table)

        constraint.create()
