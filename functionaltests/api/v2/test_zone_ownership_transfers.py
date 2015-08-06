"""
Copyright 2015 Rackspace

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from tempest_lib import exceptions

from functionaltests.common import datagen
from functionaltests.common import utils
from functionaltests.api.v2.base import DesignateV2Test
from functionaltests.api.v2.clients.transfer_requests_client import \
    TransferRequestClient
from functionaltests.api.v2.clients.transfer_accepts_client import \
    TransferAcceptClient
from functionaltests.api.v2.clients.zone_client import ZoneClient


@utils.parameterized_class
class TransferZoneOwnerShipTest(DesignateV2Test):

    def setUp(self):
        super(TransferZoneOwnerShipTest, self).setUp()
        self.increase_quotas(user='default')
        self.increase_quotas(user='alt')
        resp, self.zone = ZoneClient.as_user('default').post_zone(
            datagen.random_zone_data())
        ZoneClient.as_user('default').wait_for_zone(self.zone.id)

    def test_list_transfer_requests(self):
        resp, model = TransferRequestClient.as_user('default') \
            .list_transfer_requests()
        self.assertEqual(resp.status, 200)

    def test_create_zone_transfer_request(self):
        resp, transfer_request = TransferRequestClient.as_user('default')\
            .post_transfer_request(self.zone.id,
                                   datagen.random_transfer_request_data())
        self.assertEqual(resp.status, 201)

    def test_view_zone_transfer_request(self):
        resp, transfer_request = TransferRequestClient.as_user('default')\
            .post_transfer_request(self.zone.id,
                                   datagen.random_transfer_request_data())
        self.assertEqual(resp.status, 201)

        resp, transfer_request = TransferRequestClient.as_user('alt')\
            .get_transfer_request(transfer_request.id)

        self.assertEqual(resp.status, 200)
        self.assertEqual(getattr(transfer_request, 'key', None), None)

    def test_create_zone_transfer_request_scoped(self):

        target_project_id = TransferRequestClient.as_user('alt').tenant_id

        resp, transfer_request = TransferRequestClient.as_user('default')\
            .post_transfer_request(self.zone.id,
                                   datagen.random_transfer_request_data(
                                       target_project_id=target_project_id))
        self.assertEqual(resp.status, 201)
        self.assertEqual(transfer_request.target_project_id, target_project_id)

        resp, transfer_request = TransferRequestClient.as_user('alt')\
            .get_transfer_request(transfer_request.id)

        self.assertEqual(resp.status, 200)

    def test_view_zone_transfer_request_scoped(self):
        target_project_id = TransferRequestClient.as_user('admin').tenant_id

        resp, transfer_request = TransferRequestClient.as_user('default')\
            .post_transfer_request(self.zone.id,
                                   datagen.random_transfer_request_data(
                                       target_project_id=target_project_id))
        self.assertEqual(resp.status, 201)
        self.assertEqual(transfer_request.target_project_id, target_project_id)

        self._assert_exception(
            exceptions.NotFound, 'zone_transfer_request_not_found', 404,
            TransferRequestClient.as_user('alt').get_transfer_request,
            self.zone.id)

        resp, transfer_request = TransferRequestClient.as_user('admin')\
            .get_transfer_request(transfer_request.id)

        self.assertEqual(resp.status, 200)

    def test_create_zone_transfer_request_no_body(self):
        resp, transfer_request = TransferRequestClient.as_user('default')\
            .post_transfer_request_empty_body(self.zone.id)
        self.assertEqual(resp.status, 201)

    def test_do_zone_transfer(self):
        resp, transfer_request = TransferRequestClient.as_user('default')\
            .post_transfer_request(self.zone.id,
                                   datagen.random_transfer_request_data())
        self.assertEqual(resp.status, 201)

        resp, transfer_accept = TransferAcceptClient.as_user('alt')\
            .post_transfer_accept(
                datagen.random_transfer_accept_data(
                    key=transfer_request.key,
                    zone_transfer_request_id=transfer_request.id
                ))
        self.assertEqual(resp.status, 201)

    def test_do_zone_transfer_scoped(self):

        target_project_id = TransferRequestClient.as_user('alt').tenant_id

        resp, transfer_request = TransferRequestClient.as_user('default')\
            .post_transfer_request(self.zone.id,
                                   datagen.random_transfer_request_data(
                                       target_project_id=target_project_id))

        self.assertEqual(resp.status, 201)

        resp, retrived_transfer_request = TransferRequestClient.\
            as_user('alt').get_transfer_request(transfer_request.id)

        self.assertEqual(resp.status, 200)

        resp, transfer_accept = TransferAcceptClient.as_user('alt')\
            .post_transfer_accept(
                datagen.random_transfer_accept_data(
                    key=transfer_request.key,
                    zone_transfer_request_id=transfer_request.id
                ))
        self.assertEqual(resp.status, 201)

        client = ZoneClient.as_user('default')

        self._assert_exception(
            exceptions.NotFound, 'domain_not_found', 404,
            client.get_zone, self.zone.id)

        resp, zone = ZoneClient.as_user('alt').get_zone(self.zone.id)

        self.assertEqual(resp.status, 200)
