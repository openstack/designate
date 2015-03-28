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

CONF = cfg.CONF

CONF.register_group(cfg.OptGroup(
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
    cfg.BoolOpt('enable-recovery-timer', default=True,
                help='The flag for the recovery timer'),
    cfg.IntOpt('periodic-recovery-interval', default=120,
               help='The time between recovering from failures'),
    cfg.BoolOpt('enable-sync-timer', default=True,
                help='The flag for the sync timer'),
    cfg.IntOpt('periodic-sync-interval', default=300,
               help='The time between synchronizing the servers with Storage'),
    cfg.IntOpt('periodic-sync-seconds', default=None,
               help='Zones Updated within last N seconds will be syncd. Use '
                    'None to sync all zones.'),
    cfg.StrOpt('cache-driver', default='sqlalchemy',
               help='The cache driver to use'),
]

CONF.register_opts(OPTS, group='service:pool_manager')


def register_dynamic_pool_options():
    # Pool Options Registration Pass One

    # Find the Current Pool ID
    pool_id = CONF['service:pool_manager'].pool_id

    # Build the [pool:<id>] config section
    pool_group = cfg.OptGroup('pool:%s' % pool_id)

    pool_opts = [
        cfg.ListOpt('targets', default=[]),
        cfg.ListOpt('nameservers', default=[]),
        cfg.ListOpt('also_notifies', default=[]),
    ]

    CONF.register_group(pool_group)
    CONF.register_opts(pool_opts, group=pool_group)

    # Pool Options Registration Pass Two

    # Find the Current Pools Target ID's
    pool_target_ids = CONF['pool:%s' % pool_id].targets

    # Build the [pool_target:<id>] config sections
    pool_target_opts = [
        cfg.StrOpt('type'),
        cfg.ListOpt('masters', default=[]),
        cfg.DictOpt('options', default={}),
    ]

    for pool_target_id in pool_target_ids:
        pool_target_group = cfg.OptGroup('pool_target:%s' % pool_target_id)

        CONF.register_group(pool_target_group)
        CONF.register_opts(pool_target_opts, group=pool_target_group)

    # Find the Current Pools Nameserver ID's
    pool_nameserver_ids = CONF['pool:%s' % pool_id].nameservers

    # Build the [pool_nameserver:<id>] config sections
    pool_nameserver_opts = [
        cfg.StrOpt('host'),
        cfg.IntOpt('port'),
    ]

    for pool_nameserver_id in pool_nameserver_ids:
        pool_nameserver_group = cfg.OptGroup(
            'pool_nameserver:%s' % pool_nameserver_id)

        CONF.register_group(pool_nameserver_group)
        CONF.register_opts(pool_nameserver_opts, group=pool_nameserver_group)
