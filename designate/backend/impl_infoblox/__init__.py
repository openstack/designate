# Copyright 2015 Infoblox Inc.
# All Rights Reserved.
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

from oslo_log import log as logging

from designate.backend import base
from designate import exceptions
from designate.i18n import _LI
from designate.backend.impl_infoblox import connector
from designate.backend.impl_infoblox import object_manipulator

LOG = logging.getLogger(__name__)


class InfobloxBackend(base.Backend):
    """Provides a Designate Backend for Infoblox"""

    __backend_status__ = 'release-compatible'

    __plugin_name__ = 'infoblox'

    def __init__(self, *args, **kwargs):
        super(InfobloxBackend, self).__init__(*args, **kwargs)

        self.infoblox = object_manipulator.InfobloxObjectManipulator(
            connector.Infoblox(self.options))

        for master in self.masters:
            if master.port != 53:
                raise exceptions.ConfigurationError(
                    "Infoblox only supports mDNS instances on port 53")

    def create_zone(self, context, zone):
        LOG.info(_LI('Create Zone %r'), zone)

        dns_net_view = self.infoblox.get_dns_view(context.tenant)
        self.infoblox.create_zone_auth(
            fqdn=zone['name'][0:-1],
            dns_view=dns_net_view
        )

    def delete_zone(self, context, zone):
        LOG.info(_LI('Delete Zone %r'), zone)
        self.infoblox.delete_zone_auth(zone['name'][0:-1])

    def ping(self, context):
        LOG.info(_LI('Ping'))
