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

METRICS_GROUP = cfg.OptGroup(
    name='monasca:statsd',
    title="Configuration for Monasca Statsd"
)

METRICS_OPTS = [
    cfg.BoolOpt('enabled', default=False, help='enable'),
    cfg.IntOpt('port', default=8125, help='UDP port'),
    cfg.StrOpt('hostname', default='127.0.0.1', help='hostname'),
]


def register_opts(conf):
    conf.register_group(METRICS_GROUP)
    conf.register_opts(METRICS_OPTS, group=METRICS_GROUP)


def list_opts():
    return {
        METRICS_GROUP: METRICS_OPTS
    }
