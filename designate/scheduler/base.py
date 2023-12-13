# Copyright 2016 Hewlett Packard Enterprise Development Company, L.P.
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
from stevedore import named

import designate.conf
from designate import exceptions


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class Scheduler:
    """Scheduler that schedules zones based on the filters provided on the zone
    and other inputs.

    :raises: NoFiltersConfigured
    """
    filters = []
    """The list of filters enabled on this scheduler"""

    def __init__(self, storage):
        enabled_filters = CONF['service:central'].scheduler_filters
        self.filters = list()
        self.storage = storage

        if not enabled_filters:
            raise exceptions.NoFiltersConfigured(
                'There are no scheduling filters configured'
            )

        extensions = named.NamedExtensionManager(
            namespace='designate.scheduler.filters',
            names=enabled_filters,
            name_order=True,
        )

        for extension in extensions:
            plugin = extension.plugin(storage=self.storage)
            LOG.info('Loaded Scheduler Filter: %s', plugin.name)
            self.filters.append(plugin)

    def schedule_zone(self, context, zone):
        """Get a pool to create the new zone in.

        :param context: :class:`designate.context.DesignateContext` - Context
            Object from request
        :param zone: :class:`designate.objects.zone.Zone` - Zone to be created
        :return: string -- ID of pool to schedule the zone to.
        :raises: MultiplePoolsFound, NoValidPoolFound
        """
        pools = self.storage.find_pools(context)

        if not self.filters:
            raise exceptions.NoFiltersConfigured(
                'There are no scheduling filters configured'
            )

        for plugin in self.filters:
            LOG.debug(
                'Running %s filter with %d pools', plugin.name, len(pools)
            )
            pools = plugin.filter(context, pools, zone)
            LOG.debug(
                '%d candidate pools remaining after %s filter',
                len(pools), plugin.name
            )

        if len(pools) > 1:
            raise exceptions.MultiplePoolsFound()
        if not pools:
            raise exceptions.NoValidPoolFound(
                'There are no pools that matched your request'
            )
        return pools[0].id
