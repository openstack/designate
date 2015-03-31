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
    __plugin_name__ = 'sqlalchemy'

    def __init__(self):
        super(SQLAlchemyPoolManagerCache, self).__init__()

    def get_name(self):
        return self.name

    def clear(self, context, pool_manager_status):
        # If there is no id retrieve the relevant pool manager status
        if not pool_manager_status.id:
            pool_manager_status = self.retrieve(
                context, pool_manager_status.nameserver_id,
                pool_manager_status.domain_id, pool_manager_status.action)
        self._delete(
            context, tables.pool_manager_statuses, pool_manager_status,
            exceptions.PoolManagerStatusNotFound)

    def store(self, context, pool_manager_status):
        if pool_manager_status.id:
            self._update(
                context, tables.pool_manager_statuses, pool_manager_status,
                exceptions.DuplicatePoolManagerStatus,
                exceptions.PoolManagerStatusNotFound)
        else:
            self._create(
                tables.pool_manager_statuses, pool_manager_status,
                exceptions.DuplicatePoolManagerStatus)

    def retrieve(self, context, nameserver_id, domain_id, action):
        criterion = {
            'nameserver_id': nameserver_id,
            'domain_id': domain_id,
            'action': action
        }
        return self._find(
            context, tables.pool_manager_statuses, objects.PoolManagerStatus,
            objects.PoolManagerStatusList,
            exceptions.PoolManagerStatusNotFound, criterion, one=True)
