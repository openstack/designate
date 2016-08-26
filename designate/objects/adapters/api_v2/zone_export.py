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

from designate.objects.adapters.api_v2 import base
from designate import objects


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
    def _render_object(cls, object, *args, **kwargs):
        obj = super(ZoneExportAPIv2Adapter, cls)._render_object(
            object, *args, **kwargs)

        if obj['location'] and obj['location'].startswith('designate://'):
            # Get the base uri from the self link, which respects host headers
            base_uri = obj['links']['self']. \
                split(cls._get_path(kwargs['request']))[0]

            obj['links']['export'] = \
                '%s/%s' % \
                (base_uri, obj['location'].split('://')[1])

        return obj


class ZoneExportListAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.ZoneExportList

    MODIFICATIONS = {
        'options': {
            'links': True,
            'resource_name': 'export',
            'collection_name': 'exports',
        }
    }
