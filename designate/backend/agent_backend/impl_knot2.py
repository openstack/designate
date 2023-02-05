# Copyright 2016 Hewlett Packard Enterprise Development Company LP
#
# Author: Federico Ceratto <federico.ceratto@hpe.com>
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
backend.agent_backend.impl_knot2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Knot DNS agent backend

Create, update, delete zones locally on a Knot DNS resolver using the
knotc utility.

Supported Knot versions: >= 2.1, < 3

`Knot DNS 2 User documentation <../../admin/backends/knot2_agent.html>`_

.. WARNING::

    Untested, do not use in production.

.. NOTE::

    If the backend is killed during a configuration transaction it might be
    required to manually abort the transaction with `sudo knotc conf-abort`

Configured in [service:agent:knot2]
"""
import warnings

from oslo_concurrency import lockutils
from oslo_concurrency.processutils import ProcessExecutionError
from oslo_config import cfg
from oslo_log import log as logging

from designate.backend.agent_backend import base
from designate import exceptions
from designate.utils import execute

CFG_GROUP_NAME = 'backend:agent:knot2'
LOG = logging.getLogger(__name__)
# rootwrap requires a command name instead of full path
KNOTC_DEFAULT_PATH = 'knotc'

# TODO(Federico) on zone creation and update, agent.handler unnecessarily
# perfors AXFR from MiniDNS to the Agent to populate the `zone` argument
# (needed by the Bind backend)


class Knot2Backend(base.AgentBackend):
    __plugin_name__ = 'knot2'
    __backend_status__ = 'untested'
    _lock_name = 'knot2.lock'

    def __init__(self, *a, **kw):
        """Configure the backend"""
        super(Knot2Backend, self).__init__(*a, **kw)

        warning_msg = ('The designate agent framework and backend driver "{}" '
                       'are deprecated as of the Antelope (2023.1) release '
                       'and will be removed in the "C" '
                       'release.'.format(self.__plugin_name__))
        warnings.warn(warning_msg, DeprecationWarning)

        self._knotc_cmd_name = cfg.CONF[CFG_GROUP_NAME].knotc_cmd_name

    def start(self):
        """Start the backend"""
        LOG.info("Started knot2 backend")

    def _execute_knotc(self, *knotc_args, **kw):
        """Run the Knot client and check the output

        :param expected_output: expected output (default: 'OK')
        :type expected_output: str
        :param expected_error: expected alternative output, will be \
        logged as info(). Default: not set.
        :type expected_error: str
        """
        # Knotc returns "0" even on failure, we have to check for 'OK'
        # https://gitlab.labs.nic.cz/labs/knot/issues/456

        LOG.debug("Executing knotc with %r", knotc_args)
        expected = kw.get('expected_output', 'OK')
        expected_alt = kw.get('expected_error', None)
        try:
            out, err = execute(self._knotc_cmd_name, *knotc_args)
            out = out.rstrip()
            LOG.debug("Command output: %r", out)
            if out != expected:
                if expected_alt is not None and out == expected_alt:
                    LOG.info("Ignoring error: %r", out)
                else:
                    raise ProcessExecutionError(stdout=out, stderr=err)

        except ProcessExecutionError as e:
            LOG.error("Command output: %(out)r Stderr: %(err)r",
                      {
                          'out': e.stdout,
                          'err': e.stderr
                      })
            raise exceptions.Backend(e)

    def _start_minidns_to_knot_axfr(self, zone_name):
        """Instruct Knot to request an AXFR from MiniDNS. No need to lock
        or enter a configuration transaction.
        """
        self._execute_knotc('zone-refresh', zone_name)

    def _modify_zone(self, *knotc_args, **kw):
        """Create or delete a zone while locking, and within a
        Knot transaction.
        Knot supports only one config transaction at a time.

        :raises: exceptions.Backend
        """
        with lockutils.lock(self._lock_name):
            self._execute_knotc('conf-begin')
            try:
                self._execute_knotc(*knotc_args, **kw)
                # conf-diff can be used for debugging
                # self._execute_knotc('conf-diff')
            except Exception as e:
                self._execute_knotc('conf-abort')
                LOG.info("Zone change aborted: %r", e)
                raise
            else:
                self._execute_knotc('conf-commit')

    def find_zone_serial(self, zone_name):
        """Get serial from a zone by running knotc

        :returns: serial (int or None)
        :raises: exceptions.Backend
        """
        zone_name = zone_name.rstrip('.')
        LOG.debug("Finding %s", zone_name)
        # Output example:
        # [530336536.com.] type: slave | serial: 0 | next-event: idle |
        # auto-dnssec: disabled]
        try:
            out, err = execute(self._knotc_cmd_name, 'zone-status', zone_name)
        except ProcessExecutionError as e:
            if 'no such zone' in e.stdout:
                # Zone not found
                return None

            LOG.error("Command output: %(out)r Stderr: %(err)r",
                      {
                          'out': e.stdout,
                          'err': e.stderr
                      })
            raise exceptions.Backend(e)

        try:
            serial = out.split('|')[1].split()[1]
            return int(serial)
        except Exception:
            LOG.error("Unable to parse knotc output: %r", out)
            raise exceptions.Backend("Unexpected knotc zone-status output")

    def create_zone(self, zone):
        """Create a new Zone by executing knotc
        Do not raise exceptions if the zone already exists.

        :param zone: zone to be  created
        :type zone: raw pythondns Zone
        """
        zone_name = zone.origin.to_text(omit_final_dot=True)
        if isinstance(zone_name, bytes):
            zone_name = zone_name.decode('utf-8')
        LOG.debug("Creating %s", zone_name)
        # The zone might be already in place due to a race condition between
        # checking if the zone is there and creating it across different
        # greenlets
        self._modify_zone('conf-set', 'zone[%s]' % zone_name,
                          expected_error='duplicate identifier')

        LOG.debug("Triggering initial AXFR from MiniDNS to Knot for %s",
                  zone_name)
        self._start_minidns_to_knot_axfr(zone_name)

    def update_zone(self, zone):
        """Instruct Knot DNS to perform AXFR from MiniDNS

        :param zone: zone to be  created
        :type zone: raw pythondns Zone
        """
        zone_name = zone.origin.to_text(omit_final_dot=True)
        if isinstance(zone_name, bytes):
            zone_name = zone_name.decode('utf-8')
        LOG.debug("Triggering AXFR from MiniDNS to Knot for %s", zone_name)
        self._start_minidns_to_knot_axfr(zone_name)

    def delete_zone(self, zone_name):
        """Delete a new Zone by executing knotc
        Do not raise exceptions if the zone does not exist.

        :param zone_name: zone name
        :type zone_name: str
        """
        LOG.debug('Delete Zone: %s' % zone_name)
        self._modify_zone('conf-unset', 'zone[%s]' % zone_name,
                          expected_error='invalid identifier')
