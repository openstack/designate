# Copyright 2014 Rackspace Inc.
#
# Author: Tim Simmons <tim.simmons@rackspace.com>
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
import dns
import dns.zone
from oslo.config import cfg
from oslo_log import log as logging

from designate.i18n import _LI
from designate.i18n import _LE


LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class AXFR(object):

    def __init__(self):
        self.masters = []
        for server in CONF['service:agent'].masters:
            raw_server = server.split(':')
            master = {'ip': raw_server[0], 'port': int(raw_server[1])}
            self.masters.append(master)

        LOG.info(_LI("Agent masters: %(masters)s") %
                 {'masters': self.masters})

    def do_axfr(self, zone_name):
        """
        Performs an AXFR for a given zone name
        """
        # TODO(Tim): Try the first master, try others if they exist
        master = self.masters[0]

        LOG.info(_LI("Doing AXFR for %(name)s from %(host)s") %
                 {'name': zone_name, 'host': master})

        xfr = dns.query.xfr(master['ip'], zone_name, relativize=False,
                            port=master['port'])

        try:
            # TODO(Tim): Add a timeout to this function
            raw_zone = dns.zone.from_xfr(xfr, relativize=False)
        except Exception:
            LOG.exception(_LE("There was a problem with the AXFR"))
            raise

        LOG.debug("AXFR Successful for %s" % raw_zone.origin.to_text())

        return raw_zone
