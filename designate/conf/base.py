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
import socket

from oslo_config import cfg

import designate

DESIGNATE_OPTS = [
    cfg.StrOpt('host', default=socket.gethostname(),
               sample_default='current_hostname',
               help='Name of this node'),
    cfg.StrOpt(
        'pybasedir',
        sample_default='<Path>',
        default=designate.BASE_PATH,
        help='Directory where the designate python module is installed'
    ),
    cfg.StrOpt('state-path', default='/var/lib/designate',
               help='Top-level directory for maintaining designate\'s state'),

    cfg.ListOpt(
        'allowed_remote_exmods',
        default=[],
        help="Additional modules that contains allowed RPC exceptions.",
        deprecated_name='allowed_rpc_exception_modules'),

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
                         'PTR', 'SSHFP', 'SOA', 'NAPTR', 'CAA']),

    # TCP Settings
    cfg.IntOpt('backlog',
               default=4096,
               help="Number of backlog requests to configure the socket with"),
    cfg.IntOpt('tcp_keepidle',
               default=600,
               help="Sets the value of TCP_KEEPIDLE in seconds for each "
                    "server socket. Not supported on OS X."),

    # Root Helper
    cfg.StrOpt('root-helper',
               default='sudo designate-rootwrap /etc/designate/rootwrap.conf',
               help='designate-rootwrap configuration'),

    # Memcached
    cfg.ListOpt('memcached_servers',
                help='Memcached servers or None for in process cache.'),

    cfg.StrOpt('network_api', default='neutron', help='Which API to use.'),

    # Notifications
    cfg.BoolOpt('notify_api_faults', default=False,
                help='Send notifications if there\'s a failure in the API.'),
    cfg.StrOpt('notification-plugin', default='default',
               help='The notification plugin to use'),

    # Quota
    cfg.StrOpt('quota-driver', default='storage', help='Quota driver to use'),
    cfg.IntOpt('quota-zones', default=10,
               help='Number of zones allowed per tenant'),
    cfg.IntOpt('quota-zone-recordsets', default=500,
               help='Number of recordsets allowed per zone'),
    cfg.IntOpt('quota-zone-records', default=500,
               help='Number of records allowed per zone'),
    cfg.IntOpt('quota-recordset-records', default=20,
               help='Number of records allowed per recordset'),
    cfg.IntOpt('quota-api-export-size', default=1000,
               help='Number of recordsets allowed in a zone export'),
]


def register_opts(conf):
    conf.register_opts(DESIGNATE_OPTS)


def list_opts():
    return {
        'DEFAULT': DESIGNATE_OPTS
    }
