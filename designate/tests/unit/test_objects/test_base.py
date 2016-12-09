# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from operator import attrgetter
import copy
import unittest

from oslo_log import log as logging
import mock
from oslo_serialization import jsonutils
import oslotest.base
import testtools

from designate import exceptions
from designate import objects

LOG = logging.getLogger(__name__)


class TestObject(objects.DesignateObject):
    FIELDS = {
        'id': {},
        'name': {},
        'nested': {
            'relation': True,
            'relation_cls': 'TestObject',
        },
        'nested_list': {
            'relation': True,
            'relation_cls': 'TestObjectList',
        },
    }


class TestObjectDict(objects.DictObjectMixin, TestObject):
    pass


class TestObjectList(objects.ListObjectMixin, objects.DesignateObject):
    LIST_ITEM_TYPE = TestObject


class TestValidatableObject(objects.DesignateObject):
    FIELDS = {
        'id': {
            'schema': {
                'type': 'string',
                'format': 'uuid',
            },
            'required': True,
        },
        'nested': {
            'relation': True,
            'relation_cls': 'TestValidatableObject',
            'schema': {
                '$ref': 'obj://TestValidatableObject#/'
            }
        }
    }


class DesignateObjectTest(oslotest.base.BaseTestCase):
    def test_obj_cls_from_name(self):
        cls = objects.DesignateObject.obj_cls_from_name('TestObject')
        self.assertEqual(TestObject, cls)

        cls = objects.DesignateObject.obj_cls_from_name('TestObjectDict')
        self.assertEqual(TestObjectDict, cls)

        cls = objects.DesignateObject.obj_cls_from_name('TestObjectList')
        self.assertEqual(TestObjectList, cls)

    def test_from_primitive(self):
        primitive = {
            'designate_object.name': 'TestObject',
            'designate_object.data': {
                'id': 'MyID',
            },
            'designate_object.changes': [],
            'designate_object.original_values': {},
        }

        obj = objects.DesignateObject.from_primitive(primitive)

        # Validate it has been thawed correctly
        self.assertEqual('MyID', obj.id)

        # Ensure the ID field has a value
        self.assertTrue(obj.obj_attr_is_set('id'))

        # Ensure the name field has no value
        self.assertFalse(obj.obj_attr_is_set('name'))

        # Ensure the changes list is empty
        self.assertEqual(0, len(obj.obj_what_changed()))

    def test_from_primitive_recursive(self):
        primitive = {
            'designate_object.name': 'TestObject',
            'designate_object.data': {
                'id': 'MyID',
                'nested': {
                    'designate_object.name': 'TestObject',
                    'designate_object.data': {
                        'id': 'MyID-Nested',
                    },
                    'designate_object.changes': [],
                    'designate_object.original_values': {},
                }
            },
            'designate_object.changes': [],
            'designate_object.original_values': {},
        }

        obj = objects.DesignateObject.from_primitive(primitive)

        # Validate it has been thawed correctly
        self.assertEqual('MyID', obj.id)
        self.assertEqual('MyID-Nested', obj.nested.id)

    def test_from_dict(self):
        obj = TestObject.from_dict({
            'id': 'MyID',
        })

        # Validate it has been thawed correctly
        self.assertEqual('MyID', obj.id)

        # Ensure the ID field has a value
        self.assertTrue(obj.obj_attr_is_set('id'))

        # Ensure the name field has no value
        self.assertFalse(obj.obj_attr_is_set('name'))

        # Ensure the changes list has one entry for the id field
        self.assertEqual(set(['id']), obj.obj_what_changed())

    def test_from_dict_recursive(self):
        obj = TestObject.from_dict({
            'id': 'MyID',
            'nested': {
                'id': 'MyID-Nested',
            },
        })

        # Validate it has been thawed correctly
        self.assertEqual('MyID', obj.id)
        self.assertEqual('MyID-Nested', obj.nested.id)

        # Ensure the changes list has two entries, one for the id field and the
        # other for the nested field
        self.assertEqual(set(['id', 'nested']), obj.obj_what_changed())

        # Ensure the changes list has one entry for the id field
        self.assertEqual(set(['id']), obj.nested.obj_what_changed())

    def test_from_dict_nested_list(self):
        obj = TestObject.from_dict({
            'id': 'MyID',
            'nested_list': [{
                'id': 'MyID-Nested1',
            }, {
                'id': 'MyID-Nested2',
            }],
        })

        # Validate it has been thawed correctly
        self.assertEqual('MyID', obj.id)
        self.assertEqual('MyID-Nested1', obj.nested_list[0].id)
        self.assertEqual('MyID-Nested2', obj.nested_list[1].id)

        # Ensure the changes list has two entries, one for the id field and the
        # other for the nested field
        self.assertEqual(set(['id', 'nested_list']), obj.obj_what_changed())

    def test_from_list(self):
        with testtools.ExpectedException(NotImplementedError):
            TestObject.from_list([])

    def test_get_schema(self):
        obj = TestValidatableObject()
        obj.id = 'ffded5c4-e4f6-4e02-a175-48e13c5c12a0'
        obj.validate()
        self.assertTrue(hasattr(obj, '_obj_validator'))

        expected = {
            'description': 'Designate TestValidatableObject Object',
            'title': 'TestValidatableObject', 'required': ['id'],
            'additionalProperties': False,
            '$schema': 'http://json-schema.org/draft-04/hyper-schema',
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string', 'format': 'uuid'
                }
            }
        }
        schema = obj._obj_validator.schema
        self.assertEqual(expected, schema)

        with testtools.ExpectedException(AttributeError):  # bug
            schema = obj.obj_get_schema()

    @unittest.expectedFailure  # bug
    def test__schema_ref_resolver(self):
        from designate.objects import base
        base._schema_ref_resolver(
            'obj://TestValidatableObject#/subpathA/subpathB')

    def test_init_invalid(self):
        with testtools.ExpectedException(TypeError):
            TestObject(extra_field='Fail')

    def test_hasattr(self):
        obj = TestObject()

        # Success Cases
        self.assertTrue(hasattr(obj, 'id'),
                        "Should have id attribute")
        self.assertTrue(hasattr(obj, 'name'),
                        "Should have name attribute")

        # Failure Cases
        self.assertFalse(hasattr(obj, 'email'),
                         "Should not have email attribute")
        self.assertFalse(hasattr(obj, 'names'),
                         "Should not have names attribute")

    def test_setattr(self):
        obj = TestObject()

        obj.id = 'MyID'
        self.assertEqual('MyID', obj.id)
        self.assertEqual(1, len(obj.obj_what_changed()))

        obj.name = 'MyName'
        self.assertEqual('MyName', obj.name)
        self.assertEqual(2, len(obj.obj_what_changed()))

    def test_setattr_neg(self):
        obj = TestObject()

        with testtools.ExpectedException(AttributeError):
            obj.badthing = 'demons'

    def test_to_primitive(self):
        obj = TestObject(id='MyID')

        # Ensure only the id attribute is returned
        primitive = obj.to_primitive()
        expected = {
            'designate_object.name': 'TestObject',
            'designate_object.data': {
                'id': 'MyID',
            },
            'designate_object.changes': ['id'],
            'designate_object.original_values': {},
        }
        self.assertEqual(expected, primitive)

        # Set the name attribute to a None value
        obj.name = None

        # Ensure both the id and name attributes are returned
        primitive = obj.to_primitive()
        expected = {
            'designate_object.name': 'TestObject',
            'designate_object.data': {
                'id': 'MyID',
                'name': None,
            },
            'designate_object.changes': ['id', 'name'],
            'designate_object.original_values': {},
        }
        self.assertEqual(expected, primitive)

    def test_to_primitive_recursive(self):
        obj = TestObject(id='MyID', nested=TestObject(id='MyID-Nested'))

        # Ensure only the id attribute is returned
        primitive = obj.to_primitive()
        expected = {
            'designate_object.name': 'TestObject',
            'designate_object.data': {
                'id': 'MyID',
                'nested': {
                    'designate_object.name': 'TestObject',
                    'designate_object.data': {
                        'id': 'MyID-Nested',
                    },
                    'designate_object.changes': ['id'],
                    'designate_object.original_values': {},
                }
            },
            'designate_object.changes': ['id', 'nested'],
            'designate_object.original_values': {},
        }
        self.assertEqual(expected, primitive)

    def test_to_dict(self):
        obj = TestObject(id='MyID')

        # Ensure only the id attribute is returned
        dict_ = obj.to_dict()
        expected = {
            'id': 'MyID',
        }
        self.assertEqual(expected, dict_)

        # Set the name attribute to a None value
        obj.name = None

        # Ensure both the id and name attributes are returned
        dict_ = obj.to_dict()
        expected = {
            'id': 'MyID',
            'name': None,
        }
        self.assertEqual(expected, dict_)

    def test_to_dict_recursive(self):
        obj = TestObject(id='MyID', nested=TestObject(id='MyID-Nested'))

        # Ensure only the id attribute is returned
        dict_ = obj.to_dict()
        expected = {
            'id': 'MyID',
            'nested': {
                'id': 'MyID-Nested',
            },
        }

        self.assertEqual(expected, dict_)

    def test_update(self):
        obj = TestObject(id='MyID', name='test')
        obj.update({'id': 'new_id', 'name': 'new_name'})
        self.assertEqual('new_id', obj.id)
        self.assertEqual('new_name', obj.name)

    def test_update_unexpected_attribute(self):
        obj = TestObject(id='MyID', name='test')
        with testtools.ExpectedException(AttributeError):
            obj.update({'id': 'new_id', 'new_key': 3})

    def test_is_valid(self):
        obj = TestValidatableObject(id='MyID')

        # ID should be a UUID, So - Not Valid.
        self.assertFalse(obj.is_valid)

        # Correct the ID field
        obj.id = 'ffded5c4-e4f6-4e02-a175-48e13c5c12a0'

        # ID is now a UUID, So - Valid.
        self.assertTrue(obj.is_valid)

    def test_is_valid_recursive(self):
        obj = TestValidatableObject(
            id='MyID',
            nested=TestValidatableObject(id='MyID'))

        # ID should be a UUID, So - Not Valid.
        self.assertFalse(obj.is_valid)

        # Correct the outer objects ID field
        obj.id = 'ffded5c4-e4f6-4e02-a175-48e13c5c12a0'

        # Outer ID is now a UUID, Nested ID is Not. So - Invalid.
        self.assertFalse(obj.is_valid)

        # Correct the nested objects ID field
        obj.nested.id = 'ffded5c4-e4f6-4e02-a175-48e13c5c12a0'

        # Outer and Nested IDs are now UUIDs. So - Valid.
        self.assertTrue(obj.is_valid)

    def test_validate(self):
        obj = TestValidatableObject()

        # ID is required, so the object is not valid
        with testtools.ExpectedException(exceptions.InvalidObject):
            obj.validate()

        # Set the ID field to an invalid value
        obj.id = 'MyID'

        # ID is now set, but to an invalid value, still invalid
        with testtools.ExpectedException(exceptions.InvalidObject):
            obj.validate()

        # Set the ID field to a valid value
        obj.id = 'ffded5c4-e4f6-4e02-a175-48e13c5c12a0'
        obj.validate()

    def test_validate_recursive(self):
        obj = TestValidatableObject(
            id='MyID',
            nested=TestValidatableObject(id='MyID'))

        # ID should be a UUID, So - Invalid.
        with testtools.ExpectedException(exceptions.InvalidObject):
            obj.validate()

        # Correct the outer objects ID field
        obj.id = 'ffded5c4-e4f6-4e02-a175-48e13c5c12a0'

        # Outer ID is now set, Inner ID is not, still invalid.
        e = self.assertRaises(exceptions.InvalidObject, obj.validate)

        # Ensure we have exactly one error and fetch it
        self.assertEqual(1, len(e.errors))
        error = e.errors.pop(0)

        # Ensure the format validator has triggered the failure.
        self.assertEqual('format', error.validator)

        # Ensure the nested ID field has triggered the failure.
        # For some reason testtools turns lists into deques :/
        self.assertEqual(error.path, ['nested', 'id'])

        # Set the Nested ID field to a valid value
        obj.nested.id = 'ffded5c4-e4f6-4e02-a175-48e13c5c12a0'
        obj.validate()

    def test_obj_attr_is_set(self):
        obj = TestObject()

        self.assertFalse(obj.obj_attr_is_set('name'))

        obj.name = "My Name"

        self.assertTrue(obj.obj_attr_is_set('name'))

    def test_obj_what_changed(self):
        obj = TestObject()

        self.assertEqual(set([]), obj.obj_what_changed())

        obj.name = "My Name"

        self.assertEqual(set(['name']), obj.obj_what_changed())

    def test_obj_get_changes(self):
        obj = TestObject()

        self.assertEqual({}, obj.obj_get_changes())

        obj.name = "My Name"

        self.assertEqual({'name': "My Name"}, obj.obj_get_changes())

    def test_obj_reset_changes(self):
        obj = TestObject()
        obj.name = "My Name"

        self.assertEqual(1, len(obj.obj_what_changed()))

        obj.obj_reset_changes()

        self.assertEqual(0, len(obj.obj_what_changed()))

    def test_obj_reset_changes_subset(self):
        obj = TestObject()
        obj.id = "My ID"
        obj.name = "My Name"

        self.assertEqual(2, len(obj.obj_what_changed()))

        obj.obj_reset_changes(['id'])

        self.assertEqual(1, len(obj.obj_what_changed()))
        self.assertEqual({'name': "My Name"}, obj.obj_get_changes())

    def test_obj_get_original_value(self):
        # Create an object
        obj = TestObject()
        obj.id = "My ID"
        obj.name = "My Name"

        # Rset one of the changes
        obj.obj_reset_changes(['id'])

        # Update the reset field
        obj.id = "My New ID"

        # Ensure the "current" value is correct
        self.assertEqual("My New ID", obj.id)

        # Ensure the "original" value is correct
        self.assertEqual("My ID", obj.obj_get_original_value('id'))
        self.assertEqual("My Name", obj.obj_get_original_value('name'))

        # Update the reset field again
        obj.id = "My New New ID"

        # Ensure the "current" value is correct
        self.assertEqual("My New New ID", obj.id)

        # Ensure the "original" value is still correct
        self.assertEqual("My ID", obj.obj_get_original_value('id'))
        self.assertEqual("My Name", obj.obj_get_original_value('name'))

        # Ensure a KeyError is raised when value exists
        with testtools.ExpectedException(KeyError):
            obj.obj_get_original_value('nested')

    def test_deepcopy(self):
        # Create the Original object
        o_obj = TestObject()
        o_obj.id = "My ID"
        o_obj.name = "My Name"

        # Clear the "changed" flag for one of the two fields we set
        o_obj.obj_reset_changes(['name'])

        # Deepcopy the object
        c_obj = copy.deepcopy(o_obj)

        # Ensure the copy was successful
        self.assertEqual(o_obj.id, c_obj.id)
        self.assertEqual(o_obj.name, c_obj.name)
        self.assertEqual(o_obj.obj_attr_is_set('nested'),
                         c_obj.obj_attr_is_set('nested'))

        self.assertEqual(o_obj.obj_get_changes(), c_obj.obj_get_changes())
        self.assertEqual(o_obj.to_primitive(), c_obj.to_primitive())

    def test_eq(self):
        # Create two equal objects
        obj_one = TestObject(id="My ID", name="My Name")
        obj_two = TestObject(id="My ID", name="My Name")

        # Ensure they evaluate to equal
        self.assertEqual(obj_one, obj_two)

        # Change a value on one object
        obj_two.name = 'Other Name'

        # Ensure they do not evaluate to equal
        self.assertNotEqual(obj_one, obj_two)

    def test_eq_false(self):
        obj = TestObject(id="My ID", name="My Name")
        self.assertFalse(obj == tuple())
        self.assertNotEqual(obj, tuple())

    def test_ne(self):
        # Create two equal objects
        obj_one = TestObject(id="My ID", name="My Name")
        obj_two = TestObject(id="My ID", name="My Name")

        # Ensure they evaluate to equal
        self.assertEqual(obj_one, obj_two)

        # Change a value on one object
        obj_two.name = 'Other Name'

        # Ensure they do not evaluate to equal
        self.assertNotEqual(obj_one, obj_two)


class DictObjectMixinTest(oslotest.base.BaseTestCase):
    def test_cast_to_dict(self):
        # Create an object
        obj = TestObjectDict()
        obj.id = "My ID"
        obj.name = "My Name"

        expected = {
            'id': 'My ID',
            'name': 'My Name',
        }

        self.assertEqual(expected, dict(obj))

    def test_gititem(self):
        obj = TestObjectDict(name=1)
        self.assertEqual(1, obj['name'])

    def test_setitem(self):
        obj = TestObjectDict()
        obj['name'] = 1
        self.assertEqual(1, obj.name)

    def test_contains(self):
        obj = TestObjectDict(name=1)
        self.assertIn('name', obj)

    def test_get(self):
        obj = TestObjectDict(name=1)
        v = obj.get('name')
        self.assertEqual(1, v)

    def test_get_missing(self):
        obj = TestObjectDict(name=1)
        self.assertFalse(obj.obj_attr_is_set('foo'))
        with testtools.ExpectedException(AttributeError):
            obj.get('foo')

    def test_get_default(self):
        obj = TestObjectDict(name='n')
        v = obj.get('name', default='default')
        self.assertEqual('n', v)

    def test_get_default_with_patch(self):
        obj = TestObjectDict(name='v')
        fname = 'designate.objects.base.DesignateObject.obj_attr_is_set'
        with mock.patch(fname) as attr_is_set:
            attr_is_set.return_value = False
            v = obj.get('name', default='default')
            self.assertEqual('default', v)

    def test_iteritems(self):
        obj = TestObjectDict(name=None, id=1)
        items = tuple(obj.items())
        self.assertEqual(
            [('id', 1), ('name', None)],
            sorted(items)
        )

    def test_jsonutils_to_primitive(self):
        obj = TestObjectDict(name="foo")
        dumped = jsonutils.to_primitive(obj, convert_instances=True)
        self.assertIsInstance(dumped, dict)
        self.assertEqual('foo', dumped['name'])


class ListObjectMixinTest(oslotest.base.BaseTestCase):
    def test_from_primitive(self):
        primitive = {
            'designate_object.name': 'TestObjectList',
            'designate_object.data': {
                'objects': [
                    {'designate_object.changes': ['id'],
                     'designate_object.data': {'id': 'One'},
                     'designate_object.name': 'TestObject',
                     'designate_object.original_values': {}},
                    {'designate_object.changes': ['id'],
                     'designate_object.data': {'id': 'Two'},
                     'designate_object.name': 'TestObject',
                     'designate_object.original_values': {}},
                ],
            },
            'designate_object.changes': ['objects'],
            'designate_object.original_values': {},
        }

        obj = objects.DesignateObject.from_primitive(primitive)

        self.assertEqual(2, len(obj))
        self.assertEqual(2, len(obj.objects))

        self.assertIsInstance(obj[0], TestObject)
        self.assertIsInstance(obj[1], TestObject)

        self.assertEqual('One', obj[0].id)
        self.assertEqual('Two', obj[1].id)

    def test_cast_to_list(self):
        # Create a few objects
        obj_one = TestObject()
        obj_one.id = "One"
        obj_two = TestObject()
        obj_two.id = "Two"

        # Create a ListObject
        obj = TestObjectList(objects=[obj_one, obj_two])

        expected = [obj_one, obj_two]
        self.assertEqual(expected, list(obj))

    def test_to_primitive(self):
        # Create a few objects
        obj_one = TestObject()
        obj_one.id = "One"
        obj_two = TestObject()
        obj_two.id = "Two"

        # Create a ListObject
        obj = TestObjectList(objects=[obj_one, obj_two])

        primitive = obj.to_primitive()
        expected = {
            'designate_object.name': 'TestObjectList',
            'designate_object.data': {
                'objects': [
                    {'designate_object.changes': ['id'],
                     'designate_object.data': {'id': 'One'},
                     'designate_object.name': 'TestObject',
                     'designate_object.original_values': {}},
                    {'designate_object.changes': ['id'],
                     'designate_object.data': {'id': 'Two'},
                     'designate_object.name': 'TestObject',
                     'designate_object.original_values': {}},
                ],
            },
            'designate_object.changes': ['objects'],
            'designate_object.original_values': {},
        }
        self.assertEqual(expected, primitive)

    def test_to_primitive_nested_obj(self):
        # Create a few objects
        obj_one = TestObject()
        obj_two = TestObject()
        obj_two.id = "Two"
        obj_one.id = obj_two

        # Create a ListObject
        obj = TestObjectList(objects=[obj_one, obj_two])

        primitive = obj.to_primitive()
        expected = {
            'designate_object.name': 'TestObjectList',
            'designate_object.changes': ['objects'],
            'designate_object.data': {
                'objects': [
                    {'designate_object.changes': ['id'],
                     'designate_object.data': {'id':
                        {'designate_object.changes': ['id'],
                         'designate_object.data': {'id': 'Two'},
                         'designate_object.name': 'TestObject',
                         'designate_object.original_values': {}}},
                     'designate_object.name': 'TestObject',
                    'designate_object.original_values': {}},
                    {'designate_object.changes': ['id'],
                     'designate_object.data': {'id': 'Two'},
                     'designate_object.name': 'TestObject',
                     'designate_object.original_values': {}}]},
            'designate_object.original_values': {}}

        self.assertEqual(expected, primitive)

    def test_obj_what_changed(self):
        # Create a few objects
        obj_one = TestObject()
        obj_two = TestObject()

        # Create a ListObject
        obj = TestObjectList(objects=[obj_one, obj_two])

        # Make sure there are no changes
        obj.obj_reset_changes()

        changes = obj.obj_what_changed()
        expected = set([])

        self.assertEqual(expected, changes)

        # Make some changes
        obj_one.id = "One"
        obj_two.id = "Two"

        changes = obj.obj_what_changed()
        expected = set(['objects'])

        self.assertEqual(expected, changes)

    def test_get_slice(self):
        # Create a few objects
        obj_one = TestObject(id="One")
        obj_two = TestObject(id="Two")

        # Create a ListObject
        obj = TestObjectList(objects=[obj_one, obj_two])

        theslice = obj[1:]
        expected = TestObjectList(objects=[obj_two])

        self.assertEqual(expected.objects, theslice.objects)
        self.assertNotEqual(obj.objects, theslice.objects)

    def test_setitem(self):
        # Create a few objects
        obj_one = TestObject(id="One")
        obj_two = TestObject(id="Two")

        # Create a ListObject
        obj = TestObjectList(objects=[obj_one, obj_two])

        obj[1] = obj_one

        self.assertEqual(obj.objects, [obj_one, obj_one])

    def test_contains(self):
        # Create a few objects
        obj_one = TestObject(id="One")
        obj_two = TestObject(id="Two")
        obj_three = TestObject(id="Three")

        # Create a ListObject
        obj = TestObjectList(objects=[obj_one, obj_two])

        self.assertIn(obj_one, obj)
        self.assertIn(obj_two, obj)
        self.assertNotIn(obj_three, obj)

    def test_extend(self):
        # Create a few objects
        obj_one = TestObject(id="One")
        obj_two = TestObject(id="Two")
        obj_three = TestObject(id="Three")

        # Create a ListObject
        ext_obj = TestObjectList(objects=[obj_one])
        obj = TestObjectList(objects=[obj_one, obj_two, obj_three])

        ext_obj.extend([obj_two, obj_three])

        self.assertEqual(obj.objects, ext_obj.objects)

    def test_insert(self):
        # Create a few objects
        obj_one = TestObject(id="One")
        obj_two = TestObject(id="Two")
        obj_three = TestObject(id="Three")

        # Create a ListObject
        obj = TestObjectList(objects=[obj_one, obj_three])

        obj.insert(1, obj_two)

        self.assertEqual([obj_one, obj_two, obj_three], obj.objects)

    def test_remove(self):
        # Create a few objects
        obj_one = TestObject(id="One")
        obj_two = TestObject(id="Two")

        # Create a ListObject
        obj = TestObjectList(objects=[obj_one, obj_two])
        obj.remove(obj_one)
        self.assertEqual([obj_two], obj.objects)

    def test_index(self):
        # Create a few objects
        obj_one = TestObject(id="One")
        obj_two = TestObject(id="Two")
        obj_three = TestObject(id="Three")

        # Create a ListObject
        obj = TestObjectList(objects=[obj_one, obj_two, obj_three])

        self.assertEqual(1, obj.index(obj_two))

    def test_count(self):
        # Create a few objects
        obj_one = TestObject(id="One")
        obj_two = TestObject(id="Two")

        # Create a ListObject
        obj = TestObjectList(objects=[obj_one, obj_two, obj_two])

        self.assertEqual(2, obj.count(obj_two))

    def test_sort(self):
        # Create a few objects
        obj_one = TestObject(id=1)
        obj_two = TestObject(id=2)
        obj_three = TestObject(id=3)

        # Create a ListObject
        obj = TestObjectList(objects=[obj_two, obj_three, obj_one])
        obj.sort(key=attrgetter('id'))

        self.assertEqual([obj_one, obj_two, obj_three], obj.objects)

    def test_to_dict(self):
        # Create a ListObject containing a DesignateObject
        obj_one = objects.DesignateObject()
        obj = TestObjectList(objects=obj_one)

        dict_ = obj.to_dict()
        expected = {'objects': {}}
        self.assertEqual(expected, dict_)

    def test_to_dict_list_mixin(self):
        # Create a ListObject containing an ObjectList
        obj = TestObjectList(objects=TestObjectList())

        dict_ = obj.to_dict()
        expected = {'objects': []}
        self.assertEqual(expected, dict_)

    def test_to_list(self):
        # Create a few objects
        obj_one = TestObject(id="One")
        obj_three = TestObject(id="Three")

        # Create a ListObject
        obj = TestObjectList(objects=[obj_one, obj_three])

        li = obj.to_list()
        self.assertEqual([{'id': 'One'}, {'id': 'Three'}], li)
