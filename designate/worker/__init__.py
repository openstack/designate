# Copyright 2016 Rackspace Inc.
#
# Author: Tim Simmons <tim.simmons@rackspace.com>
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

CONF = cfg.CONF

worker_group = cfg.OptGroup(
    name='service:worker', title="Configuration for the Worker Service"
)

OPTS = [
    cfg.BoolOpt('enabled', default=False,
                help='Whether to send events to worker instead of '
                     'Pool Manager',
                deprecated_for_removal=True,
                deprecated_reason='In Newton, this option will disappear'
                                  'because worker will be enabled by default'),
    cfg.IntOpt('workers',
               help='Number of Worker worker processes to spawn'),
    cfg.IntOpt('threads', default=200,
               help='Number of Worker threads to spawn per process'),
    # cfg.ListOpt('enabled_tasks',
    #             help='Enabled tasks to run'),
    cfg.StrOpt('storage-driver', default='sqlalchemy',
               help='The storage driver to use'),
    cfg.IntOpt('threshold-percentage', default=100,
               help='The percentage of servers requiring a successful update '
                    'for a domain change to be considered active'),
    cfg.IntOpt('poll-timeout', default=30,
               help='The time to wait for a response from a server'),
    cfg.IntOpt('poll-retry-interval', default=15,
               help='The time between retrying to send a request and '
                    'waiting for a response from a server'),
    cfg.IntOpt('poll-max-retries', default=10,
               help='The maximum number of times to retry sending a request '
                    'and wait for a response from a server'),
    cfg.IntOpt('poll-delay', default=5,
               help='The time to wait before sending the first request '
                    'to a server'),
    cfg.BoolOpt('notify', default=True,
                help='Whether to allow worker to send NOTIFYs, this will '
                     'noop NOTIFYs in mdns if true'),
    cfg.BoolOpt('export-synchronous', default=True,
                help='Whether to allow synchronous zone exports'),
    cfg.StrOpt('worker_topic', default='worker',
               help='RPC topic for worker component')
]


cfg.CONF.register_group(worker_group)
cfg.CONF.register_opts(OPTS, group=worker_group)


def list_opts():
    yield worker_group, OPTS
