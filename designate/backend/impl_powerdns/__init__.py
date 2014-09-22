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
from sqlalchemy.orm import exc as sqlalchemy_exceptions

from designate.openstack.common import excutils
from designate.openstack.common import log as logging
from designate.i18n import _LC
from designate import exceptions
from designate.backend import base
from designate.backend.impl_powerdns import models
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

    # TSIG Key Methods
    def create_tsigkey(self, context, tsigkey):
        """Create a TSIG Key"""

        if tsigkey['algorithm'] not in TSIG_SUPPORTED_ALGORITHMS:
            raise exceptions.NotImplemented('Unsupported algorithm')

        tsigkey_m = models.TsigKey()

        tsigkey_m.update({
            'designate_id': tsigkey['id'],
            'name': tsigkey['name'],
            'algorithm': tsigkey['algorithm'],
            'secret': base64.b64encode(tsigkey['secret'])
        })

        tsigkey_m.save(self.session)

        # NOTE(kiall): Prepare and execute query to install this TSIG Key on
        #              every domain. We use a manual query here since anything
        #              else would be impossibly slow.
        query_select = select([
            models.Domain.__table__.c.id,
            "'TSIG-ALLOW-AXFR'",
            "'%s'" % tsigkey['name']]
        )

        columns = [
            models.DomainMetadata.__table__.c.domain_id,
            models.DomainMetadata.__table__.c.kind,
            models.DomainMetadata.__table__.c.content,
        ]

        query = InsertFromSelect(models.DomainMetadata.__table__, query_select,
                                 columns)

        # NOTE(kiall): A TX is required for, at the least, SQLite.
        self.session.begin()
        self.session.execute(query)
        self.session.commit()

    def update_tsigkey(self, context, tsigkey):
        """Update a TSIG Key"""
        tsigkey_m = self._get_tsigkey(tsigkey['id'])

        # Store a copy of the original name..
        original_name = tsigkey_m.name

        tsigkey_m.update({
            'name': tsigkey['name'],
            'algorithm': tsigkey['algorithm'],
            'secret': base64.b64encode(tsigkey['secret'])
        })

        tsigkey_m.save(self.session)

        # If the name changed, Update the necessary DomainMetadata records
        if original_name != tsigkey['name']:
            self.session.query(models.DomainMetadata)\
                .filter_by(kind='TSIG-ALLOW-AXFR', content=original_name)\
                .update(content=tsigkey['name'])

    def delete_tsigkey(self, context, tsigkey):
        """Delete a TSIG Key"""
        try:
            # Delete this TSIG Key itself
            tsigkey_m = self._get_tsigkey(tsigkey['id'])
            tsigkey_m.delete(self.session)
        except exceptions.TsigKeyNotFound:
            # If the TSIG Key is already gone, that's ok. We're deleting it
            # anyway, so just log and continue.
            LOG.critical(_LC('Attempted to delete a TSIG key which is '
                             'not present in the backend. ID: %s') %
                         tsigkey['id'])
            return

        # Delete this TSIG Key from every domain's metadata
        self.session.query(models.DomainMetadata)\
            .filter_by(kind='TSIG-ALLOW-AXFR', content=tsigkey['name'])\
            .delete()

    # Domain Methods
    def create_domain(self, context, domain):
        servers = self.central_service.find_servers(self.admin_context)

        domain_m = models.Domain()
        domain_m.update({
            'designate_id': domain['id'],
            'name': domain['name'].rstrip('.'),
            'master': servers[0]['name'].rstrip('.'),
            'type': CONF['backend:powerdns'].domain_type,
            'account': context.tenant
        })
        domain_m.save(self.session)

        # Install all TSIG Keys on this domain
        tsigkeys = self.session.query(models.TsigKey).all()
        values = [t.name for t in tsigkeys]

        self._update_domainmetadata(domain_m.id, 'TSIG-ALLOW-AXFR', values)

        # Install all Also Notify's on this domain
        self._update_domainmetadata(domain_m.id, 'ALSO-NOTIFY',
                                    CONF['backend:powerdns'].also_notify)

    def update_domain(self, context, domain):
        domain_m = self._get_domain(domain['id'])

        try:
            self.session.begin()

            # Update the Records TTLs where necessary
            self.session.query(models.Record)\
                        .filter_by(domain_id=domain_m.id, inherit_ttl=True)\
                        .update({'ttl': domain['ttl']})

        except Exception:
            with excutils.save_and_reraise_exception():
                self.session.rollback()
        else:
            self.session.commit()

    def delete_domain(self, context, domain):
        try:
            domain_m = self._get_domain(domain['id'])
        except exceptions.DomainNotFound:
            # If the Domain is already gone, that's ok. We're deleting it
            # anyway, so just log and continue.
            LOG.critical(_LC('Attempted to delete a domain which is '
                             'not present in the backend. ID: %s') %
                         domain['id'])
            return

        domain_m.delete(self.session)

        # Ensure the records are deleted
        query = self.session.query(models.Record)
        query.filter_by(domain_id=domain_m.id).delete()

        # Ensure domainmetadata is deleted
        query = self.session.query(models.DomainMetadata)
        query.filter_by(domain_id=domain_m.id).delete()

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
        query = self.session.query(models.Record)
        query.filter_by(designate_recordset_id=recordset['id']).delete()

    # Record Methods
    def create_record(self, context, domain, recordset, record):
        domain_m = self._get_domain(domain['id'])
        record_m = models.Record()

        content = self._sanitize_content(recordset['type'], record['data'])
        ttl = domain['ttl'] if recordset['ttl'] is None else recordset['ttl']

        record_m.update({
            'designate_id': record['id'],
            'designate_recordset_id': record['recordset_id'],
            'domain_id': domain_m.id,
            'name': recordset['name'].rstrip('.'),
            'type': recordset['type'],
            'content': content,
            'ttl': ttl,
            'inherit_ttl': True if recordset['ttl'] is None else False,
            'prio': record['priority'],
            'auth': self._is_authoritative(domain, recordset, record)
        })

        record_m.save(self.session)

    def update_record(self, context, domain, recordset, record):
        record_m = self._get_record(record['id'])

        content = self._sanitize_content(recordset['type'], record['data'])
        ttl = domain['ttl'] if recordset['ttl'] is None else recordset['ttl']

        record_m.update({
            'content': content,
            'ttl': ttl,
            'inherit_ttl': True if recordset['ttl'] is None else False,
            'prio': record['priority'],
            'auth': self._is_authoritative(domain, recordset, record)
        })

        record_m.save(self.session)

    def delete_record(self, context, domain, recordset, record):
        try:
            record_m = self._get_record(record['id'])
        except exceptions.RecordNotFound:
            # If the Record is already gone, that's ok. We're deleting it
            # anyway, so just log and continue.
            LOG.critical(_LC('Attempted to delete a record which is '
                             'not present in the backend. ID: %s') %
                         record['id'])
        else:
            record_m.delete(self.session)

    # Internal Methods
    def _update_domainmetadata(self, domain_id, kind, values=None,
                               delete=True):
        """Updates a domain's metadata with new values"""
        # Fetch all current metadata of the specified kind
        values = values or []

        query = self.session.query(models.DomainMetadata)
        query = query.filter_by(domain_id=domain_id, kind=kind)

        metadatas = query.all()

        for metadata in metadatas:
            if metadata.content not in values:
                if delete:
                    LOG.debug('Deleting stale domain metadata: %r' %
                              ([domain_id, kind, metadata.value],))
                    # Delete no longer necessary values
                    metadata.delete(self.session)
            else:
                # Remove pre-existing values from the list of values to insert
                values.remove(metadata.content)

        # Insert new values
        for value in values:
            LOG.debug('Inserting new domain metadata: %r' %
                      ([domain_id, kind, value],))
            m = models.DomainMetadata(domain_id=domain_id, kind=kind,
                                      content=value)
            m.save(self.session)

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

    def _get_tsigkey(self, tsigkey_id):
        query = self.session.query(models.TsigKey)

        try:
            tsigkey = query.filter_by(designate_id=tsigkey_id).one()
        except sqlalchemy_exceptions.NoResultFound:
            raise exceptions.TsigKeyNotFound('No tsigkey found')
        except sqlalchemy_exceptions.MultipleResultsFound:
            raise exceptions.TsigKeyNotFound('Too many tsigkeys found')
        else:
            return tsigkey

    def _get_domain(self, domain_id):
        query = self.session.query(models.Domain)

        try:
            domain = query.filter_by(designate_id=domain_id).one()
        except sqlalchemy_exceptions.NoResultFound:
            raise exceptions.DomainNotFound('No domain found')
        except sqlalchemy_exceptions.MultipleResultsFound:
            raise exceptions.DomainNotFound('Too many domains found')
        else:
            return domain

    def _get_record(self, record_id=None, domain=None, type=None):
        query = self.session.query(models.Record)

        if record_id:
            query = query.filter_by(designate_id=record_id)

        if type:
            query = query.filter_by(type=type)

        if domain:
            query = query.filter_by(domain_id=domain.id)

        try:
            record = query.one()
        except sqlalchemy_exceptions.NoResultFound:
            raise exceptions.RecordNotFound('No record found')
        except sqlalchemy_exceptions.MultipleResultsFound:
            raise exceptions.RecordNotFound('Too many records found')
        else:
            return record
