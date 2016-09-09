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

from designate.objects.adapters.api_v2 import base
from designate import objects


class RecordAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.Record

    MODIFICATIONS = {
        'fields': {
            "data": {
                'read_only': False
            },
        },
        'options': {
            'links': False,
            'resource_name': 'record',
            'collection_name': 'records',
        }
    }

    @classmethod
    def _render_object(cls, record, *arg, **kwargs):
        return record.data

    @classmethod
    def _parse_object(cls, value, record_object, *args, **kwargs):
        record_object.data = value
        return record_object


class RecordListAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.RecordList

    MODIFICATIONS = {
        'options': {
            'links': False,
            'resource_name': 'record',
            'collection_name': 'records',
        }
    }

    @classmethod
    def _render_list(cls, record_list, *arg, **kwargs):
        list = []
        for record in record_list:
            list.append(record.data)
        return list
