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
import os
from oslo.config import cfg
from designate.openstack.common import log as logging
from designate import utils
from designate import exceptions
from designate.backend import base
from sqlalchemy.ext.sqlsoup import SqlSoup
from sqlalchemy.engine.url import _parse_rfc1738_args
from designate.sqlalchemy.session import get_engine
from designate.sqlalchemy.session import SQLOPTS

LOG = logging.getLogger(__name__)

cfg.CONF.register_group(cfg.OptGroup(
    name='backend:mysqlbind9', title="Configuration for BIND9+MySQL Backend"
))

cfg.CONF.register_opts([
    cfg.StrOpt('rndc-host', default='127.0.0.1', help='RNDC Host'),
    cfg.IntOpt('rndc-port', default=953, help='RNDC Port'),
    cfg.StrOpt('rndc-config-file',
               default=None, help='RNDC Config File'),
    cfg.StrOpt('rndc-key-file', secret=True,
               default=None, help='RNDC Key File'),
    cfg.StrOpt('dns-server-type', default='master',
               help='slave or master DNS server?'),
    cfg.BoolOpt('write-database', default=True,
                help='Write to the DNS mysqlbind database?'),
    cfg.StrOpt('database-dns-table',
               default='dns_domains',
               help='DNS schema'),
], group='backend:mysqlbind9')

cfg.CONF.register_opts(SQLOPTS, group='backend:mysqlbind9')


class MySQLBind9Backend(base.Backend):
    __plugin_name__ = 'mysqlbind9'

    def get_url_data(self):
        url = _parse_rfc1738_args(cfg.CONF[self.name].database_connection)
        return url.translate_connect_args()

    def get_dns_table(self, table=None):
        """
        Get a Table object from SQLSoup

        :param table: Overridable table name
        """
        table = table or cfg.CONF[self.name].database_dns_table
        return getattr(self._db, table)

    def start(self):
        super(MySQLBind9Backend, self).start()

        if cfg.CONF[self.name].write_database:
            self._engine = get_engine(self.name)
            self._db = SqlSoup(self._engine)

        self._sync_domains()

    def _add_soa_record(self, domain, servers):
        """
        add the single SOA record for this domain. Must create the
        data from attributes of the domain
        """
        table = self.get_dns_table()
        data_rec = "%s. %s. %d %d %d %d %d" % (
                   servers[0]['name'],
                   domain['email'].replace("@", "."),
                   domain['serial'],
                   domain['refresh'],
                   domain['retry'],
                   domain['expire'],
                   domain['minimum'])

        # use the domain id for records that don't have a match
        # in designate's records table
        table.insert(
            tenant_id=domain['tenant_id'],
            domain_id=domain['id'],
            designate_rec_id=domain['id'],
            name=domain['name'],
            ttl=domain['ttl'],
            type='SOA',
            data=data_rec)
        self._db.commit()

    def _add_ns_records(self, domain, servers):
        """
        add the NS records, one for each server, for this domain
        """
        table = self.get_dns_table()

        # use the domain id for records that don't have a match
        # in designate's records table
        for server in servers:
            table.insert(
                tenant_id=domain['tenant_id'],
                domain_id=domain['id'],
                designate_rec_id=domain['id'],
                name=domain['name'],
                ttl=domain['ttl'],
                type='NS',
                data=server['name'])

        self._db.commit()

    def _insert_db_record(self, tenant_id, domain_id, record):
        """
        generic db insertion method for a domain record
        """
        table = self.get_dns_table()
        table.insert(
            tenant_id=tenant_id,
            domain_id=domain_id,
            designate_rec_id=record['id'],
            name=record['name'],
            ttl=record['ttl'],
            type=record['type'],
            data=record['data'])
        self._db.commit()

    def _update_ns_records(self, domain, servers):
        """
        delete and re-add all NS records : easier to just delete all
        NS records and then replace - in the case of adding new NS
        servers
        """
        table = self.get_dns_table()

        all_ns_rec = table.filter_by(tenant_id=domain['tenant_id'],
                                     domain_id=domain['id'],
                                     type=u'NS')

        # delete all NS records
        all_ns_rec.delete()
        # add all NS records (might have new servers)
        self._db.commit()

        self._add_ns_records(domain, servers)

    def _update_db_record(self, tenant_id, record):
        """
        generic domain db record update method
        """
        table = self.get_dns_table()

        q = table.filter_by(
            tenant_id=tenant_id,
            domain_id=record['domain_id'],
            designate_rec_id=record['id'])

        q.update({'ttl': record['ttl'],
                  'type': record['type'],
                  'data': record['data']})

        self._db.commit()

    def _update_soa_record(self, domain, servers):
        """
        update the one single SOA record for the domain
        """
        LOG.debug("_update_soa_record()")
        table = self.get_dns_table()

        # there will only ever be -one- of these
        existing_record = table.filter_by(tenant_id=domain['tenant_id'],
                                          domain_id=domain['id'],
                                          type=u'SOA')

        data_rec = "%s. %s. %d %d %d %d %d" % (
                   servers[0]['name'],
                   domain['email'].replace("@", "."),
                   domain['serial'],
                   domain['refresh'],
                   domain['retry'],
                   domain['expire'],
                   domain['minimum'])

        existing_record.update(
            {'ttl': domain['ttl'],
             'type': u'SOA',
             'data': data_rec})

        self._db.commit()

#    def _update_domain_ttl(self, domain):
#        LOG.debug("_update_soa_record()")
#        table = self.get_dns_table()
#
#        # there will only ever be -one- of these
#        domain_records = table.filter_by(domain_id=domain['id'])
#
#        domain_records.update({'ttl': domain['ttl']})
#
#        self._db.commit()

    def _delete_db_record(self, tenant_id, record):
        """
        delete a specific record for a given domain
        """
        table = self.get_dns_table()
        LOG.debug("_delete_db_record")

        q = table.filter_by(
            tenant_id=tenant_id,
            domain_id=record['domain_id'],
            designate_rec_id=record['id'])

        q.delete()

        self._db.commit()

    def _delete_db_domain_records(self, tenant_id, domain_id):
        """
         delete all records for a given domain
         """
        LOG.debug('_delete_db_domain_records()')
        table = self.get_dns_table()

        # delete all records for the domain id
        q = table.filter_by(tenant_id=tenant_id,
                            domain_id=domain_id)
        q.delete()

        self._db.commit()

    def create_domain(self, context, domain):
        LOG.debug('create_domain()')

        if cfg.CONF[self.name].write_database:
            servers = self.central_service.find_servers(self.admin_context)

            self._add_soa_record(domain, servers)
            self._add_ns_records(domain, servers)

        self._sync_domains()

    def update_domain(self, context, domain):
        LOG.debug('update_domain()')

        if cfg.CONF[self.name].write_database:
            servers = self.central_service.find_servers(self.admin_context)

            self._update_soa_record(domain, servers)
            self._update_ns_records(domain, servers)

    def delete_domain(self, context, domain):
        LOG.debug('delete_domain()')

        if cfg.CONF[self.name].write_database:
            self._delete_db_domain_records(domain['tenant_id'],
                                           domain['id'])

        self._sync_domains()

    def create_server(self, context, server):
        LOG.debug('create_server()')

        raise exceptions.NotImplemented('create_server() for '
                                        'mysqlbind9 backend is '
                                        'not implemented')

        """
        TODO: this first-cut will not scale. Use bulk SQLAlchemy (core) queries
        if cfg.CONF[self.name].write_database:
            domains = self.central_service.find_domains(self.admin_context)

            for domain in domains:
                self._add_ns_records(domain, server)

        self._sync_domains()
        """

#   This method could be a very expensive and should only be called
#   (e.g., from central) only if the name of the existing server is
#   changed.
    def update_server(self, context, server):
        LOG.debug('update_server()')

        raise exceptions.NotImplemented('update_server() for '
                                        'mysqlbind9 backend is '
                                        'not implemented')

        """
        TODO: this first-cut will not scale. Use bulk SQLAlchemy (core) queries
        if cfg.CONF[self.name].write_database:
            servers = self.central_service.find_servers(self.admin_context)
            domains = self.central_service.find_domains(self.admin_context)

            for domain in domains:
                self._update_ns_records(domain, servers)

        self._sync_domains()
        """

    def delete_server(self, context, server):
        LOG.debug('delete_server()')

        raise exceptions.NotImplemented('delete_server() for '
                                        'mysqlbind9 backend is'
                                        ' not implemented')

        """
        TODO: For scale, Use bulk SQLAlchemy (core) queries
        """

    def create_record(self, context, domain, record):
        LOG.debug('create_record()')
        if cfg.CONF[self.name].write_database:
            self._insert_db_record(domain['tenant_id'],
                                   domain['id'],
                                   record)

    def update_record(self, context, domain, record):
        LOG.debug('update_record()')
        if cfg.CONF[self.name].write_database:
            self._update_db_record(domain['tenant_id'],
                                   record)

    def delete_record(self, context, domain, record):
        LOG.debug('Delete Record')
        if cfg.CONF[self.name].write_database:
            self._delete_db_record(domain['tenant_id'],
                                   record)

    def _sync_domains(self):
        """
        Update the zone file and reconfig rndc to update bind.
        Unike regular bind, this only needs to be done upon adding
        or deleting domains as mysqlbind takes care of updating
        bind upon regular record changes
        """
        LOG.debug('Synchronising domains')

        domains = self.central_service.find_domains(self.admin_context)

        output_folder = os.path.join(os.path.abspath(cfg.CONF.state_path),
                                     'bind9')

        # Create the output folder tree if necessary
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        output_path = os.path.join(output_folder, 'zones.config')

        abs_state_path = os.path.abspath(cfg.CONF.state_path)

        LOG.debug("Getting ready to write zones.config at %s" % output_path)

        # NOTE(CapTofu): Might have to adapt this later on?
        url = self.get_url_data()
        utils.render_template_to_file('mysql-bind9-config.jinja2',
                                      output_path,
                                      domains=domains,
                                      state_path=abs_state_path,
                                      dns_server_type=cfg.CONF[self.name].
                                      dns_server_type,
                                      dns_db_schema=url['database'],
                                      dns_db_table=cfg.CONF[self.name].
                                      database_dns_table,
                                      dns_db_host=url['host'],
                                      dns_db_user=url['username'],
                                      dns_db_password=url['password'])

        # only do this if domain create, domain delete
        rndc_call = [
            'rndc',
            '-s', cfg.CONF[self.name].rndc_host,
            '-p', str(cfg.CONF[self.name].rndc_port),
        ]

        if cfg.CONF[self.name].rndc_config_file:
            rndc_call.extend(['-c', self.config.rndc_config_file])

        if cfg.CONF[self.name].rndc_key_file:
            rndc_call.extend(['-k', self.config.rndc_key_file])

        rndc_call.extend(['reconfig'])

        utils.execute(*rndc_call)
