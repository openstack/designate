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
from designate.common import constants
from designate import exceptions
from designate import objects
from designate.objects.adapters.api_v2 import base
from designate import policy


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
    def render_object(cls, obj, *args, **kwargs):
        new_obj = super().render_object(
            obj, *args, **kwargs
        )
        try:
            target = {constants.RBAC_PROJECT_ID: obj.tenant_id,
                      'tenant_id': obj.tenant_id}
            policy.check(
                'get_zone_transfer_request_detailed', kwargs['context'], target
            )
        except exceptions.Forbidden:
            for field in cls.MODIFICATIONS['fields']:
                if cls.MODIFICATIONS['fields'][field].get('protected', True):
                    del new_obj[field]

        return new_obj

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
