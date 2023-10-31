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
    def render_object(cls, obj, *args, **kwargs):
        new_obj = super().render_object(
            obj, *args, **kwargs)

        if new_obj['zone_id'] is not None:
            new_obj['links']['zone'] = (
                '{}/v2/{}/{}'.format(
                    cls._get_base_url(
                        kwargs['request']), 'zones', new_obj['zone_id']
                )
            )

        return new_obj


class ZoneImportListAPIv2Adapter(base.APIv2Adapter):
    ADAPTER_OBJECT = objects.ZoneImportList
    MODIFICATIONS = {
        'options': {
            'links': True,
            'resource_name': 'import',
            'collection_name': 'imports',
        }
    }
