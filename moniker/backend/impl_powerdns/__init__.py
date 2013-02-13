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
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import null
from sqlalchemy.orm import exc as sqlalchemy_exceptions
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging
from moniker import exceptions
from moniker.backend import base
from moniker.backend.impl_powerdns import models
from moniker.sqlalchemy.session import get_session, SQLOPTS
from moniker.sqlalchemy.expressions import InsertFromSelect

LOG = logging.getLogger(__name__)
TSIG_SUPPORTED_ALGORITHMS = ['hmac-md5']

cfg.CONF.register_group(cfg.OptGroup(
    name='backend:powerdns', title="Configuration for Powerdns Backend"
))

cfg.CONF.register_opts(SQLOPTS, group='backend:powerdns')


class PowerDNSBackend(base.Backend):
    __plugin_name__ = 'powerdns'

    def start(self):
        super(PowerDNSBackend, self).start()

        self.session = get_session(self.name)

    # TSIG Key Methods
    def create_tsigkey(self, context, tsigkey):
        """ Create a TSIG Key """

        if tsigkey['algorithm'] not in TSIG_SUPPORTED_ALGORITHMS:
            raise exceptions.NotImplemented('Unsupported algorithm')

        tsigkey_m = models.TsigKey()

        tsigkey_m.update({
            'moniker_id': tsigkey['id'],
            'name': tsigkey['name'],
            'algorithm': tsigkey['algorithm'],
            'secret': base64.b64encode(tsigkey['secret'])
        })

        tsigkey_m.save(self.session)

        # NOTE(kiall): Prepare and execute query to install this TSIG Key on
        #              every domain. We use a manual query here since anything
        #              else would be impossibly slow.
        query_select = select([null(),
                               models.Domain.__table__.c.id,
                               "'TSIG-ALLOW-AXFR'",
                               "'%s'" % tsigkey['name']])
        query = InsertFromSelect(models.DomainMetadata.__table__, query_select)

        # NOTE(kiall): A TX is required for, at the least, SQLite.
        self.session.begin()
        self.session.execute(query)
        self.session.commit()

    def update_tsigkey(self, context, tsigkey):
        """ Update a TSIG Key """
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
        """ Delete a TSIG Key """
        # Delete this TSIG Key itself
        tsigkey_m = self._get_tsigkey(tsigkey['id'])
        tsigkey_m.delete(self.session)

        # Delete this TSIG Key from every domain's metadata
        self.session.query(models.DomainMetadata)\
            .filter_by(kind='TSIG-ALLOW-AXFR', content=tsigkey['name'])\
            .delete()

    # Domain Methods
    def create_domain(self, context, domain):
        servers = self.central_service.get_servers(self.admin_context)

        domain_m = models.Domain()
        domain_m.update({
            'moniker_id': domain['id'],
            'name': domain['name'].rstrip('.'),
            'master': servers[0]['name'].rstrip('.'),
            'type': 'NATIVE',
            'account': context.tenant_id
        })
        domain_m.save(self.session)

        for server in servers:
            record_m = models.Record()
            record_m.update({
                'moniker_id': server['id'],
                'domain_id': domain_m.id,
                'name': domain['name'].rstrip('.'),
                'type': 'NS',
                'content': server['name'].rstrip('.')
            })
            record_m.save(self.session)

        # Install All TSIG Keys on this domain
        tsigkeys = self.session.query(models.TsigKey).all()

        for tsigkey in tsigkeys:
            domainmetadata_m = models.DomainMetadata()
            domainmetadata_m.update({
                'domain_id': domain_m.id,
                'kind': "TSIG-ALLOW-AXFR",
                'content': tsigkey['name']
            })
            domainmetadata_m.save(self.session)

        # NOTE(kiall): Do the SOA last, ensuring we don't trigger a NOTIFY
        #              before the NS records are in place.
        record_m = models.Record()
        record_m.update({
            'moniker_id': domain['id'],
            'domain_id': domain_m.id,
            'name': domain['name'].rstrip('.'),
            'type': 'SOA',
            'content': self._build_soa_content(domain, servers)
        })
        record_m.save(self.session)

    def update_domain(self, context, domain):
        servers = self.central_service.get_servers(self.admin_context)

        domain_m = self._get_domain(domain['id'])

        # TODO: Sync Server List

        soa_record_m = self._get_record(domain=domain_m, type='SOA')

        soa_record_m.update({
            'content': self._build_soa_content(domain, servers)
        })

        soa_record_m.save(self.session)

    def delete_domain(self, context, domain):
        domain_m = self._get_domain(domain['id'])
        domain_m.delete(self.session)

        # Ensure the records are deleted
        query = self.session.query(models.Record)
        query.filter_by(domain_id=domain_m.id).delete()

        # Ensure domainmetadata is deleted
        query = self.session.query(models.DomainMetadata)
        query.filter_by(domain_id=domain_m.id).delete()

    # Record Methods
    def create_record(self, context, domain, record):
        domain_m = self._get_domain(domain['id'])
        record_m = models.Record()

        record_m.update({
            'moniker_id': record['id'],
            'domain_id': domain_m.id,
            'name': record['name'].rstrip('.'),
            'type': record['type'],
            'content': self._sanitize_content(record['type'], record['data']),
            'ttl': record['ttl'],
            'prio': record['priority']
        })

        record_m.save(self.session)

    def update_record(self, context, domain, record):
        record_m = self._get_record(record['id'])

        record_m.update({
            'name': record['name'].rstrip('.'),
            'type': record['type'],
            'content': self._sanitize_content(record['type'], record['data']),
            'ttl': record['ttl'],
            'prio': record['priority']
        })

        record_m.save(self.session)

    def delete_record(self, context, domain, record):
        record_m = self._get_record(record['id'])
        record_m.delete(self.session)

    # Internal Methods
    def _sanitize_content(self, type, content):
        if type in ('CNAME', 'MX', 'SRV', 'NS', 'PTR'):
            return content.rstrip('.')

        return content

    def _build_soa_content(self, domain, servers):
        return "%s %s. %d %d %d %d %d" % (servers[0]['name'],
                                          domain['email'].replace("@", "."),
                                          domain['serial'],
                                          domain['refresh'],
                                          domain['retry'],
                                          domain['expire'],
                                          domain['minimum'])

    def _get_tsigkey(self, tsigkey_id):
        query = self.session.query(models.TsigKey)

        try:
            tsigkey = query.filter_by(moniker_id=tsigkey_id).one()
        except sqlalchemy_exceptions.NoResultFound:
            raise exceptions.TsigKeyNotFound('No tsigkey found')
        except sqlalchemy_exceptions.MultipleResultsFound:
            raise exceptions.TsigKeyNotFound('Too many tsigkeys found')
        else:
            return tsigkey

    def _get_domain(self, domain_id):
        query = self.session.query(models.Domain)

        try:
            domain = query.filter_by(moniker_id=domain_id).one()
        except sqlalchemy_exceptions.NoResultFound:
            raise exceptions.DomainNotFound('No domain found')
        except sqlalchemy_exceptions.MultipleResultsFound:
            raise exceptions.DomainNotFound('Too many domains found')
        else:
            return domain

    def _get_record(self, record_id=None, domain=None, type=None):
        query = self.session.query(models.Record)

        if record_id:
            query = query.filter_by(moniker_id=record_id)

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
