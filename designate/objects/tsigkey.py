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
from designate.common import constants
import designate.conf
from designate import exceptions
from designate.objects import base
from designate.objects import fields
from designate.objects.validation_error import ValidationError
from designate.objects.validation_error import ValidationErrorList


CONF = designate.conf.CONF


@base.DesignateRegistry.register
class TsigKey(base.DictObjectMixin, base.PersistentObjectMixin,
              base.DesignateObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    fields = {
        'name': fields.StringFields(nullable=False, maxLength=160),
        'algorithm': fields.EnumField(
            nullable=False,
            valid_values=constants.TSIG_ALGORITHMS
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

    def _raise(self, errors):
        if len(errors) != 0:
            raise exceptions.InvalidObject(
                "Provided object does not match "
                "schema", errors=errors, object=self)

    def validate(self):
        errors = ValidationErrorList()
        if not self.secret and not (
                CONF['service:api'].allow_empty_secrets_for_tsig):
            e = ValidationError()
            e.path = ['type']
            e.validator = 'value'
            e.validator_value = ['secret']
            e.message = "'secret' should not be empty"
            errors.append(e)
        self._raise(errors)
        super().validate()


@base.DesignateRegistry.register
class TsigKeyList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = TsigKey

    fields = {
        'objects': fields.ListOfObjectsField('TsigKey'),
    }
