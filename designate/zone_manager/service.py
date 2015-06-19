# Copyright 2015 Hewlett-Packard Development Company, L.P.
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
from oslo_config import cfg
from oslo_log import log as logging

from designate.i18n import _LI
from designate import coordination
from designate import service
from designate.central import rpcapi as central_api


LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class Service(coordination.CoordinationMixin, service.Service):
    def __init__(self, threads=None):
        super(Service, self).__init__(threads=threads)

        self._partitioner = coordination.Partitioner(
            self._coordinator, self.service_name, self._coordination_id,
            range(0, 4095))

    def _rebalance(self, my_partitions, members, event):
        LOG.info(_LI("Received rebalance event %s") % event)
        self.partition_range = my_partitions

    def start(self):
        super(Service, self).start()
        self._partitioner.start()
        self._partitioner.watch_partition_change(self._rebalance)

    @property
    def service_name(self):
        return 'zone_manager'

    @property
    def central_api(self):
        return central_api.CentralAPI.get_instance()
