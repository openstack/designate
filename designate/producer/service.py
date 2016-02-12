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
from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging

from designate.i18n import _LI
from designate import coordination
from designate import quota
from designate import service
from designate import storage
from designate.central import rpcapi
from designate.producer import tasks


LOG = logging.getLogger(__name__)
CONF = cfg.CONF

NS = 'designate.periodic_tasks'


class Service(service.RPCService, coordination.CoordinationMixin,
              service.Service):
    RPC_API_VERSION = '1.0'

    target = messaging.Target(version=RPC_API_VERSION)

    @property
    def storage(self):
        if not hasattr(self, '_storage'):
            # TODO(timsim): Remove this when zone_mgr goes away
            storage_driver = cfg.CONF['service:zone_manager'].storage_driver
            if cfg.CONF['service:producer'].storage_driver != storage_driver:
                storage_driver = cfg.CONF['service:producer'].storage_driver
            self._storage = storage.get_storage(storage_driver)
        return self._storage

    @property
    def quota(self):
        if not hasattr(self, '_quota'):
            # Get a quota manager instance
            self._quota = quota.get_quota()
        return self._quota

    @property
    def service_name(self):
        return 'producer'

    @property
    def central_api(self):
        return rpcapi.CentralAPI.get_instance()

    def start(self):
        super(Service, self).start()

        self._partitioner = coordination.Partitioner(
            self._coordinator, self.service_name, self._coordination_id,
            range(0, 4095))

        self._partitioner.start()
        self._partitioner.watch_partition_change(self._rebalance)

        # TODO(timsim): Remove this when zone_mgr goes away
        zmgr_enabled_tasks = CONF['service:zone_manager'].enabled_tasks
        producer_enabled_tasks = CONF['service:producer'].enabled_tasks
        enabled = zmgr_enabled_tasks
        if producer_enabled_tasks != []:
            enabled = producer_enabled_tasks

        for task in tasks.PeriodicTask.get_extensions(enabled):
            LOG.debug("Registering task %s", task)

            # Instantiate the task
            task = task()

            # Subscribe for partition size updates.
            self._partitioner.watch_partition_change(task.on_partition_change)

            interval = CONF[task.get_canonical_name()].interval
            self.tg.add_timer(interval, task)

    def _rebalance(self, my_partitions, members, event):
        LOG.info(_LI("Received rebalance event %s"), event)
        self.partition_range = my_partitions
