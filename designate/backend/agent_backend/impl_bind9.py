# Copyright 2014 Rackspace Inc.
#
# Author: Tim Simmons <tim.simmons@rackspace.com>
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
import time
import os

import dns
from oslo.config import cfg
from oslo.concurrency import lockutils
from oslo_log import log as logging

from designate.backend.agent_backend import base
from designate import exceptions
from designate import utils
from designate.i18n import _LI

LOG = logging.getLogger(__name__)
CFG_GROUP = 'backend:agent:bind9'


class Bind9Backend(base.AgentBackend):
    __plugin_name__ = 'bind9'

    @classmethod
    def get_cfg_opts(cls):
        group = cfg.OptGroup(
            name='backend:agent:bind9', title="Configuration for bind9 backend"
        )

        opts = [
            cfg.StrOpt('rndc-host', default='127.0.0.1', help='RNDC Host'),
            cfg.IntOpt('rndc-port', default=953, help='RNDC Port'),
            cfg.StrOpt('rndc-config-file', default=None,
                       help='RNDC Config File'),
            cfg.StrOpt('rndc-key-file', default=None, help='RNDC Key File'),
            cfg.StrOpt('zone-file-path', default='$state_path/zones',
                       help='Path where zone files are stored')
        ]

        return [(group, opts)]

    def start(self):
        LOG.info(_LI("Started bind9 backend"))

    def find_domain_serial(self, domain_name):
        LOG.debug("Finding %s" % domain_name)
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['127.0.0.1']
        try:
            rdata = resolver.query(domain_name, 'SOA')[0]
        except Exception:
            return None
        return rdata.serial

    def create_domain(self, domain):
        LOG.debug("Creating %s" % domain.origin.to_text())
        self._sync_domain(domain, new_domain_flag=True)

    def update_domain(self, domain):
        LOG.debug("Updating %s" % domain.origin.to_text())
        self._sync_domain(domain)

    def delete_domain(self, domain_name):
        LOG.debug('Delete Domain: %s' % domain_name)

        rndc_op = 'delzone'
        # RNDC doesn't like the trailing dot on the domain name
        rndc_call = self._rndc_base() + [rndc_op, domain_name[:-1]]

        utils.execute(*rndc_call)

    def _rndc_base(self):
        rndc_call = [
            'rndc',
            '-s', cfg.CONF[CFG_GROUP].rndc_host,
            '-p', str(cfg.CONF[CFG_GROUP].rndc_port),
        ]

        if cfg.CONF[CFG_GROUP].rndc_config_file:
            rndc_call.extend(['-c',
                             cfg.CONF[CFG_GROUP].rndc_config_file])

        if cfg.CONF[CFG_GROUP].rndc_key_file:
            rndc_call.extend(['-k',
                             cfg.CONF[CFG_GROUP].rndc_key_file])

        return rndc_call

    def _sync_domain(self, domain, new_domain_flag=False):
        """Sync a single domain's zone file and reload bind config"""

        domain_name = domain.origin.to_text()

        # NOTE: Only one thread should be working with the Zonefile at a given
        #       time. The sleep(1) below introduces a not insignificant risk
        #       of more than 1 thread working with a zonefile at a given time.
        with lockutils.lock('bind9-%s' % domain_name):
            LOG.debug('Synchronising Domain: %s' % domain_name)

            zone_path = cfg.CONF[CFG_GROUP].zone_file_path

            output_path = os.path.join(zone_path,
                                       '%szone' % domain_name)

            domain.to_file(output_path)

            rndc_call = self._rndc_base()

            if new_domain_flag:
                rndc_op = [
                    'addzone',
                    '%s { type master; file "%s"; };' % (domain_name,
                                                         output_path),
                ]
                rndc_call.extend(rndc_op)
            else:
                rndc_op = 'reload'
                rndc_call.extend([rndc_op])
                rndc_call.extend([domain_name])

            if not new_domain_flag:
                # NOTE: Bind9 will only ever attempt to re-read a zonefile if
                #       the file's timestamp has changed since the previous
                #       reload. A one second sleep ensures we cross over a
                #       second boundary before allowing the next change.
                time.sleep(1)

            LOG.debug('Calling RNDC with: %s' % " ".join(rndc_call))
            self._execute_rndc(rndc_call)

    def _execute_rndc(self, rndc_call):
        try:
            LOG.debug('Executing RNDC call: %s' % " ".join(rndc_call))
            utils.execute(*rndc_call)
        except utils.processutils.ProcessExecutionError as e:
            LOG.debug('RNDC call failure: %s' % e)
            raise exceptions.Backend(e)
