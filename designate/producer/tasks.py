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
import datetime

from designate import context
from designate import plugin
from designate import rpc
from designate.central import rpcapi
from designate.worker import rpcapi as worker_rpcapi
from designate.pool_manager import rpcapi as pool_manager_rpcapi
from designate.i18n import _LI

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import timeutils

LOG = logging.getLogger(__name__)


class PeriodicTask(plugin.ExtensionPlugin):
    """Abstract Producer periodic task
    """
    __plugin_ns__ = 'designate.producer_tasks'
    __plugin_type__ = 'producer_task'
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
            cfg.IntOpt('per_page', default=100,
                help='Default amount of results returned per page'),
        ]
        return options

    @property
    def central_api(self):
        return rpcapi.CentralAPI.get_instance()

    @property
    def worker_api(self):
        return worker_rpcapi.WorkerAPI.get_instance()

    @property
    def pool_manager_api(self):
        return pool_manager_rpcapi.PoolManagerAPI.get_instance()

    @property
    def zone_api(self):
        # TODO(timsim): Remove this when pool_manager_api is gone
        if cfg.CONF['service:worker'].enabled:
                return self.worker_api
        return self.pool_manager_api

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
        return self._iter(self.central_api.find_zones, ctxt, criterion)


class DeletedZonePurgeTask(PeriodicTask):
    """Purge deleted zones that are exceeding the grace period time interval.
    Deleted zones have values in the deleted_at column.
    Purging means removing them from the database entirely.
    """

    __plugin_name__ = 'zone_purge'
    __interval__ = 3600

    def __init__(self):
        super(DeletedZonePurgeTask, self).__init__()

    @classmethod
    def get_cfg_opts(cls):
        group = cfg.OptGroup(cls.get_canonical_name())
        options = cls.get_base_opts() + [
            cfg.IntOpt(
                'time_threshold',
                default=604800,
                help="How old deleted zones should be (deleted_at) to be "
                "purged, in seconds"
            ),
            cfg.IntOpt(
                'batch_size',
                default=100,
                help='How many zones to be purged on each run'
            ),
        ]
        return [(group, options)]

    def __call__(self):
        """Call the Central API to perform a purge of deleted zones based on
        expiration time and sharding range.
        """
        pstart, pend = self._my_range()
        msg = _LI("Performing deleted zone purging for %(start)s to %(end)s")
        LOG.info(msg, {"start": pstart, "end": pend})

        delta = datetime.timedelta(seconds=self.options.time_threshold)
        time_threshold = timeutils.utcnow() - delta
        LOG.debug("Filtering deleted zones before %s", time_threshold)

        criterion = self._filter_between('shard')
        criterion['deleted'] = '!0'
        criterion['deleted_at'] = "<=%s" % time_threshold

        ctxt = context.DesignateContext.get_admin_context()
        ctxt.all_tenants = True

        self.central_api.purge_zones(
            ctxt,
            criterion,
            limit=self.options.batch_size,
        )


class PeriodicExistsTask(PeriodicTask):
    __plugin_name__ = 'periodic_exists'
    __interval__ = 3600

    def __init__(self):
        super(PeriodicExistsTask, self).__init__()
        self.notifier = rpc.get_notifier('producer')

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

        msg = _LI("Emitting zone exist events for shards %(start)s to %(end)s")
        LOG.info(msg, {"start": pstart, "end": pend})

        ctxt = context.DesignateContext.get_admin_context()
        ctxt.all_tenants = True

        start, end = self._get_period(self.options.interval)

        extra_data = {
            "audit_period_beginning": start,
            "audit_period_ending": end
        }

        counter = 0

        for zone in self._iter_zones(ctxt):
            counter += 1

            zone_data = zone.to_dict()
            zone_data.update(extra_data)

            self.notifier.info(ctxt, 'dns.domain.exists', zone_data)
            self.notifier.info(ctxt, 'dns.zone.exists', zone_data)

        LOG.info(_LI("Finished emitting %(counter)d events for shards "
                     "%(start)s to %(end)s"),
                 {"start": pstart, "end": pend, "counter": counter})


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
        msg = _LI("Refreshing zones for shards %(start)s to %(end)s")
        LOG.info(msg, {"start": pstart, "end": pend})

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
                msg = "Zone %(id)s has %(seconds)d seconds since last " \
                      "transfer, executing AXFR"
                LOG.debug(msg, {"id": zone.id, "seconds": seconds})
                self.central_api.xfr_zone(ctxt, zone.id)


class PeriodicGenerateDelayedNotifyTask(PeriodicTask):
    """Generate delayed NOTIFY transactions
    Scan the database for zones with the delayed_notify flag set.
    """

    __plugin_name__ = 'delayed_notify'
    __interval__ = 5

    def __init__(self):
        super(PeriodicGenerateDelayedNotifyTask, self).__init__()

    @classmethod
    def get_cfg_opts(cls):
        group = cfg.OptGroup(cls.get_canonical_name())
        options = cls.get_base_opts() + [
            cfg.IntOpt(
                'interval',
                default=cls.__interval__,
                help='Run interval in seconds'
            ),
            cfg.IntOpt(
                'batch_size',
                default=100,
                help='How many zones to receive NOTIFY on each run'
            ),
        ]
        return [(group, options)]

    def __call__(self):
        """Fetch a list of zones with the delayed_notify flag set up to
        "batch_size"
        Call Worker to emit NOTIFY transactions,
        Reset the flag.
        """
        pstart, pend = self._my_range()

        ctxt = context.DesignateContext.get_admin_context()
        ctxt.all_tenants = True

        # Select zones where "delayed_notify" is set and starting from the
        # oldest "updated_at".
        # There's an index on delayed_notify.
        criterion = self._filter_between('shard')
        criterion['delayed_notify'] = True
        zones = self.central_api.find_zones(
            ctxt,
            criterion,
            limit=self.options.batch_size,
            sort_key='updated_at',
            sort_dir='asc',
        )

        msg = _LI("Performing delayed NOTIFY for %(start)s to %(end)s: %(n)d")
        LOG.debug(msg % dict(start=pstart, end=pend, n=len(zones)))

        for z in zones:
            self.zone_api.update_zone(ctxt, z)
            z.delayed_notify = False
            self.central_api.update_zone(ctxt, z)


class WorkerPeriodicRecovery(PeriodicTask):
    __plugin_name__ = 'worker_periodic_recovery'
    __interval__ = 120

    @classmethod
    def get_cfg_opts(cls):
        group = cfg.OptGroup(cls.get_canonical_name())
        options = cls.get_base_opts() + [
            cfg.IntOpt(
                'interval',
                default=cls.__interval__,
                help='Run interval in seconds'
            ),
        ]
        return [(group, options)]

    def __call__(self):
        # TODO(timsim): Remove this when worker is always on
        if not cfg.CONF['service:worker'].enabled:
                return

        pstart, pend = self._my_range()
        msg = _LI("Recovering zones for shards %(start)s to %(end)s")
        LOG.info(msg, {"start": pstart, "end": pend})

        ctxt = context.DesignateContext.get_admin_context()
        ctxt.all_tenants = True

        self.worker_api.recover_shard(ctxt, pstart, pend)
