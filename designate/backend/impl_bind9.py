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
from oslo.config import cfg
from designate.openstack.common import log as logging
from designate import utils
from designate.backend import base
import glob
import shutil

LOG = logging.getLogger(__name__)

cfg.CONF.register_group(cfg.OptGroup(
    name='backend:bind9', title="Configuration for BIND9 Backend"
))

cfg.CONF.register_opts([
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

        domains = self.central_service.find_domains(self.admin_context)

        for domain in domains:
            rndc_op = 'reload'
            rndc_call = self._rndc_base() + [rndc_op]
            rndc_call.extend([domain['name']])
            LOG.debug('Calling RNDC with: %s' % " ".join(rndc_call))
            utils.execute(*rndc_call)

    def create_server(self, context, server):
        LOG.debug('Create Server')
        self._sync_domains_on_server_change()

    def update_server(self, context, server):
        LOG.debug('Update Server')
        self._sync_domains_on_server_change()

    def delete_server(self, context, server):
        LOG.debug('Delete Server')
        self._sync_domains_on_server_change()

    def create_domain(self, context, domain):
        LOG.debug('Create Domain')
        self._sync_domain(domain, new_domain_flag=True)

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

    def _rndc_base(self):
        rndc_call = [
            'rndc',
            '-s', cfg.CONF[self.name].rndc_host,
            '-p', str(cfg.CONF[self.name].rndc_port),
        ]

        if cfg.CONF[self.name].rndc_config_file:
            rndc_call.extend(['-c', cfg.CONF[self.name].rndc_config_file])

        if cfg.CONF[self.name].rndc_key_file:
            rndc_call.extend(['-k', cfg.CONF[self.name].rndc_key_file])

        return rndc_call

    def _sync_delete_domain(self, domain, new_domain_flag=False):
        """ Remove domain zone files and reload bind config """
        LOG.debug('Delete Domain: %s' % domain['id'])

        output_folder = os.path.join(os.path.abspath(cfg.CONF.state_path),
                                     'bind9')

        output_path = os.path.join(output_folder, '%s.zone' %
                                   "_".join([domain['name'], domain['id']]))

        os.remove(output_path)

        rndc_op = 'delzone'

        rndc_call = self._rndc_base() + [rndc_op, domain['name']]

        utils.execute(*rndc_call)

        #This goes and gets the name of the .nzf file that is a mirror of the
        #zones.config file we wish to maintain. The file name can change as it
        #is a hash of rndc view name, we're only interested in the first file
        #name this returns because there is only one .nzf file
        nzf_name = glob.glob('/var/cache/bind/*.nzf')

        output_file = os.path.join(output_folder, 'zones.config')

        shutil.copyfile(nzf_name[0], output_file)

    def _sync_domain(self, domain, new_domain_flag=False):
        """ Sync a single domain's zone file and reload bind config """
        LOG.debug('Synchronising Domain: %s' % domain['id'])

        servers = self.central_service.find_servers(self.admin_context)

        records = self.central_service.find_records(self.admin_context,
                                                    domain['id'])

        output_folder = os.path.join(os.path.abspath(cfg.CONF.state_path),
                                     'bind9')

        output_path = os.path.join(output_folder, '%s.zone' %
                                   "_".join([domain['name'], domain['id']]))

        utils.render_template_to_file('bind9-zone.jinja2',
                                      output_path,
                                      servers=servers,
                                      domain=domain,
                                      records=records)

        rndc_call = self._rndc_base()

        if new_domain_flag:
            rndc_op = [
                'addzone',
                '%s { type master; file "%s"; };' % (domain['name'],
                                                     output_path),
            ]
            rndc_call.extend(rndc_op)
        else:
            rndc_op = 'reload'
            rndc_call.extend([rndc_op])
            rndc_call.extend([domain['name']])

        LOG.debug('Calling RNDC with: %s' % " ".join(rndc_call))
        utils.execute(*rndc_call)

        nzf_name = glob.glob('/var/cache/bind/*.nzf')

        output_file = os.path.join(output_folder, 'zones.config')

        shutil.copyfile(nzf_name[0], output_file)

    def _sync_domains_on_server_change(self):
        # TODO(eankutse): Improve this so it scales. Need to design
        # for it in the new Pool Manager/Agent for the backend that is
        # being proposed
        LOG.debug('Synchronising domains on server change')

        domains = self.central_service.find_domains(self.admin_context)
        for domain in domains:
            self._sync_domain(domain)
