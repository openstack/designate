# Copyright 2014 Rackspace Inc.
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

DEFAULT_AGENT_PORT = 5358

AGENT_GROUP = cfg.OptGroup(
    name='service:agent',
    title="Configuration for the Agent Service"
)

AGENT_OPTS = [
    cfg.IntOpt('workers',
               help='Number of agent worker processes to spawn',
               deprecated_for_removal=True,
               deprecated_since='Antelope(2023.1)',
               deprecated_reason='The agent framework is deprecated.'),
    cfg.IntOpt('threads', default=1000,
               help='Number of agent greenthreads to spawn',
               deprecated_for_removal=True,
               deprecated_since='Antelope(2023.1)',
               deprecated_reason='The agent framework is deprecated.'),
    cfg.ListOpt('listen',
                default=['0.0.0.0:%d' % DEFAULT_AGENT_PORT],
                help='Agent host:port pairs to listen on',
                deprecated_for_removal=True,
                deprecated_since='Antelope(2023.1)',
                deprecated_reason='The agent framework is deprecated.'),
    cfg.IntOpt('tcp_backlog', default=100,
               help='The Agent TCP Backlog',
               deprecated_for_removal=True,
               deprecated_since='Antelope(2023.1)',
               deprecated_reason='The agent framework is deprecated.'),
    cfg.FloatOpt('tcp_recv_timeout', default=0.5,
                 help='Agent TCP Receive Timeout',
                 deprecated_for_removal=True,
                 deprecated_since='Antelope(2023.1)',
                 deprecated_reason='The agent framework is deprecated.'),
    cfg.ListOpt('allow_notify', default=[],
                help='List of IP addresses allowed to NOTIFY The Agent',
                deprecated_for_removal=True,
                deprecated_since='Antelope(2023.1)',
                deprecated_reason='The agent framework is deprecated.'),
    cfg.ListOpt('masters', default=[],
                help='List of masters for the Agent, format ip:port',
                deprecated_for_removal=True,
                deprecated_since='Antelope(2023.1)',
                deprecated_reason='The agent framework is deprecated.'),
    cfg.StrOpt('backend_driver', default='bind9',
               help='The backend driver to use, e.g. bind9, djbdns, knot2',
               deprecated_for_removal=True,
               deprecated_since='Antelope(2023.1)',
               deprecated_reason='The agent framework is deprecated.'),
    cfg.StrOpt('transfer_source',
               help='An IP address to be used to fetch zones transferred in',
               deprecated_for_removal=True,
               deprecated_since='Antelope(2023.1)',
               deprecated_reason='The agent framework is deprecated.'),
    cfg.FloatOpt('notify_delay', default=0.0,
                 help='Delay after a NOTIFY arrives for a zone that the Agent '
                      'will pause and drop subsequent NOTIFYs for that zone',
                 deprecated_for_removal=True,
                 deprecated_since='Antelope(2023.1)',
                 deprecated_reason='The agent framework is deprecated.'),
]


def register_opts(conf):
    conf.register_group(AGENT_GROUP)
    conf.register_opts(AGENT_OPTS, group=AGENT_GROUP)


def list_opts():
    return {
        AGENT_GROUP: AGENT_OPTS
    }
