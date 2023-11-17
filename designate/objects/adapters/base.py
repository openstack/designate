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
import datetime

from oslo_log import log
from oslo_versionedobjects import fields

from designate import exceptions
from designate import objects
from designate import utils

LOG = log.getLogger(__name__)


class DesignateObjectAdapterMetaclass(type):
    def __init__(cls, name, bases, cls_dict):
        if not hasattr(cls, '_adapter_classes'):
            cls._adapter_classes = {}
            return

        key = f'{cls.adapter_format()}:{cls.adapter_object()}'
        if key not in cls._adapter_classes:
            cls._adapter_classes[key] = cls
        else:
            raise Exception(
                "Duplicate DesignateAdapterObject with"
                " format '%(format)s and object %(object)s'" %
                {
                    'format': cls.adapter_format(),
                    'object': cls.adapter_object()
                }
            )


class DesignateAdapter(metaclass=DesignateObjectAdapterMetaclass):
    """docstring for DesignateObjectAdapter"""
    ADAPTER_FORMAT = None
    ADAPTER_OBJECT = objects.DesignateObject
    MODIFICATIONS = None

    @classmethod
    def adapter_format(cls):
        return cls.ADAPTER_FORMAT

    @classmethod
    def adapter_object(cls):
        return cls.ADAPTER_OBJECT.obj_name()

    @classmethod
    def get_object_adapter(cls, obj, obj_format=None):
        if obj_format is None:
            obj_format = cls.ADAPTER_FORMAT
        if isinstance(obj, objects.DesignateObject):
            key = f'{obj_format}:{obj.obj_name()}'
        else:
            key = f'{obj_format}:{obj}'
        try:
            return cls._adapter_classes[key]
        except KeyError as e:
            keys = str(e).strip('\'').split(':')
            raise exceptions.AdapterNotFound(
                'Adapter for %(obj)s to format %(format)s not found' %
                {
                    'obj': keys[1],
                    'format': keys[0]
                }
            )

    #####################
    # Rendering methods #
    #####################

    @classmethod
    def render(cls, obj_format, obj, *args, **kwargs):
        adapter = cls.get_object_adapter(obj, obj_format)
        if isinstance(obj, objects.ListObjectMixin):
            return adapter.render_list(obj, *args, **kwargs)
        else:
            return adapter.render_object(obj, *args, **kwargs)

    @staticmethod
    def is_datetime_field(obj, key):
        field = obj.FIELDS.get(key, {})
        if isinstance(field, fields.Field):
            # TODO(daidv): If we change to use DateTimeField or STL
            # we should change this to exact object
            return isinstance(field, fields.DateTimeField)
        else:
            return field.get('schema', {}).get('format', '') == 'date-time'

    @staticmethod
    def obj_formatdatetime_field(obj):
        return datetime.datetime.strftime(obj, utils.DATETIME_FORMAT)

    @classmethod
    def render_object(cls, obj, *args, **kwargs):
        # The dict we will return to be rendered to JSON / output format
        r_obj = {}
        # Loop over all fields that are supposed to be output
        for key, value in cls.MODIFICATIONS['fields'].items():
            # Get properties for this field
            field_props = cls.MODIFICATIONS['fields'][key]
            # Check if it has to be renamed
            if field_props.get('rename', False):
                new_obj = getattr(obj, field_props.get('rename'))
                # if rename is specified we need to change the key
                obj_key = field_props.get('rename')
            else:
                # if not, move on
                new_obj = getattr(obj, key, None)
                obj_key = key
            # Check if this item is a relation (another DesignateObject that
            # will need to be converted itself
            field = obj.FIELDS.get(obj_key, {})
            if isinstance(field, dict) and field.get('relation'):
                # Get an adapter for the nested object
                # Get the class the object is and get its adapter, then set
                # the item in the dict to the output
                adapter = cls.get_object_adapter(
                    obj.FIELDS[obj_key].get('relation_cls')
                )
                r_obj[key] = adapter.render(cls.ADAPTER_FORMAT, new_obj, *args,
                                            **kwargs)
            elif hasattr(field, 'objname'):
                # Add by daidv: Check if field is OVO field and have a relation
                adapter = cls.get_object_adapter(field.objname)
                r_obj[key] = adapter.render(cls.ADAPTER_FORMAT, new_obj, *args,
                                            **kwargs)
            elif cls.is_datetime_field(obj, obj_key) and new_obj is not None:
                # So, we now have a datetime object to render correctly
                # see bug #1579844
                r_obj[key] = cls.obj_formatdatetime_field(new_obj)
            else:
                # Just attach the damn item if there is no weird edge cases
                r_obj[key] = new_obj

        return r_obj

    @classmethod
    def render_list(cls, list_objects, *args, **kwargs):
        r_list = []
        for obj in list_objects:
            adapter = cls.get_object_adapter(obj)
            r_list.append(
                adapter.render(cls.ADAPTER_FORMAT, obj, *args, **kwargs)
            )
        return {
            cls.MODIFICATIONS['options']['collection_name']: r_list
        }

    #####################
    #  Parsing methods  #
    #####################

    @classmethod
    def parse(cls, obj_format, values, output_object, *args, **kwargs):
        LOG.debug(
            'Creating %s object with values %r',
            output_object.obj_name(), values
        )
        try:
            adapter = cls.get_object_adapter(output_object, obj_format)
            if isinstance(output_object, objects.ListObjectMixin):
                return adapter.parse_list(
                    values, output_object, *args, **kwargs
                )
            else:
                return adapter.parse_object(
                    values, output_object, *args, **kwargs
                )
        except TypeError as e:
            LOG.exception(
                'TypeError creating %(name)s with values %(values)r',
                {
                    'name': output_object.obj_name(),
                    'values': values
                })
            raise exceptions.InvalidObject(
                'Provided object is not valid. Got a TypeError with '
                'message {}'.format(e)
            )

        except AttributeError as e:
            LOG.exception(
                'AttributeError creating %(name)s with values %(values)r',
                {
                    'name': output_object.obj_name(),
                    'values': values
                })
            raise exceptions.InvalidObject(
                'Provided object is not valid. Got an AttributeError with '
                'message {}'.format(e)
            )

        except exceptions.InvalidObject:
            LOG.info(
                'InvalidObject creating %(name)s with values %(values)r',
                {
                    'name': output_object.obj_name(),
                    'values': values
                })
            raise

        except Exception as e:
            LOG.exception(
                'Exception creating %(name)s with values %(values)r',
                {
                    'name': output_object.obj_name(),
                    'values': values
                })
            raise exceptions.InvalidObject(
                'Provided object is not valid. Got a {} error with '
                'message {}'.format(type(e).__name__, e)
            )

    @classmethod
    def parse_object(cls, values, output_object, *args, **kwargs):
        error_keys = []
        for key, value in values.items():
            if key not in cls.MODIFICATIONS['fields']:
                error_keys.append(key)
                continue

            obj_key = key
            field_props = cls.MODIFICATIONS['fields'][key]
            if field_props.get('rename', False):
                obj_key = field_props.get('rename')

            #############################################################
            # TODO(graham): Remove this section of code when validation #
            # is moved into DesignateObjects properly                   #
            #############################################################

            # Check if the field should be allowed change after it is
            # initially set (e.g. zone name)
            if field_props.get('immutable', False):
                if (getattr(output_object, obj_key, False) and
                        getattr(output_object, obj_key) != value):
                    error_keys.append(key)
                    break
            # Is this field a read only field
            elif (field_props.get('read_only', True) and
                  getattr(output_object, obj_key) != value):
                error_keys.append(key)
                break

            # Check if the key is a nested object
            check_field = output_object.FIELDS.get(obj_key, {})
            if (isinstance(check_field, fields.Field) and
                    hasattr(check_field, 'objname')):
                obj_class_name = output_object.FIELDS.get(obj_key).objname
                obj_class = objects.DesignateObject.obj_cls_from_name(
                    obj_class_name
                )
                adapter = cls.get_object_adapter(obj_class_name)
                obj = adapter.parse(value, obj_class())
                setattr(output_object, obj_key, obj)
            elif (not isinstance(check_field, fields.Field) and
                  check_field.get('relation', False)):
                obj_class_name = output_object.FIELDS.get(obj_key, {}).get(
                    'relation_cls'
                )
                obj_class = objects.DesignateObject.obj_cls_from_name(
                    obj_class_name
                )
                adapter = cls.get_object_adapter(obj_class_name)
                obj = adapter.parse(value, obj_class())
                setattr(output_object, obj_key, obj)
            else:
                # No nested objects here, just set the value
                setattr(output_object, obj_key, value)

        if error_keys:
            raise exceptions.InvalidObject(
                'Provided object does not match schema. Keys {} are not '
                'valid for {}'.format(
                    error_keys, cls.MODIFICATIONS['options']['resource_name']
                )
            )

        return output_object

    @classmethod
    def parse_list(cls, values, output_object, *args, **kwargs):
        for item in values:
            adapter = cls.get_object_adapter(output_object.LIST_ITEM_TYPE())
            output_object.append(
                adapter.parse(item, output_object.LIST_ITEM_TYPE())
            )
        return output_object
