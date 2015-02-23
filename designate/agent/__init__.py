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
from oslo.config import cfg

cfg.CONF.register_group(cfg.OptGroup(
    name='service:agent', title="Configuration for the Agent Service"
))

OPTS = [
    cfg.IntOpt('workers', default=None,
               help='Number of agent worker processes to spawn'),
    cfg.StrOpt('host', default='0.0.0.0',
               help='The Agent Bind Host'),
    cfg.IntOpt('port', default=5358,
               help='mDNS Port Number'),
    cfg.IntOpt('tcp-backlog', default=100,
               help='The Agent TCP Backlog'),
    cfg.FloatOpt('tcp-recv-timeout', default=0.5,
                 help='Agent TCP Receive Timeout'),
    cfg.ListOpt('allow-notify', default=[],
                help='List of IP addresses allowed to NOTIFY The Agent'),
    cfg.ListOpt('masters', default=[],
                help='List of masters for the Agent, format ip:port'),
    cfg.StrOpt('backend-driver', default='bind9',
               help='The backend driver to use'),
    cfg.StrOpt('transfer-source', default=None,
               help='An IP address to be used to fetch zones transferred in'),
]

cfg.CONF.register_opts(OPTS, group='service:agent')
