# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from designate import objects
from designate.objects.adapters.api_v2 import base


class PoolAPIv2Adapter(base.APIv2Adapter):
    ADAPTER_OBJECT = objects.Pool
    MODIFICATIONS = {
        'fields': {
            'id': {},
            'project_id': {
                'immutable': True,
                'rename': 'tenant_id'
            },
            'name': {
                'read_only': False
            },
            'description': {
                'read_only': False
            },
            'attributes': {
                'read_only': False
            },
            'ns_records': {
                'read_only': False
            },
            "created_at": {},
            "updated_at": {},
        },
        'options': {
            'links': True,
            'resource_name': 'pool',
            'collection_name': 'pools',
        }
    }


class PoolListAPIv2Adapter(base.APIv2Adapter):
    ADAPTER_OBJECT = objects.PoolList
    MODIFICATIONS = {
        'options': {
            'links': True,
            'resource_name': 'pool',
            'collection_name': 'pools',
        }
    }
