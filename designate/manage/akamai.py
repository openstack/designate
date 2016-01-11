# Copyright 2015 Hewlett-Packard Development Company, L.P.
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
from pprint import pformat

from oslo_config import cfg
from oslo_log import log as logging

from designate import exceptions
from designate import policy
from designate import rpc
from designate.i18n import _  # noqa
from designate.i18n import _LI
from designate.objects import pool as pool_object
from designate.backend import impl_akamai
from designate.central import rpcapi as central_rpcapi
from designate.manage import base

LOG = logging.getLogger(__name__)


class AkamaiCommands(base.Commands):
    def __init__(self):
        super(AkamaiCommands, self).__init__()
        rpc.init(cfg.CONF)
        self.central_api = central_rpcapi.CentralAPI()

    def _get_config(self, pool_id, target_id):
        pool = pool_object.Pool.from_config(cfg.CONF, pool_id)
        target = None
        for t in pool.targets:
            if t.id == target_id:
                target = t
            else:
                msg = _("Failed to find target with ID %s")
                raise exceptions.ConfigurationError(msg % target_id)
        if target is None:
            msg = _("Found multiple targets with ID %s")
            raise exceptions.ConfigurationError(msg % target_id)
        return pool, target

    @base.args('pool-id', help="Pool to Sync", type=str)
    @base.args('pool-target-id', help="Pool Target to Sync", type=str)
    @base.args('zone-name', help="Zone name")
    def debug_zone(self, pool_id, target_id, zone_name):
        pool, target = self._get_config(pool_id, target_id)

        client = impl_akamai.EnhancedDNSClient(
            target.options.get("username"), target.options.get("password"))

        # Bug 1519356 - Init policy after configuration has been read
        policy.init()
        self.context.all_tenants = True

        zone = self.central_api.find_zone(self.context, {"name": zone_name})
        akamai_zone = client.getZone(zone_name)

        print("Designate zone\n%s" % pformat(zone.to_dict()))
        print("Akamai Zone:\n%s" % repr(akamai_zone))

    @base.args('pool-id', help="Pool to Sync", type=str)
    @base.args('pool-target-id', help="Pool Target to Sync", type=str)
    @base.args('--batch-size', default=20, type=int)
    def sync_zones(self, pool_id, pool_target_id, batch_size):
        pool, target = self._get_config(pool_id, pool_target_id)

        client = impl_akamai.EnhancedDNSClient(
            target.options.get("username"), target.options.get("password"))

        LOG.info(_LI("Doing batches of %i"), batch_size)

        criterion = {"pool_id": pool_id}
        marker = None

        # Bug 1519356 - Init policy after configuration has been read
        policy.init()
        self.context.all_tenants = True

        while (marker is not False):
            zones = self.central_api.find_zones(
                self.context, criterion, limit=batch_size, marker=marker)
            update = []

            if len(zones) == 0:
                LOG.info(_LI("Stopping as there are no more zones."))
                break
            else:
                marker = zones[-1]['id']

            for zone in zones:
                z = impl_akamai.build_zone(client, target, zone)
                update.append(z)

            LOG.info(_LI('Uploading %d Zones'), len(update))

            client.setZones(update)
