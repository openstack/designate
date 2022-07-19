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
import datetime
from unittest.mock import Mock

from oslo_log import log as logging
from oslo_utils import timeutils
import oslotest.base

from designate import exceptions
from designate import objects
from designate.objects import adapters
from designate.objects import base
from designate.objects import fields

LOG = logging.getLogger(__name__)


@base.DesignateRegistry.register
class DesignateTestObject(base.DictObjectMixin, base.PersistentObjectMixin,
                          base.DesignateObject):
    def __init__(self, *args, **kwargs):
        super(DesignateTestObject, self).__init__(*args, **kwargs)

    fields = {
        'name': fields.StringFields(maxLength=255),
        'description': fields.StringFields(nullable=True, maxLength=255)
    }

    STRING_KEYS = [
        'id', 'name'
    ]


@base.DesignateRegistry.register
class DesignateTestPersistentObject(objects.base.PersistentObjectMixin,
                                    objects.DesignateObject):
    pass


class DesignateTestAdapter(adapters.DesignateAdapter):
    ADAPTER_OBJECT = DesignateTestObject
    ADAPTER_FORMAT = 'TEST_API'

    MODIFICATIONS = {
        'fields': {
            'id': {},
            'name': {
                'read_only': False
            },
            'description': {
                'read_only': False
            },
            'created_at': {},
            'updated_at': {},
        },
        'options': {
            'links': True,
            'resource_name': 'test_obj',
            'collection_name': 'test_obj',
        }
    }


class DesignateDateTimeAdaptor(adapters.DesignateAdapter):
    ADAPTER_OBJECT = DesignateTestPersistentObject
    ADAPTER_FORMAT = 'TEST_API'

    MODIFICATIONS = {
        'fields': {
            'id': {},
            'created_at': {},
            'updated_at': {},
        },
        'options': {}
    }


class DesignateAdapterTest(oslotest.base.BaseTestCase):
    def test_parse(self):
        test_obj = adapters.DesignateAdapter.parse(
            'TEST_API', {'name': 'example.test.'}, DesignateTestObject()
        )

        self.assertIsInstance(test_obj, DesignateTestObject)
        self.assertEqual('example.test.', test_obj.name)

    def test_parse_schema_does_not_match(self):
        self.assertRaisesRegex(
            exceptions.InvalidObject,
            'Provided object does not match schema. '
            'Keys \\[\'address\'\\] are not valid for test_obj',
            adapters.DesignateAdapter.parse,
            'TEST_API', {'address': '192.168.0.1'}, DesignateTestObject(),
        )

    def test_get_object_adapter(self):
        adapter = adapters.DesignateAdapter.get_object_adapter(
            DesignateTestObject(), 'TEST_API'
        )

        self.assertIsInstance(adapter(), DesignateTestAdapter)

    def test_object_render(self):
        test_obj = adapters.DesignateAdapter.render(
            'TEST_API', DesignateTestObject()
        )

        self.assertEqual(
            sorted([
                'created_at', 'description', 'id', 'name', 'updated_at',
            ]),
            sorted(test_obj)
        )

    def test_datetime_format(self):
        now = timeutils.utcnow()
        test_obj = DesignateTestPersistentObject()
        test_obj.created_at = now
        test_dict = adapters.DesignateAdapter.render('TEST_API', test_obj)

        self.assertEqual(
            datetime.datetime.strptime(
                test_dict['created_at'], '%Y-%m-%dT%H:%M:%S.%f'
            ),
            test_obj.created_at
        )


class RecordSetAPIv2AdapterTest(oslotest.base.BaseTestCase):
    def test_get_path(self):
        request = Mock()
        request.path = '/v2/recordsets'
        recordset = Mock()
        recordset.zone_id = 'a-b-c-d'
        expected_path = '/v2/zones/a-b-c-d/recordsets'

        path = adapters.RecordSetAPIv2Adapter._get_path(request, recordset)
        self.assertEqual(expected_path, path)
