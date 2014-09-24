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

import six

from designate.openstack.common import importutils


class NotSpecifiedSentinel:
    pass


def get_attrname(name):
    """Return the mangled name of the attribute's underlying storage."""
    return '_%s' % name


def make_class_properties(cls):
    """Build getter and setter methods for all the objects attributes"""
    cls.FIELDS = list(cls.FIELDS)

    for supercls in cls.mro()[1:-1]:
        if not hasattr(supercls, 'FIELDS'):
            continue
        for field in supercls.FIELDS:
            if field not in cls.FIELDS:
                cls.FIELDS.append(field)

    for field in cls.FIELDS:
        def getter(self, name=field):
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


class DesignateObjectMetaclass(type):
    def __init__(cls, names, bases, dict_):
        make_class_properties(cls)


@six.add_metaclass(DesignateObjectMetaclass)
class DesignateObject(object):
    FIELDS = []

    @staticmethod
    def from_primitive(primitive):
        """
        Construct an object from primitive types

        This is used while deserializing the object.
        """
        cls = importutils.import_class(primitive['designate_object.name'])
        return cls._obj_from_primitive(primitive)

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

    def __init__(self, **kwargs):
        self._obj_changes = set()
        self._obj_original_values = dict()

        for name, value in kwargs.items():
            if name in self.FIELDS:
                setattr(self, name, value)
            else:
                raise TypeError("'%s' is an invalid keyword argument" % name)

    def to_primitive(self):
        """
        Convert the object to primitive types so that the object can be
        serialized.
        NOTE: Currently all the designate objects contain primitive types that
        do not need special handling.  If this changes we need to modify this
        function.
        """
        class_name = self.__class__.__name__
        if self.__module__:
            class_name = self.__module__ + '.' + self.__class__.__name__

        data = {}

        for field in self.FIELDS:
            if self.obj_attr_is_set(field):
                if isinstance(getattr(self, field), DesignateObject):
                    data[field] = getattr(self, field).to_primitive()
                else:
                    data[field] = getattr(self, field)

        return {
            'designate_object.name': class_name,
            'designate_object.data': data,
            'designate_object.changes': sorted(self._obj_changes),
            'designate_object.original_values': dict(self._obj_original_values)
        }

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

    def __deepcopy__(self, memodict=None):
        """
        Efficiently make a deep copy of this object.

        "Efficiently" is used here a relative term, this will be faster
        than allowing python to naively deepcopy the object.
        """

        memodict = memodict or {}

        c_obj = self.__class__()

        for field in self.FIELDS:
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

    Eventually, this should be removed.
    """
    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __contains__(self, item):
        return item in self.FIELDS

    def get(self, key, default=NotSpecifiedSentinel):
        if key not in self.FIELDS:
            raise AttributeError("'%s' object has no attribute '%s'" % (
                                 self.__class__, key))

        if default != NotSpecifiedSentinel and not self.obj_attr_is_set(key):
            return default
        else:
            return getattr(self, key)

    def update(self, values):
        for k, v in values.iteritems():
            setattr(self, k, v)

    def iteritems(self):
        for field in self.FIELDS:
            if self.obj_attr_is_set(field):
                yield field, getattr(self, field)

    def __iter__(self):
        for field in self.FIELDS:
            if self.obj_attr_is_set(field):
                yield field, getattr(self, field)

    items = lambda self: list(self.iteritems())


class ListObjectMixin(object):
    """Mixin class for lists of objects"""
    FIELDS = ['objects']
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

    def __init__(self, *args, **kwargs):
        super(ListObjectMixin, self).__init__(*args, **kwargs)
        if 'objects' not in kwargs:
            self.objects = []
            self.obj_reset_changes(['objects'])

    def to_primitive(self):
        class_name = self.__class__.__name__
        if self.__module__:
            class_name = self.__module__ + '.' + self.__class__.__name__

        data = {}

        for field in self.FIELDS:
            if self.obj_attr_is_set(field):
                if field == 'objects':
                    data[field] = [o.to_primitive() for o in self.objects]
                elif isinstance(getattr(self, field), DesignateObject):
                    data[field] = getattr(self, field).to_primitive()
                else:
                    data[field] = getattr(self, field)

        return {
            'designate_object.name': class_name,
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
        return self.objects.insert(index)

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
    FIELDS = ['id', 'created_at', 'updated_at', 'version']


class SoftDeleteObjectMixin(object):
    """
    Mixin class for Soft-Deleted objects.

    This adds the fields that we use in common for all soft-deleted objects.
    """
    FIELDS = ['deleted', 'deleted_at']
