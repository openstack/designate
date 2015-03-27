# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hp.com>
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


class FloatingIP(base.DictObjectMixin, base.PersistentObjectMixin,
                 base.DesignateObject):
    FIELDS = {
        "address": {
            'schema': {
                'type': 'string',
                'format': ['ipv4', 'ipv6']
            },
        },
        "description": {
            'schema': {
                'type': ['string', 'null'],
                'maxLength': 160
            },
        },
        "id": {
            'schema': {
                'type': 'string',
                'format': 'uuid'
            }
        },
        "ptrdname": {
            'schema': {
                'type': ['string', 'null'],
                'format': 'domainname'
            }
        },
        "ttl": {
            'schema': {
                'type': ['integer', 'null'],
                'minimum': 1,
                'maximum': 2147483647
            }
        },
        "region": {
            'schema': {
                'type': ['string', 'null'],
            }
        },
        "action": {
            'schema': {
                'type': 'string',
                'enum': ['CREATE', 'DELETE', 'UPDATE', 'NONE'],
            }
        },
        "status": {
            'schema': {
                'type': 'string',
                'enum': ['ACTIVE', 'PENDING', 'ERROR'],
            }
        }

    }

    @property
    def key(self):
        return '%s:%s' % (self.region, self.id)


class FloatingIPList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = FloatingIP
