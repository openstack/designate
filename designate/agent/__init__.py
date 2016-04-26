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

from designate.utils import DEFAULT_AGENT_PORT

cfg.CONF.register_group(cfg.OptGroup(
    name='service:agent', title="Configuration for the Agent Service"
))

OPTS = [
    cfg.IntOpt('workers',
               help='Number of agent worker processes to spawn'),
    cfg.IntOpt('threads', default=1000,
               help='Number of agent greenthreads to spawn'),
    cfg.IPOpt('host',
              deprecated_for_removal=True,
              deprecated_reason="Replaced by 'listen' option",
              help='Agent Bind Host'),
    cfg.PortOpt('port',
                deprecated_for_removal=True,
                deprecated_reason="Replaced by 'listen' option",
                help='Agent Port Number'),
    cfg.ListOpt('listen',
                default=['0.0.0.0:%d' % DEFAULT_AGENT_PORT],
                help='Agent host:port pairs to listen on'),
    cfg.IntOpt('tcp-backlog', default=100,
               help='The Agent TCP Backlog'),
    cfg.FloatOpt('tcp-recv-timeout', default=0.5,
                 help='Agent TCP Receive Timeout'),
    cfg.ListOpt('allow-notify', default=[],
                help='List of IP addresses allowed to NOTIFY The Agent'),
    cfg.ListOpt('masters', default=[],
                help='List of masters for the Agent, format ip:port'),
    cfg.StrOpt('backend-driver', default='bind9',
               help='The backend driver to use, e.g. bind9, djbdns, knot2'),
    cfg.StrOpt('transfer-source',
               help='An IP address to be used to fetch zones transferred in'),
    cfg.FloatOpt('notify-delay', default=0.0,
                 help='Delay after a NOTIFY arrives for a zone that the Agent '
                 'will pause and drop subsequent NOTIFYs for that zone'),
]

cfg.CONF.register_opts(OPTS, group='service:agent')
