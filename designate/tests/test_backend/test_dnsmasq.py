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

from designate import tests
from designate.tests.test_backend import BackendTestMixin


class DnsmasqBackendTestCase(tests.TestCase, BackendTestMixin):
    def setUp(self):
        super(DnsmasqBackendTestCase, self).setUp()

        self.config(backend_driver='dnsmasq', group='service:agent')
        self.central_service = self.start_service('central')
        self.backend = self.get_backend_driver()

    def test_write_zonefile(self):
        domain = self.create_domain()

        recordset_one = self.create_recordset(domain, fixture=0)
        recordset_two = self.create_recordset(domain, fixture=1)

        self.create_record(domain, recordset_one, fixture=0)
        self.create_record(domain, recordset_one, fixture=1)

        self.create_record(domain, recordset_two, fixture=0)
        self.create_record(domain, recordset_two, fixture=1)

        self.backend._write_zonefile(domain)
