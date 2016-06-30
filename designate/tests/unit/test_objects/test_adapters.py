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

from mock import Mock
from oslo_log import log as logging
import oslotest.base
from oslo_utils import timeutils

from designate import objects
from designate.objects import adapters


LOG = logging.getLogger(__name__)


class DesignateTestAdapter(adapters.DesignateAdapter):
    ADAPTER_OBJECT = objects.DesignateObject
    ADAPTER_FORMAT = 'TEST_API'

    MODIFICATIONS = {
        'fields': {},
        'options': {}
    }


class DesignateTestPersistentObject(
        objects.DesignateObject, objects.base.PersistentObjectMixin):
    pass


class DesignateDateTimeAdaptor(adapters.DesignateAdapter):
    ADAPTER_OBJECT = DesignateTestPersistentObject
    ADAPTER_FORMAT = 'TEST_API'

    MODIFICATIONS = {
        'fields': {
            "id": {},
            "created_at": {},
            "updated_at": {},
        },
        'options': {}
    }


class DesignateAdapterTest(oslotest.base.BaseTestCase):
    def test_get_object_adapter(self):
        adapters.DesignateAdapter.get_object_adapter(
            'TEST_API', objects.DesignateObject())

    def test_object_render(self):
        adapters.DesignateAdapter.render('TEST_API', objects.DesignateObject())

    def test_datetime_format(self):
        test_obj = DesignateTestPersistentObject()
        test_obj.created_at = timeutils.utcnow()

        test_dict = adapters.DesignateAdapter.render('TEST_API', test_obj)

        datetime.datetime.strptime(
            test_dict['created_at'],
            '%Y-%m-%dT%H:%M:%S.%f')


class RecordSetAPIv2AdapterTest(oslotest.base.BaseTestCase):
    def test_get_path(self):
        request = Mock()
        request.path = '/v2/recordsets'
        recordset = Mock()
        recordset.zone_id = 'a-b-c-d'
        expected_path = '/v2/zones/a-b-c-d/recordsets'

        path = adapters.RecordSetAPIv2Adapter._get_path(request, recordset)
        self.assertEqual(expected_path, path)
