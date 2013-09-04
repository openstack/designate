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
from sqlalchemy import func
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import null
from sqlalchemy.sql.expression import and_
from sqlalchemy.orm import exc as sqlalchemy_exceptions
from oslo.config import cfg
from designate.openstack.common import excutils
from designate.openstack.common import log as logging
from designate import exceptions
from designate.backend import base
from designate.backend.impl_powerdns import models
from designate.sqlalchemy.session import get_session
from designate.sqlalchemy.session import SQLOPTS
from designate.sqlalchemy.expressions import InsertFromSelect

LOG = logging.getLogger(__name__)
TSIG_SUPPORTED_ALGORITHMS = ['hmac-md5']

cfg.CONF.register_group(cfg.OptGroup(
    name='backend:powerdns', title="Configuration for Powerdns Backend"
))

cfg.CONF.register_opts([
    cfg.StrOpt('domain-type', default='NATIVE', help='PowerDNS Domain Type'),
    cfg.ListOpt('also-notify', default=[], help='List of additional IPs to '
                                                'send NOTIFYs to'),
] + SQLOPTS, group='backend:powerdns')


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
            'designate_id': tsigkey['id'],
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
        try:
            # Delete this TSIG Key itself
            tsigkey_m = self._get_tsigkey(tsigkey['id'])
            tsigkey_m.delete(self.session)
        except exceptions.TsigKeyNotFound:
            # If the TSIG Key is already gone, that's ok. We're deleting it
            # anyway, so just log and continue.
            LOG.critical('Attempted to delete a TSIG key which is not present '
                         'in the backend. ID: %s', tsigkey['id'])
            return

        # Delete this TSIG Key from every domain's metadata
        self.session.query(models.DomainMetadata)\
            .filter_by(kind='TSIG-ALLOW-AXFR', content=tsigkey['name'])\
            .delete()

    def create_server(self, context, server):
        LOG.debug('Create Server')
        self._update_domains_on_server_create(server)

    def update_server(self, context, server):
        LOG.debug('Update Server')
        self._update_domains_on_server_update(server)

    def delete_server(self, context, server):
        LOG.debug('Delete Server')
        self._update_domains_on_server_delete(server)

    # Domain Methods
    def create_domain(self, context, domain):
        servers = self.central_service.find_servers(self.admin_context)

        domain_m = models.Domain()
        domain_m.update({
            'designate_id': domain['id'],
            'name': domain['name'].rstrip('.'),
            'master': servers[0]['name'].rstrip('.'),
            'type': cfg.CONF['backend:powerdns'].domain_type,
            'account': context.tenant_id
        })
        domain_m.save(self.session)

        for server in servers:
            record_m = models.Record()
            record_m.update({
                'designate_id': server['id'],
                'domain_id': domain_m.id,
                'name': domain['name'].rstrip('.'),
                'type': 'NS',
                'content': server['name'].rstrip('.'),
                'ttl': domain['ttl'],
                'auth': True
            })
            record_m.save(self.session)

        # Install all TSIG Keys on this domain
        tsigkeys = self.session.query(models.TsigKey).all()
        values = [t.name for t in tsigkeys]

        self._update_domainmetadata(domain_m.id, 'TSIG-ALLOW-AXFR', values)

        # Install all Also Notify's on this domain
        self._update_domainmetadata(domain_m.id, 'ALSO-NOTIFY',
                                    cfg.CONF['backend:powerdns'].also_notify)

        # NOTE(kiall): Do the SOA last, ensuring we don't trigger a NOTIFY
        #              before the NS records are in place.
        record_m = models.Record()
        record_m.update({
            'designate_id': domain['id'],
            'domain_id': domain_m.id,
            'name': domain['name'].rstrip('.'),
            'type': 'SOA',
            'content': self._build_soa_content(domain, servers),
            'auth': True
        })
        record_m.save(self.session)

    def update_domain(self, context, domain):
        # TODO(kiall): Sync Server List

        domain_m = self._get_domain(domain['id'])

        try:
            self.session.begin()

            # Update the Domains SOA
            self._update_soa(domain)

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
            LOG.critical('Attempted to delete a domain which is not present '
                         'in the backend. ID: %s', domain['id'])
            return

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
            'designate_id': record['id'],
            'domain_id': domain_m.id,
            'name': record['name'].rstrip('.'),
            'type': record['type'],
            'content': self._sanitize_content(record['type'], record['data']),
            'ttl': domain['ttl'] if record['ttl'] is None else record['ttl'],
            'inherit_ttl': True if record['ttl'] is None else False,
            'prio': record['priority'],
            'auth': self._is_authoritative(domain, record)
        })

        record_m.save(self.session)

        self._update_soa(domain)

    def update_record(self, context, domain, record):
        record_m = self._get_record(record['id'])

        record_m.update({
            'name': record['name'].rstrip('.'),
            'type': record['type'],
            'content': self._sanitize_content(record['type'], record['data']),
            'ttl': domain['ttl'] if record['ttl'] is None else record['ttl'],
            'inherit_ttl': True if record['ttl'] is None else False,
            'prio': record['priority'],
            'auth': self._is_authoritative(domain, record)
        })

        record_m.save(self.session)

        self._update_soa(domain)

    def delete_record(self, context, domain, record):
        try:
            record_m = self._get_record(record['id'])
        except exceptions.RecordNotFound:
            # If the Record is already gone, that's ok. We're deleting it
            # anyway, so just log and continue.
            LOG.critical('Attempted to delete a record which is not present '
                         'in the backend. ID: %s', record['id'])
        else:
            record_m.delete(self.session)

        self._update_soa(domain)

    # Internal Methods
    def _update_soa(self, domain):
        servers = self.central_service.find_servers(self.admin_context)
        domain_m = self._get_domain(domain['id'])
        record_m = self._get_record(domain=domain_m, type='SOA')

        record_m.update({
            'content': self._build_soa_content(domain, servers),
            'ttl': domain['ttl']
        })

        record_m.save(self.session)

    def _update_domainmetadata(self, domain_id, kind, values=[], delete=True):
        """ Updates a domain's metadata with new values """
        # Fetch all current metadata of the specified kind
        query = self.session.query(models.DomainMetadata)
        query = query.filter_by(domain_id=domain_id, kind=kind)

        metadatas = query.all()

        for metadata in metadatas:
            if metadata.content not in values:
                if delete:
                    LOG.debug('Deleting stale domain metadata: %r',
                              (domain_id, kind, metadata.value))
                    # Delete no longer necessary values
                    metadata.delete(self.session)
            else:
                # Remove pre-existing values from the list of values to insert
                values.remove(metadata.content)

        # Insert new values
        for value in values:
            LOG.debug('Inserting new domain metadata: %r',
                      (domain_id, kind, value))
            m = models.DomainMetadata(domain_id=domain_id, kind=kind,
                                      content=value)
            m.save(self.session)

    def _is_authoritative(self, domain, record):
        # NOTE(kiall): See http://doc.powerdns.com/dnssec-modes.html
        if record['type'] == 'NS' and record['name'] != domain['name']:
            return False
        else:
            return True

    def _sanitize_content(self, type, content):
        if type in ('CNAME', 'MX', 'SRV', 'NS', 'PTR'):
            return content.rstrip('.')

        if type in ('TXT', 'SPF'):
            return '"%s"' % content.replace('"', '\\"')

        return content

    def _sanitize_uuid_str(self, uuid):
        return uuid.replace("-", "")

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

    def _update_domains_on_server_create(self, server):
        """
        For performance, manually prepare a bulk insert query to
        build NS records for all existing domains for insertion
        into Record table
        """
        ns_rec_content = self._sanitize_content("NS", server['name'])

        LOG.debug("Content field of newly created NS records for "
                  "existing domains upon server create is: %s"
                  % ns_rec_content)

        query_select = select([null(),
                               models.Domain.__table__.c.id,
                               models.Domain.__table__.c.name,
                               "'NS'",
                               "'%s'" % ns_rec_content,
                               null(),
                               null(),
                               null(),
                               null(),
                               1,
                               "'%s'" % self._sanitize_uuid_str(server['id']),
                               1])
        query = InsertFromSelect(models.Record.__table__, query_select)

        # Execute the manually prepared query
        # A TX is required for, at the least, SQLite.
        try:
            self.session.begin()
            self.session.execute(query)
        except Exception:
            with excutils.save_and_reraise_exception():
                self.session.rollback()
        else:
            self.session.commit()

    def _update_domains_on_server_update(self, server):
        """
        For performance, manually prepare a bulk update query to
        update all NS records for all existing domains that need
        updating of their corresponding NS record in Record table
        """
        ns_rec_content = self._sanitize_content("NS", server['name'])

        LOG.debug("Content field of existing NS records will be updated"
                  " to the following upon server update: %s" % ns_rec_content)
        try:

            # Execute the manually prepared query
            # A TX is required for, at the least, SQLite.
            #
            self.session.begin()

            # first determine the old name of the server
            # before making the updates. Since the value
            # is coming from an NS record, the server name
            # will not have a trailing period (.)
            old_ns_rec = self.session.query(models.Record)\
                .filter_by(type='NS', designate_id=server['id'])\
                .first()
            old_server_name = old_ns_rec.content

            LOG.debug("old server name read from a backend NS record:"
                      " %s" % old_server_name)
            LOG.debug("new server name: %s" % server['name'])

            # Then update all NS records that need updating
            # Only the name of a server has changed when we are here
            self.session.query(models.Record)\
                .filter_by(type='NS', designate_id=server['id'])\
                .update({"content": ns_rec_content})

            # Then update all SOA records as necessary
            # Do the SOA last, ensuring we don't trigger a NOTIFY
            # before the NS records are in place.
            #
            # Update the content field of every SOA record that has the
            # old server name as part of its 'content' field to reflect
            # the new server name.
            # Need to strip the trailing period from the server['name']
            # before using it to replace the old_server_name in the SOA
            # record since the SOA record already has a trailing period
            # and we want to keep it
            self.session.execute(models.Record.__table__
                .update()
                .where(and_(models.Record.__table__.c.type == "SOA",
                       models.Record.__table__.c.content.like
                           ("%s%%" % old_server_name)))
                .values(content=
                        func.replace(
                            models.Record.__table__.c.content,
                            old_server_name,
                            server['name'].rstrip('.'))
                        )
            )

        except Exception:
            with excutils.save_and_reraise_exception():
                self.session.rollback()
        # now commit
        else:
            self.session.commit()

    def _update_domains_on_server_delete(self, server):
        """
        For performance, manually prepare a bulk update query to
        update all NS records for all existing domains that need
        updating of their corresponding NS record in Record table
        """

        # find a replacement server
        replacement_server_name = None
        servers = self.central_service.find_servers(self.admin_context)

        for replacement in servers:
            if replacement['id'] != server['id']:
                replacement_server_name = replacement['name']
                break

        LOG.debug("This existing server name will be used to update existing"
                  " SOA records upon server delete: %s "
                  % replacement_server_name)

        # NOTE: because replacement_server_name came from central storage
        # it has the trailing period

        # Execute the manually prepared query
        # A TX is required for, at the least, SQLite.
        try:
            self.session.begin()
            # first delete affected NS records
            self.session.query(models.Record)\
                .filter_by(type='NS', designate_id=server['id'])\
                .delete()

            # then update all SOA records as necessary
            # Do the SOA last, ensuring we don't trigger a
            # NOTIFY before the NS records are in place.
            #
            # Update the content field of every SOA record that
            # has the deleted server name as part of its
            # 'content' field to reflect the name of another
            # server that exists
            # both server['name'] and replacement_server_name
            # have trailing period so we are fine just doing the
            # substitution without striping trailing period
            self.session.execute(models.Record.__table__
                .update()
                .where(and_(models.Record.__table__.c.type == "SOA",
                       models.Record.__table__.c.content.like
                           ("%s%%" % server['name'])))
                .values(content=func.replace(
                        models.Record.__table__.c.content,
                        server['name'],
                        replacement_server_name)))

        except Exception:
            with excutils.save_and_reraise_exception():
                self.session.rollback()
        else:
            self.session.commit()
