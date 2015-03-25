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
from designate.objects import base


class PoolManagerStatus(base.DictObjectMixin, base.PersistentObjectMixin,
                        base.DesignateObject):
    FIELDS = {
        'nameserver_id': {
            'schema': {
                'type': 'string',
                'format': 'uuid',
            },
            'required': True
        },
        'domain_id': {
            'schema': {
                'type': 'string',
                'format': 'uuid',
            },
            'required': True},
        'status': {
            'schema': {
                'type': ['string', 'null'],
                'enum': ['ACTIVE', 'PENDING', 'ERROR'],
            },
        },
        'serial_number': {
            'schema': {
                'type': 'integer',
                'minimum': 0,
                'maximum': 4294967295,
            },
        },
        'action': {
            'schema': {
                'type': 'string',
                'enum': ['CREATE', 'DELETE', 'UPDATE', 'NONE'],
            },
        }
    }


class PoolManagerStatusList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = PoolManagerStatus
