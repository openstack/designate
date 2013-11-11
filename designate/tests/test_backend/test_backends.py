# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
from testscenarios import load_tests_apply_scenarios as load_tests  # noqa
from designate import tests
from designate.tests.test_backend.test_nsd4slave import NSD4Fixture
from designate.tests.test_backend import BackendTestMixin


class BackendTestCase(tests.TestCase, BackendTestMixin):
    scenarios = [
        ('bind9', dict(backend_driver='bind9', group='service:agent')),
        ('dnsmasq', dict(backend_driver='dnsmasq', group='service:agent')),
        ('fake', dict(backend_driver='fake', group='service:agent')),
        ('mysqlbind9', dict(backend_driver='mysqlbind9',
                            group='service:agent')),
        ('nsd4slave', dict(backend_driver='nsd4slave', group='service:agent',
                           server_fixture=NSD4Fixture)),
        ('powerdns', dict(backend_driver='powerdns', group='service:agent'))
    ]

    def setUp(self):
        super(BackendTestCase, self).setUp()
        if hasattr(self, 'server_fixture'):
            self.useFixture(self.server_fixture())
        self.config(backend_driver=self.backend_driver, group=self.group)
