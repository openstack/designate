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

DEFAULT_MDNS_PORT = 5354

MDNS_GROUP = cfg.OptGroup(
    name='service:mdns', title="Configuration for mDNS Service"
)

MDNS_OPTS = [
    cfg.IntOpt('workers',
               help='Number of mdns worker processes to spawn'),
    cfg.IntOpt('threads', default=1000,
               help='Number of mdns greenthreads to spawn'),
    cfg.ListOpt('listen',
                default=['0.0.0.0:%d' % DEFAULT_MDNS_PORT],
                help='mDNS host:port pairs to listen on'),
    cfg.IntOpt('tcp_backlog', default=100,
               help='mDNS TCP Backlog'),
    cfg.FloatOpt('tcp_recv_timeout', default=0.5,
                 help='mDNS TCP Receive Timeout'),
    cfg.IntOpt('all_tcp', help='Send all traffic over TCP',
               default=None,
               deprecated_for_removal=True,
               deprecated_reason='This parameter should now be configured in'
                                 'service:worker instead',
               deprecated_since='Zed'),
    cfg.BoolOpt('query_enforce_tsig', default=False,
                help='Enforce all incoming queries (including AXFR) are TSIG '
                     'signed'),
    cfg.StrOpt('storage_driver', default='sqlalchemy',
               help='The storage driver to use'),
    cfg.IntOpt('max_message_size', default=65535,
               help='Maximum message size to emit'),
    cfg.StrOpt('topic', default='mdns',
               help='RPC topic name for mdns'),
    cfg.IntOpt('xfr_timeout', help="Timeout in seconds for XFR's.",
               default=None,
               deprecated_for_removal=True,
               deprecated_reason='This parameter should now be configured in'
                                 'service:worker instead',
               deprecated_since='Zed'),
]


def register_opts(conf):
    conf.register_group(MDNS_GROUP)
    conf.register_opts(MDNS_OPTS, group=MDNS_GROUP)


def list_opts():
    return {
        MDNS_GROUP: MDNS_OPTS
    }
