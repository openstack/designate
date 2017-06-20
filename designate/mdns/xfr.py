# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hpe.com>
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
from oslo_config import cfg
from oslo_utils import timeutils
from oslo_log import log as logging

from designate import dnsutils
from designate import exceptions
from designate.mdns import base
from designate.metrics import metrics


LOG = logging.getLogger(__name__)


class XFRMixin(object):
    """
    Utility mixin that holds common methods for XFR functionality.
    """
    @metrics.timed('mdns.xfr.zone_sync')
    def zone_sync(self, context, zone, servers=None):
        servers = servers or zone.masters
        servers = servers.to_list()

        timeout = cfg.CONF["service:mdns"].xfr_timeout
        try:
            dnspython_zone = dnsutils.do_axfr(zone.name, servers,
                                              timeout=timeout)
        except exceptions.XFRFailure as e:
            LOG.warning(e)
            return

        zone.update(dnsutils.from_dnspython_zone(dnspython_zone))

        zone.transferred_at = timeutils.utcnow()

        self.central_api.update_zone(context, zone, increment_serial=False)


class XfrEndpoint(base.BaseEndpoint, XFRMixin):
    RPC_API_VERSION = '1.0'
    RPC_API_NAMESPACE = 'xfr'

    def perform_zone_xfr(self, context, zone):
        self.zone_sync(context, zone)
