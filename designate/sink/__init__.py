# Copyright 2012 Hewlett-Packard Development Company, L.P. All Rights Reserved.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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

sink_group = cfg.OptGroup(
    name='service:sink', title="Configuration for Sink Service"
)

OPTS = [
    cfg.IntOpt('workers',
               help='Number of sink worker processes to spawn'),
    cfg.IntOpt('threads', default=1000,
               help='Number of sink greenthreads to spawn'),
    cfg.ListOpt('enabled-notification-handlers', default=[],
                help='Enabled Notification Handlers'),
]


cfg.CONF.register_group(sink_group)
cfg.CONF.register_opts(OPTS, group=sink_group)


def list_opts():
    yield sink_group, OPTS
