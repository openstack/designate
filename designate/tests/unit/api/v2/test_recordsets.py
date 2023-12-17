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


from unittest import mock

import oslotest.base

from designate.api.v2.controllers.zones import recordsets
from designate.central import rpcapi
from designate import exceptions
from designate import objects


class TestRecordsetAPI(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.central_api = mock.Mock()
        self.zone = objects.Zone(
            id='1e8952a5-e5a4-426a-afab-4cd10131a351',
            name='example.com.',
            email='example@example.com'
        )
        mock.patch.object(rpcapi.CentralAPI, 'get_instance',
                          return_value=self.central_api).start()

        self.controller = recordsets.RecordSetsController()

    @mock.patch('pecan.response', mock.Mock())
    @mock.patch('pecan.request')
    def test_post_all_soa_not_allowed(self, mock_request):
        mock_request.environ = {'context': mock.Mock()}
        mock_request.body_dict = {
            'name': 'soa.example.com.',
            'type': 'SOA'
        }

        self.assertRaisesRegex(
            exceptions.BadRequest,
            'Creating a SOA recordset is not allowed',
            self.controller.post_all, self.zone.id
        )

    @mock.patch('pecan.response')
    @mock.patch('pecan.request')
    def test_put_one(self, mock_request, mock_response):
        mock_context = mock.Mock()
        mock_context.edit_managed_records = False

        mock_request.environ = {'context': mock_context}

        record_set = objects.RecordSet(name='www.example.org.', type='NS')
        record_set.records = objects.RecordList(
            objects=[objects.Record(data='ns1.example.org.', action='NONE')]
        )

        self.central_api.get_recordset.return_value = record_set
        self.central_api.update_recordset.return_value = record_set
        self.central_api.get_zone.return_value = self.zone

        self.controller.put_one(
            self.zone.id, '99a60ad0-b9ac-4e83-9eee-859e99299bcf'
        )
        self.assertEqual(200, mock_response.status_int)

    @mock.patch('pecan.response', mock.Mock())
    @mock.patch('pecan.request')
    def test_put_one_managed_not_allowed(self, mock_request):
        mock_context = mock.Mock()
        mock_context.edit_managed_records = False

        mock_request.environ = {'context': mock_context}

        record_set = objects.RecordSet(name='www.example.org.', type='A')
        record_set.records = objects.RecordList(
            objects=[objects.Record(data='192.0.2.1', managed=True)]
        )

        self.central_api.get_recordset.return_value = record_set

        self.assertRaisesRegex(
            exceptions.BadRequest,
            'Managed records may not be updated',
            self.controller.put_one, self.zone.id,
            '3a2a2c3a-8f47-4788-8622-231f1c8f19c3'
        )

    @mock.patch('pecan.response', mock.Mock())
    @mock.patch('pecan.request')
    def test_put_one_soa_not_allowed(self, mock_request):
        mock_context = mock.Mock()

        mock_request.environ = {'context': mock_context}

        record_set = objects.RecordSet(name='soa.example.org.', type='SOA')
        record_set.records = objects.RecordList(
            objects=[objects.Record(data='192.0.2.2', managed=True)]
        )

        self.central_api.get_recordset.return_value = record_set

        self.assertRaisesRegex(
            exceptions.BadRequest,
            'Updating SOA recordsets is not allowed',
            self.controller.put_one, self.zone.id,
            '3a2a2c3a-8f47-4788-8622-231f1c8f19c3'
        )

    @mock.patch('pecan.response', mock.Mock())
    @mock.patch('pecan.request')
    def test_put_one_update_root_ns_not_allowed(self, mock_request):
        mock_context = mock.Mock()

        mock_request.environ = {'context': mock_context}

        record_set = objects.RecordSet(name='example.com.', type='NS')
        record_set.records = objects.RecordList(
            objects=[objects.Record(data='192.0.2.3', managed=True)]
        )

        self.central_api.get_recordset.return_value = record_set
        self.central_api.get_zone.return_value = self.zone

        self.assertRaisesRegex(
            exceptions.BadRequest,
            'Updating a root zone NS record is not allowed',
            self.controller.put_one, self.zone.id,
            '3a2a2c3a-8f47-4788-8622-231f1c8f19c3'
        )

    @mock.patch('pecan.response', mock.Mock())
    @mock.patch('pecan.request')
    def test_delete_one_soa_not_allowed(self, mock_request):
        mock_request.environ = {'context': mock.Mock()}

        record_set = objects.RecordSet(name='soa.example.com.', type='SOA')
        record_set.records = objects.RecordList(
            objects=[objects.Record(data='192.0.2.4')]
        )

        self.central_api.get_recordset.return_value = record_set

        self.assertRaisesRegex(
            exceptions.BadRequest,
            'Deleting a SOA recordset is not allowed',
            self.controller.delete_one, self.zone.id,
            '3a2a2c3a-8f47-4788-8622-231f1c8f19c3'
        )
