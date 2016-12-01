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
import six

from designate import objects
from designate import utils
from designate import exceptions
from designate.i18n import _LE, _LI

LOG = log.getLogger(__name__)


class DesignateObjectAdapterMetaclass(type):

    def __init__(cls, names, bases, dict_):
        if not hasattr(cls, '_adapter_classes'):
            cls._adapter_classes = {}
            return

        key = '%s:%s' % (cls.adapter_format(), cls.adapter_object())

        if key not in cls._adapter_classes:
            cls._adapter_classes[key] = cls
        else:
            raise Exception(
                "Duplicate DesignateAdapterObject with"
                " format '%(format)s and object %(object)s'" %
                {'format': cls.adapter_format(),
                 'object': cls.adapter_object()}
            )


@six.add_metaclass(DesignateObjectAdapterMetaclass)
class DesignateAdapter(object):
    """docstring for DesignateObjectAdapter"""

    ADAPTER_OBJECT = objects.DesignateObject

    @classmethod
    def adapter_format(cls):
        return cls.ADAPTER_FORMAT

    @classmethod
    def adapter_object(cls):
        return cls.ADAPTER_OBJECT.obj_name()

    @classmethod
    def get_object_adapter(cls, format_, object):
        if isinstance(object, objects.DesignateObject):
            key = '%s:%s' % (format_, object.obj_name())
        else:
            key = '%s:%s' % (format_, object)
        try:
            return cls._adapter_classes[key]
        except KeyError as e:
            keys = six.text_type(e).split(':')
            msg = "Adapter for %(object)s to format %(format)s not found" % {
                "object": keys[1],
                "format": keys[0]
            }
            raise exceptions.AdapterNotFound(msg)

    #####################
    # Rendering methods #
    #####################

    @classmethod
    def render(cls, format_, object, *args, **kwargs):

        if isinstance(object, objects.ListObjectMixin):
            # type_ = 'list'
            return cls.get_object_adapter(
                format_, object)._render_list(object, *args, **kwargs)
        else:
            # type_ = 'object'
            return cls.get_object_adapter(
                format_, object)._render_object(object, *args, **kwargs)

    @classmethod
    def _render_object(cls, object, *args, **kwargs):

        # We need to findout the type of field sometimes - these are helper
        # methods for that.

        def _is_datetime_field(object, key):
            field = object.FIELDS.get(key, {})
            return field.get('schema', {}).get('format', '') == 'date-time'

        def _format_datetime_field(obj):
            return datetime.datetime.strftime(
                    obj, utils.DATETIME_FORMAT)

        # The dict we will return to be rendered to JSON / output format
        r_obj = {}
        # Loop over all fields that are supposed to be output
        for key, value in cls.MODIFICATIONS['fields'].items():
            # Get properties for this field
            field_props = cls.MODIFICATIONS['fields'][key]
            # Check if it has to be renamed
            if field_props.get('rename', False):
                obj = getattr(object, field_props.get('rename'))
                # if rename is specified we need to change the key
                obj_key = field_props.get('rename')
            else:
                # if not, move on
                obj = getattr(object, key, None)
                obj_key = key
            # Check if this item is a relation (another DesignateObject that
            # will need to be converted itself
            if object.FIELDS.get(obj_key, {}).get('relation'):
                # Get a adapter for the nested object
                # Get the class the object is and get its adapter, then set
                # the item in the dict to the output
                r_obj[key] = cls.get_object_adapter(
                    cls.ADAPTER_FORMAT,
                    object.FIELDS[obj_key].get('relation_cls')).render(
                        cls.ADAPTER_FORMAT, obj, *args, **kwargs)
            elif _is_datetime_field(object, obj_key) and obj is not None:
                # So, we now have a datetime object to render correctly
                # see bug #1579844
                r_obj[key] = _format_datetime_field(obj)
            else:
                # Just attach the damn item if there is no weird edge cases
                r_obj[key] = obj
        # Send it back
        return r_obj

    @classmethod
    def _render_list(cls, list_object, *args, **kwargs):
        # The list we will return to be rendered to JSON / output format
        r_list = []
        # iterate and convert each DesignateObject in the list, and append to
        # the object we are returning
        for object in list_object:
            r_list.append(cls.get_object_adapter(
                cls.ADAPTER_FORMAT,
                object).render(cls.ADAPTER_FORMAT, object, *args, **kwargs))
        return {cls.MODIFICATIONS['options']['collection_name']: r_list}

    #####################
    #  Parsing methods  #
    #####################

    @classmethod
    def parse(cls, format_, values, output_object, *args, **kwargs):

        LOG.debug("Creating %s object with values %r" %
                  (output_object.obj_name(), values))

        try:
            if isinstance(output_object, objects.ListObjectMixin):
                # type_ = 'list'
                return cls.get_object_adapter(
                    format_,
                    output_object)._parse_list(
                        values, output_object, *args, **kwargs)
            else:
                # type_ = 'object'
                return cls.get_object_adapter(
                    format_,
                    output_object)._parse_object(
                        values, output_object, *args, **kwargs)

        except TypeError as e:
            LOG.exception(_LE("TypeError creating %(name)s with values"
                              " %(values)r") %
                          {"name": output_object.obj_name(), "values": values})
            error_message = (u'Provided object is not valid. '
                            u'Got a TypeError with message {}'.format(
                                six.text_type(e)))
            raise exceptions.InvalidObject(error_message)

        except AttributeError as e:
            LOG.exception(_LE("AttributeError creating %(name)s "
                              "with values %(values)r") %
                          {"name": output_object.obj_name(), "values": values})
            error_message = (u'Provided object is not valid. '
                            u'Got an AttributeError with message {}'.format(
                                six.text_type(e)))
            raise exceptions.InvalidObject(error_message)

        except exceptions.InvalidObject:
            LOG.info(_LI("InvalidObject creating %(name)s with "
                         "values %(values)r"),
                     {"name": output_object.obj_name(), "values": values})
            raise

        except Exception as e:
            LOG.exception(_LE("Exception creating %(name)s with "
                              "values %(values)r") %
                          {"name": output_object.obj_name(), "values": values})
            error_message = (u'Provided object is not valid. '
                            u'Got a {} error with message {}'.format(
                                type(e).__name__, six.text_type(e)))
            raise exceptions.InvalidObject(error_message)

    @classmethod
    def _parse_object(cls, values, output_object, *args, **kwargs):
        error_keys = []

        for key, value in values.items():
            if key in cls.MODIFICATIONS['fields']:
                # No rename needed
                obj_key = key
                # This item may need to be translated
                if cls.MODIFICATIONS['fields'][key].get('rename', False):
                    obj_key = cls.MODIFICATIONS['fields'][key].get('rename')

                ##############################################################
                # TODO(graham): Remove this section of code  when validation #
                # is moved into DesignateObjects properly                    #
                ##############################################################

                # Check if the field should be allowed change after it is
                # initially set (eg zone name)
                if cls.MODIFICATIONS['fields'][key].get('immutable', False):
                    if getattr(output_object, obj_key, False) and \
                            getattr(output_object, obj_key) != value:
                        error_keys.append(key)
                        break
                # Is this field a read only field
                elif cls.MODIFICATIONS['fields'][key].get('read_only', True) \
                        and getattr(output_object, obj_key) != value:
                    error_keys.append(key)
                    break

                # Check if the key is a nested object
                if output_object.FIELDS.get(obj_key, {}).get(
                        'relation', False):
                    # Get the right class name
                    obj_class_name = output_object.FIELDS.get(
                        obj_key, {}).get('relation_cls')
                    # Get the an instance of it
                    obj_class = \
                        objects.DesignateObject.obj_cls_from_name(
                            obj_class_name)
                    # Get the adapted object
                    obj = \
                        cls.get_object_adapter(
                            cls.ADAPTER_FORMAT, obj_class_name).parse(
                                value, obj_class())
                    # Set the object on the main object
                    setattr(output_object, obj_key, obj)
                else:
                    # No nested objects here, just set the value
                    setattr(output_object, obj_key, value)
            else:
                # We got an extra key
                error_keys.append(key)

        if error_keys:
            error_message = str.format(
                'Provided object does not match schema.  Keys {0} are not '
                'valid for {1}',
                error_keys, cls.MODIFICATIONS['options']['resource_name'])

            raise exceptions.InvalidObject(error_message)

        return output_object

    @classmethod
    def _parse_list(cls, values, output_object, *args, **kwargs):

        for item in values:
            # Add the object to the list
            output_object.append(
                # Get the right Adapter
                cls.get_object_adapter(
                    cls.ADAPTER_FORMAT,
                    # This gets the internal type of the list, and parses it
                    # We need to do `get_object_adapter` as we need a new
                    # instance of the Adapter
                    output_object.LIST_ITEM_TYPE()).parse(
                        item, output_object.LIST_ITEM_TYPE()))

        # Return the filled list
        return output_object
