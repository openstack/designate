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
import time

from oslo_config import cfg
from oslo_log import log
import tenacity
import tooz.coordination

from designate.utils import generate_uuid
from designate.i18n import _LI
from designate.i18n import _LW
from designate.i18n import _LE


LOG = log.getLogger(__name__)

coordination_group = cfg.OptGroup(
    name='coordination', title="Configuration for coordination"
)

coordination_opts = [
    cfg.StrOpt('backend_url',
               help='The backend URL to use for distributed coordination. If '
                    'unset services that need coordination will function as '
                    'a standalone service.'),
    cfg.FloatOpt('heartbeat_interval',
                 default=1.0,
                 help='Number of seconds between heartbeats for distributed '
                      'coordination.'),
    cfg.FloatOpt('run_watchers_interval',
                 default=10.0,
                 help='Number of seconds between checks to see if group '
                      'membership has changed')

]
cfg.CONF.register_group(coordination_group)
cfg.CONF.register_opts(coordination_opts, group=coordination_group)

CONF = cfg.CONF


def _retry_if_tooz_error(exception):
    """Return True if we should retry, False otherwise"""
    return isinstance(exception, tooz.coordination.ToozError)


class CoordinationMixin(object):
    def __init__(self, *args, **kwargs):
        super(CoordinationMixin, self).__init__(*args, **kwargs)

        self._coordinator = None

    def start(self):
        self._coordination_id = ":".join([CONF.host, generate_uuid()])

        if CONF.coordination.backend_url is not None:
            backend_url = cfg.CONF.coordination.backend_url
            self._coordinator = tooz.coordination.get_coordinator(
                backend_url, self._coordination_id)
            self._coordination_started = False

            self.tg.add_timer(cfg.CONF.coordination.heartbeat_interval,
                              self._coordinator_heartbeat)
            self.tg.add_timer(cfg.CONF.coordination.run_watchers_interval,
                              self._coordinator_run_watchers)

        else:
            msg = _LW("No coordination backend configured, distributed "
                      "coordination functionality will be disabled. "
                      "Please configure a coordination backend.")
            LOG.warning(msg)

        super(CoordinationMixin, self).start()

        if self._coordinator is not None:
            while not self._coordination_started:
                try:
                    self._coordinator.start()

                    try:
                        create_group_req = self._coordinator.create_group(
                            self.service_name)
                        create_group_req.get()
                    except tooz.coordination.GroupAlreadyExist:
                        pass

                    join_group_req = self._coordinator.join_group(
                        self.service_name)
                    join_group_req.get()

                    self._coordination_started = True

                except Exception:
                    LOG.warning(_LW("Failed to start Coordinator:"),
                                exc_info=True)
                    time.sleep(15)

    def stop(self):
        if self._coordinator is not None:
            self._coordination_started = False

            leave_group_req = self._coordinator.leave_group(self.service_name)
            leave_group_req.get()
            self._coordinator.stop()

        super(CoordinationMixin, self).stop()

        self._coordinator = None

    def _coordinator_heartbeat(self):
        if not self._coordination_started:
            return

        try:
            self._coordinator.heartbeat()
        except tooz.coordination.ToozError:
            LOG.exception(_LE('Error sending a heartbeat to coordination '
                          'backend.'))

    def _coordinator_run_watchers(self):
        if not self._coordination_started:
            return

        self._coordinator.run_watchers()


class Partitioner(object):
    def __init__(self, coordinator, group_id, my_id, partitions):
        self._coordinator = coordinator
        self._group_id = group_id
        self._my_id = my_id
        self._partitions = partitions

        self._started = False
        self._my_partitions = None
        self._callbacks = []

    def _warn_no_backend(self):
        LOG.warning(_LW('No coordination backend configured, assuming we are '
                        'the only worker. Please configure a coordination '
                        'backend'))

    @tenacity.retry(stop=tenacity.stop_after_attempt(5),
                    wait=tenacity.wait_random(max=2),
                    retry=tenacity.retry_if_exception(_retry_if_tooz_error),
                    reraise=True)
    def _get_members(self, group_id):
        get_members_req = self._coordinator.get_members(group_id)
        try:
            return get_members_req.get()

        except tooz.coordination.GroupNotCreated:
            LOG.error(_LE('Attempting to partition over a non-existent group: '
                          '%s'), self._group_id)

            raise
        except tooz.coordination.ToozError:
            LOG.error(_LE('Error getting group membership info from '
                          'coordination backend.'))
            raise

    def _on_group_change(self, event):
        LOG.debug("Received member change %s" % event)
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
        LOG.debug("Starting partitioner")
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
        LOG.debug("Watching for change %s" % self._group_id)
        self._callbacks.append(callback)
        if self._started:
            if not self._coordinator:
                self._warn_no_backend()
            callback(self._my_partitions, None, None)

    def unwatch_partition_change(self, callback):
        self._callbacks.remove(callback)


class LeaderElection(object):
    def __init__(self, coordinator, group_id):
        self._coordinator = coordinator
        self._group_id = group_id

        self._callbacks = []
        self._started = False
        self._leader = False

    def _warn_no_backend(self):
        LOG.warning(_LW('No coordination backend configured, assuming we are '
                        'the leader. Please configure a coordination backend'))

    def start(self):
        self._started = True

        if self._coordinator:
            LOG.info(_LI('Starting leader election for group %(group)s'),
                     {'group': self._group_id})

            # Nominate myself for election
            self._coordinator.watch_elected_as_leader(
                self._group_id, self._on_elected_leader)
        else:
            self._warn_no_backend()
            self._leader = True

            for callback in self._callbacks:
                callback(None)

    def stop(self):
        self._started = False

        if self._coordinator:
            LOG.info(_LI('Stopping leader election for group %(group)s'),
                     {'group': self._group_id})

            # Remove the elected_as_leader callback
            self._coordinator.unwatch_elected_as_leader(
                self._group_id, self._on_elected_leader)

            if self._leader:
                # Tell Tooz we no longer wish to be the leader
                LOG.info(_LI('Standing down as leader candidate for group '
                             '%(group)s'), {'group': self._group_id})
                self._leader = False
                self._coordinator.stand_down_group_leader(self._group_id)

        elif self._leader:
            LOG.info(_LI('Standing down as leader candidate for group '
                         '%(group)s'), {'group': self._group_id})
            self._leader = False

    @property
    def is_leader(self):
        return self._leader

    def _on_elected_leader(self, event):
        LOG.info(_LI('Successfully elected as leader of group %(group)s'),
                 {'group': self._group_id})
        self._leader = True

        for callback in self._callbacks:
            callback(event)

    def watch_elected_as_leader(self, callback):
        self._callbacks.append(callback)

        if self._started and self._leader:
            # We're started, and we're the leader, we should trigger the
            # callback
            callback(None)

        elif self._started and not self._coordinator:
            # We're started, and there's no coordination backend configured,
            # we assume we're leader and call the callback.
            self._warn_no_backend()
            callback(None)

    def unwatch_elected_as_leader(self, callback):
        self._callbacks.remove(callback)
