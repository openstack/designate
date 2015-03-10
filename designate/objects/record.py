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


class Record(base.DictObjectMixin, base.PersistentObjectMixin,
             base.DesignateObject):
    # TODO(kiall): `hash` is an implementation detail of our SQLA driver,
    #              so we should remove it.
    FIELDS = {
        'data': {},
        'domain_id': {
            'schema': {
                'type': 'string',
                'format': 'uuid',
            },
            'required': True
        },
        'managed': {
            'schema': {
                'type': 'boolean'
            }
        },
        'managed_resource_type': {
            'schema': {
                'type': ['string', 'null'],
                'maxLength': 160
            },
        },
        'managed_resource_id': {
            'schema': {
                'type': ['string', 'null'],
                'format': 'uuid',
            },
        },
        'managed_plugin_name': {
            'schema': {
                'type': ['string', 'null'],
                'maxLength': 160
            },
        },
        'managed_plugin_type': {
            'schema': {
                'type': ['string', 'null'],
                'maxLength': 160
            },
        },
        'hash': {
            'schema': {
                'type': 'string',
                'maxLength': 32
            },
            'required': True
        },
        'description': {
            'schema': {
                'type': ['string', 'null'],
                'maxLength': 160
            },
        },
        'status': {
            'schema': {
                'type': 'string',
                'enum': ['ACTIVE', 'PENDING', 'ERROR'],
            },
        },
        'tenant_id': {
            'schema': {
                'type': 'string',
            },
        },
        'recordset_id': {
            'schema': {
                'type': 'string',
                'format': 'uuid',
            },
            'required': True
        },
        'managed_tenant_id': {
            'schema': {
                'type': ['string', 'null'],
            }
        },
        'managed_resource_region': {
            'schema': {
                'type': ['string', 'null'],
                'maxLength': 160
            },
        },
        'managed_extra': {
            'schema': {
                'type': ['string', 'null'],
                'maxLength': 160
            },
        },
        'action': {
            'schema': {
                'type': 'string',
                'enum': ['CREATE', 'DELETE', 'UPDATE', 'NONE'],
            },
        },
        'serial': {
            'schema': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 4294967295,
            },
        },
    }


class RecordList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = Record
