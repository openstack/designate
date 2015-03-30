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
from designate.objects.domain_attribute import DomainAttribute
from designate.objects.domain_attribute import DomainAttributeList


class Domain(base.DictObjectMixin, base.SoftDeleteObjectMixin,
             base.PersistentObjectMixin, base.DesignateObject):
    FIELDS = {
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
            'required': True
        },
        'ttl': {
            'schema': {
                'type': ['integer', 'null'],
                'minimum': 0,
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
        'parent_domain_id': {
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
                'enum': ['ACTIVE', 'PENDING', 'ERROR'],
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
            'relation_cls': 'DomainAttributeList'
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
    }

    @property
    def masters(self):
        if self.obj_attr_is_set('attributes'):
            return [i.value for i in self.attributes if i.key == 'master']
        else:
            return None

    # TODO(ekarlso): Make this a property sette rpr Kiall's comments later.
    def set_masters(self, masters):
        attributes = DomainAttributeList()

        for m in masters:
            obj = DomainAttribute(key='master', value=m)
            attributes.append(obj)
        self.attributes = attributes

    def get_master_by_ip(self, host):
        """
        Utility to get the master by it's ip for this domain.
        """
        for srv in self.masters:
            srv_host, _ = utils.split_host_port(srv)
            if host == srv_host:
                return srv
        return False

    def validate(self):
        if self.type == 'SECONDARY' and self.masters is None:
            errors = ValidationErrorList()
            e = ValidationError()
            e.path = ['type']
            e.validator = 'required'
            e.validator_value = ['masters']
            e.message = "'masters' is a required property"
            errors.append(e)
            raise exceptions.InvalidObject(
                "Provided object does not match "
                "schema", errors=errors, object=self)

        super(Domain, self).validate()


class DomainList(base.ListObjectMixin, base.DesignateObject,
                 base.PagedListObjectMixin):
    LIST_ITEM_TYPE = Domain
