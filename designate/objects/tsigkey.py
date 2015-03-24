# Copyright (c) 2014 Rackspace Hosting
# All Rights Reserved.
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
from designate.objects import base


class TsigKey(base.DictObjectMixin, base.PersistentObjectMixin,
              base.DesignateObject):
    FIELDS = {
        'name': {
            'schema': {
                'type': 'string',
                'maxLength': 160,
                'format': 'domainnamne'
            },
            'required': True
        },
        'algorithm': {
            'schema': {
                'type': 'string',
                'enum': [
                        'hmac-md5',
                        'hmac-sha1',
                        'hmac-sha224',
                        'hmac-sha256',
                        'hmac-sha384',
                        'hmac-sha512'
                ]
            },
            'required': True
        },
        'secret': {
            'schema': {
                'type': 'string',
                'maxLength': 160
            },
            'required': True
        },
        'scope': {
            'schema': {
                'type': 'string',
                'enum': ['POOL', 'ZONE'],
            },
            'required': True
        },
        'resource_id': {
            'schema': {
                'type': 'string',
                'format': 'uuid'
            },
            'read_only': True,
            'required': True
        },
    }

    STRING_KEYS = [
        'id', 'name', 'algorithm', 'scope', 'resource_id'
    ]


class TsigKeyList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = TsigKey
