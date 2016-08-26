# Copyright 2016 Hewlett-Packard Development Company, L.P.
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


class ServiceStatusAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.ServiceStatus

    MODIFICATIONS = {
        'fields': {
            "id": {},
            "hostname": {},
            "service_name": {},
            "status": {},
            "stats": {},
            "capabilities": {},
            "heartbeated_at": {},
            "created_at": {},
            "updated_at": {},
        },
        'options': {
            'links': True,
            'resource_name': 'service_status',
            'collection_name': 'service_statuses',
        }
    }

    @classmethod
    def _render_object(cls, object, *args, **kwargs):
        obj = super(ServiceStatusAPIv2Adapter, cls)._render_object(
            object, *args, **kwargs)

        obj['links']['self'] = \
            '%s/v2/%s/%s' % (cls.BASE_URI, 'service_statuses', obj['id'])

        return obj


class ServiceStatusListAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.ServiceStatusList

    MODIFICATIONS = {
        'options': {
            'links': True,
            'resource_name': 'service_status',
            'collection_name': 'service_statuses',
        }
    }
