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
    __plugin_ns__ = 'designate.zone_manager_tasks'
    __plugin_type__ = 'zone_manager_task'
    __interval__ = None

    def __init__(self):
        self.my_partitions = None
        self.options = cfg.CONF[self.get_canonical_name()]

    @classmethod
    def get_base_opts(cls):
        options = [
            cfg.IntOpt('interval', default=cls.__interval__),
            cfg.IntOpt('per_page', default=100),
        ]
        return options

    @property
    def central_api(self):
        return rpcapi.CentralAPI.get_instance()

    def on_partition_change(self, my_partitions, members, event):
        self.my_partitions = my_partitions

    def _my_range(self):
        return self.my_partitions[0], self.my_partitions[-1]

    def _filter_between(self, col):
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
