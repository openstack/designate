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


class FloatingIPAPIv2Adapter(base.APIv2Adapter):
    ADAPTER_OBJECT = objects.FloatingIP
    MODIFICATIONS = {
        'fields': {
            "id": {
                'rename': 'key'
            },
            "description": {
                'read_only': False
            },
            "address": {},
            "ptrdname": {
                'read_only': False
            },
            "ttl": {
                'read_only': False
            },
            "action": {
                "read_only": True,
            },
            "status": {
                "read_only": True
            }
        },
        'options': {
            'links': True,
            'resource_name': 'floatingip',
            'collection_name': 'floatingips',
        }
    }

    @classmethod
    def _get_resource_links(cls, obj, request):
        return {
            'self': '{}{}/{}'.format(
                cls._get_base_url(request),
                cls._get_path(request),
                obj.key
            )
        }


class FloatingIPListAPIv2Adapter(base.APIv2Adapter):
    ADAPTER_OBJECT = objects.FloatingIPList
    MODIFICATIONS = {
        'options': {
            'links': True,
            'resource_name': 'floatingip',
            'collection_name': 'floatingips',
        }
    }
