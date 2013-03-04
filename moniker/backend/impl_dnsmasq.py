# Copyright 2012 Managed I.T.
#
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
import shutil
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging
from moniker import utils
from moniker.backend import base
from moniker.context import MonikerContext

LOG = logging.getLogger(__name__)


class DnsmasqBackend(base.Backend):
    __plugin_name__ = 'dnsmasq'

    def start(self):
        super(DnsmasqBackend, self).start()

        output_folder = os.path.join(os.path.abspath(cfg.CONF.state_path),
                                     'dnsmasq')

        # Create the output folder tree if necessary
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # TODO: This is a hack to ensure the data dir is 100% up to date
        admin_context = MonikerContext.get_admin_context()

        domains = self.central_service.get_domains(admin_context)
        for domain in domains:
            self._sync_domain(domain)
        self._sync_domains()

    def create_domain(self, context, domain):
        LOG.debug('Create Domain')
        self._sync_domain(domain)

    def update_domain(self, context, domain):
        LOG.debug('Update Domain')
        self._sync_domain(domain)

    def delete_domain(self, context, domain):
        LOG.debug('Delete Domain')
        self._sync_delete_domain(domain)

    def create_record(self, context, domain, record):
        LOG.debug('Create Record')
        self._sync_domain(domain)

    def update_record(self, context, domain, record):
        LOG.debug('Update Record')
        self._sync_domain(domain)

    def delete_record(self, context, domain, record):
        LOG.debug('Delete Record')
        self._sync_domain(domain)

    def _sync_domains(self):
        """ Sync the list of domains this server handles """
        LOG.debug('Synchronising domains')

        admin_context = MonikerContext.get_admin_context()
        domains = self.central_service.get_domains(admin_context)

        output_path = os.path.join(os.path.abspath(cfg.CONF.state_path),
                                   'dnsmasq', 'flatdns.zone')

        output_file = open(output_path, 'w+')
        for domain in domains:
            zone_file = os.path.join(os.path.abspath(cfg.CONF.state_path),
                                     'dnsmasq', '%s.zone' % domain['id'])
            LOG.debug('Merging %s' % zone_file)
            if os.path.exists(zone_file):
                shutil.copyfileobj(open(zone_file, 'r'), output_file)
        output_file.close()

        # Send HUP to dnsmasq
        utils.execute('killall', '-HUP', 'dnsmasq')

    def _sync_delete_domain(self, domain):
        """ Remove domain zone files rebuild flat zone """
        LOG.debug('Delete Domain: %s' % domain['id'])

        output_folder = os.path.join(os.path.abspath(cfg.CONF.state_path),
                                     'dnsmasq')

        output_path = os.path.join(output_folder, '%s.zone' % domain['id'])
        os.remove(output_path)
        self._sync_domains()

    def _sync_domain(self, domain):
        """ Sync a single domain's zone file """
        LOG.debug('Synchronising Domain: %s' % domain['id'])

        admin_context = MonikerContext.get_admin_context()
        records = self.central_service.get_records(admin_context, domain['id'])

        output_folder = os.path.join(os.path.abspath(cfg.CONF.state_path),
                                     'dnsmasq')

        output_path = os.path.join(output_folder, '%s.zone' % domain['id'])
        utils.render_template_to_file('dnsmasq-zone.jinja2',
                                      output_path,
                                      records=records)

        self._sync_domains()
