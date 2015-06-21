#
# Copyright 2014 Red Hat, Inc.
# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hp.com>
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

import uuid

from oslo_config import cfg
from oslo_log import log
import tooz.coordination

from designate.i18n import _LE
from designate.i18n import _LW


LOG = log.getLogger(__name__)

OPTS = [
    cfg.StrOpt('backend_url',
               default=None,
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
cfg.CONF.register_opts(OPTS, group='coordination')

CONF = cfg.CONF


class CoordinationMixin(object):
    def __init__(self, *args, **kwargs):
        super(CoordinationMixin, self).__init__(*args, **kwargs)

        self._coordination_id = ":".join([CONF.host, str(uuid.uuid4())])
        self._coordinator = None
        if CONF.coordination.backend_url is not None:
            self._init_coordination()
        else:
            msg = _LW("No coordination backend configured, distributed "
                      "coordination functionality will be disabled."
                      " Please configure a coordination backend.")
            LOG.warn(msg)

    def _init_coordination(self):
        backend_url = cfg.CONF.coordination.backend_url
        self._coordinator = tooz.coordination.get_coordinator(
            backend_url, self._coordination_id)
        self._coordination_started = False

        self.tg.add_timer(cfg.CONF.coordination.heartbeat_interval,
                          self._coordinator_heartbeat)
        self.tg.add_timer(cfg.CONF.coordination.run_watchers_interval,
                          self._coordinator_run_watchers)

    def start(self):
        super(CoordinationMixin, self).start()

        if self._coordinator is not None:
            self._coordinator.start()

            self._coordinator.create_group(self.service_name)
            self._coordinator.join_group(self.service_name)

            self._coordination_started = True

    def stop(self):
        if self._coordinator is not None:
            self._coordination_started = False

            self._coordinator.leave_group(self.service_name)
            self._coordinator.stop()

        super(CoordinationMixin, self).stop()

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
