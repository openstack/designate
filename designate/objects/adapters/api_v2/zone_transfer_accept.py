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


class ZoneTransferAcceptAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.ZoneTransferAccept

    MODIFICATIONS = {
        'fields': {
            "id": {},
            "zone_transfer_request_id": {
                'immutable': True
            },
            "project_id": {
                'rename': 'tenant_id',
            },
            "key": {
                'read_only': False
            },
            "status": {},
            "zone_id": {},
            "created_at": {},
            "updated_at": {},
        },
        'options': {
            'links': True,
            'resource_name': 'transfer_accept',
            'collection_name': 'transfer_accepts',
        }
    }

    @classmethod
    def _render_object(cls, object, *args, **kwargs):
        obj = super(ZoneTransferAcceptAPIv2Adapter, cls)._render_object(
            object, *args, **kwargs)

        obj['links']['zone'] = \
            '%s/v2/%s/%s' % (cls.BASE_URI, 'zones', obj['zone_id'])

        return obj


class ZoneTransferAcceptListAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.ZoneTransferAcceptList

    MODIFICATIONS = {
        'options': {
            'links': True,
            'resource_name': 'transfer_accept',
            'collection_name': 'transfer_accepts',
        }
    }
