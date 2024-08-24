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

import subprocess

from oslo_log import log as logging
from oslo_utils import strutils

from designate.backend import base
from designate.conf.mdns import DEFAULT_MDNS_PORT
from designate import exceptions
from designate import utils

LOG = logging.getLogger(__name__)
DEFAULT_MASTER_PORT = DEFAULT_MDNS_PORT


class Bind9Backend(base.Backend):
    __plugin_name__ = 'bind9'

    __backend_status__ = 'integrated'

    def __init__(self, target):
        super().__init__(target)

        self._view = self.options.get('view')

        # Removes zone files when a zone is deleted.
        # This option will take effect on bind>=9.10.0.
        self._clean_zonefile = strutils.bool_from_string(
                                  self.options.get('clean_zonefile', 'false'))

        self._rndc_call_base = self._generate_rndc_base_call()
        self._rndc_timeout = self.options.get('rndc_timeout', None)

        if self._rndc_timeout == 0 or self._rndc_timeout == '0':
            self._rndc_timeout = None

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
            masters.append(f'{host} port {port}')

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
            if "already exists" not in str(e):
                LOG.warning('RNDC call failure: %s', e)
                raise

    def get_zone(self, context, zone):
        """Returns True if zone exists and False if not"""
        LOG.debug('Get Zone')

        view = 'in %s' % self._view if self._view else ''

        rndc_op = [
            'showzone',
            '{} {}'.format(zone['name'].rstrip('.'), view),
        ]
        try:
            self._execute_rndc(rndc_op)
        except exceptions.Backend as e:
            if "not found" in str(e):
                LOG.debug('Zone %s not found on the backend', zone['name'])
                return False
            else:
                LOG.warning('RNDC call failure: %s', e)
                raise e

        return True

    def delete_zone(self, context, zone, zone_params=None):
        """Delete a new Zone by executin rndc
        Do not raise exceptions if the zone does not exist.
        """
        LOG.debug('Delete Zone')

        view = 'in %s' % self._view if self._view else ''

        rndc_op = [
            'delzone',
            '{} {}'.format(zone['name'].rstrip('.'), view),
        ]
        if (self._clean_zonefile or (zone_params and
                                     zone_params.get('hard_delete'))):
            rndc_op.insert(1, '-clean')

        try:
            self._execute_rndc(rndc_op)
        except exceptions.Backend as e:
            # If zone is already deleted, don't reraise
            if "not found" not in str(e):
                LOG.warning('RNDC call failure: %s', e)
                raise

    def update_zone(self, context, zone):
        """
        Update a DNS zone.

        This will execute a rndc modzone if the zone
        already exists but masters might need to be refreshed.
        Or, will create the zone if it does not exist.

        :param context: Security context information.
        :param zone: the DNS zone.
        """
        LOG.debug('Update Zone')

        if not self.get_zone(context, zone):
            # If zone does not exist yet, create it
            self.create_zone(context, zone)
            # Newly created zone won't require an update
            return

        masters = []
        for master in self.masters:
            host = master['host']
            port = master['port']
            masters.append(f'{host} port {port}')

        # Ensure different MiniDNS instances are targeted for AXFRs
        random.shuffle(masters)

        view = 'in %s' % self._view if self._view else ''

        rndc_op = [
            'modzone',
            '%s %s { type slave; masters { %s;}; file "slave.%s%s"; };' %
            (zone['name'].rstrip('.'), view, '; '.join(masters), zone['name'],
             zone['id']),
        ]

        try:
            self._execute_rndc(rndc_op)
        except exceptions.Backend as e:
            LOG.warning("Error updating zone: %s", e)
            pass
        super().update_zone(context, zone)

    def _execute_rndc(self, rndc_op):
        """Execute rndc

        :param rndc_op: rndc arguments
        :type rndc_op: list
        :returns: None
        :raises: exceptions.Backend
        """
        try:
            rndc_call = self._rndc_call_base + rndc_op
            LOG.debug('Executing RNDC call: %r with timeout %s',
                      rndc_call, self._rndc_timeout)
            utils.execute(*rndc_call, timeout=self._rndc_timeout)
        except (utils.processutils.ProcessExecutionError,
                subprocess.TimeoutExpired) as e:
            raise exceptions.Backend(e)
