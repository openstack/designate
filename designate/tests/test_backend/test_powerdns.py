# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Author: Artom Lifshitz <artom.lifshitz@enovance.com>
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

import os

from mock import MagicMock

from designate import tests
from designate.tests import DatabaseFixture
from designate.tests.test_backend import BackendTestMixin
from designate import utils


# impl_powerdns needs to register its options before being instanciated.
# Import it and pretend to use it to avoid flake8 unused import errors.
from designate.backend import impl_powerdns
impl_powerdns

REPOSITORY = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                          '..', '..',
                                          'backend', 'impl_powerdns',
                                          'migrate_repo'))


class PowerDNSBackendTestCase(tests.TestCase, BackendTestMixin):

    def get_tsigkey_fixture(self):
        return super(PowerDNSBackendTestCase, self).get_tsigkey_fixture(
            values={
                'id': utils.generate_uuid()
            }
        )

    def get_server_fixture(self):
        return super(PowerDNSBackendTestCase, self).get_server_fixture(
            values={
                'id': utils.generate_uuid()
            }
        )

    def get_domain_fixture(self):
        return super(PowerDNSBackendTestCase, self).get_domain_fixture(
            values={
                'id': utils.generate_uuid(),
                'ttl': 42,
                'serial': 42,
                'refresh': 42,
                'retry': 42,
                'expire': 42,
                'minimum': 42,
            }
        )

    def setUp(self):
        super(PowerDNSBackendTestCase, self).setUp()
        self.db_fixture = DatabaseFixture.get_fixture(REPOSITORY)
        self.useFixture(self.db_fixture)
        self.config(backend_driver='powerdns', group='service:agent')
        self.config(connection=self.db_fixture.url,
                    group='backend:powerdns')
        self.backend = self.get_backend_driver()
        self.backend.start()
        # Since some CRUD methods in impl_powerdns call central's find_servers
        # method, mock it up to return our fixture.
        self.backend.central_service.find_servers = MagicMock(
            return_value=[self.get_server_fixture()])

    def test_create_tsigkey(self):
        context = self.get_context()
        tsigkey = self.get_tsigkey_fixture()
        self.backend.create_tsigkey(context, tsigkey)

    def test_update_tsigkey(self):
        context = self.get_context()
        tsigkey = self.get_tsigkey_fixture()
        self.backend.create_tsigkey(context, tsigkey)
        self.backend.update_tsigkey(context, tsigkey)

    def test_delete_tsigkey(self):
        context = self.get_context()
        tsigkey = self.get_tsigkey_fixture()
        self.backend.create_tsigkey(context, tsigkey)
        self.backend.delete_tsigkey(context, tsigkey)

    def test_create_server(self):
        context = self.get_context()
        server = self.get_server_fixture()
        self.backend.create_server(context, server)

    def test_update_server(self):
        context = self.get_context()
        server = self.get_server_fixture()
        self.backend.create_server(context, server)
        self.backend.update_server(context, server)

    def test_delete_server(self):
        context = self.get_context()
        server = self.get_server_fixture()
        self.backend.create_server(context, server)
        self.backend.delete_server(context, server)

    def test_create_domain(self):
        context = self.get_context()
        server = self.get_server_fixture()
        domain = self.get_domain_fixture()
        self.backend.create_server(context, server)
        self.backend.create_domain(context, domain)

    def test_update_domain(self):
        context = self.get_context()
        server = self.get_server_fixture()
        domain = self.get_domain_fixture()
        self.backend.create_server(context, server)
        self.backend.create_domain(context, domain)
        self.backend.update_domain(context, domain)

    def test_delete_domain(self):
        context = self.get_context()
        server = self.get_server_fixture()
        domain = self.get_domain_fixture()
        self.backend.create_server(context, server)
        self.backend.create_domain(context, domain)
        self.backend.delete_domain(context, domain)
