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
from designate import utils
from designate import exceptions
from designate.objects import base
from designate.objects.validation_error import ValidationError
from designate.objects.validation_error import ValidationErrorList


class Zone(base.DictObjectMixin, base.SoftDeleteObjectMixin,
           base.PersistentObjectMixin, base.DesignateObject):
    FIELDS = {
        'shard': {
            'schema': {
                'type': 'integer',
                'minimum': 0,
                'maximum': 4095
            }
        },
        'tenant_id': {
            'schema': {
                'type': 'string',
            },
            'immutable': True
        },
        'name': {
            'schema': {
                'type': 'string',
                'description': 'Zone name',
                'format': 'domainname',
                'maxLength': 255,
            },
            'immutable': True,
            'required': True
        },
        'email': {
            'schema': {
                'type': 'string',
                'description': 'Hostmaster email address',
                'format': 'email',
                'maxLength': 255
            },
            'required': False
        },
        'ttl': {
            'schema': {
                'type': ['integer', 'null'],
                'minimum': 1,
                'maximum': 2147483647
            },
        },
        'refresh': {
            'schema': {
                'type': 'integer',
                'minimum': 0,
                'maximum': 2147483647
            },
            'read_only': True
        },
        'retry': {
            'schema': {
                'type': 'integer',
                'minimum': 0,
                'maximum': 2147483647
            },
            'read_only': True
        },
        'expire': {
            'schema': {
                'type': 'integer',
                'minimum': 0,
                'maximum': 2147483647
            },
            'read_only': True
        },
        'minimum': {
            'schema': {
                'type': 'integer',
                'minimum': 0,
                'maximum': 2147483647
            },
            'read_only': True
        },
        'parent_zone_id': {
            'schema': {
                'type': ['string', 'null'],
                'format': 'uuid'
            },
            'read_only': True
        },
        'serial': {
            'schema': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 4294967295,
            },
            'read_only': True
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
                'enum': ['ACTIVE', 'PENDING', 'ERROR',
                        'DELETED', 'SUCCESS', 'NO_ZONE']
            },
            'read_only': True,
        },
        'action': {
            'schema': {
                'type': 'string',
                'enum': ['CREATE', 'DELETE', 'UPDATE', 'NONE'],
            },
            'read_only': True
        },
        'pool_id': {
            'schema': {
                'type': 'string',
                'format': 'uuid',
            },
            'immutable': True,
        },
        'recordsets': {
            'relation': True,
            'relation_cls': 'RecordSetList'
        },
        'attributes': {
            'relation': True,
            'relation_cls': 'ZoneAttributeList'
        },
        'masters': {
            'relation': True,
            'relation_cls': 'ZoneMasterList'
        },
        'type': {
            'schema': {
                'type': 'string',
                'enum': ['SECONDARY', 'PRIMARY'],
            },
            'immutable': True
        },
        'transferred_at': {
            'schema': {
                'type': ['string', 'null'],
                'format': 'date-time',
            },
            'read_only': True
        },
        'delayed_notify': {
            'schema': {
                'type': 'boolean',
            },
        },
    }

    STRING_KEYS = [
        'id', 'type', 'name', 'pool_id', 'serial', 'action', 'status'
    ]

    def get_master_by_ip(self, host):
        """
        Utility to get the master by it's ip for this zone.
        """
        for srv in self.masters:
            srv_host, _ = utils.split_host_port(srv.to_data())
            if host == srv_host:
                return srv
        return False

    def _raise(self, errors):
        if len(errors) != 0:
            raise exceptions.InvalidObject(
                "Provided object does not match "
                "schema", errors=errors, object=self)

    def __hash__(self):
        return hash(self.id)

    def validate(self):
        errors = ValidationErrorList()

        if self.type == 'PRIMARY':
            if self.obj_attr_is_set('masters') and len(self.masters) != 0:
                e = ValidationError()
                e.path = ['type']
                e.validator = 'maxItems'
                e.validator_value = ['masters']
                e.message = "'masters' has more items than allowed"
                errors.append(e)
            if self.email is None:
                e = ValidationError()
                e.path = ['type']
                e.validator = 'required'
                e.validator_value = 'email'
                e.message = "'email' is a required property"
                errors.append(e)
            self._raise(errors)

        try:
            if self.type == 'SECONDARY':
                if self.masters is None or len(self.masters) == 0:
                    e = ValidationError()
                    e.path = ['type']
                    e.validator = 'required'
                    e.validator_value = ['masters']
                    e.message = "'masters' is a required property"
                    errors.append(e)

                for i in ['email', 'ttl']:
                    if i in self.obj_what_changed():
                        e = ValidationError()
                        e.path = ['type']
                        e.validator = 'not_allowed'
                        e.validator_value = i
                        e.message = "'%s' can't be specified when type is " \
                            "SECONDARY" % i
                        errors.append(e)
                self._raise(errors)

            super(Zone, self).validate()
        except exceptions.RelationNotLoaded as ex:
            errors = ValidationErrorList()
            e = ValidationError()
            e.path = ['type']
            e.validator = 'required'
            e.validator_value = [ex.relation]
            e.message = "'%s' is a required property" % ex.relation
            errors.append(e)
            self._raise(errors)


class ZoneList(base.ListObjectMixin, base.DesignateObject,
               base.PagedListObjectMixin):
    LIST_ITEM_TYPE = Zone
