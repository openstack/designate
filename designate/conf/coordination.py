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
from oslo_config import cfg

COORDINATION_GROUP = cfg.OptGroup(
    name='coordination',
    title="Configuration for coordination"
)

COORDINATION_OPTS = [
    cfg.StrOpt(
        'backend_url',
        secret=True,
        help=(
            'The backend URL to use for distributed coordination. If '
            'unset services that need coordination will function as '
            'a standalone service. This is a `tooz` url - see '
            'https://docs.openstack.org/tooz/latest/user/compatibility.html')
    ),
    cfg.FloatOpt('heartbeat_interval',
                 default=5.0,
                 help='Number of seconds between heartbeats for distributed '
                      'coordination.'),
    cfg.FloatOpt('run_watchers_interval',
                 default=10.0,
                 help='Number of seconds between checks to see if group '
                      'membership has changed'),
]


def register_opts(conf):
    conf.register_group(COORDINATION_GROUP)
    conf.register_opts(COORDINATION_OPTS, group=COORDINATION_GROUP)


def list_opts():
    return {
        COORDINATION_GROUP: COORDINATION_OPTS
    }
