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
from designate import exceptions
from designate import quota
from designate import service
from designate import storage
from designate import utils
from designate.central import rpcapi
from designate.zone_manager import tasks


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
            storage_driver = cfg.CONF['service:zone_manager'].storage_driver
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
        return 'zone_manager'

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

        enabled = CONF['service:zone_manager'].enabled_tasks
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

    # Begin RPC Implementation

    # Zone Export
    def start_zone_export(self, context, zone, export):
        criterion = {'zone_id': zone.id}
        count = self.storage.count_recordsets(context, criterion)

        export = self._determine_export_method(context, export, count)

        self.central_api.update_zone_export(context, export)

    def render_zone(self, context, zone_id):
        return self._export_zone(context, zone_id)

    def _determine_export_method(self, context, export, size):
        synchronous = CONF['service:zone_manager'].export_synchronous

        # NOTE(timsim):
        # The logic here with swift will work like this:
        #     cfg.CONF.export_swift_enabled:
        #         An export will land in their swift container, even if it's
        #         small, but the link that comes back will be the synchronous
        #         link (unless export_syncronous is False, in which case it
        #         will behave like the next option)
        #     cfg.CONF.export_swift_preffered:
        #         The link that the user gets back will always be the swift
        #         container, and status of the export resource will depend
        #         on the Swift process.
        #     If the export is too large for synchronous, or synchronous is not
        #     enabled and swift is not enabled, it will fall through to ERROR
        # swift = False

        if synchronous:
            try:
                self.quota.limit_check(
                        context, context.tenant, api_export_size=size)
            except exceptions.OverQuota:
                LOG.debug('Zone Export too large to perform synchronously')
                export['status'] = 'ERROR'
                export['message'] = 'Zone is too large to export'
                return export

            export['location'] = \
                "designate://v2/zones/tasks/exports/%(eid)s/export" % \
                {'eid': export['id']}

            export['status'] = 'COMPLETE'
        else:
            LOG.debug('No method found to export zone')
            export['status'] = 'ERROR'
            export['message'] = 'No suitable method for export'

        return export

    def _export_zone(self, context, zone_id):
        zone = self.central_api.get_zone(context, zone_id)

        criterion = {'zone_id': zone_id}
        recordsets = self.storage.find_recordsets_export(context, criterion)

        return utils.render_template('export-zone.jinja2',
                                     zone=zone,
                                     recordsets=recordsets)
