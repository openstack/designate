#
# Copyright 2014 Red Hat, Inc.
# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hpe.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import math

from oslo_concurrency import lockutils
from oslo_log import log
from oslo_utils import uuidutils
import tenacity
import tooz.coordination

import designate.conf


CONF = designate.conf.CONF
LOG = log.getLogger(__name__)


def _retry_if_tooz_error(exception):
    """Return True if we should retry, False otherwise"""
    return isinstance(exception, tooz.coordination.ToozError)


class Coordination:
    def __init__(self, name, tg, grouping_enabled=False):
        self.name = name.encode('ascii')
        self.tg = tg
        self.coordination_id = None
        self._grouping_enabled = grouping_enabled
        self._coordinator = None
        self._started = False

    @property
    def coordinator(self):
        return self._coordinator

    @property
    def started(self):
        return self._started

    def get_lock(self, name):
        if self._coordinator:
            return self._coordinator.get_lock(name)
        return lockutils.lock(name)

    def start(self):
        self.coordination_id = (
            ':'.join([CONF.host, uuidutils.generate_uuid()]).encode()
        )
        self._started = False

        backend_url = CONF.coordination.backend_url
        if backend_url is None:
            LOG.warning('No coordination backend configured, distributed '
                        'coordination functionality will be disabled. '
                        'Please configure a coordination backend.')
            return

        self._coordinator = tooz.coordination.get_coordinator(
            backend_url, self.coordination_id
        )
        while not self._coordinator.is_started:
            self._coordinator.start(start_heart=True)

        self._started = True

        if self._grouping_enabled:
            self._enable_grouping()

    def stop(self):
        if self._coordinator is None:
            return

        try:
            if self._grouping_enabled:
                self._disable_grouping()
            self._coordinator.stop()
            self._coordinator = None
        finally:
            self._started = False

    def _coordinator_run_watchers(self):
        if not self._started:
            return
        self._coordinator.run_watchers()

    def _create_group(self):
        try:
            create_group_req = self._coordinator.create_group(
                self.name
            )
            create_group_req.get()
        except tooz.coordination.GroupAlreadyExist:
            pass
        join_group_req = self._coordinator.join_group(self.name)
        join_group_req.get()

    def _disable_grouping(self):
        try:
            leave_group_req = self._coordinator.leave_group(self.name)
            leave_group_req.get()
        except tooz.coordination.GroupNotCreated:
            pass

    def _enable_grouping(self):
        self._create_group()
        self.tg.add_timer_args(
            CONF.coordination.run_watchers_interval,
            self._coordinator_run_watchers,
            stop_on_exception=False,
        )


class Partitioner:
    def __init__(self, coordinator, group_id, my_id, partitions):
        self._coordinator = coordinator
        self._group_id = group_id
        self._my_id = my_id
        self._partitions = partitions

        self._started = False
        self._my_partitions = None
        self._callbacks = []

    def _warn_no_backend(self):
        LOG.warning('No coordination backend configured, assuming we are '
                    'the only worker. Please configure a coordination '
                    'backend')

    @tenacity.retry(stop=tenacity.stop_after_attempt(5),
                    wait=tenacity.wait_random(max=2),
                    retry=tenacity.retry_if_exception(_retry_if_tooz_error),
                    reraise=True)
    def _get_members(self, group_id):
        get_members_req = self._coordinator.get_members(group_id)
        try:
            return get_members_req.get()

        except tooz.coordination.GroupNotCreated:
            LOG.error('Attempting to partition over a non-existent group: %s',
                      self._group_id)

            raise
        except tooz.coordination.ToozError:
            LOG.error('Error getting group membership info from coordination '
                      'backend.')
            raise

    def _on_group_change(self, event):
        LOG.debug('Received member change %s', event)
        members, self._my_partitions = self._update_partitions()

        self._run_callbacks(members, event)

    def _partition(self, members, me, partitions):
        member_count = len(members)
        partition_count = len(partitions)
        partition_size = int(
            math.ceil(float(partition_count) / float(member_count)))

        my_index = members.index(me)
        my_start = partition_size * my_index
        my_end = my_start + partition_size

        return partitions[my_start:my_end]

    def _run_callbacks(self, members, event):
        for cb in self._callbacks:
            cb(self.my_partitions, members, event)

    def _update_partitions(self):
        # Recalculate partitions - we need to sort the list of members
        # alphabetically so that it's the same order across all nodes.
        members = sorted(list(self._get_members(self._group_id)))
        partitions = self._partition(
            members, self._my_id, self._partitions)
        return members, partitions

    @property
    def my_partitions(self):
        return self._my_partitions

    def start(self):
        """Allow the partitioner to start timers after the coordinator has
        gotten it's connections up.
        """
        LOG.debug('Starting partitioner')
        if self._coordinator:
            self._coordinator.watch_join_group(
                self._group_id, self._on_group_change)
            self._coordinator.watch_leave_group(
                self._group_id, self._on_group_change)

            # We need to get our partitions now. Events doesn't help in this
            # case since they require state change in the group that we wont
            # get when starting initially
            self._my_partitions = self._update_partitions()[1]
        else:
            self._my_partitions = self._partitions
            self._run_callbacks(None, None)

        self._started = True

    def watch_partition_change(self, callback):
        LOG.debug('Watching for change %s', self._group_id)
        self._callbacks.append(callback)
        if self._started:
            if not self._coordinator:
                self._warn_no_backend()
            callback(self._my_partitions, None, None)

    def unwatch_partition_change(self, callback):
        self._callbacks.remove(callback)
