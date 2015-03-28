# Copyright (c) 2014 Rackspace Hosting
#
# Author: Betsy Luzader <betsy.luzader@rackspace.com>
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
from designate import utils
from designate.objects import base


class Pool(base.DictObjectMixin, base.PersistentObjectMixin,
           base.DesignateObject):
    FIELDS = {
        'name': {
            'schema': {
                'type': 'string',
                'description': 'Pool name',
                'maxLength': 50,
            },
            'immutable': True,
            'required': True
        },
        'description': {
            'schema': {
                'type': ['string', 'null'],
                'description': 'Description for the pool',
                'maxLength': 160
            }
        },
        'tenant_id': {
            'schema': {
                'type': ['string', 'null'],
                'description': 'Project identifier',
                'maxLength': 36,
            },
            'immutable': True
        },
        'provisioner': {
            'schema': {
                'type': ['string', 'null'],
                'description': 'Provisioner used for this pool',
                'maxLength': 160
            }
        },
        'attributes': {
            'relation': True,
            'relation_cls': 'PoolAttributeList',
        },
        'ns_records': {
            'relation': True,
            'relation_cls': 'PoolNsRecordList',
            'required': True
        },
        'nameservers': {
            'relation': True,
            'relation_cls': 'PoolNameserverList'
        },
        'targets': {
            'relation': True,
            'relation_cls': 'PoolTargetList'
        },
        'also_notifies': {
            'relation': True,
            'relation_cls': 'PoolAlsoNotifiesList'
        },
    }

    @classmethod
    def from_config(cls, CONF):
        pool_id = CONF['service:pool_manager'].pool_id

        pool_target_ids = CONF['pool:%s' % pool_id].targets
        pool_nameserver_ids = CONF['pool:%s' % pool_id].nameservers
        pool_also_notifies = CONF['pool:%s' % pool_id].also_notifies

        # Build Base Pool
        pool = {
            'id': pool_id,
            'description': 'Pool built from configuration on %s' % CONF.host,
            'targets': [],
            'nameservers': [],
            'also_notifies': [],
        }

        # Build Pool Also Notifies
        for pool_also_notify in pool_also_notifies:
            host, port = utils.split_host_port(pool_also_notify)
            pool['also_notifies'].append({
                'host': host,
                'port': port,
            })

        # Build Pool Targets
        for pool_target_id in pool_target_ids:
            pool_target_group = 'pool_target:%s' % pool_target_id

            pool_target = {
                'id': pool_target_id,
                'type': CONF[pool_target_group].type,
                'masters': [],
                'options': [],
            }

            # Build Pool Target Masters
            for pool_target_master in CONF[pool_target_group].masters:
                host, port = utils.split_host_port(pool_target_master)
                pool_target['masters'].append({
                    'host': host,
                    'port': port,
                })

            # Build Pool Target Options
            for k, v in CONF[pool_target_group].options.items():
                pool_target['options'].append({
                    'key': k,
                    'value': v,
                })

            pool['targets'].append(pool_target)

        # Build Pool Nameservers
        for pool_nameserver_id in pool_nameserver_ids:
            pool_nameserver_group = 'pool_nameserver:%s' % pool_nameserver_id

            pool_nameserver = {
                'id': pool_nameserver_id,
                'host': CONF[pool_nameserver_group].host,
                'port': CONF[pool_nameserver_group].port,
            }

            pool['nameservers'].append(pool_nameserver)

        return cls.from_dict(pool)


class PoolList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = Pool
