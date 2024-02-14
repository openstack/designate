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
from designate import exceptions
from designate.objects import base
from designate.objects import fields
from designate.objects.validation_error import ValidationError
from designate.objects.validation_error import ValidationErrorList
from designate import utils


@base.DesignateRegistry.register
class Zone(base.DesignateObject, base.DictObjectMixin,
           base.PersistentObjectMixin, base.SoftDeleteObjectMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    fields = {
        'shard': fields.IntegerFields(nullable=True, minimum=0, maximum=4095),
        'tenant_id': fields.StringFields(nullable=True, read_only=False),
        'name': fields.DomainField(maxLength=255),
        'email': fields.EmailField(maxLength=255, nullable=True),
        'ttl': fields.IntegerFields(nullable=True, minimum=0,
                                    maximum=2147483647),
        'refresh': fields.IntegerFields(nullable=True, minimum=0,
                                        maximum=2147483647, read_only=False),
        'retry': fields.IntegerFields(nullable=True, minimum=0,
                                      maximum=2147483647, read_only=False),
        'expire': fields.IntegerFields(nullable=True, minimum=0,
                                       maximum=2147483647, read_only=False),
        'minimum': fields.IntegerFields(nullable=True, minimum=0,
                                        maximum=2147483647, read_only=False),
        'parent_zone_id': fields.UUIDFields(nullable=True, read_only=False),
        'serial': fields.IntegerFields(nullable=True, minimum=0,
                                       maximum=4294967295, read_only=False),
        'description': fields.StringFields(nullable=True, maxLength=160),
        'status': fields.EnumField(nullable=True, read_only=False,
                                   valid_values=[
                                       'ACTIVE', 'PENDING', 'ERROR',
                                       'DELETED', 'SUCCESS', 'NO_ZONE']

                                   ),
        'action': fields.EnumField(nullable=True,
                                   valid_values=[
                                       'CREATE', 'DELETE', 'UPDATE', 'NONE']
                                   ),
        'pool_id': fields.UUIDFields(nullable=True, read_only=False),
        'recordsets': fields.ObjectField('RecordSetList', nullable=True),
        'attributes': fields.ObjectField('ZoneAttributeList', nullable=True),
        'masters': fields.ObjectField('ZoneMasterList', nullable=True),
        'shared': fields.BooleanField(default=False, nullable=True),
        'type': fields.EnumField(nullable=True,
                                 valid_values=['SECONDARY', 'PRIMARY',
                                               'CATALOG'],
                                 read_only=False
                                 ),
        'transferred_at': fields.DateTimeField(nullable=True, read_only=False),
        'delayed_notify': fields.BooleanField(nullable=True),
        'increment_serial': fields.BooleanField(nullable=True),
    }

    STRING_KEYS = [
        'id', 'type', 'name', 'pool_id', 'serial', 'action', 'status', 'shard'
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
                        e.message = ("'%s' can't be specified when type is "
                                     "SECONDARY" % i)
                        errors.append(e)
                self._raise(errors)

            super().validate()
        except exceptions.RelationNotLoaded as ex:
            errors = ValidationErrorList()
            e = ValidationError()
            e.path = ['type']
            e.validator = 'required'
            e.validator_value = [ex.relation]
            e.message = "'%s' is a required property" % ex.relation
            errors.append(e)
            self._raise(errors)


@base.DesignateRegistry.register
class ZoneList(base.ListObjectMixin, base.DesignateObject,
               base.PagedListObjectMixin):
    LIST_ITEM_TYPE = Zone

    fields = {
        'objects': fields.ListOfObjectsField('Zone'),
    }
