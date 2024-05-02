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
from oslo_log import log as logging
import oslo_messaging as messaging

from designate.central import rpcapi
import designate.conf
from designate import coordination
from designate import exceptions
from designate.producer import tasks
from designate import service


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)

NS = 'designate.periodic_tasks'


class Service(service.RPCService):
    RPC_API_VERSION = '1.0'

    target = messaging.Target(version=RPC_API_VERSION)

    def __init__(self):
        self._partitioner = None

        self._storage = None
        self._quota = None

        super().__init__(
            self.service_name, CONF['service:producer'].topic,
            threads=CONF['service:producer'].threads,
        )

        self.coordination = coordination.Coordination(
            self.service_name, self.tg, grouping_enabled=True
        )

    @property
    def service_name(self):
        return 'producer'

    @property
    def central_api(self):
        return rpcapi.CentralAPI.get_instance()

    def start(self):
        super().start()
        self.coordination.start()

        self._partitioner = coordination.Partitioner(
            self.coordination.coordinator, self.service_name,
            self.coordination.coordination_id, range(0, 4096)
        )

        self._partitioner.start()
        self._partitioner.watch_partition_change(self._rebalance)

        enabled_tasks = tasks.PeriodicTask.get_extensions(
            CONF['service:producer'].enabled_tasks
        )
        if not enabled_tasks:
            raise exceptions.ConfigurationError(
                'No periodic tasks found matching: %s' %
                CONF['service:producer'].enabled_tasks
            )
        for task in enabled_tasks:
            LOG.debug('Registering task %s', task)

            # Instantiate the task
            task = task()

            # Subscribe for partition size updates.
            self._partitioner.watch_partition_change(task.on_partition_change)

            interval = CONF[task.get_canonical_name()].interval
            self.tg.add_timer_args(interval, task, stop_on_exception=False)

    def stop(self, graceful=True):
        super().stop(graceful)
        self.coordination.stop()

    def _rebalance(self, my_partitions, members, event):
        LOG.info('Received rebalance event %s', event)
        self.partition_range = my_partitions
