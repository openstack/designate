# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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

from designate import dnsutils


cfg.CONF.register_group(cfg.OptGroup(
    name='service:mdns', title="Configuration for mDNS Service"
))

OPTS = [
    cfg.IntOpt('workers', default=None,
               help='Number of mdns worker processes to spawn'),
    cfg.IntOpt('threads', default=1000,
               help='Number of mdns greenthreads to spawn'),
    cfg.StrOpt('host', default='0.0.0.0',
               help='mDNS Bind Host'),
    cfg.IntOpt('port', default=5354,
               help='mDNS Port Number'),
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
]

cfg.CONF.register_opts(OPTS, group='service:mdns')
cfg.CONF.register_opts(dnsutils.util_opts, group='service:mdns')
