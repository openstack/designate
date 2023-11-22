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

from oslo_log import log
from oslo_versionedobjects import exception as ovo_exc

import designate.conf
from designate import exceptions
from designate.objects import base
from designate.objects import fields
from designate.objects.validation_error import ValidationError
from designate.objects.validation_error import ValidationErrorList
from designate import utils


CONF = designate.conf.CONF
LOG = log.getLogger(__name__)


@base.DesignateRegistry.register
class RecordSet(base.DesignateObject, base.DictObjectMixin,
                base.PersistentObjectMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def action(self):
        # Return action as UPDATE if present. CREATE and DELETE are returned
        # if they are the only ones.
        action = 'NONE'
        actions = {'CREATE': 0, 'DELETE': 0, 'UPDATE': 0, 'NONE': 0}
        for record in self.records:
            actions[record.action] += 1

        if actions['CREATE'] != 0 and actions['UPDATE'] == 0 and \
                        actions['DELETE'] == 0 and actions['NONE'] == 0:  # noqa
            action = 'CREATE'
        elif actions['DELETE'] != 0 and actions['UPDATE'] == 0 and \
                        actions['CREATE'] == 0 and actions['NONE'] == 0:  # noqa
            action = 'DELETE'
        elif actions['UPDATE'] != 0 or actions['CREATE'] != 0 or \
                        actions['DELETE'] != 0:  # noqa
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
        # Return the worst status in order of ERROR, PENDING, ACTIVE, DELETED.
        status = None
        statuses = {
            'ERROR': 0,
            'PENDING': 1,
            'ACTIVE': 2,
            'DELETED': 3,
        }
        for record in self.records:
            if not status or statuses[record.status] < statuses[status]:
                status = record.status
        return status or 'ACTIVE'

    fields = {
        'shard': fields.IntegerFields(nullable=True, minimum=0, maximum=4095),
        'tenant_id': fields.StringFields(nullable=True, read_only=True),
        'zone_id': fields.UUIDFields(nullable=True, read_only=True),
        'zone_name': fields.DomainField(nullable=True, maxLength=255),
        'name': fields.HostField(maxLength=255, nullable=True),
        'type': fields.StringFields(nullable=True, read_only=True),
        'ttl': fields.IntegerFields(nullable=True,
                                    minimum=0, maximum=2147483647),
        'description': fields.StringFields(nullable=True, maxLength=160),
        'records': fields.PolymorphicObjectField('RecordList', nullable=True),
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
        LOG.debug(list(self.records))

        errors = ValidationErrorList()

        # Get the right classes (e.g. A for Recordsets with type: 'A')
        try:
            record_list_cls = self.obj_cls_from_name('%sList' % self.type)
            record_cls = self.obj_cls_from_name(self.type)
        except (KeyError, ovo_exc.UnsupportedObjectError):
            err_msg = ("'%(type)s' is not a valid record type"
                       % {'type': self.type})
            self._validate_fail(errors, err_msg)

        if self.type not in CONF.supported_record_type:
            err_msg = ("'%(type)s' is not a supported record type"
                       % {'type': self.type})
            self._validate_fail(errors, err_msg)

        # Get any rules that the record type imposes on the record
        changes = record_cls.get_recordset_schema_changes()
        old_fields = {}
        if changes:
            LOG.debug("Record %s is overriding the RecordSet schema with: %s",
                      record_cls.obj_name(), changes)
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
                record_obj.from_string(record.data)
            # The from_string() method will throw a ValueError if there is not
            # enough data blobs
            except ValueError as e:
                # Something broke in the from_string() method
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
                error_message = (
                        'Provided object is not valid. Got a %s error with '
                        'message %s' % (type(e).__name__, str(e))
                )
                raise exceptions.InvalidObject(error_message)

            else:
                # Seems to have loaded right - add it to be validated by
                # JSONSchema
                self.records.append(record_obj)
            i += 1

        try:
            # Run the actual validate code
            super().validate()

        except exceptions.InvalidObject as e:
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
        'id', 'type', 'name', 'zone_id', 'shard'
    ]


@base.DesignateRegistry.register
class RecordSetList(base.ListObjectMixin, base.DesignateObject,
                    base.PagedListObjectMixin):
    LIST_ITEM_TYPE = RecordSet

    fields = {
        'objects': fields.ListOfObjectsField('RecordSet'),
    }
