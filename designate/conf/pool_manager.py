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
from oslo_config import cfg
from oslo_db import options

POOL_MANAGER_GROUP = cfg.OptGroup(
    name='service:pool_manager',
    title="Configuration for Pool Manager Service"
)

POOL_MANAGER_SQLALCHEMY_GROUP = cfg.OptGroup(
    name='pool_manager_cache:sqlalchemy',
    title="Configuration for SQLAlchemy Pool Manager Cache"
)

POOL_MANAGER_MEMCACHE_GROUP = cfg.OptGroup(
    name='pool_manager_cache:memcache',
    title="Configuration for memcache Pool Manager Cache"
)

POOL_MANAGER_OPTS = [
    cfg.IntOpt('workers',
               help='Number of Pool Manager worker processes to spawn'),
    cfg.IntOpt('threads', default=1000,
               help='Number of Pool Manager greenthreads to spawn'),
    cfg.StrOpt('pool_id', default='794ccc2c-d751-44fe-b57f-8894c9f5c842',
               help='The ID of the pool managed by this instance of the '
                    'Pool Manager'),
    cfg.IntOpt('threshold_percentage', default=100,
               help='The percentage of servers requiring a successful update '
                    'for a zone change to be considered active',
               deprecated_for_removal=True,
               deprecated_reason='Migrated to designate-worker'),
    cfg.IntOpt('poll_timeout', default=30,
               help='The time to wait for a response from a server',
               deprecated_for_removal=True,
               deprecated_reason='Migrated to designate-worker'),
    cfg.IntOpt('poll_retry_interval', default=15,
               help='The time between retrying to send a request and '
                    'waiting for a response from a server',
               deprecated_for_removal=True,
               deprecated_reason='Migrated to designate-worker'),
    cfg.IntOpt('poll_max_retries', default=10,
               help='The maximum number of times to retry sending a request '
                    'and wait for a response from a server',
               deprecated_for_removal=True,
               deprecated_reason='Migrated to designate-worker'),
    cfg.IntOpt('poll_delay', default=5,
               help='The time to wait before sending the first request '
                    'to a server',
               deprecated_for_removal=True,
               deprecated_reason='Migrated to designate-worker'),
    cfg.BoolOpt('enable_recovery_timer', default=True,
                help='The flag for the recovery timer'),
    cfg.IntOpt('periodic_recovery_interval', default=120,
               help='The time between recovering from failures'),
    cfg.BoolOpt('enable_sync_timer', default=True,
                help='The flag for the sync timer'),
    cfg.IntOpt('periodic_sync_interval', default=1800,
               help='The time between synchronizing the servers with storage'),
    cfg.IntOpt('periodic_sync_seconds', default=21600,
               help='Zones Updated within last N seconds will be syncd.'
                    'Use an empty value to sync all zones.'),
    cfg.IntOpt('periodic_sync_max_attempts', default=3,
               help='Number of attempts to update a zone during sync'),
    cfg.IntOpt('periodic_sync_retry_interval', default=30,
               help='Interval between zone update attempts during sync'),
    cfg.StrOpt('cache_driver', default='memcache',
               help='The cache driver to use'),
    cfg.StrOpt('topic', default='pool_manager',
               help='RPC topic name for pool-manager'),
]

POOL_MANAGER_MEMCACHE_OPTS = [
    cfg.ListOpt('memcached_servers',
                help='Memcached servers or None for in process cache.'),
    cfg.IntOpt('expiration', default=3600,
               help='Time in seconds to expire cache.'),
]


def register_opts(conf):
    conf.register_group(POOL_MANAGER_GROUP)
    conf.register_opts(POOL_MANAGER_OPTS,
                       group=POOL_MANAGER_GROUP)
    conf.register_group(POOL_MANAGER_SQLALCHEMY_GROUP)
    conf.register_opts(options.database_opts,
                       group=POOL_MANAGER_SQLALCHEMY_GROUP)
    conf.register_group(POOL_MANAGER_MEMCACHE_GROUP)
    conf.register_opts(POOL_MANAGER_MEMCACHE_OPTS,
                       group=POOL_MANAGER_MEMCACHE_GROUP)


def list_opts():
    return {
        POOL_MANAGER_GROUP: POOL_MANAGER_OPTS,
        POOL_MANAGER_MEMCACHE_GROUP: POOL_MANAGER_MEMCACHE_OPTS,
        POOL_MANAGER_SQLALCHEMY_GROUP: options.database_opts,
    }
