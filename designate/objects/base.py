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
import copy
import urlparse

import six
import jsonschema
from oslo_log import log as logging

from designate import exceptions
from designate.schema import validators
from designate.schema import format


LOG = logging.getLogger(__name__)


class NotSpecifiedSentinel:
    pass


def get_attrname(name):
    """Return the mangled name of the attribute's underlying storage."""
    return '_obj_field_%s' % name


def make_class_properties(cls):
    """Build getter and setter methods for all the objects attributes"""
    # Prepare an empty dict to gather the merged/final set of fields
    fields = {}

    # Add each supercls's fields
    for supercls in cls.mro()[1:-1]:
        if not hasattr(supercls, 'FIELDS'):
            continue
        fields.update(supercls.FIELDS)

    # Add our fields
    fields.update(cls.FIELDS)

    # Store the results
    cls.FIELDS = fields

    for field in cls.FIELDS.keys():
        def getter(self, name=field):
            self._obj_check_relation(name)
            return getattr(self, get_attrname(name), None)

        def setter(self, value, name=field):
            if (self.obj_attr_is_set(name) and value != getattr(self, name)
                    or not self.obj_attr_is_set(name)):
                self._obj_changes.add(name)

            if (self.obj_attr_is_set(name) and value != getattr(self, name)
                    and name not in self._obj_original_values.keys()):
                self._obj_original_values[name] = getattr(self, name)

            return setattr(self, get_attrname(name), value)

        setattr(cls, field, property(getter, setter))


def _schema_ref_resolver(uri):
    """
    Fetches an DesignateObject's schema from a JSON Schema Reference URI

    Sample URI: obj://ObjectName#/subpathA/subpathB
    """
    obj_name = urlparse.urlsplit(uri).netloc
    obj = DesignateObject.obj_cls_from_name(obj_name)

    return obj.obj_get_schema()


def make_class_validator(obj):

    schema = {
        '$schema': 'http://json-schema.org/draft-04/hyper-schema',
        'title': obj.obj_name(),
        'description': 'Designate %s Object' % obj.obj_name(),
    }

    if isinstance(obj, ListObjectMixin):

        schema['type'] = 'array',
        schema['items'] = make_class_validator(obj.LIST_ITEM_TYPE)

    else:
        schema['type'] = 'object'
        schema['additionalProperties'] = False
        schema['required'] = []
        schema['properties'] = {}

        for name, properties in obj.FIELDS.items():
            if properties.get('relation', False):
                if obj.obj_attr_is_set(name):
                    schema['properties'][name] = \
                        make_class_validator(getattr(obj, name))
            else:
                schema['properties'][name] = properties.get('schema', {})

            if properties.get('required', False):
                schema['required'].append(name)

    resolver = jsonschema.RefResolver.from_schema(
        schema, handlers={'obj': _schema_ref_resolver})

    obj._obj_validator = validators.Draft4Validator(
        schema, resolver=resolver, format_checker=format.draft4_format_checker)

    return schema


class DesignateObjectMetaclass(type):
    def __init__(cls, names, bases, dict_):
        if not hasattr(cls, '_obj_classes'):
            # This means we're working on the base DesignateObject class,
            # and can skip the remaining Metaclass functionality
            cls._obj_classes = {}
            return

        make_class_properties(cls)

        # Add a reference to the finished class into the _obj_classes
        # dictionary, allowing us to lookup classes by their name later - this
        # is useful for e.g. referencing another DesignateObject in a
        # validation schema.
        if cls.obj_name() not in cls._obj_classes:
            cls._obj_classes[cls.obj_name()] = cls
        else:
            raise Exception("Duplicate DesignateObject with name '%(name)s'" %
                            {'name': cls.obj_name()})


@six.add_metaclass(DesignateObjectMetaclass)
class DesignateObject(object):
    FIELDS = {}

    def _obj_check_relation(self, name):
        if name in self.FIELDS and self.FIELDS[name].get('relation', False):
            if not self.obj_attr_is_set(name):
                raise exceptions.RelationNotLoaded

    @classmethod
    def obj_cls_from_name(cls, name):
        """Retrieves a object cls from the registry by name and returns it."""
        return cls._obj_classes[name]

    @classmethod
    def from_primitive(cls, primitive):
        """
        Construct an object from primitive types

        This is used while deserializing the object.
        """
        objcls = cls.obj_cls_from_name(primitive['designate_object.name'])
        return objcls._obj_from_primitive(primitive)

    @classmethod
    def _obj_from_primitive(cls, primitive):
        instance = cls()

        for field, value in primitive['designate_object.data'].items():
            if isinstance(value, dict) and 'designate_object.name' in value:
                setattr(instance, field, DesignateObject.from_primitive(value))
            else:
                setattr(instance, field, value)

        instance._obj_changes = set(primitive['designate_object.changes'])
        instance._obj_original_values = \
            primitive['designate_object.original_values']

        return instance

    @classmethod
    def from_dict(cls, _dict):
        instance = cls()

        for field, value in _dict.items():
            if (field in instance.FIELDS and
                    instance.FIELDS[field].get('relation', False)):
                relation_cls_name = instance.FIELDS[field]['relation_cls']
                # We're dealing with a relation, we'll want to create the
                # correct object type and recurse
                relation_cls = cls.obj_cls_from_name(relation_cls_name)

                if isinstance(value, list):
                    setattr(instance, field, relation_cls.from_list(value))
                else:
                    setattr(instance, field, relation_cls.from_dict(value))

            else:
                setattr(instance, field, value)

        return instance

    @classmethod
    def from_list(cls, _list):
        raise NotImplementedError()

    @classmethod
    def obj_name(cls):
        """Return a canonical name for this object which will be used over
        the wire and in validation schemas.
        """
        return cls.__name__

    @classmethod
    def obj_get_schema(cls):
        """Returns the JSON Schema for this Object."""
        return cls._obj_validator.schema

    def __init__(self, **kwargs):
        self._obj_changes = set()
        self._obj_original_values = dict()

        for name, value in kwargs.items():
            if name in self.FIELDS.keys():
                setattr(self, name, value)
            else:
                raise TypeError("__init__() got an unexpected keyword "
                                "argument '%(name)s'" % {'name': name})

    def to_primitive(self):
        """
        Convert the object to primitive types so that the object can be
        serialized.
        NOTE: Currently all the designate objects contain primitive types that
        do not need special handling.  If this changes we need to modify this
        function.
        """
        data = {}

        for field in self.FIELDS.keys():
            if self.obj_attr_is_set(field):
                if isinstance(getattr(self, field), DesignateObject):
                    data[field] = getattr(self, field).to_primitive()
                else:
                    data[field] = getattr(self, field)

        return {
            'designate_object.name': self.obj_name(),
            'designate_object.data': data,
            'designate_object.changes': sorted(self._obj_changes),
            'designate_object.original_values': dict(self._obj_original_values)
        }

    def to_dict(self):
        """Convert the object to a simple dictionary."""
        data = {}

        for field in self.FIELDS.keys():
            if self.obj_attr_is_set(field):
                if isinstance(getattr(self, field), ListObjectMixin):
                    data[field] = getattr(self, field).to_list()
                elif isinstance(getattr(self, field), DesignateObject):
                    data[field] = getattr(self, field).to_dict()
                else:
                    data[field] = getattr(self, field)

        return data

    def update(self, values):
        """Update a object's fields with the supplied key/value pairs"""
        for k, v in values.iteritems():
            setattr(self, k, v)

    @property
    def is_valid(self):
        """Returns True if the Object is valid."""

        make_class_validator(self)

        return self._obj_validator.is_valid(self.to_dict())

    def validate(self):

        make_class_validator(self)

        # NOTE(kiall): We make use of the Object registry here in order to
        #              avoid an impossible circular import.
        ValidationErrorList = self.obj_cls_from_name('ValidationErrorList')
        ValidationError = self.obj_cls_from_name('ValidationError')

        values = self.to_dict()
        errors = ValidationErrorList()

        LOG.debug("Validating '%(name)s' object with values: %(values)r", {
            'name': self.obj_name(),
            'values': values,
        })

        for error in self._obj_validator.iter_errors(values):
            errors.append(ValidationError.from_js_error(error))

        if len(errors) > 0:
            raise exceptions.InvalidObject(
                "Provided object does not match "
                "schema", errors=errors, object=self)

    def obj_attr_is_set(self, name):
        """
        Return True or False depending of if a particular attribute has had
        an attribute's value explicitly set.
        """
        return hasattr(self, get_attrname(name))

    def obj_what_changed(self):
        """Returns a set of fields that have been modified."""
        return set(self._obj_changes)

    def obj_get_changes(self):
        """Returns a dict of changed fields and their new values."""
        changes = {}

        for key in self.obj_what_changed():
            changes[key] = getattr(self, key)

        return changes

    def obj_reset_changes(self, fields=None):
        """Reset the list of fields that have been changed."""
        if fields:
            self._obj_changes -= set(fields)
            for field in fields:
                self._obj_original_values.pop(field, None)

        else:
            self._obj_changes.clear()
            self._obj_original_values = dict()

    def obj_get_original_value(self, field):
        """Returns the original value of a field."""
        if field in self._obj_original_values.keys():
            return self._obj_original_values[field]
        elif self.obj_attr_is_set(field):
            return getattr(self, field)
        else:
            raise KeyError(field)

    def __setattr__(self, name, value):
        """Enforces all object attributes are private or well defined"""
        if name[0:5] == '_obj_' or name in self.FIELDS.keys():
            super(DesignateObject, self).__setattr__(name, value)

        else:
            raise AttributeError(
                "Designate object '%(type)s' has no attribute '%(name)s'" % {
                    'type': self.obj_name(),
                    'name': name,
                })

    def __deepcopy__(self, memodict=None):
        """
        Efficiently make a deep copy of this object.

        "Efficiently" is used here a relative term, this will be faster
        than allowing python to naively deepcopy the object.
        """

        memodict = memodict or {}

        c_obj = self.__class__()

        for field in self.FIELDS.keys():
            if self.obj_attr_is_set(field):
                c_field = copy.deepcopy(getattr(self, field), memodict)
                setattr(c_obj, field, c_field)

        c_obj._obj_changes = set(self._obj_changes)

        return c_obj

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False

        return self.to_primitive() == other.to_primitive()

    def __ne__(self, other):
        return not(self.__eq__(other))


class DictObjectMixin(object):
    """
    Mixin to allow DesignateObjects to behave like dictionaries

    Eventually, this should be removed as other code is updated to use object
    rather than dictionary accessors.
    """
    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __contains__(self, item):
        return item in self.FIELDS.keys()

    def get(self, key, default=NotSpecifiedSentinel):
        if key not in self.FIELDS.keys():
            raise AttributeError("'%s' object has no attribute '%s'" % (
                                 self.__class__, key))

        if default != NotSpecifiedSentinel and not self.obj_attr_is_set(key):
            return default
        else:
            return getattr(self, key)

    def iteritems(self):
        for field in self.FIELDS.keys():
            if self.obj_attr_is_set(field):
                yield field, getattr(self, field)

    def __iter__(self):
        for field in self.FIELDS.keys():
            if self.obj_attr_is_set(field):
                yield field, getattr(self, field)

    items = lambda self: list(self.iteritems())


class ListObjectMixin(object):
    """Mixin to allow DesignateObjects to behave like python lists."""
    FIELDS = {
        'objects': {
            'relation': True
        }
    }
    LIST_ITEM_TYPE = DesignateObject

    @classmethod
    def _obj_from_primitive(cls, primitive):
        instance = cls()

        for field, value in primitive['designate_object.data'].items():
            if field == 'objects':
                instance.objects = [DesignateObject.from_primitive(v) for v in
                                    value]
            elif isinstance(value, dict) and 'designate_object.name' in value:
                setattr(instance, field, DesignateObject.from_primitive(value))
            else:
                setattr(instance, field, value)

        instance._obj_changes = set(primitive['designate_object.changes'])
        instance._obj_original_values = \
            primitive['designate_object.original_values']

        return instance

    @classmethod
    def from_list(cls, _list):
        instance = cls()

        for item in _list:
            instance.append(cls.LIST_ITEM_TYPE.from_dict(item))

        return instance

    def to_list(self):

        list_ = []

        for item in self.objects:
            if isinstance(item, ListObjectMixin):
                list_.append(item.to_list())
            elif isinstance(item, DesignateObject):
                list_.append(item.to_dict())
            else:
                list_.append(item)

        return list_

    def __init__(self, *args, **kwargs):
        super(ListObjectMixin, self).__init__(*args, **kwargs)
        if 'objects' not in kwargs:
            self.objects = []
            self.obj_reset_changes(['objects'])

    def to_primitive(self):
        data = {}

        for field in self.FIELDS.keys():
            if self.obj_attr_is_set(field):
                if field == 'objects':
                    data[field] = [o.to_primitive() for o in self.objects]
                elif isinstance(getattr(self, field), DesignateObject):
                    data[field] = getattr(self, field).to_primitive()
                else:
                    data[field] = getattr(self, field)

        return {
            'designate_object.name': self.obj_name(),
            'designate_object.data': data,
            'designate_object.changes': list(self._obj_changes),
            'designate_object.original_values': dict(self._obj_original_values)
        }

    def __iter__(self):
        """List iterator interface"""
        return iter(self.objects)

    def __len__(self):
        """List length"""
        return len(self.objects)

    def __getitem__(self, index):
        """List index access"""
        if isinstance(index, slice):
            new_obj = self.__class__()
            new_obj.objects = self.objects[index]
            new_obj.obj_reset_changes()
            return new_obj
        return self.objects[index]

    def __setitem__(self, index, value):
        """Set list index value"""
        self.objects[index] = value

    def __contains__(self, value):
        """List membership test"""
        return value in self.objects

    def append(self, value):
        """Append a value to the list"""
        return self.objects.append(value)

    def extend(self, values):
        """Extend the list by appending all the items in the given list"""
        return self.objects.extend(values)

    def pop(self, index):
        """Pop a value from the list"""
        return self.objects.pop(index)

    def insert(self, index, value):
        """Insert a value into the list at the given index"""
        return self.objects.insert(index, value)

    def remove(self, value):
        """Remove a value from the list"""
        return self.objects.remove(value)

    def index(self, value):
        """List index of value"""
        return self.objects.index(value)

    def count(self, value):
        """List count of value occurrences"""
        return self.objects.count(value)

    def sort(self, cmp=None, key=None, reverse=False):
        self.objects.sort(cmp=cmp, key=key, reverse=reverse)

    def obj_what_changed(self):
        changes = set(self._obj_changes)
        for item in self.objects:
            if item.obj_what_changed():
                changes.add('objects')
        return changes


class PersistentObjectMixin(object):
    """
    Mixin class for Persistent objects.

    This adds the fields that we use in common for all persistent objects.
    """
    FIELDS = {
        'id': {
            'schema': {
                'type': 'string',
                'format': 'uuid',
            },
            'read_only': True
        },
        'created_at': {
            'schema': {
                'type': 'string',
                'format': 'date-time',
            },
            'read_only': True
        },
        'updated_at': {
            'schema': {
                'type': ['string', 'null'],
                'format': 'date-time',
            },
            'read_only': True
        },
        'version': {
            'schema': {
                'type': 'integer',
            },
            'read_only': True
        }
    }


class SoftDeleteObjectMixin(object):
    """
    Mixin class for Soft-Deleted objects.

    This adds the fields that we use in common for all soft-deleted objects.
    """
    FIELDS = {
        'deleted': {
            'schema': {
                'type': ['string', 'integer'],
            },
            'read_only': True
        },
        'deleted_at': {
            'schema': {
                'type': ['string', 'null'],
                'format': 'date-time',
            },
            'read_only': True
        }
    }


class PagedListObjectMixin(object):
    """
    Mixin class for List objects.

    This adds fields that would populate API metadata for collections.
    """
    FIELDS = {
        'total_count': {
            'schema': {
                'type': ['integer'],
            }
        }
    }
