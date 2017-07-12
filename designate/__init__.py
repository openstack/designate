# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
import os

# Eventlet's GreenDNS Patching will prevent the resolution of names in
# the /etc/hosts file, causing problems for for installs.
os.environ['EVENTLET_NO_GREENDNS'] = 'yes'

import socket

from oslo_config import cfg
from oslo_log import log
from oslo_concurrency import lockutils
import oslo_messaging as messaging


designate_opts = [
    cfg.StrOpt('host', default=socket.gethostname(),
               help='Name of this node'),
    cfg.StrOpt(
        'pybasedir',
        default=os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             '../')),
        help='Directory where the designate python module is installed'
    ),
    cfg.StrOpt('state-path', default='/var/lib/designate',
               help='Top-level directory for maintaining designate\'s state'),

    cfg.StrOpt('central-topic', default='central', help='Central Topic'),
    cfg.StrOpt('mdns-topic', default='mdns', help='mDNS Topic'),
    cfg.StrOpt('pool-manager-topic', default='pool_manager',
               help='Pool Manager Topic'),
    cfg.StrOpt('worker-topic', default='worker', help='Worker Topic'),

    # Default TTL
    cfg.IntOpt('default-ttl', default=3600, help='TTL Value'),

    # Default SOA Values
    cfg.IntOpt('default-soa-refresh-min', default=3500,
               deprecated_name='default-soa-refresh',
               help='SOA refresh-min value'),
    cfg.IntOpt('default-soa-refresh-max', default=3600,
               help='SOA max value'),
    cfg.IntOpt('default-soa-retry', default=600, help='SOA retry'),
    cfg.IntOpt('default-soa-expire', default=86400, help='SOA expire'),
    cfg.IntOpt('default-soa-minimum', default=3600, help='SOA minimum value'),

    # Supported record types
    cfg.ListOpt('supported-record-type', help='Supported record types',
                default=['A', 'AAAA', 'CNAME', 'MX', 'SRV', 'TXT', 'SPF', 'NS',
                         'PTR', 'SSHFP', 'SOA']),
]

# Set some Oslo Log defaults
log.set_defaults(default_log_levels=[
    'amqplib=WARN',
    'amqp=WARN',
    'boto=WARN',
    'eventlet.wsgi.server=WARN',
    'iso8601=WARN',
    'kazoo.client=WARN',
    'keystone=INFO',
    'keystonemiddleware.auth_token=INFO',
    'oslo_messaging=WARN',
    'oslo.messaging=INFO',
    'oslo_service.loopingcall=WARN',
    'sqlalchemy=WARN',
    'stevedore=WARN',
    'suds=INFO',
])

# Set some Oslo RPC defaults
messaging.set_transport_defaults('designate')

# Set some Oslo Oslo Concurrency defaults
lockutils.set_defaults(lock_path='$state_path')

cfg.CONF.register_opts(designate_opts)
