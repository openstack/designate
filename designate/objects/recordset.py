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
from copy import deepcopy

from designate import exceptions
from designate.objects import base
from designate.objects.validation_error import ValidationError
from designate.objects.validation_error import ValidationErrorList


class RecordSet(base.DictObjectMixin, base.PersistentObjectMixin,
                base.DesignateObject):

    @property
    def action(self):
        # Return action as UPDATE if present. CREATE and DELETE are returned
        # if they are the only ones.
        action = 'NONE'
        actions = {'CREATE': 0, 'DELETE': 0, 'UPDATE': 0, 'NONE': 0}
        for record in self.records:
            actions[record.action] += 1

        if actions['CREATE'] != 0 and actions['UPDATE'] == 0 and \
                actions['DELETE'] == 0 and actions['NONE'] == 0:
            action = 'CREATE'
        elif actions['DELETE'] != 0 and actions['UPDATE'] == 0 and \
                actions['CREATE'] == 0 and actions['NONE'] == 0:
            action = 'DELETE'
        elif actions['UPDATE'] != 0 or actions['CREATE'] != 0 or \
                actions['DELETE'] != 0:
            action = 'UPDATE'
        return action

    @property
    def status(self):
        # Return the worst status in order of ERROR, PENDING, ACTIVE
        status = 'ACTIVE'
        for record in self.records:
            if (record.status == 'ERROR') or \
                    (record.status == 'PENDING' and status != 'ERROR') or \
                    (status != 'PENDING'):
                status = record.status
        return status

    FIELDS = {
        'tenant_id': {
            'schema': {
                'type': 'string',
            },
            'read_only': True
        },
        'domain_id': {
            'schema': {
                'type': 'string',
                'description': 'Zone identifier',
                'format': 'uuid'
            },
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
        'type': {
            'schema': {
                'type': 'string',
                'description': 'RecordSet type (TODO: Make types extensible)',
                'enum': ['A', 'AAAA', 'CNAME', 'MX', 'SRV', 'TXT', 'SPF', 'NS',
                         'PTR', 'SSHFP', 'SOA']
            },
            'required': True,
            'immutable': True
        },
        'ttl': {
            'schema': {
                'type': ['integer', 'null'],
                'description': 'Default time to live',
                'minimum': 0,
                'maximum': 2147483647
            },
        },
        'description': {
            'schema': {
                'type': ['string', 'null'],
                'maxLength': 160
            },
        },
        'records': {
            'relation': True,
            'relation_cls': 'RecordList'
        },
        # TODO(graham): implement the polymorphic class relations
        # 'records': {
        #     'polymorphic': 'type',
        #     'relation': True,
        #     'relation_cls': lambda type_: '%sList' % type_
        # },
    }

    def validate(self):

        # Get the right classes (e.g. A for Recordsets with type: 'A')
        record_list_cls = self.obj_cls_from_name('%sList' % self.type)
        record_cls = self.obj_cls_from_name(self.type)

        errors = ValidationErrorList()
        error_indexes = []
        # Copy these for safekeeping
        old_records = deepcopy(self.records)

        # Blank the records for this object with the right list type
        self.records = record_list_cls()

        i = 0

        for record in old_records:
            record_obj = record_cls()
            try:
                record_obj._from_string(record.data)
            # The _from_string() method will throw a ValueError if there is not
            # enough data blobs
            except ValueError as e:
                # Something broke in the _from_string() method
                # Fake a correct looking ValidationError() object
                e = ValidationError()
                e.path = ['records', i]
                e.validator = 'format'
                e.validator_value = [self.type]
                e.message = ("'%(data)s' is not a '%(type)s' Record"
                             % {'data': record.data, 'type': self.type})
                # Add it to the list for later
                errors.append(e)
                error_indexes.append(i)
            else:
                # Seems to have loaded right - add it to be validated by
                # JSONSchema
                self.records.append(record_obj)
            i += 1

        try:
            # Run the actual validate code
            super(RecordSet, self).validate()

        except exceptions.InvalidObject as e:
            # Something is wrong according to JSONSchema - append our errors
            increment = 0
            # This code below is to make sure we have the index for the record
            # list correct. JSONSchema may be missing some of the objects due
            # to validation above, so this re - inserts them, and makes sure
            # the index is right
            for error in e.errors:
                error.path[1] += increment
                while error.path[1] in error_indexes:
                    increment += 1
                    error.path[1] += 1
            # Add the list from above
            e.errors.extend(errors)
            # Raise the exception
            raise e
        else:
            # If JSONSchema passes, but we found parsing errors,
            # raise an exception
            if len(errors) > 0:
                raise exceptions.InvalidObject(
                    "Provided object does not match "
                    "schema", errors=errors, object=self)
        # Send in the traditional Record objects to central / storage
        self.records = old_records


class RecordSetList(base.ListObjectMixin, base.DesignateObject,
                    base.PagedListObjectMixin):
    LIST_ITEM_TYPE = RecordSet
