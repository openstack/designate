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


class ZoneImportAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.ZoneImport

    MODIFICATIONS = {
        'fields': {
            "id": {},
            "status": {},
            "message": {},
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
            'resource_name': 'import',
            'collection_name': 'imports',
        }
    }

    @classmethod
    def _render_object(cls, object, *args, **kwargs):
        obj = super(ZoneImportAPIv2Adapter, cls)._render_object(
            object, *args, **kwargs)

        if obj['zone_id'] is not None:
            obj['links']['zone'] = \
                '%s/v2/%s/%s' % (cls.BASE_URI, 'zones', obj['zone_id'])

        return obj


class ZoneImportListAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.ZoneImportList

    MODIFICATIONS = {
        'options': {
            'links': True,
            'resource_name': 'import',
            'collection_name': 'imports',
        }
    }
