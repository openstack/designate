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
backend.agent_backend.impl_gdnsd
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
gdnsd agent backend

Create, update, delete zones locally on a gdnsd resolver using the
gdnsd utility.

Supported Knot versions: >= 2.1, < 3

`User documentation <../../admin/backends/gdnsd_agent.html>`_

.. WARNING::

    Untested, do not use in production.

.. NOTE::

    If the backend is killed during a configuration transaction it might be
    required to manually abort the transaction with `sudo gdnsd conf-abort`

Configured in [service:agent:gdnsd]
"""

import errno
import os
import string
import tempfile
import warnings

import dns
import dns.resolver
from oslo_concurrency.processutils import ProcessExecutionError
from oslo_config import cfg
from oslo_log import log as logging

from designate.backend.agent_backend import base
from designate import exceptions
from designate import utils

CFG_GROUP_NAME = 'backend:agent:gdnsd'
LOG = logging.getLogger(__name__)
# rootwrap requires a command name instead of full path
GDNSD_DEFAULT_PATH = 'gdnsd'
CONFDIR_PATH = '/etc/gdnsd'
SOA_QUERY_TIMEOUT = 1
ZONE_FILE_PERMISSIONS = 0o0644


def filter_exceptions(fn):
    # Let Backend() exceptions pass through, log out every other exception
    # and re-raise it as Backend()
    def wrapper(*a, **kw):
        try:
            return fn(*a, **kw)
        except exceptions.Backend as e:
            raise e
        except Exception as e:
            LOG.error("Unhandled exception %s", e, exc_info=True)
            raise exceptions.Backend(e)

    return wrapper


class GdnsdBackend(base.AgentBackend):
    __plugin_name__ = 'gdnsd'
    __backend_status__ = 'experimental'

    def __init__(self, *a, **kw):
        """Configure the backend"""
        super(GdnsdBackend, self).__init__(*a, **kw)

        warning_msg = ('The designate agent framework and backend driver "{}" '
                       'are deprecated as of the Antelope (2023.1) release '
                       'and will be removed in the "C" '
                       'release.'.format(self.__plugin_name__))
        warnings.warn(warning_msg, DeprecationWarning)

        self._gdnsd_cmd_name = cfg.CONF[CFG_GROUP_NAME].gdnsd_cmd_name
        LOG.info("gdnsd command: %r", self._gdnsd_cmd_name)
        self._confdir_path = cfg.CONF[CFG_GROUP_NAME].confdir_path
        self._zonedir_path = os.path.join(self._confdir_path, 'zones')
        LOG.info("gdnsd conf directory: %r", self._confdir_path)
        self._resolver = dns.resolver.Resolver(configure=False)
        self._resolver.timeout = SOA_QUERY_TIMEOUT
        self._resolver.lifetime = SOA_QUERY_TIMEOUT
        self._resolver.nameservers = [
            cfg.CONF[CFG_GROUP_NAME].query_destination
        ]
        LOG.info("Resolvers: %r", self._resolver.nameservers)
        self._check_dirs(self._zonedir_path)

    def start(self):
        """Start the backend, check gdnsd configuration

        :raises: exception.Backend on invalid configuration
        """
        LOG.info("Started gdnsd backend")
        self._check_conf()

    def _check_conf(self):
        """Run gdnsd to check its configuration
        """
        try:
            out, err = utils.execute(
                cfg.CONF[CFG_GROUP_NAME].gdnsd_cmd_name,
                '-D', '-x', 'checkconf', '-c', self._confdir_path,
                run_as_root=False,
            )
        except ProcessExecutionError as e:
            LOG.error("Command output: %(out)r Stderr: %(err)r",
                      {
                          'out': e.stdout,
                          'err': e.stderr
                      })
            raise exceptions.Backend("Configuration check failed")

    def _check_dirs(self, *dirnames):
        """Check if directories are writable
        """
        for dn in dirnames:
            if not os.path.isdir(dn):
                raise exceptions.Backend("Missing directory %s" % dn)
            if not os.access(dn, os.W_OK):
                raise exceptions.Backend("Directory not writable: %s" % dn)

    def find_zone_serial(self, zone_name):
        """Query the local resolver for a zone
        Times out after SOA_QUERY_TIMEOUT
        """
        LOG.debug("Finding %s", zone_name)
        try:
            rdata = self._resolver.query(
                zone_name, rdtype=dns.rdatatype.SOA)[0]
            return rdata.serial
        except Exception:
            return None

    def _generate_zone_filename(self, zone_name):
        """Generate a filename for a zone file
        "/" is traslated into "@"
        Non-valid characters are translated into \\ NNN
        where NNN is a decimal integer in the range 0 - 255
        The filename is lowercase

        :returns: valid filename (string)
        """
        valid_chars = "-_.@%s%s" % (string.ascii_letters, string.digits)
        fname = zone_name.replace('/', '@').lower()
        fname = [c if c in valid_chars else "\03%d" % ord(c)
                 for c in fname]
        return ''.join(fname)

    def _write_zone_file(self, zone):
        """Create or update a zone file atomically.
        The zone file is written to a unique temp file and then renamed
        """
        zone_name = zone.origin.to_text(omit_final_dot=True)
        if isinstance(zone_name, bytes):
            zone_name = zone_name.decode('utf-8')
        zone_base_fname = self._generate_zone_filename(zone_name)
        zone_fname = os.path.join(self._zonedir_path, zone_base_fname)
        try:
            # gdnsd ignores hidden files
            tmp_zone_fname = tempfile.mkstemp(
                prefix=".%s" % zone_base_fname,
                dir=self._zonedir_path,
            )[1]
            LOG.debug("Writing zone %r to %r and renaming it to %r",
                      zone_name, tmp_zone_fname, zone_fname)
            zone.to_file(tmp_zone_fname)
            os.chmod(tmp_zone_fname, ZONE_FILE_PERMISSIONS)
            os.rename(tmp_zone_fname, zone_fname)
        finally:
            try:
                os.remove(tmp_zone_fname)
            except OSError:
                pass

    @filter_exceptions
    def create_zone(self, zone):
        """Create a new Zone
        Do not raise exceptions if the zone already exists.

        :param zone: zone to be  created
        :type zone: raw pythondns Zone
        :raises: exceptions.Backend on error
        """
        # The zone might be already in place due to a race condition between
        # checking if the zone is there and creating it across different
        # greenlets
        self._write_zone_file(zone)

    @filter_exceptions
    def update_zone(self, zone):
        """Instruct Djbdns DNS to perform AXFR from MiniDNS

        :param zone: zone to be  created
        :type zone: raw pythondns Zone
        :raises: exceptions.Backend on error
        """
        self._write_zone_file(zone)

    @filter_exceptions
    def delete_zone(self, zone_name):
        """Delete a new Zone
        Do not raise exceptions if the zone does not exist.

        :param zone_name: zone name
        :type zone_name: str
        :raises: exceptions.Backend on error
        """
        zone_name = zone_name.rstrip('.')
        LOG.debug('Deleting Zone: %s', zone_name)
        zone_fn = self._generate_zone_filename(zone_name)
        zone_fn = os.path.join(self._zonedir_path, zone_fn)
        try:
            os.remove(zone_fn)
            LOG.debug('Deleted Zone: %s', zone_name)
        except OSError as e:
            if errno.ENOENT == e.errno:
                LOG.info("Zone datafile %s was already deleted", zone_fn)
                return
            raise
