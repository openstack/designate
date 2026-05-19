# Copyright 2016 Rackspace Inc.
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
import time

from oslo_log import log as logging
import oslo_messaging as messaging

from designate import backend
from designate.central import rpcapi as central_api
from designate.common.decorators import rpc
import designate.conf
from designate.context import DesignateContext
from designate import exceptions
from designate import service
from designate import storage
from designate.worker import processing
from designate.worker.tasks import zone as zonetasks


LOG = logging.getLogger(__name__)
CONF = designate.conf.CONF


class AlsoNotifyTask:
    """
    Placeholder to define options for also_notify targets
    """
    pass


class Service(service.RPCService):
    RPC_API_VERSION = '1.2'

    target = messaging.Target(version=RPC_API_VERSION)

    def __init__(self):
        self._central_api = None
        self._storage = None

        self._executor = None
        self._pools_map = None

        super().__init__(
            self.service_name, CONF['service:worker'].topic,
            threads=CONF['service:worker'].threads,
        )

    @property
    def central_api(self):
        if not self._central_api:
            self._central_api = central_api.CentralAPI.get_instance()
        return self._central_api

    @staticmethod
    def _setup_target_backends(pool):
        for target in pool.targets:
            # Fetch an instance of the Backend class
            target.backend = backend.get_backend(target)

        LOG.info('%d targets setup', len(pool.targets))

        if not pool.targets:
            raise exceptions.NoPoolTargetsConfigured()

        return pool

    def load_pool(self, pool_id):
        # Build the Pool (and related) Object from Config
        context = DesignateContext.get_admin_context()

        pool = None
        has_targets = False

        while not has_targets:
            try:
                pool = self.central_api.get_pool(context, pool_id)

                if len(pool.targets) > 0:
                    has_targets = True
                else:
                    LOG.error('No targets for %s found.', pool)
                    time.sleep(5)

            # Pool data may not have migrated to the DB yet
            except exceptions.PoolNotFound:
                LOG.error('Pool ID %s not found.', pool_id)
                time.sleep(5)
            # designate-central service may not have started yet
            except messaging.exceptions.MessagingTimeout:
                time.sleep(0.2)

        return self._setup_target_backends(pool)

    @property
    def service_name(self):
        return 'worker'

    @property
    def storage(self):
        if not self._storage:
            self._storage = storage.get_storage()
        return self._storage

    @property
    def executor(self):
        if not self._executor:
            # TODO(elarson): Create this based on config
            self._executor = processing.Executor()
        return self._executor

    @property
    def pools_map(self):
        if self._pools_map is None:
            self._pools_map = {}
        return self._pools_map

    def get_pool(self, pool_id):
        if pool_id not in self.pools_map:
            LOG.info('Lazily loading pool %s', pool_id)
            self.pools_map[pool_id] = self.load_pool(pool_id)
        return self.pools_map[pool_id]

    def start(self):
        super().start()
        LOG.info('Started worker')

    def stop(self, graceful=True):
        super().stop(graceful)

    def _do_zone_action(self, context, zone, zone_params=None):
        pool = self.get_pool(zone.pool_id)
        all_tasks = [
            zonetasks.ZoneAction(self.executor, context, pool, zone,
                                 zone.action, zone_params)
        ]

        # Send a NOTIFY to each also-notifies
        for also_notify in pool.also_notifies:
            notify_target = AlsoNotifyTask()
            notify_target.options = {'host': also_notify.host,
                                     'port': also_notify.port}
            all_tasks.append(zonetasks.SendNotify(self.executor,
                                                  zone,
                                                  notify_target))
        return self.executor.run(all_tasks)

    @rpc.expected_exceptions()
    def create_zone(self, context, zone):
        """
        :param context: Security context information.
        :param zone: Zone to be created
        :return: None
        """
        self._do_zone_action(context, zone)

    @rpc.expected_exceptions()
    def update_zone(self, context, zone):
        """
        :param context: Security context information.
        :param zone: Zone to be updated
        :return: None
        """
        self._do_zone_action(context, zone)

    @rpc.expected_exceptions()
    def delete_zone(self, context, zone, hard_delete=False):
        """
        :param context: Security context information.
        :param zone: Zone to be deleted
        :param hard_delete: Zone resources (files) to be deleted or not
        :return: None
        """
        zone_params = {}
        if hard_delete:
            zone_params.update({'hard_delete': True})
        self._do_zone_action(context, zone, zone_params)

    @rpc.expected_exceptions()
    def recover_shard(self, context, begin, end):
        """
        :param begin: the beginning of the shards to recover
        :param end: the end of the shards to recover
        :return: None
        """
        return self.executor.run(zonetasks.RecoverShard(
            self.executor, context, begin, end
        ))

    @rpc.expected_exceptions()
    def start_zone_export(self, context, zone, export):
        """
        :param zone: Zone to be exported
        :param export: Zone Export object to update
        :return: None
        """
        return self.executor.run(zonetasks.ExportZone(
            self.executor, context, zone, export
        ))

    @rpc.expected_exceptions()
    def perform_zone_xfr(self, context, zone, servers=None):
        """
        :param zone: Zone to be exported
        :param servers:
        :return: None
        """
        return self.executor.run(zonetasks.ZoneXfr(
            self.executor, context, zone, servers
        ))

    @rpc.expected_exceptions()
    def get_serial_number(self, context, zone, host, port):
        """
        :param zone: Zone to get serial number
        :param host:
        :param port:
        :return: tuple
        """
        return self.executor.run(zonetasks.GetZoneSerial(
            self.executor, context, zone, host, port,
        ))[0]
