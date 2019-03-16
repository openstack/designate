# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hpe.com>
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

from designate.producer import tasks

PRODUCER_GROUP = cfg.OptGroup(
    name='service:producer',
    title="Configuration for Producer Service"
)

ZONE_MANAGER_GROUP = cfg.OptGroup(
    name='service:zone_manager', title="Configuration for Zone Manager Service"
)

PRODUCER_OPTS = [
    cfg.IntOpt('workers',
               help='Number of Producer worker processes to spawn'),
    cfg.IntOpt('threads', default=1000,
               help='Number of Producer greenthreads to spawn'),
    cfg.ListOpt('enabled_tasks',
                help='Enabled tasks to run'),
    cfg.StrOpt('storage-driver', default='sqlalchemy',
               help='The storage driver to use'),
    cfg.BoolOpt('export-synchronous', default=True,
                help='Whether to allow synchronous zone exports',
                deprecated_for_removal=True,
                deprecated_reason='Migrated to designate-worker'),
]

ZONE_MANAGER_OPTS = [
    cfg.IntOpt('workers',
               help='Number of Zone Manager worker processes to spawn',
               deprecated_for_removal=True,
               deprecated_reason='Migrated to designate-worker'),
    cfg.IntOpt('threads', default=1000,
               help='Number of Zone Manager greenthreads to spawn',
               deprecated_for_removal=True,
               deprecated_reason='Migrated to designate-worker'),
    cfg.ListOpt('enabled_tasks',
                help='Enabled tasks to run',
                deprecated_for_removal=True,
                deprecated_reason='Migrated to designate-worker'),
    cfg.StrOpt('storage-driver', default='sqlalchemy',
               help='The storage driver to use',
               deprecated_for_removal=True,
               deprecated_reason='Migrated to designate-worker'),
    cfg.BoolOpt('export-synchronous', default=True,
                help='Whether to allow synchronous zone exports',
                deprecated_for_removal=True,
                deprecated_reason='Migrated to designate-worker'),
]

# NOTE(trungnv): Get [producer_task:zone_purge] config
zone_purge_opts = tasks.DeletedZonePurgeTask.get_cfg_opts()[0][1]
zone_purge_old_group = tasks.DeletedZonePurgeTask.get_cfg_opts()[0][0].name
zone_purge_group = cfg.OptGroup(zone_purge_old_group)

# NOTE(trungnv): Get [producer_task:periodic_exists] config
periodic_exists_opts = tasks.PeriodicExistsTask.get_cfg_opts()[0][1]
periodic_exists_old_group = tasks.PeriodicExistsTask.get_cfg_opts()[0][0].name
periodic_exists_group = cfg.OptGroup(periodic_exists_old_group)

# NOTE(trungnv): Get [producer_task:periodic_secondary_refresh] config
psr_opts = tasks.PeriodicSecondaryRefreshTask.get_cfg_opts()[0][1]
psr_old_group = tasks.PeriodicSecondaryRefreshTask.get_cfg_opts()[0][0].name
psr_group = cfg.OptGroup(psr_old_group)

# NOTE(trungnv): Get [producer_task:delayed_notify] config
delayed_notify_opts = \
    tasks.PeriodicGenerateDelayedNotifyTask.get_cfg_opts()[0][1]
delayed_notify_old_group = \
    tasks.PeriodicGenerateDelayedNotifyTask.get_cfg_opts()[0][0].name
delayed_notify_group = cfg.OptGroup(delayed_notify_old_group)

# NOTE(trungnv): Get [producer_task:worker_periodic_recovery] config
wpr_opts = tasks.WorkerPeriodicRecovery.get_cfg_opts()[0][1]
wpr_old_group = tasks.WorkerPeriodicRecovery.get_cfg_opts()[0][0].name
wpr_group = cfg.OptGroup(wpr_old_group)


def register_opts(conf):
    conf.register_group(PRODUCER_GROUP)
    conf.register_opts(PRODUCER_OPTS, group=PRODUCER_GROUP)
    conf.register_group(ZONE_MANAGER_GROUP)
    conf.register_opts(ZONE_MANAGER_OPTS, group=ZONE_MANAGER_GROUP)
    conf.register_group(zone_purge_group)
    conf.register_opts(zone_purge_opts, group=zone_purge_group)
    conf.register_group(periodic_exists_group)
    conf.register_opts(periodic_exists_opts, group=periodic_exists_group)
    conf.register_group(psr_group)
    conf.register_opts(psr_opts, group=psr_group)
    conf.register_group(delayed_notify_group)
    conf.register_opts(delayed_notify_opts, group=delayed_notify_group)
    conf.register_group(wpr_group)
    conf.register_opts(wpr_opts, group=wpr_group)


def list_opts():
    return {
        PRODUCER_GROUP: PRODUCER_OPTS,
        ZONE_MANAGER_GROUP: ZONE_MANAGER_OPTS,
        zone_purge_group: zone_purge_opts,
        periodic_exists_group: periodic_exists_opts,
        psr_group: psr_opts,
        delayed_notify_group: delayed_notify_opts,
        wpr_group: wpr_opts,
    }
