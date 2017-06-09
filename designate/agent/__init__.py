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
from designate.backend.agent_backend import impl_bind9
from designate.backend.agent_backend import impl_denominator
from designate.backend.agent_backend import impl_djbdns
from designate.backend.agent_backend import impl_gdnsd
from designate.backend.agent_backend import impl_knot2
from designate.backend.agent_backend import impl_msdns


agent_group = cfg.OptGroup(
    name='service:agent', title="Configuration for the Agent Service"
)

agent_opts = [
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

cfg.CONF.register_group(agent_group)
cfg.CONF.register_opts(agent_opts, group=agent_group)


def list_opts():
    yield agent_group, agent_opts
    yield impl_bind9.bind9_group, impl_bind9.bind9_opts
    yield impl_denominator.denominator_group, impl_denominator.denominator_opts
    yield impl_djbdns.djbdns_group, impl_djbdns.djbdns_opts
    yield impl_gdnsd.gdnsd_group, impl_gdnsd.gdnsd_opts
    yield impl_knot2.knot2_group, impl_knot2.knot2_opts
    yield impl_msdns.msdns_group, impl_msdns.msdns_opts
