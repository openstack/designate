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
import subprocess
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging
from moniker import utils
from moniker.backend import base
from moniker.central import api as central_api
from moniker.context import MonikerContext

LOG = logging.getLogger(__name__)

cfg.CONF.register_group(cfg.OptGroup(
    name='backend:bind9', title="Configuration for BIND9 Backend"
))

cfg.CONF.register_opts([
    cfg.StrOpt('rndc-path', default='/usr/sbin/rndc',
               help='RNDC Path'),
    cfg.StrOpt('rndc-host', default='127.0.0.1', help='RNDC Host'),
    cfg.IntOpt('rndc-port', default=953, help='RNDC Port'),
    cfg.StrOpt('rndc-config-file', default=None,
               help='RNDC Config File'),
    cfg.StrOpt('rndc-key-file', default=None, help='RNDC Key File'),
], group='backend:bind9')


class Bind9Backend(base.Backend):
    __plugin_name__ = 'bind9'

    def start(self):
        super(Bind9Backend, self).start()

        # TODO: This is a hack to ensure the data dir is 100% up to date
        admin_context = MonikerContext.get_admin_context()

        domains = central_api.get_domains(admin_context)

        for domain in domains:
            self._sync_domain(domain)

        self._sync_domains()

    def create_domain(self, context, domain, servers):
        LOG.debug('Create Domain')
        self._sync_domain(domain, servers, new_domain_flag=True)

    def update_domain(self, context, domain, servers):
        LOG.debug('Update Domain')
        self._sync_domain(domain, servers)

    def delete_domain(self, context, domain, servers):
        LOG.debug('Delete Domain')
        self._sync_delete_domain(domain, servers)

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
        # TODO: Rewrite this entire thing ASAP
        LOG.debug('Synchronising domains')

        admin_context = MonikerContext.get_admin_context()

        domains = central_api.get_domains(admin_context)

        output_folder = os.path.join(os.path.abspath(cfg.CONF.state_path),
                                     'bind9')

        # Create the output folder tree if necessary
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        output_path = os.path.join(output_folder, 'zones.config')

        abs_state_path = os.path.abspath(cfg.CONF.state_path)

        utils.render_template_to_file('bind9-config.jinja2',
                                      output_path,
                                      domains=domains,
                                      state_path=abs_state_path)

    """ Remove domain zone files and reload bind config """
    def _sync_delete_domain(self, domain, new_domain_flag=False):
        """ delete a single domain's zone file """
        # TODO: Rewrite this entire thing ASAP
        LOG.debug('Delete Domain: %s' % domain['id'])

        output_folder = os.path.join(os.path.abspath(cfg.CONF.state_path),
                                     'bind9')

        output_path = os.path.join(output_folder, '%s.zone' % domain['id'])

        os.remove(output_path)

        self._sync_domains()

        rndc_call = [
            'sudo',
            cfg.CONF[self.name].rndc_path,
            '-s', cfg.CONF[self.name].rndc_host,
            '-p', str(cfg.CONF[self.name].rndc_port),
        ]

        if cfg.CONF[self.name].rndc_config_file:
            rndc_call.extend(['-c', cfg.CONF[self.name].rndc_config_file])

        if cfg.CONF[self.name].rndc_key_file:
            rndc_call.extend(['-k', cfg.CONF[self.name].rndc_key_file])

        rndc_call.extend(['reload'])

        LOG.debug('Calling RNDC with: %s' % " ".join(rndc_call))
        subprocess.call(rndc_call)

    """ Update the bind to read in new zone files or changes to existin """
    def _sync_domain(self, domain, servers=None, new_domain_flag=False):
        """ Sync a single domain's zone file """
        # TODO: Rewrite this entire thing ASAP
        LOG.debug('Synchronising Domain: %s' % domain['id'])

        if not servers:
            # TODO: This is a hack... FIXME
            admin_context = MonikerContext.get_admin_context()
            servers = central_api.get_servers(admin_context)

        records = central_api.get_records(admin_context, domain['id'])

        output_folder = os.path.join(os.path.abspath(cfg.CONF.state_path),
                                     'bind9')

        output_path = os.path.join(output_folder, '%s.zone' % domain['id'])

        utils.render_template_to_file('bind9-zone.jinja2',
                                      output_path,
                                      servers=servers,
                                      domain=domain,
                                      records=records)

        self._sync_domains()

        rndc_call = [
            'sudo',
            cfg.CONF[self.name].rndc_path,
            '-s', cfg.CONF[self.name].rndc_host,
            '-p', str(cfg.CONF[self.name].rndc_port),
        ]

        if cfg.CONF[self.name].rndc_config_file:
            rndc_call.extend(['-c', cfg.CONF[self.name].rndc_config_file])

        if cfg.CONF[self.name].rndc_key_file:
            rndc_call.extend(['-k', cfg.CONF[self.name].rndc_key_file])

        rndc_op = 'reconfig' if new_domain_flag else 'reload'
        rndc_call.extend([rndc_op])

        if not new_domain_flag:
            rndc_call.extend([domain['name']])

        LOG.debug('Calling RNDC with: %s' % " ".join(rndc_call))
        subprocess.call(rndc_call)
