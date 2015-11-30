# Copyright 2014 Hewlett-Packard Development Company, L.P
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import six
from tempest.api.dns import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest import test


class DnsDomainsTest(base.BaseDnsTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(DnsDomainsTest, cls).setUpClass()
        cls.client = cls.dns_domains_client
        cls.setup_domains = list()
        for i in range(2):
            name = data_utils.rand_name('domain') + '.com.'
            email = data_utils.rand_name('dns') + '@testmail.com'
            _, domain = cls.client.create_zone(name, email)
            cls.setup_domains.append(domain)

    @classmethod
    def tearDownClass(cls):
        for domain in cls.setup_domains:
            cls.client.delete_zone(domain['id'])
        super(DnsDomainsTest, cls).tearDownClass()

    def _delete_domain(self, domain_id):
        self.client.delete_zone(domain_id)
        self.assertRaises(exceptions.NotFound,
                          self.client.get_zone, domain_id)

    @test.attr(type='gate')
    def test_list_domains(self):
        # Get a list of domains
        _, domains = self.client.list_domains()
        # Verify domains created in setup class are in the list
        for domain in self.setup_domains:
            self.assertIn(domain['id'],
                          six.moves.map(lambda x: x['id'], domains))

    @test.attr(type='smoke')
    def test_create_update_get_domain(self):
        # Create Zone
        d_name = data_utils.rand_name('domain') + '.com.'
        d_email = data_utils.rand_name('dns') + '@testmail.com'
        _, domain = self.client.create_zone(name=d_name, email=d_email)
        self.addCleanup(self._delete_domain, domain['id'])
        self.assertEqual(d_name, domain['name'])
        self.assertEqual(d_email, domain['email'])
        # Update Zone with  ttl
        d_ttl = 3600
        _, update_domain = self.client.update_zone(domain['id'],
                                                   ttl=d_ttl)
        self.assertEqual(d_ttl, update_domain['ttl'])
        # Get the details of Zone
        _, get_domain = self.client.get_zone(domain['id'])
        self.assertEqual(update_domain['name'], get_domain['name'])
        self.assertEqual(update_domain['email'], get_domain['email'])
        self.assertEqual(update_domain['ttl'], get_domain['ttl'])
