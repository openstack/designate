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
import abc

from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class Filter(metaclass=abc.ABCMeta):
    """This is the base class used for filtering Pools.

    This class should implement a single public function
    :func:`filter` which accepts
    a :class:`designate.objects.pool.PoolList` and returns a
    :class:`designate.objects.pool.PoolList`
    """

    name = ''

    def __init__(self, storage):
        self.storage = storage
        LOG.debug('Loaded %s filter in chain' % self.name)

    @abc.abstractmethod
    def filter(self, context, pools, zone):
        """Filter list of supplied pools based on attributes in the request

        :param context: :class:`designate.context.DesignateContext` - Context
            Object from request
        :param pools: :class:`designate.objects.pool.PoolList` - List of pools
            to choose from
        :param zone: :class:`designate.objects.zone.Zone` - Zone to be created
        :return: :class:`designate.objects.pool.PoolList` - Filtered list of
            Pools
        """
