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

from designate import exceptions
from designate import objects
from designate.openstack.common import memorycache
from designate.pool_manager.cache import base as cache_base

cfg.CONF.register_group(cfg.OptGroup(
    name='pool_manager_cache:memcache',
    title="Configuration for memcache Pool Manager Cache"
))


OPTS = [
    cfg.IntOpt('expiration', default=3600,
               help='Time in seconds to expire cache.')
]
OPTS.extend(memorycache.memcache_opts)

cfg.CONF.register_opts(OPTS,
                       group='pool_manager_cache:memcache')

DEFAULT_STATUS = 'NONE'


class MemcachePoolManagerCache(cache_base.PoolManagerCache):
    __plugin_name__ = 'memcache'

    def __init__(self):
        super(MemcachePoolManagerCache, self).__init__()

        self.cache = memorycache.get_client(
            cfg.CONF['pool_manager_cache:memcache'].memcached_servers)
        self.expiration = cfg.CONF['pool_manager_cache:memcache'].expiration

    def get_name(self):
        return self.name

    def clear(self, context, pool_manager_status):
        status_key = self._build_status_key(pool_manager_status)
        self.cache.delete(status_key)

        serial_number_key = self._build_serial_number_key(pool_manager_status)
        self.cache.delete(serial_number_key)

    def store(self, context, pool_manager_status):
        status_key = self._build_status_key(pool_manager_status)

        # TODO(vinod): memcache does not seem to store None as the values
        # Investigate if we can do a different default value for status
        if pool_manager_status.status:
            self.cache.set(
                status_key, pool_manager_status.status, self.expiration)
        else:
            self.cache.set(status_key, DEFAULT_STATUS, self.expiration)

        serial_number_key = self._build_serial_number_key(pool_manager_status)
        self.cache.set(
            serial_number_key, pool_manager_status.serial_number,
            self.expiration)

    def retrieve(self, context, nameserver_id, domain_id, action):
        values = {
            'nameserver_id': nameserver_id,
            'domain_id': domain_id,
            'action': action,
        }
        pool_manager_status = objects.PoolManagerStatus(**values)

        status_key = self._build_status_key(pool_manager_status)
        status = self.cache.get(status_key)
        if status is None:
            raise exceptions.PoolManagerStatusNotFound

        serial_number_key = self._build_serial_number_key(pool_manager_status)
        serial_number = self.cache.get(serial_number_key)
        if serial_number is None:
            raise exceptions.PoolManagerStatusNotFound

        pool_manager_status.serial_number = serial_number
        if status == DEFAULT_STATUS:
            pool_manager_status.status = None
        else:
            pool_manager_status.status = status

        return pool_manager_status

    @staticmethod
    def _status_key(pool_manager_status, tail):
        key = '{nameserver}-{domain}-{action}-{tail}'.format(
            nameserver=pool_manager_status.nameserver_id,
            domain=pool_manager_status.domain_id,
            action=pool_manager_status.action,
            tail=tail
        )
        return key.encode('utf-8')

    def _build_serial_number_key(self, pool_manager_status):
        return self._status_key(pool_manager_status, 'serial_number')

    def _build_status_key(self, pool_manager_status):
        return self._status_key(pool_manager_status, 'status')
