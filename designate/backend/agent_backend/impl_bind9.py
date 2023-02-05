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
import os
import warnings

import dns
import dns.resolver
from oslo_concurrency import lockutils
from oslo_config import cfg
from oslo_log import log as logging

from designate.backend.agent_backend import base
from designate import exceptions
from designate import utils

CFG_GROUP_NAME = 'backend:agent:bind9'
LOG = logging.getLogger(__name__)


class Bind9Backend(base.AgentBackend):
    __plugin_name__ = 'bind9'
    __backend_status__ = 'untested'

    def __init__(self, agent_service):
        super(Bind9Backend, self).__init__(agent_service)
        warning_msg = ('The designate agent framework and backend driver "{}" '
                       'are deprecated as of the Antelope (2023.1) release '
                       'and will be removed in the "C" '
                       'release.'.format(self.__plugin_name__))
        warnings.warn(warning_msg, DeprecationWarning)

    def start(self):
        LOG.info("Started bind9 backend")

    def find_zone_serial(self, zone_name):
        LOG.debug("Finding %s", zone_name)
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [cfg.CONF[CFG_GROUP_NAME].query_destination]
        try:
            rdata = resolver.query(zone_name, 'SOA')[0]
        except Exception:
            return None
        return rdata.serial

    def create_zone(self, zone):
        LOG.debug("Creating %s", zone.origin.to_text())
        self._sync_zone(zone, new_zone_flag=True)

    def update_zone(self, zone):
        LOG.debug("Updating %s", zone.origin.to_text())
        self._sync_zone(zone)

    def delete_zone(self, zone_name):
        LOG.debug('Delete Zone: %s' % zone_name)

        rndc_op = 'delzone'
        # RNDC doesn't like the trailing dot on the zone name
        rndc_call = self._rndc_base() + [rndc_op, zone_name.rstrip('.')]

        utils.execute(*rndc_call)

    def _rndc_base(self):
        rndc_call = [
            'rndc',
            '-s', cfg.CONF[CFG_GROUP_NAME].rndc_host,
            '-p', str(cfg.CONF[CFG_GROUP_NAME].rndc_port),
        ]

        if cfg.CONF[CFG_GROUP_NAME].rndc_config_file:
            rndc_call.extend(['-c',
                              cfg.CONF[CFG_GROUP_NAME].rndc_config_file])

        if cfg.CONF[CFG_GROUP_NAME].rndc_key_file:
            rndc_call.extend(['-k',
                              cfg.CONF[CFG_GROUP_NAME].rndc_key_file])

        return rndc_call

    def _sync_zone(self, zone, new_zone_flag=False):
        """Sync a single zone's zone file and reload bind config"""

        # NOTE: Different versions of BIND9 behave differently with a trailing
        #       dot, so we're just going to take it off.
        zone_name = zone.origin.to_text(omit_final_dot=True)
        if isinstance(zone_name, bytes):
            zone_name = zone_name.decode('utf-8')

        # NOTE: Only one thread should be working with the Zonefile at a given
        #       time. The sleep(1) below introduces a not insignificant risk
        #       of more than 1 thread working with a zonefile at a given time.
        with lockutils.lock('bind9-%s' % zone_name):
            LOG.debug('Synchronising Zone: %s' % zone_name)

            zone_path = cfg.CONF[CFG_GROUP_NAME].zone_file_path

            output_path = os.path.join(zone_path,
                                       '%s.zone' % zone_name)

            zone.to_file(output_path, relativize=False)

            rndc_call = self._rndc_base()

            if new_zone_flag:
                rndc_op = [
                    'addzone',
                    '%s { type master; file "%s"; };' % (zone_name,
                                                         output_path),
                ]
                rndc_call.extend(rndc_op)
            else:
                rndc_op = 'reload'
                rndc_call.extend([rndc_op])
                rndc_call.extend([zone_name])

            LOG.debug('Calling RNDC with: %s' % " ".join(rndc_call))
            self._execute_rndc(rndc_call)

    def _execute_rndc(self, rndc_call):
        try:
            LOG.debug('Executing RNDC call: %s' % " ".join(rndc_call))
            utils.execute(*rndc_call)
        except utils.processutils.ProcessExecutionError as e:
            LOG.debug('RNDC call failure: %s' % e)
            raise exceptions.Backend(e)
