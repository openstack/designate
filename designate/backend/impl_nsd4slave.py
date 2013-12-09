# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Author: Artom Lifshitz <artom.lifshitz@enovance.com>
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

import eventlet
import os
import socket
import ssl
from designate import exceptions
from designate.backend import base
from designate.openstack.common import log as logging
from oslo.config import cfg

LOG = logging.getLogger(__name__)

CFG_GRP = 'backend:nsd4slave'

cfg.CONF.register_group(
    cfg.OptGroup(name=CFG_GRP, title='Configuration for NSD4-slave backend')
)

cfg.CONF.register_opts([
    cfg.StrOpt('keyfile', default='/etc/nsd/nsd_control.key',
               help='Keyfile to use when connecting to the NSD4 servers over '
                    'SSL'),
    cfg.StrOpt('certfile', default='/etc/nsd/nsd_control.pem',
               help='Certfile to use when connecting to the NSD4 servers over '
                    'SSL'),
    cfg.ListOpt('servers',
                help='Comma-separated list of servers to control, in '
                     ' <host>:<port> format. If <port> is omitted, '
                     ' the default 8952 is used.'),
    cfg.StrOpt('pattern', default='slave',
               help='Pattern to use when creating zones on the NSD4 servers. '
                    'This pattern must be identically configured on all NSD4 '
                    'servers.'),
], group=CFG_GRP)

DEFAULT_PORT = 8952


class NSD4SlaveBackend(base.Backend):
    __plugin__name__ = 'nsd4slave'
    NSDCT_VERSION = 'NSDCT1'

    def __init__(self, central_service):
        self._keyfile = cfg.CONF[CFG_GRP].keyfile
        self._certfile = cfg.CONF[CFG_GRP].certfile
        # Make sure keyfile and certfile are readable to avoid cryptic SSL
        # errors later
        if not os.access(self._keyfile, os.R_OK):
            raise exceptions.NSD4SlaveBackendError(
                'Keyfile %s missing or permission denied' % self._keyfile)
        if not os.access(self._certfile, os.R_OK):
            raise exceptions.NSD4SlaveBackendError(
                'Certfile %s missing or permission denied' % self._certfile)
        self._pattern = cfg.CONF[CFG_GRP].pattern
        try:
            self._servers = [self._parse_server(cfg_server)
                             for cfg_server in cfg.CONF[CFG_GRP].servers]
        except TypeError:
            raise exceptions.ConfigurationError('No NSD4 servers defined')

    def _parse_server(self, cfg_server):
        try:
            (host, port) = cfg_server.split(':')
            port = int(port)
        except ValueError:
            host = str(cfg_server)
            port = DEFAULT_PORT
        return {'host': host, 'port': port}

    def create_domain(self, context, domain):
        command = 'addzone %s %s' % (domain['name'], self._pattern)
        self._all_servers(command)

    def update_domain(self, context, domain):
        pass

    def delete_domain(self, context, domain):
        command = 'delzone %s' % domain['name']
        self._all_servers(command)

    def _all_servers(self, command):
        for server in self._servers:
            try:
                result = self._command(command, server['host'], server['port'])
            except (ssl.SSLError, socket.error) as e:
                raise exceptions.NSD4SlaveBackendError(e)
            if result != 'ok':
                raise exceptions.NSD4SlaveBackendError(result)

    def _command(self, command, host, port):
        sock = eventlet.wrap_ssl(eventlet.connect((host, port)),
                                 keyfile=self._keyfile,
                                 certfile=self._certfile)
        stream = sock.makefile()
        stream.write('%s %s\n' % (self.NSDCT_VERSION, command))
        stream.flush()
        result = stream.read()
        stream.close()
        sock.close()
        return result.rstrip()

    def create_record(self, context, domain, record):
        pass

    def update_record(self, context, domain, record):
        pass

    def delete_record(self, context, domain, record):
        pass

    def create_server(self, context, server):
        pass

    def update_server(self, context, server):
        pass

    def delete_server(self, context, server):
        pass
