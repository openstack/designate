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
    def create_pool_manager_status(self, context, pool_manager_status):
        """
        Create a pool manager status.

        :param context: Security context information
        :param pool_manager_status: Pool manager status object to create
        """

    @abc.abstractmethod
    def get_pool_manager_status(self, context, pool_manager_status_id):
        """
        Get a pool manager status by ID.

        :param context: Security context information
        :param pool_manager_status_id: Pool manager status ID to get
        """

    @abc.abstractmethod
    def find_pool_manager_statuses(self, context, criterion=None, marker=None,
                                   limit=None, sort_key=None, sort_dir=None):
        """
        Find pool manager statuses.

        :param context: Security context information
        :param criterion: Criteria to filter by
        :param marker: Resource ID from which after the requested page will
                       start after
        :param limit: Integer limit of objects of the page size after the
                      marker
        :param sort_key: Key from which to sort after
        :param sort_dir: Direction to sort after using sort_key
        """

    @abc.abstractmethod
    def find_pool_manager_status(self, context, criterion):
        """
        Find a single pool manager status.

        :param context: Security context information
        :param criterion: Criteria to filter by
        """

    @abc.abstractmethod
    def update_pool_manager_status(self, context, pool_manager_status):
        """
        Update a pool manager status

        :param context: Security context information
        :param pool_manager_status: Pool manager status object to update
        """

    @abc.abstractmethod
    def delete_pool_manager_status(self, context, pool_manager_status_id):
        """
        Delete a pool manager status

        :param context: Security context information
        :param pool_manager_status_id: Pool manager status ID to delete
        """
