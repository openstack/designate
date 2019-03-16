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

CONF = cfg.CONF


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
        cfg.DictOpt('options', default={}, secret=True),
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
