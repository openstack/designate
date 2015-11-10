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
from designate.objects import base


class ZoneImport(base.DictObjectMixin, base.PersistentObjectMixin,
               base.DesignateObject):
    FIELDS = {
        'status': {
            'schema': {
                "type": "string",
                "enum": ["ACTIVE", "PENDING", "DELETED", "ERROR", "COMPLETE"],
            },
            'read_only': True
        },
        'task_type': {
            'schema': {
                "type": "string",
                "enum": ["IMPORT"],
            },
            'read_only': True
        },
        'tenant_id': {
            'schema': {
                'type': 'string',
            },
            'read_only': True
        },
        'message': {
            'schema': {
                'type': ['string', 'null'],
                'maxLength': 160
            },
            'read_only': True
        },
        'zone_id': {
            'schema': {
                "type": "string",
                "format": "uuid"
            },
            'read_only': True
        },
    }


class ZoneImportList(base.ListObjectMixin, base.DesignateObject,
                   base.PagedListObjectMixin):
    LIST_ITEM_TYPE = ZoneImport
