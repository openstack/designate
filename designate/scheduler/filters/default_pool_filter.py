# Copyright 2016 Hewlett Packard Enterprise Development Company, L.P.
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


class DefaultPoolFilter(base.Filter):
    """This filter will always return the default pool specified in the
    designate config file

    .. warning::

        This should be used as the only filter, as it will always return the
        same thing - a :class:`designate.objects.pool.PoolList` with a single
        :class:`designate.objects.pool.Pool`
    """

    name = 'default_pool'
    """Name to enable in the ``[designate:central:scheduler].filters`` option
    list
    """

    def filter(self, context, pools, zone):
        pools = objects.PoolList()
        pools.append(
            objects.Pool(id=CONF['service:central'].default_pool_id))
        return pools
