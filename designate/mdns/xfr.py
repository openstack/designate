# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hp.com>
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
from oslo_utils import timeutils
from oslo_log import log as logging

from designate import dnsutils
from designate import exceptions
from designate.mdns import base


LOG = logging.getLogger(__name__)


class XFRMixin(object):
    """
    Utility mixin that holds common methods for XFR functionality.
    """
    def domain_sync(self, context, domain, servers=None):
        servers = servers or domain.masters
        servers = dnsutils.expand_servers(servers)

        timeout = cfg.CONF["service:mdns"].xfr_timeout
        try:
            dnspython_zone = dnsutils.do_axfr(domain.name, servers,
                                              timeout=timeout)
        except exceptions.XFRFailure as e:
            LOG.warning(e.message)
            return

        zone = dnsutils.from_dnspython_zone(dnspython_zone)
        domain.update(zone)

        domain.transferred_at = timeutils.utcnow()

        self.central_api.update_domain(context, domain, increment_serial=False)


class XfrEndpoint(base.BaseEndpoint, XFRMixin):
    RPC_API_VERSION = '1.0'
    RPC_API_NAMESPACE = 'xfr'

    def perform_zone_xfr(self, context, domain):
        self.domain_sync(context, domain)
