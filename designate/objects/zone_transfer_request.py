# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Graham Hayes <graham.hayes@hpe.com>
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


class ZoneTransferRequest(base.DictObjectMixin, base.PersistentObjectMixin,
                          base.DesignateObject,):
    FIELDS = {
        'key': {
            'schema': {
                "type": "string",
                "maxLength": 160
            },
        },
        'zone_id': {
            'schema': {
                "type": "string",
                "description": "Zone identifier",
                "format": "uuid"
            },
            "immutable": True
        },
        'description': {
            'schema': {
                "type": ["string", "null"],
                "maxLength": 160
            }
        },
        'tenant_id': {
            'schema': {
                'type': 'string',
            },
            'read_only': True
        },
        'target_tenant_id': {
            'schema': {
                'type': ['string', 'null'],
            },
            'immutable': True
        },
        'status': {
            'schema': {
                "type": "string",
                "enum": ["ACTIVE", "PENDING", "DELETED", "ERROR", "COMPLETE"],
            }
        },
        'zone_name': {
            'schema': {
                "type": ["string", "null"],
                "maxLength": 255,
            },
            'read_only': True
        },
    }

    STRING_KEYS = [
        'id', 'zone_id', 'zone_name', 'target_tenant_id'
    ]


class ZoneTransferRequestList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = ZoneTransferRequest
