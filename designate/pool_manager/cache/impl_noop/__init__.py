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
from designate import exceptions
from designate.pool_manager.cache import base as cache_base


class NoopPoolManagerCache(cache_base.PoolManagerCache):
    __plugin_name__ = 'noop'

    def __init__(self):
        super(NoopPoolManagerCache, self).__init__()

    def get_name(self):
        return self.name

    def clear(self, context, pool_manager_status):
        pass

    def store(self, context, pool_manager_status):
        pass

    def retrieve(self, context, nameserver_id, domain_id, action):
        raise exceptions.PoolManagerStatusNotFound
