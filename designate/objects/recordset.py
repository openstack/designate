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

from oslo_config import cfg
from oslo_log import log
import six

from designate import exceptions
from designate import utils
from designate.objects import base
from designate.objects.validation_error import ValidationError
from designate.objects.validation_error import ValidationErrorList


LOG = log.getLogger(__name__)

cfg.CONF.import_opt('supported_record_type', 'designate')


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
    def managed(self):
        managed = False
        for record in self.records:
            if record.managed:
                return True
        return managed

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
            'read_only': True
        },
        'zone_id': {
            'schema': {
                'type': 'string',
                'description': 'Zone identifier',
                'format': 'uuid'
            },
        },
        'zone_name': {
            'schema': {
                'type': 'string',
                'description': 'Zone name',
                'format': 'domainname',
                'maxLength': 255,
            },
            'read_only': True
        },
        'name': {
            'schema': {
                'type': 'string',
                'description': 'Recordset name',
                'format': 'hostname',
                'maxLength': 255,
            },
            'immutable': True,
            'required': True
        },
        'type': {
            'schema': {
                'type': 'string',
                'description': 'RecordSet type (TODO: Make types extensible)',
            },
            'required': True,
            'immutable': True
        },
        'ttl': {
            'schema': {
                'type': ['integer', 'null'],
                'description': 'Default time to live',
                'minimum': 1,
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

    def _validate_fail(self, errors, msg):
        e = ValidationError()
        e.path = ['recordset', 'type']
        e.validator = 'value'
        e.validator_value = [self.type]
        e.message = msg
        # Add it to the list for later
        errors.append(e)
        raise exceptions.InvalidObject(
            "Provided object does not match "
            "schema", errors=errors, object=self)

    def validate(self):

        LOG.debug("Validating '%(name)s' object with values: %(values)r", {
            'name': self.obj_name(),
            'values': self.to_dict(),
        })

        errors = ValidationErrorList()

        # Get the right classes (e.g. A for Recordsets with type: 'A')
        try:
            record_list_cls = self.obj_cls_from_name('%sList' % self.type)
            record_cls = self.obj_cls_from_name(self.type)
        except KeyError as e:
            err_msg = ("'%(type)s' is not a valid record type"
                       % {'type': self.type})
            self._validate_fail(errors, err_msg)

        if self.type not in cfg.CONF.supported_record_type:
            err_msg = ("'%(type)s' is not a supported record type"
                       % {'type': self.type})
            self._validate_fail(errors, err_msg)

        # Get any rules that the record type imposes on the record
        changes = record_cls.get_recordset_schema_changes()
        old_fields = {}
        if changes:
            LOG.debug("Record %s is overriding the RecordSet schema with: %s" %
                      (record_cls.obj_name(), changes))
            old_fields = deepcopy(self.FIELDS)
            self.FIELDS = utils.deep_dict_merge(self.FIELDS, changes)

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

            except TypeError as e:
                e = ValidationError()
                e.path = ['records', i]
                e.validator = 'format'
                e.validator_value = [self.type]
                e.message = ("'%(data)s' is not a '%(type)s' Record"
                             % {'data': record.data, 'type': self.type})
                # Add it to the list for later
                errors.append(e)
                error_indexes.append(i)

            except AttributeError as e:
                e = ValidationError()
                e.path = ['records', i]
                e.validator = 'format'
                e.validator_value = [self.type]
                e.message = ("'%(data)s' is not a '%(type)s' Record"
                             % {'data': record.data, 'type': self.type})
                # Add it to the list for later
                errors.append(e)
                error_indexes.append(i)

            except Exception as e:
                error_message = str.format(
                    'Provided object is not valid. '
                    'Got a %s error with message %s' %
                    (type(e).__name__, six.text_type(e)))
                raise exceptions.InvalidObject(error_message)

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
                if len(error.path) > 1 and isinstance(error.path[1], int):
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
                LOG.debug(
                    "Error Validating '%(name)s' object with values: "
                    "%(values)r", {
                        'name': self.obj_name(),
                        'values': self.to_dict(),
                    }
                )
                raise exceptions.InvalidObject(
                    "Provided object does not match "
                    "schema", errors=errors, object=self)
        finally:
            if old_fields:
                self.FIELDS = old_fields
        # Send in the traditional Record objects to central / storage
        self.records = old_records

    STRING_KEYS = [
        'id', 'type', 'name', 'zone_id'
    ]


class RecordSetList(base.ListObjectMixin, base.DesignateObject,
                    base.PagedListObjectMixin):
    LIST_ITEM_TYPE = RecordSet
