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

"""
Bind 9 backend. Create and delete zones by executing rndc
"""

import random

import six
from oslo_log import log as logging
from oslo_utils import strutils

from designate import exceptions
from designate import utils
from designate.backend import base
from designate.utils import DEFAULT_MDNS_PORT
from designate.i18n import _LI


LOG = logging.getLogger(__name__)
DEFAULT_MASTER_PORT = DEFAULT_MDNS_PORT


class Bind9Backend(base.Backend):
    __plugin_name__ = 'bind9'

    __backend_status__ = 'integrated'

    def __init__(self, target):
        super(Bind9Backend, self).__init__(target)

        self._host = self.options.get('host', '127.0.0.1')
        self._port = int(self.options.get('port', 53))
        self._view = self.options.get('view')

        # Removes zone files when a zone is deleted.
        # This option will take effect on bind>=9.10.0.
        self._clean_zonefile = strutils.bool_from_string(
                                  self.options.get('clean_zonefile', 'false'))

        self._rndc_call_base = self._generate_rndc_base_call()

    def _generate_rndc_base_call(self):
        """Generate argument list to execute rndc"""
        rndc_host = self.options.get('rndc_host', '127.0.0.1')
        rndc_port = int(self.options.get('rndc_port', 953))
        rndc_bin_path = self.options.get('rndc_bin_path', 'rndc')
        rndc_config_file = self.options.get('rndc_config_file')
        rndc_key_file = self.options.get('rndc_key_file')
        rndc_call = [rndc_bin_path, '-s', rndc_host, '-p', str(rndc_port)]

        if rndc_config_file:
            rndc_call.extend(['-c', rndc_config_file])

        if rndc_key_file:
            rndc_call.extend(['-k', rndc_key_file])

        return rndc_call

    def create_zone(self, context, zone):
        """Create a new Zone by executin rndc, then notify mDNS
        Do not raise exceptions if the zone already exists.
        """
        LOG.debug('Create Zone')
        masters = []
        for master in self.masters:
            host = master['host']
            port = master['port']
            masters.append('%s port %s' % (host, port))

        # Ensure different MiniDNS instances are targeted for AXFRs
        random.shuffle(masters)

        view = 'in %s' % self._view if self._view else ''

        rndc_op = [
            'addzone',
            '%s %s { type slave; masters { %s;}; file "slave.%s%s"; };' %
            (zone['name'].rstrip('.'), view, '; '.join(masters), zone['name'],
             zone['id']),
        ]

        try:
            self._execute_rndc(rndc_op)
        except exceptions.Backend as e:
            # If create fails because the zone exists, don't reraise
            if "already exists" not in six.text_type(e):
                raise

        self.mdns_api.notify_zone_changed(
            context, zone, self._host, self._port, self.timeout,
            self.retry_interval, self.max_retries, self.delay)

    def delete_zone(self, context, zone):
        """Delete a new Zone by executin rndc
        Do not raise exceptions if the zone does not exist.
        """
        LOG.debug('Delete Zone')

        view = 'in %s' % self._view if self._view else ''

        rndc_op = [
            'delzone',
            '%s %s' % (zone['name'].rstrip('.'), view),
        ]
        if self._clean_zonefile:
            rndc_op.insert(1, '-clean')

        try:
            self._execute_rndc(rndc_op)
        except exceptions.Backend as e:
            # If zone is already deleted, don't reraise
            if "not found" not in six.text_type(e):
                raise

    def _execute_rndc(self, rndc_op):
        """Execute rndc

        :param rndc_op: rndc arguments
        :type rndc_op: list
        :returns: None
        :raises: exceptions.Backend
        """
        try:
            rndc_call = self._rndc_call_base + rndc_op
            LOG.debug('Executing RNDC call: %r', rndc_call)
            utils.execute(*rndc_call)
        except utils.processutils.ProcessExecutionError as e:
            LOG.info(_LI('RNDC call failure: %s'), e)
            raise exceptions.Backend(e)
