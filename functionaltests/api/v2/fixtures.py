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

from __future__ import absolute_import
from __future__ import print_function
import sys
import traceback

import fixtures
from tempest_lib.exceptions import NotFound
from testtools.runtest import MultipleExceptions

from functionaltests.api.v2.clients.blacklist_client import BlacklistClient
from functionaltests.api.v2.clients.pool_client import PoolClient
from functionaltests.api.v2.clients.recordset_client import RecordsetClient
from functionaltests.api.v2.clients.tld_client import TLDClient
from functionaltests.api.v2.clients.zone_client import ZoneClient
from functionaltests.api.v2.clients.transfer_requests_client import \
    TransferRequestClient
from functionaltests.common import datagen


class BaseFixture(fixtures.Fixture):

    def setUp(self):
        # Sometimes, exceptions are raised in _setUp methods on fixtures.
        # testtools pushes the exception into a MultipleExceptions object along
        # with an artificial SetupError, which produces bad error messages.
        # This just logs those stack traces to stderr for easier debugging.
        try:
            super(BaseFixture, self).setUp()
        except MultipleExceptions as e:
            for i, exc_info in enumerate(e.args):
                print('--- printing MultipleExceptions traceback {} of {} ---'
                      .format(i + 1, len(e.args)), file=sys.stderr)
                traceback.print_exception(*exc_info)
            raise


class ZoneFixture(BaseFixture):

    def __init__(self, post_model=None, user='default'):
        super(ZoneFixture, self).__init__()
        self.post_model = post_model or datagen.random_zone_data()
        self.user = user

    def _setUp(self):
        super(ZoneFixture, self)._setUp()
        self._create_zone()

    def _create_zone(self):
        client = ZoneClient.as_user(self.user)
        self.post_resp, self.created_zone = client.post_zone(self.post_model)
        assert self.post_resp.status == 202
        self.addCleanup(self.cleanup_zone, client, self.created_zone.id)
        client.wait_for_zone(self.created_zone.id)

    @classmethod
    def cleanup_zone(cls, client, zone_id):
        try:
            client.delete_zone(zone_id)
        except NotFound:
            pass


class RecordsetFixture(BaseFixture):

    def __init__(self, zone_id, post_model, user='default'):
        super(RecordsetFixture, self).__init__()
        self.zone_id = zone_id
        self.post_model = post_model
        self.user = user

    def _setUp(self):
        super(RecordsetFixture, self)._setUp()
        self._create_recordset()

    def _create_recordset(self):
        client = RecordsetClient.as_user(self.user)
        self.post_resp, self.created_recordset = client.post_recordset(
            self.zone_id, self.post_model)
        assert self.post_resp.status == 202
        self.addCleanup(self.cleanup_recordset, client, self.zone_id,
                        self.created_recordset.id)

        assert self.created_recordset.status == "PENDING"
        assert self.created_recordset.name == self.post_model.name
        assert self.created_recordset.ttl == self.post_model.ttl
        assert self.created_recordset.records == self.post_model.records

        RecordsetClient.as_user('default').wait_for_recordset(
            self.zone_id, self.created_recordset.id)

    @classmethod
    def cleanup_recordset(cls, client, zone_id, recordset_id):
        try:
            client.delete_recordset(zone_id, recordset_id)
        except NotFound:
            pass


class PoolFixture(BaseFixture):

    def __init__(self, post_model=None, user='admin'):
        super(PoolFixture, self).__init__()
        self.post_model = post_model or datagen.random_pool_data()
        self.user = user

    def _setUp(self):
        super(PoolFixture, self)._setUp()
        self._create_pool()

    def _create_pool(self):
        client = PoolClient.as_user(self.user)
        self.post_resp, self.created_pool = client.post_pool(self.post_model)
        assert self.post_resp.status == 201
        self.addCleanup(self.cleanup_pool, client, self.created_pool.id)

    @classmethod
    def cleanup_pool(cls, client, pool_id):
        try:
            client.delete_pool(pool_id)
        except NotFound:
            pass


class TransferRequestFixture(BaseFixture):

    def __init__(self, zone, post_model=None, user='default',
                 target_user='alt'):
        """Assuming the zone is being transferred between the two users, this
        fixture will ensure that zone is deleted by trying to delete the zone
        as each user.
        """
        self.zone = zone
        self.post_model = post_model or datagen.random_transfer_request_data()
        self.user = user
        self.target_user = target_user

    def _setUp(self):
        super(TransferRequestFixture, self)._setUp()
        self._create_transfer_request()

    def _create_transfer_request(self):
        client = TransferRequestClient.as_user(self.user)
        self.post_resp, self.transfer_request = client \
            .post_transfer_request(self.zone.id, self.post_model)
        assert self.post_resp.status == 201
        self.addCleanup(self.cleanup_transfer_request, client,
                        self.transfer_request.id)
        self.addCleanup(ZoneFixture.cleanup_zone,
                        ZoneClient.as_user(self.user), self.zone.id)
        self.addCleanup(ZoneFixture.cleanup_zone,
                        ZoneClient.as_user(self.target_user), self.zone.id)

    @classmethod
    def cleanup_transfer_request(self, client, transfer_id):
        try:
            client.delete_transfer_request(transfer_id)
        except NotFound:
            pass


class BlacklistFixture(BaseFixture):

    def __init__(self, post_model=None, user='admin'):
        super(BlacklistFixture, self).__init__()
        self.post_model = post_model or datagen.random_blacklist_data()
        self.user = user

    def _setUp(self):
        super(BlacklistFixture, self)._setUp()
        self._create_blacklist()

    def _create_blacklist(self):
        client = BlacklistClient.as_user(self.user)
        self.post_resp, self.created_blacklist = client.post_blacklist(
            self.post_model)
        assert self.post_resp.status == 201
        self.addCleanup(self.cleanup_blacklist, client,
                        self.created_blacklist.id)

    @classmethod
    def cleanup_blacklist(cls, client, blacklist_id):
        try:
            client.delete_blacklist(blacklist_id)
        except NotFound:
            pass


class TLDFixture(BaseFixture):

    def __init__(self, post_model=None, user='admin'):
        super(TLDFixture, self).__init__()
        self.post_model = post_model or datagen.random_tld_data()
        self.user = user

    def _setUp(self):
        super(TLDFixture, self)._setUp()
        self._create_tld()

    def _create_tld(self):
        client = TLDClient.as_user(self.user)
        self.post_resp, self.created_tld = client.post_tld(self.post_model)
        assert self.post_resp.status == 201
        self.addCleanup(self.cleanup_tld, client, self.created_tld.id)

    @classmethod
    def cleanup_tld(cls, client, tld_id):
        try:
            client.delete_tld(tld_id)
        except NotFound:
            pass
