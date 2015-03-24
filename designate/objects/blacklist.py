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


class Blacklist(base.DictObjectMixin, base.PersistentObjectMixin,
                base.DesignateObject):
    FIELDS = {
        'pattern': {
            'schema': {
                'type': 'string',
                'description': 'Regex for blacklisted zone name',
                'format': 'regex',
                'maxLength': 255,
            },
            'required': True
        },
        'description': {
            'schema': {
                'type': ['string', 'null'],
                'description': 'Description for the blacklisted zone',
                'maxLength': 160
            }
        }
    }

    STRING_KEYS = [
        'id', 'pattern'
    ]


class BlacklistList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = Blacklist
