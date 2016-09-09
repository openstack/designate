# Copyright 2014 Hewlett-Packard Development Company, L.P.
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
import re

from designate.objects.adapters.api_v2 import base
from designate import objects


class NotSpecifiedSential:
    pass

REQUIRED_RE = re.compile("\'([\w]*)\' is a required property")


class ValidationErrorAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.ValidationError

    MODIFICATIONS = {
        'fields': {
            "path": {},
            "message": {},
            "validator": {},
            "validator_value": {},
        },
        'options': {
            'links': False,
            'resource_name': 'error',
            'collection_name': 'errors',
        }
    }

    @classmethod
    def _render_object(cls, error, *args, **kwargs):

        # Do the usual rename
        error_dict = super(ValidationErrorAPIv2Adapter, cls)._render_object(
            error, *args, **kwargs)

        # Currently JSON Schema doesn't add the path on for required items
        if error_dict.get('validator', '') == 'required':
            error_dict['path'].append(
                REQUIRED_RE.match(error.message).group(1))

        object = kwargs['failed_object']

        # Rename the keys in the path list
        error_dict['path'] = cls._rename_path(object, error_dict['path'])

        return error_dict

    @classmethod
    def _rename_path(cls, object, path):
        new_path = list()

        obj_adapter = cls.get_object_adapter(cls.ADAPTER_FORMAT, object)

        for path_segment in path:
            new_path_segment, obj_adapter = cls._rename_path_segment(
                obj_adapter, object, path_segment)
            new_path.append(new_path_segment)

        return new_path

    @classmethod
    def _rename_path_segment(cls, obj_adapter, object, path_segment):

        # Check if the object is a list - lists will just have an index as a
        # value, ands this can't be renamed
        if issubclass(obj_adapter.ADAPTER_OBJECT, objects.ListObjectMixin):
            obj_adapter = cls.get_object_adapter(
                cls.ADAPTER_FORMAT,
                obj_adapter.ADAPTER_OBJECT.LIST_ITEM_TYPE.obj_name())
            # Return the segment as is, and the next adapter (which is the
            # LIST_ITEM_TYPE)
            return path_segment, obj_adapter

        for key, value in obj_adapter.MODIFICATIONS.get(
                'fields', {}).items():

            # Check if this field as actually a nested object
            if object.FIELDS.get(path_segment, {}).get('relation', False):

                obj_cls = object.FIELDS.get(path_segment).get('relation_cls')
                obj_adapter = cls.get_object_adapter(
                    cls.ADAPTER_FORMAT,
                    obj_cls)

                object = objects.DesignateObject.obj_cls_from_name(obj_cls)()
                # Recurse down into this object
                path_segment, obj_adapter = cls._rename_path_segment(
                    obj_adapter, object, path_segment)

                # No need to continue the loop
                break

            if not isinstance(
                value.get(
                    'rename', NotSpecifiedSential()), NotSpecifiedSential)\
                    and path_segment == value.get('rename'):
                # Just do the rename
                path_segment = key

        return path_segment, obj_adapter


class ValidationErrorListAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.ValidationErrorList

    MODIFICATIONS = {
        'options': {
            'links': False,
            'resource_name': 'error',
            'collection_name': 'errors',
        }
    }
