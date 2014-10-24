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
from oslo.config import cfg

from designate.openstack.common import log as logging
from designate import utils
from designate.backend import base


LOG = logging.getLogger(__name__)

cfg_opts = [
    cfg.ListOpt('masters', help="Master servers from which to transfer from"),
    cfg.StrOpt('rndc-host', default='127.0.0.1', help='RNDC Host'),
    cfg.IntOpt('rndc-port', default=953, help='RNDC Port'),
    cfg.StrOpt('rndc-config-file', default=None, help='RNDC Config File'),
    cfg.StrOpt('rndc-key-file', default=None, help='RNDC Key File'),
]


class Bind9PoolBackend(base.PoolBackend):
    __plugin_name__ = 'bind9_pool'

    @classmethod
    def get_cfg_opts(cls):
        return cfg_opts

    def create_domain(self, context, domain):
        LOG.debug('Create Domain')
        masters = '; '.join(self.get_backend_option('masters'))
        rndc_op = [
            'addzone',
            '%s { type slave; masters { %s;}; file "%s.slave"; };' %
            (domain['name'], masters, domain['name']),
        ]
        self._execute_rndc(rndc_op)

    def delete_domain(self, context, domain):
        LOG.debug('Delete Domain')
        rndc_op = [
            'delzone',
            '%s' % domain['name'],
        ]
        self._execute_rndc(rndc_op)

    def _rndc_base(self):
        rndc_call = [
            'rndc',
            '-s', self.get_backend_option('rndc_host'),
            '-p', str(self.get_backend_option('rndc_port')),
        ]

        if self.get_backend_option('rndc_config_file'):
            rndc_call.extend(
                ['-c', self.get_backend_option('rndc_config_file')])

        if self.get_backend_option('rndc_key_file'):
            rndc_call.extend(
                ['-k', self.get_backend_option('rndc_key_file')])

        return rndc_call

    def _execute_rndc(self, rndc_op):
        rndc_call = self._rndc_base()
        rndc_call.extend(rndc_op)
        LOG.debug('Executing RNDC call: %s' % " ".join(rndc_call))
        utils.execute(*rndc_call)
