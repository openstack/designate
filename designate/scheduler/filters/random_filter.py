# Copyright 2016 Hewlett-Packard Development Company, L.P.
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
import random

from oslo_log import log as logging

from designate.objects import PoolList
from designate.scheduler.filters import base

LOG = logging.getLogger(__name__)


class RandomFilter(base.Filter):
    """Randomly chooses one of the input pools if there are multiple
    ones supplied.

    .. note::

        This should be used as one of the last filters, as it reduces the
        supplied pool list to one.
    """
    name = 'random'
    """Name to enable in the ``[designate:central:scheduler].filters`` option
    list
    """

    def filter(self, context, pools, zone):
        if pools:
            new_pool_list = PoolList()
            new_pool_list.append(random.choice(pools))
            return new_pool_list
        return pools
