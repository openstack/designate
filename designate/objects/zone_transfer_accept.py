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


class ZoneTransferAccept(base.DictObjectMixin, base.PersistentObjectMixin,
                         base.DesignateObject):
    FIELDS = {
        'zone_transfer_request_id': {
            'schema': {
                "type": "string",
                "format": "uuid"
            },
            "immutable": True
        },
        'tenant_id': {
            'schema': {
                'type': 'string',
            },
            'read_only': True
        },
        'status': {
            'schema': {
                "type": "string",
                "enum": ["ACTIVE", "PENDING", "DELETED", "ERROR", "COMPLETE"],
            },
            'read_only': True
        },
        'key': {
            'schema': {
                "type": "string",
                "maxLength": 160
            },
            'required': True
        },
        'zone_id': {
            'schema': {
                "type": "string",
                "format": "uuid"
            },
            "immutable": True
        },
    }

    STRING_KEYS = [
        'id', 'zone_id', 'tenant_id', 'zone_transfer_request_id'
    ]


class ZoneTransferAcceptList(base.ListObjectMixin, base.DesignateObject,
                             base.PagedListObjectMixin):
    LIST_ITEM_TYPE = ZoneTransferAccept
