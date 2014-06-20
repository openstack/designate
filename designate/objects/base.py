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
import six


class NotSpecifiedSentinel:
    pass


def get_attrname(name):
    """ Return the mangled name of the attribute's underlying storage. """
    return '_%s' % name


def make_class_properties(cls):
    """ Build getter and setter methods for all the objects attributes """
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
            return setattr(self, get_attrname(name), value)

        setattr(cls, field, property(getter, setter))


class DesignateObjectMetaclass(type):
    def __init__(cls, names, bases, dict_):
        make_class_properties(cls)


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

        if default != NotSpecifiedSentinel and not self.attr_is_set(key):
            return default
        else:
            return self[key]

    def update(self, values):
        """ Make the model object behave like a dict """
        for k, v in values.iteritems():
            self[k] = v

    def iteritems(self):
        """
        Make the model object behave like a dict.

        Includes attributes from joins.
        """
        local = dict(self)
        joined = dict([(k, v) for k, v in self.__dict__.iteritems()
                      if not k[0] == '_'])
        local.update(joined)
        return local.iteritems()


class PersistentObjectMixin(object):
    """
    Mixin class for Persistent objects.

    This adds the fields that we use in common for all persisent objects.
    """
    FIELDS = ['id', 'created_at', 'updated_at', 'version']


@six.add_metaclass(DesignateObjectMetaclass)
class DesignateObject(DictObjectMixin):
    FIELDS = []

    @classmethod
    def from_sqla(cls, obj):
        """
        Convert from a SQLA Model to a Designate Object

        Eventually, when we move from SQLA ORM to SQLA Core, this can be
        removed.
        """
        fields = {}

        for fieldname in cls.FIELDS:
            if hasattr(obj, fieldname):
                fields[fieldname] = getattr(obj, fieldname)

        return cls(**fields)

    @classmethod
    def from_primitive(cls, primitive):
        """
        Construct an object from primitive types

        This is used while deserializing the object.

        NOTE: Currently all the designate objects contain primitive types that
        do not need special handling.  If this changes we need to modify this
        function.
        """
        fields = primitive['designate_object.data']
        return cls(**fields)

    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            if name in self.FIELDS:
                setattr(self, name, value)
            else:
                raise TypeError("'%s' is an invalid keyword argument" % name)

    def attr_is_set(self, name):
        """
        Return True or False depending of if a particular attribute has had
        an attribute's value explicitly set.
        """
        return hasattr(self, get_attrname(name))

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
            if self.attr_is_set(field):
                data[field] = self[field]

        return {
            'designate_object.name': class_name,
            'designate_object.data': data,
        }

    def __iter__(self):
        # Redundant?
        self._i = iter(self.FIELDS)
        return self

    def next(self):
        # Redundant?
        n = self._i.next()
        return n, getattr(self, n)
