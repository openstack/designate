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

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging

from designate.i18n import _LI
from designate.i18n import _LE
from designate import backend
from designate import exceptions
from designate import service
from designate import storage
from designate.central import rpcapi as central_api
from designate.context import DesignateContext
from designate.worker.tasks import zone as zonetasks
from designate.worker import processing


LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class Service(service.RPCService, service.Service):
    RPC_API_VERSION = '1.0'

    target = messaging.Target(version=RPC_API_VERSION)

    @property
    def central_api(self):
        if not hasattr(self, '_central_api'):
            self._central_api = central_api.CentralAPI.get_instance()
        return self._central_api

    def _setup_target_backends(self, pool):
        for target in pool.targets:
            # Fetch an instance of the Backend class
            target.backend = backend.get_backend(
                    target.type, target)

        LOG.info(_LI('%d targets setup'), len(pool.targets))

        if len(pool.targets) == 0:
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
                    LOG.error(_LE("No targets for %s found."), pool)
                    time.sleep(5)

            # Pool data may not have migrated to the DB yet
            except exceptions.PoolNotFound:
                LOG.error(_LE("Pool ID %s not found."), pool_id)
                time.sleep(5)
            # designate-central service may not have started yet
            except messaging.exceptions.MessagingTimeout:
                time.sleep(0.2)

        return self._setup_target_backends(pool)

    @property
    def service_name(self):
        return cfg.CONF['service:worker'].worker_topic

    @property
    def storage(self):
        if not hasattr(self, '_storage'):
            storage_driver = cfg.CONF['service:worker'].storage_driver
            self._storage = storage.get_storage(storage_driver)
        return self._storage

    @property
    def executor(self):
        if not hasattr(self, '_executor'):
            # TODO(elarson): Create this based on config
            self._executor = processing.Executor()
        return self._executor

    @property
    def pools_map(self):
        if not hasattr(self, '_pools_map'):
            self._pools_map = {}
        return self._pools_map

    def get_pool(self, pool_id):
        if pool_id not in self.pools_map:
            LOG.info(_LI("Lazily loading pool %s"), pool_id)
            self.pools_map[pool_id] = self.load_pool(pool_id)
        return self.pools_map[pool_id]

    def start(self):
        super(Service, self).start()
        LOG.info(_LI('Started worker'))

    def _do_zone_action(self, context, zone):
        pool = self.get_pool(zone.pool_id)
        task = zonetasks.ZoneAction(
            self.executor, context, pool, zone, zone.action
        )
        return self.executor.run(task)

    def create_zone(self, context, zone):
        """
        :param context: Security context information.
        :param zone: Zone to be created
        :return: None
        """
        self._do_zone_action(context, zone)

    def update_zone(self, context, zone):
        """
        :param context: Security context information.
        :param zone: Zone to be updated
        :return: None
        """
        self._do_zone_action(context, zone)

    def delete_zone(self, context, zone):
        """
        :param context: Security context information.
        :param zone: Zone to be deleted
        :return: None
        """
        self._do_zone_action(context, zone)

    def recover_shard(self, context, begin, end):
        """
        :param begin: the beginning of the shards to recover
        :param end: the end of the shards to recover
        :return: None
        """
        return self.executor.run(zonetasks.RecoverShard(
            self.executor, context, begin, end
        ))

    def start_zone_export(self, context, zone, export):
        """
        :param zone: Zone to be exported
        :param export: Zone Export object to update
        :return: None
        """
        return self.executor.run(zonetasks.ExportZone(
            self.executor, context, zone, export
        ))
