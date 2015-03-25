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
import abc

import six

from designate.plugin import DriverPlugin


@six.add_metaclass(abc.ABCMeta)
class PoolManagerCache(DriverPlugin):

    """Base class for cache plugins"""
    __plugin_ns__ = 'designate.pool_manager.cache'
    __plugin_type__ = 'pool_manager_cache'

    @abc.abstractmethod
    def clear(self, context, pool_manager_status):
        """

        Clear the pool manager status object from the cache.

        :param context:  Security context information
        :param pool_manager_status: Pool manager status object to clear
        """

    @abc.abstractmethod
    def store(self, context, pool_manager_status):
        """

        Store the pool manager status object in the cache.

        :param context: Security context information
        :param pool_manager_status: Pool manager status object to store
        :return:
        """

    @abc.abstractmethod
    def retrieve(self, context, nameserver_id, domain_id, action):
        """

        Retrieve the pool manager status object.

        :param context: Security context information
        :param nameserver_id: the nameserver ID of the pool manager status
                              object
        :param domain_id: the domain ID of the pool manger status object
        :param action: the action of the pool manager status object
        :return: the pool manager status object
        """
