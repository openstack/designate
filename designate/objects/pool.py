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
            'required': True
        },
        'nameservers': {
            'relation': True,
            'relation_cls': 'NameServerList',
            'required': True
        },
    }


class PoolList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = Pool
