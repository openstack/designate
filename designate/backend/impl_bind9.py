# Copyright 2014 eBay Inc.
#
# Author: Ron Rickard <rrickard@ebay.com>
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
from oslo_log import log as logging

from designate import exceptions
from designate import utils
from designate.backend import base


LOG = logging.getLogger(__name__)
DEFAULT_MASTER_PORT = 5354


class Bind9Backend(base.Backend):
    __plugin_name__ = 'bind9'

    def __init__(self, target):
        super(Bind9Backend, self).__init__(target)

        self.rndc_host = self.options.get('rndc_host', '127.0.0.1')
        self.rndc_port = int(self.options.get('rndc_port', 953))
        self.rndc_config_file = self.options.get('rndc_config_file')
        self.rndc_key_file = self.options.get('rndc_key_file')

    def create_domain(self, context, domain):
        LOG.debug('Create Domain')
        masters = []
        for master in self.masters:
            host = master['host']
            port = master['port']
            masters.append('%s port %s' % (host, port))
        rndc_op = [
            'addzone',
            '%s { type slave; masters { %s;}; file "slave.%s%s"; };' %
            (domain['name'].rstrip('.'), '; '.join(masters), domain['name'],
             domain['id']),
        ]

        try:
            self._execute_rndc(rndc_op)
        except exceptions.Backend as e:
            # If create fails because the domain exists, don't reraise
            if "already exists" not in str(e.message):
                raise

    def delete_domain(self, context, domain):
        LOG.debug('Delete Domain')
        rndc_op = [
            'delzone',
            '%s' % domain['name'].rstrip('.'),
        ]

        try:
            self._execute_rndc(rndc_op)
        except exceptions.Backend as e:
            # If domain is already deleted, don't reraise
            if "not found" not in str(e.message):
                raise

    def _rndc_base(self):
        rndc_call = [
            'rndc',
            '-s', self.rndc_host,
            '-p', str(self.rndc_port),
        ]

        if self.rndc_config_file:
            rndc_call.extend(
                ['-c', self.rndc_config_file])

        if self.rndc_key_file:
            rndc_call.extend(
                ['-k', self.rndc_key_file])

        return rndc_call

    def _execute_rndc(self, rndc_op):
        try:
            rndc_call = self._rndc_base()
            rndc_call.extend(rndc_op)
            LOG.debug('Executing RNDC call: %s' % " ".join(rndc_call))
            utils.execute(*rndc_call)
        except utils.processutils.ProcessExecutionError as e:
            LOG.debug('RNDC call failure: %s' % e)
            raise exceptions.Backend(e)
