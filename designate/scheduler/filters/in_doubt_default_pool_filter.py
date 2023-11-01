# Copyright 2017 SAP SE
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
import designate.conf
from designate import objects
from designate.scheduler.filters import base


CONF = designate.conf.CONF


class InDoubtDefaultPoolFilter(base.Filter):
    """If the previous filter(s) didn't make a clear selection of one pool
    and if the default pool is in the set of multiple pools, this filter will
    select the default pool.

    This filter will pass through the pool list, if there are one or
    less pools available to schedule to, or if the default pool is
    not in the set of multiple pools.

    .. note::

        This should be used as one of the last filters.

    """

    name = 'in_doubt_default_pool'
    """Name to enable in the ``[designate:central:scheduler].filters`` option
    list
    """

    def filter(self, context, pools, zone):
        if len(pools) > 1:
            default_pool_id = CONF['service:central'].default_pool_id
            try:
                default_pool = self.storage.get_pool(context, default_pool_id)
            except Exception:
                return pools

            if default_pool in pools:
                pools = objects.PoolList()
                pools.append(default_pool)

        return pools
