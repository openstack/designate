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
from designate.pool_manager import rpcapi as pool_rpcapi

from oslo.config import cfg

cfg.CONF.register_group(cfg.OptGroup(
    name='service:mdns', title="Configuration for mDNS Service"
))

OPTS = [
    cfg.IntOpt('workers', default=None,
               help='Number of mdns worker processes to spawn'),
    cfg.StrOpt('host', default='0.0.0.0',
               help='mDNS Bind Host'),
    cfg.ListOpt('slave-nameserver-ips-and-ports', default=[],
                help='Ips and ports of slave nameservers that are notified of '
                     'zone changes. The format of each item in the list is'
                     '"ipaddress:port"'),
    cfg.IntOpt('notify-timeout', default=60,
               help='The number of seconds to wait before the notify query '
                    'times out.'),
    cfg.IntOpt('notify-retry-interval', default=2,
               help='The number of seconds to wait before retrying the notify'
                    'query.'),
    cfg.IntOpt('notify-retries', default=1,
               help='The number of retries of a notify to a slave '
                    'nameserver.  A notify-retries of 1 implies that on an '
                    'error after sending a NOTIFY, there would not be any '
                    'retries.  A 0 implies that NOTIFYs are not sent at all'),
    cfg.IntOpt('port', default=5354,
               help='mDNS Port Number'),
    cfg.IntOpt('tcp-backlog', default=100,
               help='mDNS TCP Backlog'),
    cfg.FloatOpt('tcp-recv-timeout', default=0.5,
                 help='mDNS TCP Receive Timeout'),
    cfg.StrOpt('storage-driver', default='sqlalchemy',
               help='The storage driver to use'),
]

cfg.CONF.register_opts(OPTS, group='service:mdns')


POOL_MANAGER_API = None


def get_pool_manager_api():
    """
    The rpc.get_client() which is called upon the API object initialization
    will cause a assertion error if the designate.rpc.TRANSPORT isn't setup by
    rpc.init() before.

    This fixes that by creating the rpcapi when demanded.
    """
    global POOL_MANAGER_API
    if not POOL_MANAGER_API:
        POOL_MANAGER_API = pool_rpcapi.PoolManagerAPI()
    return POOL_MANAGER_API
