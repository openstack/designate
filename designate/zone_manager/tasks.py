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
import datetime

from designate import context
from designate import plugin
from designate import rpc
from designate.central import rpcapi
from designate.i18n import _LI

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import timeutils

LOG = logging.getLogger(__name__)


class PeriodicTask(plugin.ExtensionPlugin):
    """Abstract Zone Manager periodic task
    """
    __plugin_ns__ = 'designate.zone_manager_tasks'
    __plugin_type__ = 'zone_manager_task'
    __interval__ = None

    def __init__(self):
        self.my_partitions = None
        self.options = cfg.CONF[self.get_canonical_name()]

    @classmethod
    def get_base_opts(cls):
        options = [
            cfg.IntOpt(
                'interval',
                default=cls.__interval__,
                help='Run interval in seconds'
            ),
            cfg.IntOpt('per_page', default=100),
        ]
        return options

    @property
    def central_api(self):
        return rpcapi.CentralAPI.get_instance()

    def on_partition_change(self, my_partitions, members, event):
        """Refresh partitions attribute
        """
        self.my_partitions = my_partitions

    def _my_range(self):
        """Returns first and last partitions
        """
        return self.my_partitions[0], self.my_partitions[-1]

    def _filter_between(self, col):
        """Generate BETWEEN filter based on _my_range
        """
        return {col: "BETWEEN %s,%s" % self._my_range()}

    def _iter(self, method, *args, **kwargs):
        kwargs.setdefault("limit", self.options.per_page)
        while True:
            items = method(*args, **kwargs)

            # Stop fetching if there's no more items
            if len(items) == 0:
                raise StopIteration
            else:
                kwargs["marker"] = items[-1].id

            for i in items:
                yield i

    def _iter_zones(self, ctxt, criterion=None):
        criterion = criterion or {}
        criterion.update(self._filter_between('shard'))
        return self._iter(self.central_api.find_domains, ctxt, criterion)


class DeletedDomainPurgeTask(PeriodicTask):
    """Purge deleted domains that are exceeding the grace period time interval.
    Deleted domains have values in the deleted_at column.
    Purging means removing them from the database entirely.
    """

    __plugin_name__ = 'domain_purge'
    __interval__ = 3600

    def __init__(self):
        super(DeletedDomainPurgeTask, self).__init__()

    @classmethod
    def get_cfg_opts(cls):
        group = cfg.OptGroup(cls.get_canonical_name())
        options = cls.get_base_opts() + [
            cfg.IntOpt(
                'time_threshold',
                default=604800,
                help="How old deleted domains should be (deleted_at) to be "
                "purged, in seconds"
            ),
            cfg.IntOpt(
                'batch_size',
                default=100,
                help='How many domains to be purged on each run'
            ),
        ]
        return [(group, options)]

    def __call__(self):
        """Call the Central API to perform a purge of deleted zones based on
        expiration time and sharding range.
        """
        pstart, pend = self._my_range()
        msg = _LI("Performing deleted domain purging for %(start)s to %(end)s")
        LOG.info(msg % {"start": pstart, "end": pend})

        delta = datetime.timedelta(seconds=self.options.time_threshold)
        time_threshold = timeutils.utcnow() - delta
        LOG.debug("Filtering deleted domains before %s", time_threshold)

        criterion = self._filter_between('shard')
        criterion['deleted'] = '!0'
        criterion['deleted_at'] = "<=%s" % time_threshold

        ctxt = context.DesignateContext.get_admin_context()
        ctxt.all_tenants = True

        self.central_api.purge_domains(
            ctxt,
            criterion,
            limit=self.options.batch_size,
        )


class PeriodicExistsTask(PeriodicTask):
    __plugin_name__ = 'periodic_exists'
    __interval__ = 3600

    def __init__(self):
        super(PeriodicExistsTask, self).__init__()
        self.notifier = rpc.get_notifier('zone_manager')

    @classmethod
    def get_cfg_opts(cls):
        group = cfg.OptGroup(cls.get_canonical_name())
        options = cls.get_base_opts()
        return [(group, options)]

    @staticmethod
    def _get_period(seconds):
        interval = datetime.timedelta(seconds=seconds)
        end = timeutils.utcnow()
        return end - interval, end

    def __call__(self):
        pstart, pend = self._my_range()
        msg = _LI("Emitting zone exist events for %(start)s to %(end)s")
        LOG.info(msg % {"start": pstart, "end": pend})

        ctxt = context.DesignateContext.get_admin_context()
        ctxt.all_tenants = True

        start, end = self._get_period(self.options.interval)

        data = {
            "audit_period_beginning": str(start),
            "audit_period_ending": str(end)
        }

        for zone in self._iter_zones(ctxt):
            zone_data = dict(zone)
            zone_data.update(data)
            self.notifier.info(ctxt, 'dns.domain.exists', zone_data)

        LOG.info(_LI("Finished emitting events."))


class PeriodicSecondaryRefreshTask(PeriodicTask):
    __plugin_name__ = 'periodic_secondary_refresh'
    __interval__ = 3600

    @classmethod
    def get_cfg_opts(cls):
        group = cfg.OptGroup(cls.get_canonical_name())
        options = cls.get_base_opts()
        return [(group, options)]

    def __call__(self):
        pstart, pend = self._my_range()
        msg = _LI("Refreshing zones between for %(start)s to %(end)s")
        LOG.info(msg % {"start": pstart, "end": pend})

        ctxt = context.DesignateContext.get_admin_context()
        ctxt.all_tenants = True

        # each zone can have a different refresh / expire etc interval defined
        # in the SOA at the source / master servers
        criterion = {
            "type": "SECONDARY"
        }
        for zone in self._iter_zones(ctxt, criterion):
            # NOTE: If the zone isn't transferred yet, ignore it.
            if zone.transferred_at is None:
                continue

            now = timeutils.utcnow(True)

            transferred = timeutils.parse_isotime(zone.transferred_at)
            seconds = timeutils.delta_seconds(transferred, now)
            if seconds > zone.refresh:
                msg = "Zone %(id)s has %(seconds)d seconds since last transfer, " \
                      "executing AXFR"
                LOG.debug(msg % {"id": zone.id, "seconds": seconds})
                self.central_api.xfr_domain(ctxt, zone.id)
