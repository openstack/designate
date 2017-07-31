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

CONF = cfg.CONF

producer_group = cfg.OptGroup(
    name='service:producer', title="Configuration for Producer Service"
)

OPTS = [
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

# TODO(timsim): Remove these when zone-manager is removed
zone_manager_group = cfg.OptGroup(
    name='service:zone_manager', title="Configuration for Zone Manager Service"
)

ZONEMGROPTS = [
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


cfg.CONF.register_group(producer_group)
cfg.CONF.register_opts(OPTS, group=producer_group)

cfg.CONF.register_group(zone_manager_group)
cfg.CONF.register_opts(ZONEMGROPTS, group=zone_manager_group)

# NOTE(trungnv): Get [producer_task:zone_purge] config
zone_purge_opts = tasks.DeletedZonePurgeTask.get_cfg_opts()[0][1]
zone_purge_old_group = tasks.DeletedZonePurgeTask.get_cfg_opts()[0][0].name
zone_purge_group = cfg.OptGroup(zone_purge_old_group)
cfg.CONF.register_group(zone_purge_group)
cfg.CONF.register_opts(zone_purge_opts, group=zone_purge_group)

# NOTE(trungnv): Get [producer_task:periodic_exists] config
periodic_exists_opts = tasks.PeriodicExistsTask.get_cfg_opts()[0][1]
periodic_exists_old_group = tasks.PeriodicExistsTask.get_cfg_opts()[0][0].name
periodic_exists_group = cfg.OptGroup(periodic_exists_old_group)
cfg.CONF.register_group(periodic_exists_group)
cfg.CONF.register_opts(periodic_exists_opts, group=periodic_exists_group)

# NOTE(trungnv): Get [producer_task:periodic_secondary_refresh] config
psr_opts = tasks.PeriodicSecondaryRefreshTask.get_cfg_opts()[0][1]
psr_old_group = tasks.PeriodicSecondaryRefreshTask.get_cfg_opts()[0][0].name
psr_group = cfg.OptGroup(psr_old_group)
cfg.CONF.register_group(psr_group)
cfg.CONF.register_opts(psr_opts, group=psr_group)

# NOTE(trungnv): Get [producer_task:delayed_notify] config
delayed_notify_opts =\
    tasks.PeriodicGenerateDelayedNotifyTask.get_cfg_opts()[0][1]
delayed_notify_old_group =\
    tasks.PeriodicGenerateDelayedNotifyTask.get_cfg_opts()[0][0].name
delayed_notify_group = cfg.OptGroup(delayed_notify_old_group)
cfg.CONF.register_group(delayed_notify_group)
cfg.CONF.register_opts(delayed_notify_opts, group=delayed_notify_group)

# NOTE(trungnv): Get [producer_task:worker_periodic_recovery] config
wpr_opts = tasks.WorkerPeriodicRecovery.get_cfg_opts()[0][1]
wpr_old_group = tasks.WorkerPeriodicRecovery.get_cfg_opts()[0][0].name
wpr_group = cfg.OptGroup(wpr_old_group)
cfg.CONF.register_group(wpr_group)
cfg.CONF.register_opts(wpr_opts, group=wpr_group)


def list_opts():
    yield producer_group, OPTS
    yield zone_manager_group, ZONEMGROPTS
    yield zone_purge_group, zone_purge_opts
    yield periodic_exists_group, periodic_exists_opts
    yield psr_group, psr_opts
    yield delayed_notify_group, delayed_notify_opts
    yield wpr_group, wpr_opts
