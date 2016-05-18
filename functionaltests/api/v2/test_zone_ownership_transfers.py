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
from functionaltests.api.v2.fixtures import ZoneFixture
from functionaltests.api.v2.fixtures import TransferRequestFixture


@utils.parameterized_class
class TransferZoneOwnerShipTest(DesignateV2Test):

    def setUp(self):
        super(TransferZoneOwnerShipTest, self).setUp()
        self.increase_quotas(user='default')
        self.increase_quotas(user='alt')
        self.ensure_tld_exists('com')
        self.zone = self.useFixture(ZoneFixture()).created_zone

    def test_create_zone_transfer_request_scoped(self):
        target_project_id = TransferRequestClient.as_user('alt').tenant_id
        post_model = datagen.random_transfer_request_data(
            target_project_id=target_project_id)
        fixture = self.useFixture(TransferRequestFixture(
            zone=self.zone,
            post_model=post_model,
            user='default',
            target_user='alt',
        ))

        self.assertEqual(201, fixture.post_resp.status)
        self.assertEqual(self.zone.id, fixture.transfer_request.zone_id)
        # todo: the zone_name is null initially, but shows up on later gets
        # self.assertEqual(fixture.transfer_request.zone_name, self.zone.name)
        self.assertEqual(TransferRequestClient.as_user(fixture.user).tenant_id,
                         fixture.transfer_request.project_id)
        self.assertEqual(target_project_id,
                         fixture.transfer_request.target_project_id)

        resp, transfer_request = TransferRequestClient.as_user('alt')\
            .get_transfer_request(fixture.transfer_request.id)

        self.assertEqual(200, resp.status)

    def test_view_zone_transfer_request_scoped(self):
        target_project_id = TransferRequestClient.as_user('admin').tenant_id

        post_model = datagen.random_transfer_request_data(
            target_project_id=target_project_id)
        fixture = self.useFixture(TransferRequestFixture(
            zone=self.zone,
            post_model=post_model,
            user='default',
            target_user='admin',
        ))
        transfer_request = fixture.transfer_request

        self.assertEqual(transfer_request.target_project_id,
                         target_project_id)

        self._assert_exception(
            exceptions.NotFound, 'zone_transfer_request_not_found', 404,
            TransferRequestClient.as_user('alt').get_transfer_request,
            self.zone.id)

        resp, transfer_request = TransferRequestClient.as_user('admin')\
            .get_transfer_request(transfer_request.id)

        self.assertEqual(200, resp.status)

    def test_create_zone_transfer_request_no_body(self):
        client = TransferRequestClient.as_user('default')
        resp, transfer_request = client \
            .post_transfer_request_empty_body(self.zone.id)
        self.assertEqual(201, resp.status)
        self.addCleanup(TransferRequestFixture.cleanup_transfer_request,
                        client, transfer_request.id)

    def test_do_zone_transfer_scoped(self):
        target_project_id = TransferRequestClient.as_user('alt').tenant_id
        post_model = datagen.random_transfer_request_data(
            target_project_id=target_project_id)
        fixture = self.useFixture(TransferRequestFixture(
            zone=self.zone,
            post_model=post_model,
            user='default',
            target_user='alt',
        ))
        transfer_request = fixture.transfer_request

        resp, retrived_transfer_request = TransferRequestClient.\
            as_user('alt').get_transfer_request(transfer_request.id)

        self.assertEqual(200, resp.status)

        resp, transfer_accept = TransferAcceptClient.as_user('alt')\
            .post_transfer_accept(
                datagen.random_transfer_accept_data(
                    key=transfer_request.key,
                    zone_transfer_request_id=transfer_request.id
                ))
        self.assertEqual(201, resp.status)

        client = ZoneClient.as_user('default')

        self._assert_exception(
            exceptions.NotFound, 'zone_not_found', 404,
            client.get_zone, self.zone.id)

        resp, zone = ZoneClient.as_user('alt').get_zone(self.zone.id)

        self.assertEqual(200, resp.status)
