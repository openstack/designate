# Copyright (c) 2017 Fujitsu Vietnam Ltd.
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
from oslo_log import log as logging
from oslo_versionedobjects import exception
from oslo_utils import excutils
from oslo_versionedobjects import base
from oslo_versionedobjects.base import VersionedObjectDictCompat as DictObjectMixin  # noqa

from designate.i18n import _
from designate.i18n import _LE
from designate.objects import fields
from designate import exceptions

LOG = logging.getLogger(__name__)


def _get_attrname(name):
    return "_obj_{}".format(name)


def get_dict_attr(klass, attr):
    for klass in [klass] + klass.mro():
        if attr in klass.__dict__:
            return klass.__dict__[attr]
    raise AttributeError


class DesignateObject(base.VersionedObject):
    OBJ_SERIAL_NAMESPACE = 'designate_object'
    OBJ_PROJECT_NAMESPACE = 'designate'

    STRING_KEYS = []

    def __init__(self, *args, **kwargs):
        super(DesignateObject, self).__init__(self, *args, **kwargs)
        self._obj_original_values = dict()
        self.FIELDS = self.fields

    @classmethod
    def _make_obj_str(cls, keys):
        msg = "<%(name)s" % {'name': cls.obj_name()}
        for key in keys:
            msg += " {0}:'%({0})s'".format(key)
        msg += ">"
        return msg

    def __str__(self):
        return (self._make_obj_str(self.STRING_KEYS)
                % self)

    def save(self, context):
        pass

    def _obj_check_relation(self, name):
        if name in self.fields:
            if hasattr(self.fields.get(name), 'objname'):
                if not self.obj_attr_is_set(name):
                    raise exceptions.RelationNotLoaded(
                        object=self, relation=name)

    def to_dict(self):
        """Convert the object to a simple dictionary."""
        data = {}

        for field in six.iterkeys(self.fields):
            if self.obj_attr_is_set(field):
                val = getattr(self, field)
                if isinstance(val, ListObjectMixin):
                    data[field] = val.to_list()
                elif isinstance(val, DesignateObject):
                    data[field] = val.to_dict()
                else:
                    data[field] = val

        return data

    def update(self, values):
        """Update a object's fields with the supplied key/value pairs"""
        for k, v in values.items():
            setattr(self, k, v)

    @classmethod
    def from_dict(cls, _dict):
        instance = cls()

        for field, value in _dict.items():
            if (field in instance.fields and
                    hasattr(instance.fields.get(field), 'objname')):
                relation_cls_name = instance.fields[field].objname
                # We're dealing with a relation, we'll want to create the
                # correct object type and recurse
                relation_cls = cls.obj_class_from_name(
                    relation_cls_name, '1.0')

                if isinstance(value, list):
                    setattr(instance, field, relation_cls.from_list(value))
                else:
                    setattr(instance, field, relation_cls.from_dict(value))

            else:
                setattr(instance, field, value)

        return instance

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False

        return self.obj_to_primitive() == other.obj_to_primitive()

    def __ne__(self, other):
        return not (self.__eq__(other))

    def __repr__(self):
        return "OVO Objects"

    # TODO(daidv): all of bellow functions should
    # be removed when we completed migration.
    def to_primitive(self):
        return self.obj_to_primitive()

    @classmethod
    def from_primitive(cls, primitive, context=None):
        return cls.obj_from_primitive(primitive, context)

    @classmethod
    def obj_cls_from_name(cls, name):
        return cls.obj_class_from_name(name, '1.0')

    @classmethod
    def obj_get_schema(cls):
        return cls.to_json_schema()

    def obj_reset_changes(self, fields=None, recursive=False):
        """Reset the list of fields that have been changed.

        :param fields: List of fields to reset, or "all" if None.
        :param recursive: Call obj_reset_changes(recursive=True) on
                          any sub-objects within the list of fields
                          being reset.

        This is NOT "revert to previous values".

        Specifying fields on recursive resets will only be honored at the top
        level. Everything below the top will reset all.
        """
        if recursive:
            for field in self.obj_get_changes():

                # Ignore fields not in requested set (if applicable)
                if fields and field not in fields:
                    continue

                # Skip any fields that are unset
                if not self.obj_attr_is_set(field):
                    continue

                value = getattr(self, field)

                # Don't reset nulled fields
                if value is None:
                    continue

                # Reset straight Object and ListOfObjects fields
                if isinstance(self.fields[field], self.obj_fields.ObjectField):
                    value.obj_reset_changes(recursive=True)
                elif isinstance(self.fields[field],
                                self.obj_fields.ListOfObjectsField):
                    for thing in value:
                        thing.obj_reset_changes(recursive=True)

        if fields:
            self._changed_fields -= set(fields)
            for field in fields:
                self._obj_original_values.pop(field, None)
        else:
            self._changed_fields.clear()
            self._obj_original_values = dict()

    def obj_get_original_value(self, field):
        """Returns the original value of a field."""
        if field in list(six.iterkeys(self._obj_original_values)):
            return self._obj_original_values[field]
        elif self.obj_attr_is_set(field):
            return getattr(self, field)
        else:
            raise KeyError(field)

    @property
    def obj_fields(self):
        return list(self.fields.keys()) + self.obj_extra_fields

    @property
    def obj_context(self):
        return self._context

    def validate(self):
        self.fields = self.FIELDS
        try:
            for name in self.fields:
                field = self.fields[name]
                if self.obj_attr_is_set(name):
                    value = getattr(self, name)  # Check relation
                    field.coerce(self, name, value)  # Check value
                    if isinstance(value, base.ObjectListBase):
                        for obj in value:
                            obj.validate()
                elif not field.nullable:
                    # Check required is True ~ nullable is False
                    raise exceptions.InvalidObject
        except Exception:
            raise exceptions.InvalidObject


class ListObjectMixin(base.ObjectListBase):
    LIST_ITEM_TYPE = DesignateObject

    @classmethod
    def _obj_from_primitive(cls, context, objver, primitive):
        instance = cls()
        instance.VERSION = objver
        instance._context = context

        for field, value in primitive['designate_object.data'].items():
            if field == 'objects':
                instance.objects = [
                    DesignateObject.obj_from_primitive(v) for v in value]
            elif isinstance(value, dict) and 'designate_object.name' in value:
                setattr(instance, field,
                        DesignateObject.obj_from_primitive(value))
            else:
                setattr(instance, field, value)

        instance._obj_changes = set(
            primitive.get('designate_object.changes', []))
        instance._obj_original_values = \
            primitive.get('designate_object.original_values', {})

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

    def __str__(self):
        return (_("<%(type)s count:'%(count)s' object:'%(list_type)s'>")
                % {'count': len(self),
                   'type': self.LIST_ITEM_TYPE.obj_name(),
                   'list_type': self.obj_name()})

    def __iter__(self):
        """List iterator interface"""
        return iter(self.objects)

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


class AttributeListObjectMixin(ListObjectMixin):
    """
    Mixin class for "Attribute" objects.

    Attribute objects are ListObjects, who's memebers have a "key" and "value"
    property, which should be exposed on the list itself as list.<key>.
    """

    @classmethod
    def from_dict(cls, _dict):
        instances = cls.from_list([{'key': k, 'value': v} for k, v
                                   in _dict.items()])

        return cls.from_list(instances)

    def to_dict(self):
        data = {}

        for item in self.objects:
            data[item.key] = item.value

        return data

    def get(self, key, default=None):
        for obj in self.objects:
            if obj.key == key:
                return obj.value

        return default


class PersistentObjectMixin(object):
    """
    Mixin class for Persistent objects.

    This adds the fields that we use in common for all persistent objects.
    """
    fields = {
        'id': fields.UUIDFields(nullable=True),
        'created_at': fields.DateTimeField(nullable=True),
        'updated_at': fields.DateTimeField(nullable=True),
        'version': fields.IntegerFields(nullable=True)
    }


class SoftDeleteObjectMixin(object):
    """
    Mixin class for Soft-Deleted objects.

    This adds the fields that we use in common for all soft-deleted objects.
    """
    fields = {
        'deleted': fields.StringFields(nullable=True),
        'deleted_at': fields.DateTimeField(nullable=True),
    }


class PagedListObjectMixin(object):
    """
    Mixin class for List objects.

    This adds fields that would populate API metadata for collections.
    """
    fields = {
        'total_count': fields.IntegerFields(nullable=True)
    }


class DesignateRegistry(base.VersionedObjectRegistry):
    def registration_hook(self, cls, index):
        for name, field in six.iteritems(cls.fields):
            attr = get_dict_attr(cls, name)

            def getter(self, name=name):
                attrname = _get_attrname(name)
                self._obj_check_relation(name)
                return getattr(self, attrname, None)

            def setter(self, value, name=name, field=field):
                attrname = _get_attrname(name)
                field_value = field.coerce(self, name, value)
                if field.read_only and hasattr(self, attrname):
                    # Note(yjiang5): _from_db_object() may iterate
                    # every field and write, no exception in such situation.
                    if getattr(self, attrname) != field_value:
                        raise exception.ReadOnlyFieldError(field=name)
                    else:
                        return

                self._changed_fields.add(name)
                # TODO(daidv): _obj_original_values shoud be removed
                # after OVO migration completed.
                if (self.obj_attr_is_set(name) and value != getattr(self, name)
                    and name not in list(six.iterkeys(
                        self._obj_original_values))):
                    self._obj_original_values[name] = getattr(self, name)
                try:
                    return setattr(self, attrname, field_value)
                except Exception:
                    with excutils.save_and_reraise_exception():
                        attr = "%s.%s" % (self.obj_name(), name)
                        LOG.exception(_LE('Error setting %(attr)s'),
                                      {'attr': attr})

            setattr(cls, name, property(getter, setter, attr.fdel))
