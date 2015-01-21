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
from oslo.config import cfg
from oslo_db import options
from oslo_log import log as logging

from designate import exceptions
from designate import objects
from designate.pool_manager.cache import base as cache_base
from designate.sqlalchemy import base as sqlalchemy_base
from designate.pool_manager.cache.impl_sqlalchemy import tables


LOG = logging.getLogger(__name__)

cfg.CONF.register_group(cfg.OptGroup(
    name='pool_manager_cache:sqlalchemy',
    title="Configuration for SQLAlchemy Pool Manager Cache"
))

cfg.CONF.register_opts(options.database_opts,
                       group='pool_manager_cache:sqlalchemy')


class SQLAlchemyPoolManagerCache(sqlalchemy_base.SQLAlchemy,
                                 cache_base.PoolManagerCache):
    """SQLAlchemy connection"""
    __plugin_name__ = 'sqlalchemy'

    def __init__(self):
        super(SQLAlchemyPoolManagerCache, self).__init__()

    def get_name(self):
        return self.name

    def _find_pool_manager_statuses(self, context, criterion, one=False,
                                    marker=None, limit=None, sort_key=None,
                                    sort_dir=None):
        return self._find(
            context, tables.pool_manager_statuses, objects.PoolManagerStatus,
            objects.PoolManagerStatusList,
            exceptions.PoolManagerStatusNotFound, criterion, one, marker,
            limit, sort_key, sort_dir)

    def create_pool_manager_status(self, context, pool_manager_status):
        return self._create(
            tables.pool_manager_statuses, pool_manager_status,
            exceptions.DuplicatePoolManagerStatus)

    def get_pool_manager_status(self, context, pool_manager_status_id):
        return self._find_pool_manager_statuses(
            context, {'id': pool_manager_status_id}, one=True)

    def find_pool_manager_statuses(self, context, criterion=None, marker=None,
                                   limit=None, sort_key=None, sort_dir=None):
        return self._find_pool_manager_statuses(
            context, criterion, marker=marker, limit=limit, sort_key=sort_key,
            sort_dir=sort_dir)

    def find_pool_manager_status(self, context, criterion):
        return self._find_pool_manager_statuses(context, criterion, one=True)

    def update_pool_manager_status(self, context, pool_manager_status):
        return self._update(
            context, tables.pool_manager_statuses, pool_manager_status,
            exceptions.DuplicatePoolManagerStatus,
            exceptions.PoolManagerStatusNotFound)

    def delete_pool_manager_status(self, context, pool_manager_status_id):
        pool_manager_status = self._find_pool_manager_statuses(
            context, {'id': pool_manager_status_id}, one=True)

        return self._delete(
            context, tables.pool_manager_statuses, pool_manager_status,
            exceptions.PoolManagerStatusNotFound)
