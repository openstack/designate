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

WORKER_GROUP = cfg.OptGroup(
    name='service:worker', title="Configuration for the Worker Service"
)

WORKER_OPTS = [
    cfg.IntOpt('workers',
               help='Number of Worker worker processes to spawn'),
    cfg.IntOpt('threads', default=200,
               help='Number of Worker threads to spawn per process'),
    # cfg.ListOpt('enabled_tasks',
    #             help='Enabled tasks to run'),
    cfg.IntOpt('threshold-percentage', default=100,
               help='The percentage of servers requiring a successful update '
                    'for a domain change to be considered active'),
    cfg.IntOpt('poll_timeout', default=30,
               help='The time to wait for a response from a server'),
    cfg.IntOpt('poll_retry_interval', default=15,
               help='The time between retrying to send a request and '
                    'waiting for a response from a server'),
    cfg.IntOpt('poll_max_retries', default=10,
               help='The maximum number of times to retry sending a request '
                    'and wait for a response from a server'),
    cfg.IntOpt('poll_delay', default=5,
               help='The time to wait before sending the first request '
                    'to a server'),
    cfg.BoolOpt('export_synchronous', default=True,
                help='Whether to allow synchronous zone exports'),
    cfg.StrOpt('topic', default='worker',
               help='RPC topic name for worker'),
    cfg.IntOpt('xfr_timeout', help="Timeout in seconds for XFR's.",
               default=10),
    cfg.IntOpt('serial_max_retries',
               help='The maximum number of times to retry fetching a zones '
                    'serial.',
               default=3),
    cfg.IntOpt('serial_retry_delay',
               help='The time to wait before retrying a zone serial request.',
               default=1),
    cfg.IntOpt('serial_timeout',
               help='Timeout in seconds before giving up on fetching a zones '
                    'serial.',
               default=1),
    cfg.BoolOpt('all_tcp', default=False,
                help='Send all traffic over TCP'),
]


def register_opts(conf):
    conf.register_group(WORKER_GROUP)
    conf.register_opts(WORKER_OPTS, group=WORKER_GROUP)


def list_opts():
    return {
        WORKER_GROUP: WORKER_OPTS,
    }
