# Copyright 2016 Hewlett Packard Enterprise Development Company LP
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

HEARTBEAT_GROUP = cfg.OptGroup(
    name='heartbeat_emitter',
    title="Configuration for heartbeat_emitter"
)

HEARTBEAT_OPTS = [
    cfg.FloatOpt('heartbeat_interval',
                 default=10.0,
                 help='Number of seconds between heartbeats for reporting '
                      'state'),
    cfg.StrOpt('emitter_type', default="rpc", help="Emitter to use"),
]


def register_opts(conf):
    conf.register_group(HEARTBEAT_GROUP)
    conf.register_opts(HEARTBEAT_OPTS, group=HEARTBEAT_GROUP)


def list_opts():
    return {
        HEARTBEAT_GROUP: HEARTBEAT_OPTS
    }
