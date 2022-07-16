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


class QuotaAPIv2Adapter(base.APIv2Adapter):
    ADAPTER_OBJECT = objects.Quota
    MODIFICATIONS = {
        'fields': {
            'resource': {
                'read_only': False
            },
            'hard_limit': {
                'read_only': False
            },
        },
        'options': {
            'links': True,
            'resource_name': 'quota',
            'collection_name': 'quotas',
        }
    }


class QuotaListAPIv2Adapter(base.APIv2Adapter):
    ADAPTER_OBJECT = objects.QuotaList
    MODIFICATIONS = {
        'options': {
            'links': True,
            'resource_name': 'quota',
            'collection_name': 'quotas',
        }
    }

    @classmethod
    def render_list(cls, list_objects, *args, **kwargs):
        r_list = {}
        for obj in list_objects:
            r_list[obj.resource] = obj.hard_limit
        return r_list

    @classmethod
    def parse_list(cls, values, output_object, *args, **kwargs):
        for key, value in values.items():
            # Add the object to the list
            output_object.append(
                cls.ADAPTER_OBJECT.LIST_ITEM_TYPE.from_dict(
                    {
                        'resource': key,
                        'hard_limit': value,
                    }
                )
            )
        return output_object
