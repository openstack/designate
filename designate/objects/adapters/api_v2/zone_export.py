# Copyright 2015 Rackspace Inc.
#
# Author: Tim Simmons <tim.simmons@rackspace.com>
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
from designate import objects
from designate.objects.adapters.api_v2 import base


class ZoneExportAPIv2Adapter(base.APIv2Adapter):
    ADAPTER_OBJECT = objects.ZoneExport
    MODIFICATIONS = {
        'fields': {
            "id": {},
            "status": {},
            "message": {},
            "location": {},
            "zone_id": {},
            "project_id": {
                'rename': 'tenant_id'
            },
            "created_at": {},
            "updated_at": {},
            "version": {},
        },
        'options': {
            'links': True,
            'resource_name': 'export',
            'collection_name': 'exports',
        }
    }

    @classmethod
    def _get_path(cls, request, *args):
        return '/v2/zones/tasks/exports'

    @classmethod
    def render_object(cls, obj, *args, **kwargs):
        new_obj = super().render_object(
            obj, *args, **kwargs
        )

        if (new_obj['location'] and
                new_obj['location'].startswith('designate://')):
            # Get the base uri from the self link, which respects host headers
            base_uri = new_obj['links']['self'].split(
                cls._get_path(kwargs['request']))[0]

            new_obj['links']['export'] = (
                    '{}/{}'.format(
                        base_uri, new_obj['location'].split('://')[1]
                    )
            )

        return new_obj


class ZoneExportListAPIv2Adapter(base.APIv2Adapter):
    ADAPTER_OBJECT = objects.ZoneExportList
    MODIFICATIONS = {
        'options': {
            'links': True,
            'resource_name': 'export',
            'collection_name': 'exports',
        }
    }
