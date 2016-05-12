# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hp.com>
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

import uuid

from tempest_lib import exceptions

from functionaltests.common import datagen
from functionaltests.api.v2.base import DesignateV2Test
from functionaltests.api.v2.clients.tld_client import TLDClient
from functionaltests.api.v2.fixtures import TLDFixture


class TLDTest(DesignateV2Test):

    def setUp(self):
        super(TLDTest, self).setUp()
        self.ensure_tld_exists('com')
        self.client = TLDClient.as_user('admin')
        self.fixture = self.useFixture(TLDFixture())

    def test_get_tld_404(self):
        self._assert_exception(
            exceptions.NotFound, 'tld_not_found', 404, self.client.get_tld,
            str(uuid.uuid4()))

    def test_update_tld_404(self):
        model = datagen.random_tld_data()
        self._assert_exception(
            exceptions.NotFound, 'tld_not_found', 404, self.client.patch_tld,
            str(uuid.uuid4()), model)

    def test_delete_tld_404(self):
        self._assert_exception(
            exceptions.NotFound, 'tld_not_found', 404, self.client.delete_tld,
            str(uuid.uuid4()))

    def test_get_tld_invalid_uuid(self):
        self._assert_invalid_uuid(self.client.get_tld, 'fooo')

    def test_update_tld_invalid_uuid(self):
        model = datagen.random_tld_data()
        self._assert_invalid_uuid(self.client.patch_tld, 'fooo', model)

    def test_delete_tld_invalid_uuid(self):
        self._assert_invalid_uuid(self.client.get_tld, 'fooo')
