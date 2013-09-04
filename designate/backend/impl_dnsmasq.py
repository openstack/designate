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
import glob
import shutil
from oslo.config import cfg
from designate.openstack.common import log as logging
from designate import utils
from designate.backend import base

LOG = logging.getLogger(__name__)


class DnsmasqBackend(base.Backend):
    __plugin_name__ = 'dnsmasq'

    def start(self):
        super(DnsmasqBackend, self).start()

        self.output_folder = os.path.join(os.path.abspath(cfg.CONF.state_path),
                                          'dnsmasq')

        # Create the output folder tree if necessary
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        # TODO(Andrey): Remove this..
        self._sync_domains_hack()

    def _sync_domains_hack(self):
        # TODO(Andrey): This is a hack to ensure the data dir is 100% up to
        #               date
        domains = self.central_service.find_domains(self.admin_context)

        for domain in domains:
            self._sync_domain(domain)

        self._sync_domains()

    # Since dnsmasq only supports A and AAAA records, create_server,
    # update_server, and delete_server can be noop's
    def create_server(self, context, server):
        LOG.debug('Create Server - noop')
        pass

    def update_server(self, context, server):
        LOG.debug('Update Server - noop')
        pass

    def delete_server(self, context, server):
        LOG.debug('Delete Server - noop')
        pass

    def create_domain(self, context, domain):
        LOG.debug('Create Domain')

        self._write_zonefile(domain)
        self._merge_zonefiles()
        self._reload_dnsmasq()

    def update_domain(self, context, domain):
        LOG.debug('Update Domain')

        self._write_zonefile(domain)
        self._merge_zonefiles()
        self._reload_dnsmasq()

    def delete_domain(self, context, domain):
        LOG.debug('Delete Domain')

        self._purge_zonefile(domain)
        self._merge_zonefiles()
        self._reload_dnsmasq()

    def create_record(self, context, domain, record):
        LOG.debug('Create Record')

        self._write_zonefile(domain)
        self._merge_zonefiles()
        self._reload_dnsmasq()

    def update_record(self, context, domain, record):
        LOG.debug('Update Record')

        self._write_zonefile(domain)
        self._merge_zonefiles()
        self._reload_dnsmasq()

    def delete_record(self, context, domain, record):
        LOG.debug('Delete Record')

        self._write_zonefile(domain)
        self._merge_zonefiles()
        self._reload_dnsmasq()

    def _write_zonefile(self, domain):
        records = self.central_service.find_records(self.admin_context,
                                                    domain['id'])

        filename = os.path.join(self.output_folder, '%s.zone' % domain['id'])

        utils.render_template_to_file('dnsmasq-zone.jinja2',
                                      filename,
                                      records=records)

    def _purge_zonefile(self, domain):
        filename = os.path.join(self.output_folder, '%s.zone' % domain['id'])

        if os.exists(filename):
            os.unlink(filename)

    def _merge_zonefiles(self):
        filename = os.path.join(self.output_folder, 'dnsmasq.conf')
        zonefiles = glob.glob(os.path.join(self.output_folder, '*.zone'))

        with open(filename, 'w+') as out_fh:
            for zonefile in zonefiles:
                with open(zonefile, 'r') as in_fh:
                    # Append the zone to the output file
                    shutil.copyfileobj(in_fh, out_fh)

    def _reload_dnsmasq(self):
        """ Send HUP to dnsmasq """
        # TODO(Andrey): Lets be a little more targetted that every dnsmasq
        #               instance
        utils.execute('killall', '-HUP', 'dnsmasq')
