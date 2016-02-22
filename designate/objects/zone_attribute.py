# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hpe.com>
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


class ZoneAttribute(base.DictObjectMixin, base.PersistentObjectMixin,
                    base.DesignateObject):
    FIELDS = {
        'zone_id': {
            'schema': {
                'type': 'string',
                'description': 'Zone identifier',
                'format': 'uuid',
            },
        },
        'key': {
            'schema': {
                'type': 'string',
                'maxLength': 50,
            },
            'required': True,
        },
        'value': {
            'schema': {
                'type': 'string',
                'maxLength': 50,
            },
            'required': True
        }
    }

    STRING_KEYS = [
        'id', 'key', 'value', 'zone_id'
    ]


class ZoneAttributeList(base.AttributeListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = ZoneAttribute
