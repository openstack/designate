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
from moniker.openstack.common import rpc
from moniker.openstack.common import manager
from moniker.openstack.common.context import get_admin_context
from moniker.openstack.common.rpc import dispatcher as rpc_dispatcher
from moniker.openstack.common.periodic_task import periodic_task
from moniker.central import api as central_api

LOG = logging.getLogger(__name__)

cfg.CONF.register_opts([
    cfg.StrOpt('rndc-path', default='/usr/sbin/rndc', help='RNDC Path'),
    cfg.StrOpt('rndc-host', default='127.0.0.1', help='RNDC Host'),
    cfg.IntOpt('rndc-port', default=953, help='RNDC Port'),
    cfg.StrOpt('rndc-config-file', default='/etc/rndc.conf',
               help='RNDC Config File'),
    cfg.StrOpt('rndc-key-file', default=None, help='RNDC Key File'),
])


class Manager(manager.Manager):
    def init_host(self):
        LOG.warn('Init Host')

        self.init_rpc()

    def init_rpc(self):
        self.connection = rpc.create_connection()
        dispatcher = rpc_dispatcher.RpcDispatcher([self])
        self.connection.create_consumer(cfg.CONF.agent_topic, dispatcher,
                                        fanout=True)

        self.connection.consume_in_thread()

    def create_domain(self, context, domain):
        LOG.debug('Create Domain')
        self._sync_domain(domain=domain)

    def update_domain(self, context, domain):
        LOG.debug('Update Domain')
        self._sync_domain(domain=domain)

    def delete_domain(self, context, domain_id):
        LOG.debug('Delete Domain')

        raise NotImplementedError()

    def create_record(self, context, domain, record):
        LOG.debug('Create Record')
        self._sync_domain(servers, domain, records)

    def update_record(self, context, domain, record):
        LOG.debug('Update Record')
        self._sync_domain(domain)

    def delete_record(self, context, domain, record_id):
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

        output_path = os.path.join(os.path.abspath(cfg.CONF.state_path),
                                   'bind9', 'zones.config')

        self._render_template(template_path, output_path, domains=domains,
                              state_path=os.path.abspath(cfg.CONF.state_path))

    def _sync_domain(self, domain_id):
        """ Sync a single domain's zone file """
        # TODO: Rewrite this entire thing ASAP
        LOG.debug('Synchronising Domain: %s' % domain['id'])

        admin_context = get_admin_context()

        template_path = os.path.join(os.path.abspath(
            cfg.CONF.templates_path), 'bind9-zone.jinja2')

        output_path = os.path.join(os.path.abspath(cfg.CONF.state_path),
                                   'bind9', '%s.zone' % domain['id'])

        self._render_template(template_path, output_path, servers=servers,
                              domain=domain, records=records)

        self._sync_domains()

        rndc_call = [
            'sudo',
            cfg.CONF.rndc_path,
            '-c', cfg.CONF.rndc_config_file,
            '-s', cfg.CONF.rndc_host,
            '-p', str(cfg.CONF.rndc_port),
        ]

        if cfg.CONF.rndc_key_file:
            rndc_call.extend(['-k', c.cfg.CONF.rndc_key_file])

        rndc_call.extend(['reload', domain['name']])

        subprocess.call(rndc_call)

    def _render_template(self, template_path, output_path, **template_context):
        # TODO: Handle failures...
        with open(template_path) as template_fh:
            template = Template(template_fh.read())

        content = template.render(**template_context)

        with open(output_path, 'w') as output_fh:
            output_fh.write(content)
