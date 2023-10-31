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
from designate.objects import fields


@base.DesignateRegistry.register
class TsigKey(base.DictObjectMixin, base.PersistentObjectMixin,
              base.DesignateObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    fields = {
        'name': fields.StringFields(nullable=False, maxLength=160),
        'algorithm': fields.EnumField(
            nullable=False,
            valid_values=[
                'hmac-md5',
                'hmac-sha1',
                'hmac-sha224',
                'hmac-sha256',
                'hmac-sha384',
                'hmac-sha512'
            ]
        ),
        'secret': fields.StringFields(maxLength=160),
        'scope': fields.EnumField(
            nullable=False, valid_values=['POOL', 'ZONE']
        ),
        'resource_id': fields.UUIDFields(nullable=False)
    }

    STRING_KEYS = [
        'id', 'name', 'algorithm', 'scope', 'resource_id'
    ]


@base.DesignateRegistry.register
class TsigKeyList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = TsigKey

    fields = {
        'objects': fields.ListOfObjectsField('TsigKey'),
    }
