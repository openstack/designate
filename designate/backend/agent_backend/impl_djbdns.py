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
backend.agent_backend.impl_djbdns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Djbdns DNS agent backend

Create, update, delete zones locally on a Djbdns DNS resolver using the
axfr-get utility.

`Djbdns User documentation <backends/djbdns_agent.html>`_

.. WARNING::

    Untested, do not use in production.


Configured in [service:agent:djbdns]

Requires rootwrap (or equivalent sudo privileges) to execute:
    - tcpclient
    - axfr-get
    - tinydns-data

"""

import glob
import os
import random
import tempfile

import dns
import dns.resolver
from oslo_concurrency import lockutils
from oslo_concurrency.processutils import ProcessExecutionError
from oslo_config import cfg
from oslo_log import log as logging

from designate import exceptions
from designate import utils
from designate.backend.agent_backend import base
from designate.i18n import _LI
from designate.i18n import _LE
from designate.utils import execute


LOG = logging.getLogger(__name__)
CFG_GROUP = 'backend:agent:djbdns'
# rootwrap requires a command name instead of full path
TCPCLIENT_DEFAULT_PATH = 'tcpclient'
AXFR_GET_DEFAULT_PATH = 'axfr-get'
TINYDNS_DATA_DEFAULT_PATH = 'tinydns-data'

TINYDNS_DATADIR_DEFAULT_PATH = '/var/lib/djbdns'
SOA_QUERY_TIMEOUT = 1

"""GROUP = backend:agent:djbdns"""
djbdns_group = cfg.OptGroup(
            name='backend:agent:djbdns',
            title="Configuration for Djbdns backend"
        )
djbdns_opts = [
    cfg.StrOpt(
        'tcpclient-cmd-name',
        help='tcpclient executable path or rootwrap command name',
        default='tcpclient'
    ),
    cfg.StrOpt(
        'axfr-get-cmd-name',
        help='axfr-get executable path or rootwrap command name',
        default='axfr-get'
    ),
    cfg.StrOpt(
        'tinydns-data-cmd-name',
        help='tinydns-data executable path or rootwrap command name',
        default='tinydns-data'
    ),
    cfg.StrOpt(
        'tinydns-datadir',
        help='TinyDNS data directory',
        default='/var/lib/djbdns'
    ),
    cfg.StrOpt('query-destination', default='127.0.0.1',
               help='Host to query when finding zones')
]

cfg.CONF.register_group(djbdns_group)
cfg.CONF.register_opts(djbdns_opts, group=djbdns_group)


# TODO(Federico) on zone creation and update, agent.handler unnecessarily
# perfors AXFR from MiniDNS to the Agent to populate the `zone` argument
# (needed by the Bind backend)


def filter_exceptions(fn):
    # Let Backend() exceptions pass through, log out every other exception
    # and re-raise it as Backend()
    def wrapper(*a, **kw):
        try:
            return fn(*a, **kw)
        except exceptions.Backend:
            raise
        except Exception as e:
            LOG.error(_LE("Unhandled exception %s"), str(e), exc_info=True)
            raise exceptions.Backend(str(e))

    return wrapper


class DjbdnsBackend(base.AgentBackend):
    __plugin_name__ = 'djbdns'
    __backend_status__ = 'experimental'

    @classmethod
    def get_cfg_opts(cls):
        return [(djbdns_group, djbdns_opts)]

    def __init__(self, *a, **kw):
        """Configure the backend"""
        super(DjbdnsBackend, self).__init__(*a, **kw)

        self._resolver = dns.resolver.Resolver(configure=False)
        self._resolver.timeout = SOA_QUERY_TIMEOUT
        self._resolver.lifetime = SOA_QUERY_TIMEOUT
        self._resolver.nameservers = [cfg.CONF[CFG_GROUP].query_destination]
        self._masters = [utils.split_host_port(ns)
                         for ns in cfg.CONF['service:agent'].masters]
        LOG.info(_LI("Resolvers: %r"), self._resolver.nameservers)
        LOG.info(_LI("AXFR masters: %r"), self._masters)
        if not self._masters:
            raise exceptions.Backend("Missing agent AXFR masters")

        self._tcpclient_cmd_name = cfg.CONF[CFG_GROUP].tcpclient_cmd_name
        self._axfr_get_cmd_name = cfg.CONF[CFG_GROUP].axfr_get_cmd_name

        # Directory where data.cdb lives, usually /var/lib/djbdns/root
        tinydns_root_dir = os.path.join(cfg.CONF[CFG_GROUP].tinydns_datadir,
                                        'root')

        # Usually /var/lib/djbdns/root/data.cdb
        self._tinydns_cdb_filename = os.path.join(tinydns_root_dir, 'data.cdb')
        LOG.info(_LI("data.cdb path: %r"), self._tinydns_cdb_filename)

        # Where the agent puts the zone datafiles,
        # usually /var/lib/djbdns/datafiles
        self._datafiles_dir = datafiles_dir = os.path.join(
            cfg.CONF[CFG_GROUP].tinydns_datadir,
            'datafiles')
        self._datafiles_tmp_path_tpl = os.path.join(datafiles_dir, "%s.ztmp")
        self._datafiles_path_tpl = os.path.join(datafiles_dir, "%s.zonedata")
        self._datafiles_path_glob = self._datafiles_path_tpl % '*'

        self._check_dirs(tinydns_root_dir, datafiles_dir)

    @staticmethod
    def _check_dirs(*dirnames):
        """Check if directories are writable
        """
        for dn in dirnames:
            if not os.path.isdir(dn):
                raise exceptions.Backend("Missing directory %s" % dn)
            if not os.access(dn, os.W_OK):
                raise exceptions.Backend("Directory not writable: %s" % dn)

    def start(self):
        """Start the backend"""
        LOG.info(_LI("Started djbdns backend"))

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

    @staticmethod
    def _concatenate_zone_datafiles(data_fn, path_glob):
        """Concatenate all zone datafiles into 'data'
        """
        with open(data_fn, 'w') as data_f:
            zone_cnt = 0
            for zone_fn in glob.glob(path_glob):
                zone_cnt += 1
                with open(zone_fn) as zf:
                    data_f.write(zf.read())

        LOG.info(_LI("Loaded %d zone datafiles."), zone_cnt)

    def _rebuild_data_cdb(self):
        """Rebuild data.cdb file from zone datafiles
        Requires global lock

        On zone creation, axfr-get creates datafiles atomically by doing
        rename. On zone deletion, os.remove deletes the file atomically
        Globbing and reading the datafiles can be done without locking on
        them.
        The data and data.cdb files are written into a unique temp directory
        """

        tmpdir = tempfile.mkdtemp(dir=self._datafiles_dir)
        data_fn = os.path.join(tmpdir, 'data')
        tmp_cdb_fn = os.path.join(tmpdir, 'data.cdb')

        try:
            self._concatenate_zone_datafiles(data_fn,
                                             self._datafiles_path_glob)
            # Generate the data.cdb file
            LOG.info(_LI("Updating data.cdb"))
            LOG.debug("Convert %s to %s", data_fn, tmp_cdb_fn)
            try:
                out, err = execute(
                    cfg.CONF[CFG_GROUP].tinydns_data_cmd_name,
                    cwd=tmpdir
                )
            except ProcessExecutionError as e:
                LOG.error(_LE("Failed to generate data.cdb"))
                LOG.error(_LE("Command output: %(out)r Stderr: %(err)r"), {
                    'out': e.stdout, 'err': e.stderr
                })
                raise exceptions.Backend("Failed to generate data.cdb")

            LOG.debug("Move %s to %s", tmp_cdb_fn, self._tinydns_cdb_filename)
            try:
                os.rename(tmp_cdb_fn, self._tinydns_cdb_filename)
            except OSError:
                os.remove(tmp_cdb_fn)
                LOG.error(_LE("Unable to move data.cdb to %s"),
                          self._tinydns_cdb_filename)
                raise exceptions.Backend("Unable to move data.cdb")

        finally:
            try:
                os.remove(data_fn)
            except OSError:
                pass
            try:
                os.removedirs(tmpdir)
            except OSError:
                pass

    def _perform_axfr_from_minidns(self, zone_name):
        """Instruct axfr-get to request an AXFR from MiniDNS.

        :raises: exceptions.Backend on error
        """
        zone_fn = self._datafiles_path_tpl % zone_name
        zone_tmp_fn = self._datafiles_tmp_path_tpl % zone_name

        # Perform AXFR, create or update a zone datafile
        # No need to lock globally here.
        # Axfr-get creates the datafile atomically by doing rename
        mdns_hostname, mdns_port = random.choice(self._masters)
        with lockutils.lock("%s.lock" % zone_name):
            LOG.debug("writing to %s", zone_fn)
            cmd = (
                self._tcpclient_cmd_name,
                mdns_hostname,
                "%d" % mdns_port,
                self._axfr_get_cmd_name,
                zone_name,
                zone_fn,
                zone_tmp_fn
            )

            LOG.debug("Executing AXFR as %r", ' '.join(cmd))
            try:
                out, err = execute(*cmd)
            except ProcessExecutionError as e:
                LOG.error(_LE("Error executing AXFR as %r"), ' '.join(cmd))
                LOG.error(_LE("Command output: %(out)r Stderr: %(err)r"), {
                    'out': e.stdout, 'err': e.stderr
                })
                raise exceptions.Backend(str(e))

            finally:
                try:
                    os.remove(zone_tmp_fn)
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
        zone_name = zone.origin.to_text(omit_final_dot=True).decode('utf-8')
        LOG.debug("Creating %s", zone_name)
        # The zone might be already in place due to a race condition between
        # checking if the zone is there and creating it across different
        # greenlets

        LOG.debug("Triggering initial AXFR from MiniDNS to Djbdns for %s",
                  zone_name)
        self._perform_axfr_from_minidns(zone_name)
        self._rebuild_data_cdb()

    @filter_exceptions
    def update_zone(self, zone):
        """Instruct Djbdns DNS to perform AXFR from MiniDNS

        :param zone: zone to be  created
        :type zone: raw pythondns Zone
        :raises: exceptions.Backend on error
        """
        zone_name = zone.origin.to_text(omit_final_dot=True).decode('utf-8')
        LOG.debug("Triggering AXFR from MiniDNS to Djbdns for %s", zone_name)
        self._perform_axfr_from_minidns(zone_name)
        self._rebuild_data_cdb()

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
        zone_fn = self._datafiles_path_tpl % zone_name
        try:
            os.remove(zone_fn)
            LOG.debug('Deleted Zone: %s', zone_name)
        except OSError as e:
            if os.errno.ENOENT == e.errno:
                LOG.info(_LI("Zone datafile %s was already deleted"), zone_fn)
                return

            raise

        self._rebuild_data_cdb()
