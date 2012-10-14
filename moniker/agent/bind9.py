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
from jinja2 import Template
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging
from moniker.openstack.common.rpc import service as rpc_service
from moniker.openstack.common.context import get_admin_context
from moniker.central import api as central_api

LOG = logging.getLogger(__name__)

cfg.CONF.register_opts([
    cfg.StrOpt('rndc-path', default='/usr/sbin/rndc', help='RNDC Path'),
    cfg.StrOpt('rndc-host', default='127.0.0.1', help='RNDC Host'),
    cfg.IntOpt('rndc-port', default=953, help='RNDC Port'),
    cfg.StrOpt('rndc-config-file', default=None, help='RNDC Config File'),
    cfg.StrOpt('rndc-key-file', default=None, help='RNDC Key File'),
])


class Service(rpc_service.Service):
    def __init__(self, *args, **kwargs):
        kwargs.update(
            host=cfg.CONF.host,
            topic=cfg.CONF.agent_topic
        )

        super(Service, self).__init__(*args, **kwargs)

        # TODO: This is a hack to ensure the data dir is 100% up to date
        admin_context = get_admin_context()

        domains = central_api.get_domains(admin_context)

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

        raise NotImplementedError()

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

        admin_context = get_admin_context()

        domains = central_api.get_domains(admin_context)

        template_path = os.path.join(os.path.abspath(
            cfg.CONF.templates_path), 'bind9-config.jinja2')

        output_folder = os.path.join(os.path.abspath(cfg.CONF.state_path),
                                     'bind9')

        # Create the output folder tree if necessary
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        output_path = os.path.join(output_folder, 'zones.config')

        self._render_template(template_path, output_path, domains=domains,
                              state_path=os.path.abspath(cfg.CONF.state_path))

    def _sync_domain(self, domain):
        """ Sync a single domain's zone file """
        # TODO: Rewrite this entire thing ASAP
        LOG.debug('Synchronising Domain: %s' % domain['id'])

        admin_context = get_admin_context()

        servers = central_api.get_servers(admin_context)
        records = central_api.get_records(admin_context, domain['id'])

        template_path = os.path.join(os.path.abspath(
            cfg.CONF.templates_path), 'bind9-zone.jinja2')

        output_folder = os.path.join(os.path.abspath(cfg.CONF.state_path),
                                     'bind9')

        # Create the output folder tree if necessary
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        output_path = os.path.join(output_folder, '%s.zone' % domain['id'])

        self._render_template(template_path, output_path, servers=servers,
                              domain=domain, records=records)

        self._sync_domains()

        rndc_call = [
            'sudo',
            cfg.CONF.rndc_path,
            '-s', cfg.CONF.rndc_host,
            '-p', str(cfg.CONF.rndc_port),
        ]

        if cfg.CONF.rndc_config_file:
            rndc_call.extend(['-c', cfg.CONF.rndc_config_file])

        if cfg.CONF.rndc_key_file:
            rndc_call.extend(['-k', c.cfg.CONF.rndc_key_file])

        rndc_call.extend(['reload', domain['name']])

        LOG.warn(rndc_call)

        subprocess.call(rndc_call)

    def _render_template(self, template_path, output_path, **template_context):
        # TODO: Handle failures...
        with open(template_path) as template_fh:
            template = Template(template_fh.read())

        content = template.render(**template_context)

        with open(output_path, 'w') as output_fh:
            output_fh.write(content)
