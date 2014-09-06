# Copyright 2012 Hewlett-Packard Development Company, L.P. All Rights Reserved.
# Copyright 2012 Managed I.T.
#
# Author: Patrick Galbraith <patg@hp.com>
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
import base64
import threading

from oslo.config import cfg
from oslo.db import options
from sqlalchemy.sql import select

from designate.openstack.common import excutils
from designate.openstack.common import log as logging
from designate.i18n import _LC
from designate import exceptions
from designate.backend import base
from designate.backend.impl_powerdns import tables
from designate.sqlalchemy import session
from designate.sqlalchemy.expressions import InsertFromSelect


LOG = logging.getLogger(__name__)
CONF = cfg.CONF
TSIG_SUPPORTED_ALGORITHMS = ['hmac-md5']

CONF.register_group(cfg.OptGroup(
    name='backend:powerdns', title="Configuration for Powerdns Backend"
))

CONF.register_opts([
    cfg.StrOpt('domain-type', default='NATIVE', help='PowerDNS Domain Type'),
    cfg.ListOpt('also-notify', default=[], help='List of additional IPs to '
                                                'send NOTIFYs to'),
] + options.database_opts, group='backend:powerdns')

# Overide the default DB connection registered above, to avoid name conflicts
# between the Designate and PowerDNS databases.
CONF.set_default('connection', 'sqlite:///$state_path/powerdns.sqlite',
                 group='backend:powerdns')


def _map_col(keys, col):
    return dict([(keys[i], col[i]) for i in range(len(keys))])


class PowerDNSBackend(base.Backend):
    __plugin_name__ = 'powerdns'

    def __init__(self, *args, **kwargs):
        super(PowerDNSBackend, self).__init__(*args, **kwargs)

        self.local_store = threading.local()

    def start(self):
        super(PowerDNSBackend, self).start()

    @property
    def session(self):
        # NOTE: This uses a thread local store, allowing each greenthread to
        #       have it's own session stored correctly. Without this, each
        #       greenthread may end up using a single global session, which
        #       leads to bad things happening.
        global LOCAL_STORE

        if not hasattr(self.local_store, 'session'):
            self.local_store.session = session.get_session(self.name)

        return self.local_store.session

    def _create(self, table, values):
        query = table.insert()

        resultproxy = self.session.execute(query, values)

        # Refetch the row, for generated columns etc
        query = select([table])\
            .where(table.c.id == resultproxy.inserted_primary_key[0])
        resultproxy = self.session.execute(query)

        return _map_col(query.columns.keys(), resultproxy.fetchone())

    def _update(self, table, values, exc_notfound, id_col=None):
        if id_col is None:
            id_col = table.c.id

        query = table.update()\
            .where(id_col == values[id_col.name])\
            .values(**values)

        resultproxy = self.session.execute(query)

        if resultproxy.rowcount != 1:
            raise exc_notfound()

        # Refetch the row, for generated columns etc
        query = select([table])\
            .where(id_col == values[id_col.name])
        resultproxy = self.session.execute(query)

        return _map_col(query.columns.keys(), resultproxy.fetchone())

    def _get(self, table, id_, exc_notfound, id_col=None):
        if id_col is None:
            id_col = table.c.id

        query = select([table])\
            .where(id_col == id_)

        resultproxy = self.session.execute(query)

        results = resultproxy.fetchall()

        if len(results) != 1:
            raise exc_notfound()

        # Map col keys to values in result
        return _map_col(query.columns.keys(), results[0])

    def _delete(self, table, id_, exc_notfound, id_col=None):
        if id_col is None:
            id_col = table.c.id

        query = table.delete()\
            .where(id_col == id_)

        resultproxy = self.session.execute(query)

        if resultproxy.rowcount != 1:
            raise exc_notfound()

    # TSIG Key Methods
    def create_tsigkey(self, context, tsigkey):
        """Create a TSIG Key"""

        if tsigkey['algorithm'] not in TSIG_SUPPORTED_ALGORITHMS:
            raise exceptions.NotImplemented('Unsupported algorithm')

        values = {
            'designate_id': tsigkey['id'],
            'name': tsigkey['name'],
            'algorithm': tsigkey['algorithm'],
            'secret': base64.b64encode(tsigkey['secret'])
        }

        self._create(tables.tsigkeys, values)

        # NOTE(kiall): Prepare and execute query to install this TSIG Key on
        #              every domain. We use a manual query here since anything
        #              else would be impossibly slow.
        query_select = select([
            tables.domains.c.id,
            "'TSIG-ALLOW-AXFR'",
            "'%s'" % tsigkey['name']]
        )

        columns = [
            tables.domain_metadata.c.domain_id,
            tables.domain_metadata.c.kind,
            tables.domain_metadata.c.content,
        ]

        query = InsertFromSelect(tables.domain_metadata, query_select,
                                 columns)

        # NOTE(kiall): A TX is required for, at the least, SQLite.
        self.session.begin()
        self.session.execute(query)
        self.session.commit()

    def update_tsigkey(self, context, tsigkey):
        """Update a TSIG Key"""
        values = self._get(
            tables.tsigkeys,
            tsigkey['id'],
            exceptions.TsigKeyNotFound,
            id_col=tables.tsigkeys.c.designate_id)

        # Store a copy of the original name..
        original_name = values['name']

        values.update({
            'name': tsigkey['name'],
            'algorithm': tsigkey['algorithm'],
            'secret': base64.b64encode(tsigkey['secret'])
        })

        self._update(tables.tsigkeys, values,
                     id_col=tables.tsigkeys.c.designate_id,
                     exc_notfound=exceptions.TsigKeyNotFound)

        # If the name changed, Update the necessary DomainMetadata records
        if original_name != tsigkey['name']:
            query = tables.domain_metadata.update()\
                .where(tables.domain_metadata.c.kind == 'TSIG_ALLOW_AXFR')\
                .where(tables.domain_metadata.c.content == original_name)

            query.values(content=tsigkey['name'])
            self.session.execute(query)

    def delete_tsigkey(self, context, tsigkey):
        """Delete a TSIG Key"""
        try:
            # Delete this TSIG Key itself
            self._delete(
                tables.tsigkeys, tsigkey['id'],
                exceptions.TsigKeyNotFound,
                id_col=tables.tsigkeys.c.designate_id)
        except exceptions.TsigKeyNotFound:
            # If the TSIG Key is already gone, that's ok. We're deleting it
            # anyway, so just log and continue.
            LOG.critical(_LC('Attempted to delete a TSIG key which is '
                             'not present in the backend. ID: %s') %
                         tsigkey['id'])
            return

        query = tables.domain_metadata.delete()\
            .where(tables.domain_metadata.c.kind == 'TSIG-ALLOW-AXFR')\
            .where(tables.domain_metadata.c.content == tsigkey['name'])
        self.session.execute(query)

    # Domain Methods
    def create_domain(self, context, domain):
        try:
            self.session.begin()
            servers = self.central_service.find_servers(self.admin_context)

            domain_values = {
                'designate_id': domain['id'],
                'name': domain['name'].rstrip('.'),
                'master': servers[0]['name'].rstrip('.'),
                'type': CONF['backend:powerdns'].domain_type,
                'account': context.tenant
            }

            domain_ref = self._create(tables.domains, domain_values)

            # Install all TSIG Keys on this domain
            query = select([tables.tsigkeys.c.name])
            resultproxy = self.session.execute(query)
            values = [i for i in resultproxy.fetchall()]

            self._update_domainmetadata(domain_ref['id'], 'TSIG-ALLOW-AXFR',
                                        values)

            # Install all Also Notify's on this domain
            self._update_domainmetadata(domain_ref['id'], 'ALSO-NOTIFY',
                                        CONF['backend:powerdns'].also_notify)
        except Exception:
            with excutils.save_and_reraise_exception():
                self.session.rollback()
        else:
            self.session.commit()

    def update_domain(self, context, domain):
        domain_ref = self._get(tables.domains, domain['id'],
                               exceptions.DomainNotFound,
                               id_col=tables.domains.c.designate_id)

        try:
            self.session.begin()

            # Update the Records TTLs where necessary
            query = tables.records.update()\
                .where(tables.records.c.domain_id == domain_ref['id'])
            query = query.where(tables.records.c.inherit_ttl == True)  # noqa\
            query = query.values(ttl=domain['ttl'])
            self.session.execute(query)
        except Exception:
            with excutils.save_and_reraise_exception():
                self.session.rollback()
        else:
            self.session.commit()

    def delete_domain(self, context, domain):
        try:
            domain_ref = self._get(tables.domains, domain['id'],
                                   exceptions.DomainNotFound,
                                   id_col=tables.domains.c.designate_id)
        except exceptions.DomainNotFound:
            # If the Domain is already gone, that's ok. We're deleting it
            # anyway, so just log and continue.
            LOG.critical(_LC('Attempted to delete a domain which is '
                             'not present in the backend. ID: %s') %
                         domain['id'])
            return

        self._delete(tables.domains, domain['id'],
                     exceptions.DomainNotFound,
                     id_col=tables.domains.c.designate_id)

        # Ensure the records are deleted
        query = tables.records.delete()\
            .where(tables.records.c.domain_id == domain_ref['id'])
        self.session.execute(query)

        # Ensure domainmetadata is deleted
        query = tables.domain_metadata.delete()\
            .where(tables.domain_metadata.c.domain_id == domain_ref['id'])
        self.session.execute(query)

    # RecordSet Methods
    def create_recordset(self, context, domain, recordset):
        try:
            self.session.begin(subtransactions=True)

            # Create all the records..
            for record in recordset.records:
                self.create_record(context, domain, recordset, record)
        except Exception:
            with excutils.save_and_reraise_exception():
                self.session.rollback()
        else:
            self.session.commit()

    def update_recordset(self, context, domain, recordset):
        # TODO(kiall): This is a total kludge. Intended as the simplest
        #              possible fix for the issue. This needs to be
        #              re-implemented correctly.
        try:
            self.session.begin(subtransactions=True)

            self.delete_recordset(context, domain, recordset)
            self.create_recordset(context, domain, recordset)
        except Exception:
            with excutils.save_and_reraise_exception():
                self.session.rollback()
        else:
            self.session.commit()

    def delete_recordset(self, context, domain, recordset):
        # Ensure records are deleted
        query = tables.records.delete()\
            .where(tables.records.c.designate_recordset_id == recordset['id'])
        self.session.execute(query)

    # Record Methods
    def create_record(self, context, domain, recordset, record):
        domain_ref = self._get(tables.domains, domain['id'],
                               exceptions.DomainNotFound,
                               id_col=tables.domains.c.designate_id)

        content = self._sanitize_content(recordset['type'], record['data'])
        ttl = domain['ttl'] if recordset['ttl'] is None else recordset['ttl']

        record_values = {
            'designate_id': record['id'],
            'designate_recordset_id': record['recordset_id'],
            'domain_id': domain_ref['id'],
            'name': recordset['name'].rstrip('.'),
            'type': recordset['type'],
            'content': content,
            'ttl': ttl,
            'inherit_ttl': True if recordset['ttl'] is None else False,
            'prio': record['priority'],
            'auth': self._is_authoritative(domain, recordset, record)
        }

        self._create(tables.records, record_values)

    def update_record(self, context, domain, recordset, record):
        record_ref = self._get_record(record['id'])

        content = self._sanitize_content(recordset['type'], record['data'])
        ttl = domain['ttl'] if recordset['ttl'] is None else recordset['ttl']

        record_ref.update({
            'content': content,
            'ttl': ttl,
            'inherit_ttl': True if recordset['ttl'] is None else False,
            'prio': record['priority'],
            'auth': self._is_authoritative(domain, recordset, record)
        })

        self._update(tables.records, record_ref,
                     exc_notfound=exceptions.RecordNotFound)

    def delete_record(self, context, domain, recordset, record):
        try:
            record_ref = self._get(tables.records, record['id'],
                                   exceptions.RecordNotFound,
                                   id_col=tables.records.c.designate_id)
        except exceptions.RecordNotFound:
            # If the Record is already gone, that's ok. We're deleting it
            # anyway, so just log and continue.
            LOG.critical(_LC('Attempted to delete a record which is '
                             'not present in the backend. ID: %s') %
                         record['id'])
        else:
            self._delete(tables.records, record_ref['id'],
                         exceptions.RecordNotFound)

    # Internal Methods
    def _update_domainmetadata(self, domain_id, kind, values=None,
                               delete=True):
        """Updates a domain's metadata with new values"""
        # Fetch all current metadata of the specified kind
        values = values or []

        query = select([tables.domain_metadata.c.content])\
            .where(tables.domain_metadata.c.domain_id == domain_id)\
            .where(tables.domain_metadata.c.kind == kind)
        resultproxy = self.session.execute(query)
        results = resultproxy.fetchall()

        for metadata_id, content in results:
            if content not in values:
                if delete:
                    LOG.debug('Deleting stale domain metadata: %r' %
                              ([domain_id, kind, content],))
                    # Delete no longer necessary values
                    # We should never get a notfound here, so UnknownFailure is
                    # a reasonable choice.
                    self._delete(tables.domain_metadata, metadata_id,
                                 exceptions.UnknownFailure)
            else:
                # Remove pre-existing values from the list of values to insert
                values.remove(content)

        # Insert new values
        for value in values:
            LOG.debug('Inserting new domain metadata: %r' %
                      ([domain_id, kind, value],))
            self._create(
                tables.domain_metadata,
                {
                    "domain_id": domain_id,
                    "kind": kind,
                    "content": value
                })

    def _is_authoritative(self, domain, recordset, record):
        # NOTE(kiall): See http://doc.powerdns.com/dnssec-modes.html
        if recordset['type'] == 'NS' and recordset['name'] != domain['name']:
            return False
        else:
            return True

    def _sanitize_content(self, type, content):
        if type in ('CNAME', 'MX', 'SRV', 'NS', 'PTR'):
            return content.rstrip('.')

        if type in ('TXT', 'SPF'):
            return '"%s"' % content.replace('"', '\\"')

        return content

    def _get_record(self, record_id=None, domain=None, type_=None):
        query = select([tables.records])

        if record_id:
            query = query.where(tables.records.c.designate_id == record_id)

        if type_:
            query = query.where(tables.records.c.type == type_)

        if domain:
            query = query.where(tables.records.c.domain_id == domain['id'])

        resultproxy = self.session.execute(query)
        results = resultproxy.fetchall()

        if len(results) < 1:
            raise exceptions.RecordNotFound('No record found')
        elif len(results) > 1:
            raise exceptions.RecordNotFound('Too many records found')
        else:
            return _map_col(query.columns.keys(), results[0])
