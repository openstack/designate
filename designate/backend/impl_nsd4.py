# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
# Copyright 2014 eBay Inc.
# Copyright 2015 Zetta.IO.
#
# Author: Ron Rickard <rrickard@ebay.com>
# Author: Artom Lifshitz <artom.lifshitz@enovance.com>
# Author: Dag Stenstad <dag@stenstad.net>
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

import random
import ssl

import eventlet
from oslo_log import log as logging

from designate.backend import base
from designate import exceptions


LOG = logging.getLogger(__name__)


class NSD4Backend(base.Backend):

    __backend_status__ = 'untested'

    __plugin_name__ = 'nsd4'
    NSDCT_VERSION = 'NSDCT1'

    def __init__(self, target):
        super().__init__(target)

        self.host = self.options.get('host', '127.0.0.1')
        self.port = int(self.options.get('port', 8952))
        self.certfile = self.options.get('certfile',
                                         '/etc/nsd/nsd_control.pem')
        self.keyfile = self.options.get('keyfile',
                                        '/etc/nsd/nsd_control.key')
        self.pattern = self.options.get('pattern', 'slave')

    def _command(self, command):
        sock = eventlet.wrap_ssl(
            eventlet.connect((self.host, self.port)),
            keyfile=self.keyfile,
            certfile=self.certfile)
        stream = sock.makefile()
        stream.write(f'{self.NSDCT_VERSION} {command}\n')
        stream.flush()
        result = stream.read()
        stream.close()
        sock.close()
        return result

    def _execute_nsd4(self, command):
        try:
            LOG.debug('Executing NSD4 control call: %s on %s',
                      command, self.host)
            result = self._command(command)
        except (ssl.SSLError, OSError) as e:
            LOG.debug('NSD4 control call failure: %s' % e)
            raise exceptions.Backend(e)
        if result.rstrip("\n") != 'ok':
            raise exceptions.Backend(result)

    def create_zone(self, context, zone):
        LOG.debug('Create Zone')
        masters = []
        for master in self.masters:
            host = master['host']
            port = master['port']
            masters.append(f'{host} port {port}')

        # Ensure different MiniDNS instances are targeted for AXFRs
        random.shuffle(masters)

        command = 'addzone {} {}'.format(zone['name'], self.pattern)

        try:
            self._execute_nsd4(command)
        except exceptions.Backend as e:
            # If create fails because the zone exists, don't reraise
            if "already exists" not in str(e):
                raise

    def delete_zone(self, context, zone, zone_params=None):
        LOG.debug('Delete Zone')
        command = 'delzone %s' % zone['name']

        try:
            self._execute_nsd4(command)
        except exceptions.Backend as e:
            # If zone is already deleted, don't reraise
            if "not found" not in str(e):
                raise
