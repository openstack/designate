# Copyright 2016 Cloudbase Solutions Srl
# All Rights Reserved.
#
#    Author: Alin Balutoiu <abalutoiu@cloudbasesolutions.com>
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_config import cfg
from oslo_log import log as logging
from os_win import utilsfactory
from os_win import constants
from os_win import exceptions as os_win_exc

from designate.backend.agent_backend import base
from designate import exceptions
from designate.i18n import _LI


LOG = logging.getLogger(__name__)
CFG_GROUP = 'backend:agent:msdns'

"""GROUP = backend:agent:msdns"""
msdns_group = cfg.OptGroup(
    name='backend:agent:msdns',
    title="Configuration for Microsoft DNS Server"
)
msdns_opts = [

]

cfg.CONF.register_group(msdns_group)
cfg.CONF.register_opts(msdns_opts, group=msdns_group)


class MSDNSBackend(base.AgentBackend):

    __plugin_name__ = 'msdns'
    __backend_status__ = 'experimental'

    def __init__(self, agent_service):
        """Configure the backend"""
        super(MSDNSBackend, self).__init__(agent_service)

        self._dnsutils = utilsfactory.get_dnsutils()

        masters = cfg.CONF['service:agent'].masters
        if not masters:
            raise exceptions.Backend("Missing agent AXFR masters")
        # Only ip addresses are needed
        self._masters = [ns.split(":")[0] for ns in masters]

        LOG.info(_LI("AXFR masters: %r"), self._masters)

    @classmethod
    def get_cfg_opts(cls):
        return [(msdns_group, msdns_opts)]

    def start(self):
        """Start the backend"""
        LOG.info(_LI("Started msdns backend"))

    def find_zone_serial(self, zone_name):
        """Return the zone's serial"""
        zone_name = zone_name.rstrip(".")
        LOG.debug("Finding zone: %s" % zone_name)
        try:
            return self._dnsutils.get_zone_serial(zone_name)
        except os_win_exc.DNSZoneNotFound:
            # Return None if the zone was not found
            return None

    def create_zone(self, zone):
        """Create a new DNS Zone"""
        zone_name = zone.origin.to_text(omit_final_dot=True).decode('utf-8')
        LOG.debug("Creating zone: %s" % zone_name)
        try:
            self._dnsutils.zone_create(
                zone_name=zone_name,
                zone_type=constants.DNS_ZONE_TYPE_SECONDARY,
                ds_integrated=False,
                ip_addrs=self._masters)
        except os_win_exc.DNSZoneAlreadyExists:
            # Zone already exists, check its properties to see if the
            # existing zone is identical to the requested one
            zone_properties = self._dnsutils.get_zone_properties(zone_name)

            identical_zone_exists = (
                zone_properties['zone_type'] == (
                    constants.DNS_ZONE_TYPE_SECONDARY) and
                zone_properties['ds_integrated'] is False and
                set(zone_properties['master_servers']) == set(self._masters))

            if not identical_zone_exists:
                raise

    def update_zone(self, zone):
        """Instruct MSDNS to request an AXFR from MiniDNS.
        """
        zone_name = zone.origin.to_text(omit_final_dot=True).decode('utf-8')
        LOG.debug("Updating zone: %s" % zone_name)
        self._dnsutils.zone_update(zone_name)

    def delete_zone(self, zone_name):
        """Delete a DNS Zone
        Do not raise exception if the zone does not exist.
        """
        LOG.debug('Deleting zone: %s' % zone_name)
        zone_name = zone_name.rstrip(".")
        self._dnsutils.zone_delete(zone_name)
