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


class ZoneAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.Zone

    MODIFICATIONS = {
        'fields': {
            "id": {},
            "pool_id": {},
            "project_id": {
                'rename': 'tenant_id'
            },
            "name": {
                'immutable': True,
            },
            "email": {
                'read_only': False
            },
            "description": {
                'read_only': False
            },
            "ttl": {
                'read_only': False
            },
            "serial": {},
            "status": {},
            "action": {},
            "version": {},
            "attributes": {
                "immutable": True
            },
            "type": {
                "immutable": True
            },
            "masters": {},
            "created_at": {},
            "updated_at": {},
            "transferred_at": {},
        },
        'options': {
            'links': True,
            'resource_name': 'zone',
            'collection_name': 'zones',
        }
    }

    @classmethod
    def _parse_object(cls, values, object, *args, **kwargs):

        if 'masters' in values:

            object.masters = objects.adapters.DesignateAdapter.parse(
                cls.ADAPTER_FORMAT,
                values['masters'],
                objects.ZoneMasterList(),
                *args, **kwargs)

            del values['masters']

        if 'attributes' in values:

            object.attributes = objects.adapters.DesignateAdapter.parse(
                cls.ADAPTER_FORMAT,
                values['attributes'],
                objects.ZoneAttributeList(),
                *args, **kwargs)

            del values['attributes']

        return super(ZoneAPIv2Adapter, cls)._parse_object(
            values, object, *args, **kwargs)


class ZoneListAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.ZoneList

    MODIFICATIONS = {
        'options': {
            'links': True,
            'resource_name': 'zone',
            'collection_name': 'zones',
        }
    }
