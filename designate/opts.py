# Copyright 2017 Fujitsu Ltd.
#
# Author: Nguyen Van Trung <trungnv@vn.fujitsu.com>
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

from oslo_db import options

from designate import central
import designate
import designate.network_api
from designate.network_api import neutron
from designate import metrics
from designate.notification_handler import neutron as neutrons
from designate import notifications
from designate.notification_handler import nova
from designate.pool_manager.cache import impl_memcache
from designate.pool_manager.cache import impl_sqlalchemy as impl_sql
from designate import quota
from designate import scheduler
from designate.storage import impl_sqlalchemy as ssql
from designate import dnsutils
from designate import coordination as co
from designate import utils
from designate import service
from designate import service_status as stt


# TODO(trungnv): creating and auto-genconfig for:
# Hook Points.
def list_opts():
    yield None, designate.designate_opts
    yield None, designate.network_api.neutron_opts
    yield neutron.neutron_group, neutron.neutron_opts
    yield metrics.metrics_group, metrics.metrics_opts
    yield neutrons.neutron_group, neutrons.neutron_opts
    yield nova.nova_group, nova.nova_opts
    yield None, notifications.notify_opts
    yield impl_memcache.memcache_group, impl_memcache.OPTS
    yield impl_sql.sqlalchemy_group, impl_sql.options.database_opts
    yield None, quota.quota_opts
    yield central.central_group, scheduler.scheduler_opts
    yield ssql.storage_group, options.database_opts
    yield None, dnsutils.util_opts
    yield co.coordination_group, co.coordination_opts
    yield None, utils.helper_opts
    yield utils.proxy_group, utils.proxy_opts
    yield None, service.wsgi_socket_opts
    yield stt.heartbeat_group, stt.heartbeat_opts
