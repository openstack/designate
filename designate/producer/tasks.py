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

from oslo_log import log as logging
from oslo_utils import timeutils

from designate.central import rpcapi
import designate.conf
from designate import context
from designate import plugin
from designate import rpc
from designate.worker import rpcapi as worker_rpcapi


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class PeriodicTask(plugin.ExtensionPlugin):
    """Abstract Producer periodic task
    """
    __plugin_ns__ = 'designate.producer_tasks'
    __plugin_type__ = 'producer_task'

    def __init__(self):
        super().__init__()
        self.my_partitions = None

    @property
    def central_api(self):
        return rpcapi.CentralAPI.get_instance()

    @property
    def worker_api(self):
        return worker_rpcapi.WorkerAPI.get_instance()

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
        kwargs.setdefault("limit", CONF[self.name].per_page)
        while True:
            items = method(*args, **kwargs)

            # Stop fetching if there's no more items
            if len(items) == 0:
                return
            else:
                kwargs["marker"] = items[-1].id

            yield from items

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

    def __init__(self):
        super().__init__()

    def __call__(self):
        """Call the Central API to perform a purge of deleted zones based on
        expiration time and sharding range.
        """
        pstart, pend = self._my_range()
        LOG.info(
            "Performing deleted zone purging for %(start)s to %(end)s",
            {
                "start": pstart,
                "end": pend
            })

        delta = datetime.timedelta(seconds=CONF[self.name].time_threshold)
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
            limit=CONF[self.name].batch_size,
        )


class PeriodicExistsTask(PeriodicTask):
    __plugin_name__ = 'periodic_exists'

    def __init__(self):
        super().__init__()
        self.notifier = rpc.get_notifier('producer')

    @staticmethod
    def _get_period(seconds):
        interval = datetime.timedelta(seconds=seconds)
        end = timeutils.utcnow()
        return end - interval, end

    def __call__(self):
        pstart, pend = self._my_range()

        LOG.info(
            "Emitting zone exist events for shards %(start)s to %(end)s",
            {
                "start": pstart,
                "end": pend
            })

        ctxt = context.DesignateContext.get_admin_context()
        ctxt.all_tenants = True

        start, end = self._get_period(CONF[self.name].interval)

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

        LOG.info(
            "Finished emitting %(counter)d events for shards "
            "%(start)s to %(end)s",
            {
                "start": pstart,
                "end": pend,
                "counter": counter
            })


class PeriodicSecondaryRefreshTask(PeriodicTask):
    __plugin_name__ = 'periodic_secondary_refresh'

    def __call__(self):
        pstart, pend = self._my_range()
        LOG.info(
            "Refreshing zones for shards %(start)s to %(end)s",
            {
                "start": pstart,
                "end": pend
            })

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

            transferred = timeutils.parse_isotime(str(zone.transferred_at))
            seconds = timeutils.delta_seconds(transferred, now)
            if seconds > zone.refresh:
                LOG.debug(
                    "Zone %(id)s has %(seconds)d seconds since last transfer, "
                    "executing AXFR",
                    {
                        "id": zone.id,
                        "seconds": seconds
                    }
                )
                self.central_api.xfr_zone(ctxt, zone.id)


class PeriodicGenerateDelayedNotifyTask(PeriodicTask):
    """Generate delayed NOTIFY transactions
    Scan the database for zones with the delayed_notify flag set.
    """
    __plugin_name__ = 'delayed_notify'

    def __init__(self):
        super().__init__()

    def __call__(self):
        """Fetch a list of zones with the delayed_notify flag set up to
        "batch_size"
        Call Worker to emit NOTIFY transactions,
        Reset the flag.
        """
        ctxt = context.DesignateContext.get_admin_context()
        ctxt.all_tenants = True

        # Select zones where "delayed_notify" is set and starting from the
        # oldest "updated_at".
        # There's an index on delayed_notify.
        criterion = self._filter_between('shard')
        criterion['delayed_notify'] = True
        criterion['increment_serial'] = False
        zones = self.central_api.find_zones(
            ctxt,
            criterion,
            limit=CONF[self.name].batch_size,
            sort_key='updated_at',
            sort_dir='asc',
        )

        for zone in zones:
            if zone.action == 'NONE':
                zone.action = 'UPDATE'
                zone.status = 'PENDING'
            elif zone.action == 'DELETE':
                LOG.debug(
                    'Skipping delayed NOTIFY for %(id)s being DELETED',
                    {
                        'id': zone.id,
                    }
                )
                continue
            self.worker_api.update_zone(ctxt, zone)
            zone.delayed_notify = False
            self.central_api.update_zone(ctxt, zone)
            LOG.debug(
                'Performed delayed NOTIFY for %(id)s',
                {
                    'id': zone.id,
                }
            )


class PeriodicIncrementSerialTask(PeriodicTask):
    __plugin_name__ = 'increment_serial'

    def __init__(self):
        super().__init__()

    def __call__(self):
        ctxt = context.DesignateContext.get_admin_context()
        ctxt.all_tenants = True

        # Select zones where "increment_serial" is set and starting from the
        # oldest "updated_at".
        # There's an index on increment_serial.
        criterion = self._filter_between('shard')
        criterion['increment_serial'] = True
        zones = self.central_api.find_zones(
            ctxt,
            criterion,
            limit=CONF[self.name].batch_size,
            sort_key='updated_at',
            sort_dir='asc',
        )
        for zone in zones:
            if zone.action == 'DELETE':
                LOG.debug(
                    'Skipping increment serial for %(id)s being DELETED',
                    {
                        'id': zone.id,
                    }
                )
                continue

            serial = self.central_api.increment_zone_serial(ctxt, zone)
            LOG.debug(
                'Incremented serial for %(id)s to %(serial)d',
                {
                    'id': zone.id,
                    'serial': serial,
                }
            )
            if not zone.delayed_notify:
                # Notify the backend.
                if zone.action == 'NONE':
                    zone.action = 'UPDATE'
                    zone.status = 'PENDING'
                self.worker_api.update_zone(ctxt, zone)


class WorkerPeriodicRecovery(PeriodicTask):
    __plugin_name__ = 'worker_periodic_recovery'

    def __call__(self):
        pstart, pend = self._my_range()
        LOG.info(
            "Recovering zones for shards %(start)s to %(end)s",
            {
                "start": pstart,
                "end": pend
            })

        ctxt = context.DesignateContext.get_admin_context()
        ctxt.all_tenants = True

        self.worker_api.recover_shard(ctxt, pstart, pend)
