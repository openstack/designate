# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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
import testtools

from designate.openstack.common import log as logging
from designate import tests
from designate import objects


LOG = logging.getLogger(__name__)


class TestObject(objects.DesignateObject):
        FIELDS = ['id', 'name']


TEST_OBJECT_PATH = 'designate.tests.test_objects.test_base.TestObject'


class DesignateObjectTest(tests.TestCase):
    def test_from_primitive(self):
        primitive = {
            'designate_object.name': TEST_OBJECT_PATH,
            'designate_object.data': {
                'id': 'MyID',
            },
            'designate_object.changes': [],
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

    def test_init_invalid(self):
        with testtools.ExpectedException(TypeError):
            TestObject(extra_field='Fail')

    def test_hasattr(self):
        obj = TestObject()

        # Suceess Cases
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
        self.assertEqual('MyID', obj._id)
        self.assertEqual(1, len(obj.obj_what_changed()))

        obj.name = 'MyName'
        self.assertEqual('MyName', obj._name)
        self.assertEqual(2, len(obj.obj_what_changed()))

    def test_to_primitive(self):
        obj = TestObject(id='MyID')

        # Ensure only the id attribute is returned
        primitive = obj.to_primitive()
        expected = {
            'designate_object.name': TEST_OBJECT_PATH,
            'designate_object.data': {
                'id': 'MyID',
            },
            'designate_object.changes': ['id'],
        }
        self.assertEqual(expected, primitive)

        # Set the name attribute to a None value
        obj.name = None

        # Ensure both the id and name attributes are returned
        primitive = obj.to_primitive()
        expected = {
            'designate_object.name': TEST_OBJECT_PATH,
            'designate_object.data': {
                'id': 'MyID',
                'name': None,
            },
            'designate_object.changes': ['id', 'name'],
        }
        self.assertEqual(expected, primitive)

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
