# Copyright 2014 eBay Inc.
#
# Author: Ron Rickard <rrickard@ebaysf.com>
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

from designate.central import rpcapi as central_rpcapi
from designate.mdns import rpcapi as mdns_rpcapi

cfg.CONF.register_group(cfg.OptGroup(
    name='service:pool_manager', title="Configuration for Pool Manager Service"
))

OPTS = [
    cfg.IntOpt('workers', default=None,
               help='Number of Pool Manager worker processes to spawn'),
    cfg.StrOpt('pool-id', default='794ccc2c-d751-44fe-b57f-8894c9f5c842',
               help='The ID of the pool managed by this instance of the '
                    'Pool Manager'),
    cfg.IntOpt('threshold-percentage', default=100,
               help='The percentage of servers requiring a successful update '
                    'for a domain change to be considered active'),
    cfg.IntOpt('poll-timeout', default=30,
               help='The time to wait for a response from a server'),
    cfg.IntOpt('poll-retry-interval', default=2,
               help='The time between retrying to send a request and '
                    'waiting for a response from a server'),
    cfg.IntOpt('poll-max-retries', default=3,
               help='The maximum number of times to retry sending a request '
                    'and wait for a response from a server'),
    cfg.IntOpt('poll-delay', default=1,
               help='The time to wait before sending the first request '
                    'to a server'),
    cfg.IntOpt('periodic-sync-interval', default=120,
               help='The time between synchronizing the servers with Storage'),
    cfg.StrOpt('cache-driver', default='sqlalchemy',
               help='The cache driver to use'),
]

cfg.CONF.register_opts(OPTS, group='service:pool_manager')

CENTRAL_API = None
MDNS_API = None


def get_central_api():
    """
    The rpc.get_client() which is called upon the API object initialization
    will cause a assertion error if the designate.rpc.TRANSPORT isn't setup by
    rpc.init() before.

    This fixes that by creating the rpcapi when demanded.
    """
    global CENTRAL_API
    if not CENTRAL_API:
        CENTRAL_API = central_rpcapi.CentralAPI()
    return CENTRAL_API


def get_mdns_api():
    """
    The rpc.get_client() which is called upon the API object initialization
    will cause a assertion error if the designate.rpc.TRANSPORT isn't setup by
    rpc.init() before.

    This fixes that by creating the rpcapi when demanded.
    """
    global MDNS_API
    if not MDNS_API:
        MDNS_API = mdns_rpcapi.MdnsAPI()
    return MDNS_API
