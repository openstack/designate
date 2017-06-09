# Copyright 2014 Hewlett-Packard Development Company, L.P.
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

from designate import dnsutils
from designate.utils import DEFAULT_MDNS_PORT


mdns_group = cfg.OptGroup(
    name='service:mdns', title="Configuration for mDNS Service"
)

OPTS = [
    cfg.IntOpt('workers',
               help='Number of mdns worker processes to spawn'),
    cfg.IntOpt('threads', default=1000,
               help='Number of mdns greenthreads to spawn'),
    cfg.IPOpt('host',
              deprecated_for_removal=True,
              deprecated_reason="Replaced by 'listen' option",
              help='mDNS Bind Host'),
    cfg.PortOpt('port',
                deprecated_for_removal=True,
                deprecated_reason="Replaced by 'listen' option",
                help='mDNS Port Number'),
    cfg.ListOpt('listen',
                default=['0.0.0.0:%d' % DEFAULT_MDNS_PORT],
                help='mDNS host:port pairs to listen on'),
    cfg.IntOpt('tcp-backlog', default=100,
               help='mDNS TCP Backlog'),
    cfg.FloatOpt('tcp-recv-timeout', default=0.5,
                 help='mDNS TCP Receive Timeout'),
    cfg.BoolOpt('all-tcp', default=False,
                help='Send all traffic over TCP'),
    cfg.BoolOpt('query-enforce-tsig', default=False,
                help='Enforce all incoming queries (including AXFR) are TSIG '
                     'signed'),
    cfg.StrOpt('storage-driver', default='sqlalchemy',
               help='The storage driver to use'),
    cfg.IntOpt('max-message-size', default=65535,
               help='Maximum message size to emit'),
    cfg.StrOpt('mdns_topic', default='mdns',
               help='RPC topic name for mini-DNS')
]


cfg.CONF.register_group(mdns_group)
cfg.CONF.register_opts(OPTS, group=mdns_group)
cfg.CONF.register_opts(dnsutils.util_opts, group=mdns_group)


def list_opts():
    yield mdns_group, OPTS
