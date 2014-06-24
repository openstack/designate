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
from designate.objects import base


LOG = logging.getLogger(__name__)


class TestObject(base.DesignateObject):
        FIELDS = ['id', 'name']


class DesignateObjectTest(tests.TestCase):
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

        obj.name = 'MyName'
        self.assertEqual('MyName', obj._name)

    def test_from_primitive(self):
        primitive = {
            'designate_object.data': {
                'id': 'MyID',
            }
        }

        obj = TestObject.from_primitive(primitive)

        # Validate it has been thawed correctly
        self.assertEqual('MyID', obj.id)

        # Ensure the ID field has a value
        self.assertTrue(obj.attr_is_set('id'))

        # Ensure the name field has no value
        self.assertFalse(obj.attr_is_set('name'))

    def test_to_primitive(self):
        obj = TestObject(id='MyID')

        # Ensure only the id attribute is returned
        primitive = obj.to_primitive()
        self.assertEqual({'id': 'MyID'}, primitive['designate_object.data'])

        # Set the name attribute to a None value
        obj.name = None

        # Ensure both the id and name attributes are returned
        primitive = obj.to_primitive()
        self.assertEqual({'id': 'MyID', 'name': None},
                         primitive['designate_object.data'])
