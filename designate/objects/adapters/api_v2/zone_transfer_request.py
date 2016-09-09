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
from designate import policy
from designate import exceptions


class ZoneTransferRequestAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.ZoneTransferRequest

    MODIFICATIONS = {
        'fields': {
            "id": {
                'protected': False
            },
            "zone_id": {
                'immutable': True,
                'protected': False
            },
            "project_id": {
                'rename': 'tenant_id',
            },
            "target_project_id": {
                'rename': 'target_tenant_id',
                'immutable': True
            },
            "description": {
                'read_only': False,
                'protected': False
            },
            "key": {},
            "status": {
                'protected': False
            },
            "zone_name": {
                'immutable': True,
                'protected': False
            },
            "created_at": {},
            "updated_at": {},
        },
        'options': {
            'links': True,
            'resource_name': 'transfer_request',
            'collection_name': 'transfer_requests',
        }
    }

    @classmethod
    def _render_object(cls, object, *args, **kwargs):
        obj = super(ZoneTransferRequestAPIv2Adapter, cls)._render_object(
            object, *args, **kwargs)

        try:
            target = {
                'tenant_id': object.tenant_id,
            }

            policy.check(
                'get_zone_transfer_request_detailed',
                kwargs['context'],
                target)

        except exceptions.Forbidden:
            for field in cls.MODIFICATIONS['fields']:
                if cls.MODIFICATIONS['fields'][field].get('protected', True):
                    del obj[field]

        return obj

    @classmethod
    def _get_path(cls, request, *args):
        return '/v2/zones/tasks/transfer_requests'


class ZoneTransferRequestListAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.ZoneTransferRequestList

    MODIFICATIONS = {
        'options': {
            'links': True,
            'resource_name': 'transfer_request',
            'collection_name': 'transfer_requests',
        }
    }
